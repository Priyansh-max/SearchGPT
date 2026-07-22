"""
User accounts + shared credit pool + scoped API keys (Developers, multi-user model).

Hosted auth is passwordless: Google OAuth or one-time email codes. Password helpers remain
only for legacy tests/data compatibility, but new auth paths do not accept passwords.
"""
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple

VALID_MODES = ["search", "scrape", "analyze", "news"]
CREDIT_COSTS = {"search": 1, "news": 1, "scrape": 2, "analyze": 3}
SYNTH_SURCHARGE = 2
PERIOD_SECONDS = 30 * 24 * 3600


def credits_for(mode: str, synthesize: bool) -> int:
    return CREDIT_COSTS.get(mode, 1) + (SYNTH_SURCHARGE if synthesize else 0)


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _gen_key() -> str:
    return "sbk_live_" + secrets.token_hex(20)


def _prefix(raw: str) -> str:
    return f"{raw[:12]}...{raw[-4:]}"


def hash_password(pw: str) -> str:
    """Legacy helper. New hosted auth is passwordless."""
    try:
        import bcrypt
        return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
    except Exception:
        salt = secrets.token_hex(8)
        return "sha256$" + salt + "$" + hashlib.sha256((salt + pw).encode()).hexdigest()


def verify_password(pw: str, stored: str) -> bool:
    """Legacy helper. New hosted auth is passwordless."""
    if not stored:
        return False
    if stored.startswith("sha256$"):
        _, salt, digest = stored.split("$", 2)
        return hashlib.sha256((salt + pw).encode()).hexdigest() == digest
    try:
        import bcrypt
        return bcrypt.checkpw(pw.encode(), stored.encode())
    except Exception:
        return False


@dataclass
class User:
    id: str
    email: str
    name: str = ""
    picture: str = ""
    password_hash: Optional[str] = None
    google_sub: Optional[str] = None
    email_verified: bool = False
    heard_about: str = ""
    use_cases: List[str] = field(default_factory=list)
    onboarding_completed: bool = False
    onboarded_at: Optional[float] = None
    created_at: float = 0.0
    monthly_quota: int = 1000
    credits_used: int = 0
    period_start: float = 0.0

    def public(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "picture": self.picture,
            "email_verified": self.email_verified,
            "heard_about": self.heard_about,
            "use_cases": self.use_cases,
            "onboarding_completed": self.onboarding_completed,
            "onboarded_at": self.onboarded_at,
            "monthly_quota": self.monthly_quota,
            "credits_used": self.credits_used,
            "credits_remaining": max(0, self.monthly_quota - self.credits_used),
            "period_start": self.period_start,
        }


@dataclass
class ApiKey:
    id: str
    user_id: str
    name: str
    key_hash: str
    prefix: str
    scopes: List[str]
    created_at: float
    last_used_at: Optional[float] = None
    revoked: bool = False
    usage_count: int = 0
    credits_spent: int = 0

    def public(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "prefix": self.prefix,
            "scopes": self.scopes,
            "created_at": self.created_at,
            "last_used_at": self.last_used_at,
            "revoked": self.revoked,
            "usage_count": self.usage_count,
            "credits_spent": self.credits_spent,
        }


class LocalAccountStore:
    def __init__(self, path: Optional[str] = None, monthly_quota: int = 1000):
        self.path = path
        self.monthly_quota = monthly_quota
        self._lock = threading.Lock()
        self._users: Dict[str, User] = {}
        self._keys: Dict[str, ApiKey] = {}
        self._hash_index: Dict[str, str] = {}
        self._email_codes: Dict[str, dict] = {}
        self._load()

    def _load(self):
        if not self.path or not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for u in data.get("users", []):
                u.setdefault("email_verified", False)
                u.setdefault("heard_about", "")
                u.setdefault("use_cases", [])
                u.setdefault("onboarding_completed", False)
                u.setdefault("onboarded_at", None)
                self._users[u["id"]] = User(**u)
            for k in data.get("keys", []):
                rec = ApiKey(**k)
                self._keys[rec.id] = rec
                if not rec.revoked:
                    self._hash_index[rec.key_hash] = rec.id
            self._email_codes = data.get("email_codes", {})
        except Exception:
            pass

    def _save(self):
        if not self.path:
            return
        try:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({
                    "users": [asdict(u) for u in self._users.values()],
                    "keys": [asdict(k) for k in self._keys.values()],
                    "email_codes": self._email_codes,
                }, f, indent=2)
        except Exception:
            pass

    def create_user(self, email: str, *, name: str = "", picture: str = "",
                    password: Optional[str] = None, google_sub: Optional[str] = None,
                    email_verified: bool = False) -> User:
        u = User(
            id=secrets.token_hex(8),
            email=(email or "").lower().strip(),
            name=name,
            picture=picture,
            password_hash=hash_password(password) if password else None,
            google_sub=google_sub,
            email_verified=email_verified,
            heard_about="",
            use_cases=[],
            onboarding_completed=False,
            onboarded_at=None,
            created_at=time.time(),
            monthly_quota=self.monthly_quota,
            credits_used=0,
            period_start=time.time(),
        )
        with self._lock:
            self._users[u.id] = u
            self._save()
        return u

    def get_user(self, uid: str) -> Optional[User]:
        return self._users.get(uid)

    def get_by_email(self, email: str) -> Optional[User]:
        email = (email or "").lower().strip()
        return next((u for u in self._users.values() if u.email == email), None)

    def get_by_google(self, sub: str) -> Optional[User]:
        return next((u for u in self._users.values() if u.google_sub == sub), None)

    def upsert_google_user(self, sub: str, email: str, name: str = "", picture: str = "",
                           email_verified: bool = True) -> User:
        u = self.get_by_google(sub) or self.get_by_email(email)
        if u:
            u.google_sub = sub
            if name and not u.name:
                u.name = name
            if picture:
                u.picture = picture
            if email_verified:
                u.email_verified = True
            self._save()
            return u
        return self.create_user(email, name=name, picture=picture, google_sub=sub,
                                email_verified=email_verified)

    def create_email_code(self, email: str, ttl_seconds: int = 600) -> str:
        email = (email or "").lower().strip()
        code = f"{secrets.randbelow(1_000_000):06d}"
        with self._lock:
            self._email_codes[email] = {
                "code_hash": _hash(code),
                "expires_at": time.time() + ttl_seconds,
                "attempts": 0,
            }
            self._save()
        return code

    def verify_email_code(self, email: str, code: str, *, max_attempts: int = 5) -> bool:
        email = (email or "").lower().strip()
        code = (code or "").strip()
        with self._lock:
            rec = self._email_codes.get(email)
            if not rec or rec.get("expires_at", 0) < time.time():
                self._email_codes.pop(email, None)
                self._save()
                return False
            rec["attempts"] = int(rec.get("attempts", 0)) + 1
            if rec["attempts"] > max_attempts:
                self._email_codes.pop(email, None)
                self._save()
                return False
            ok = hmac.compare_digest(rec.get("code_hash", ""), _hash(code))
            if ok:
                self._email_codes.pop(email, None)
            self._save()
            return ok

    def get_or_create_verified_email_user(self, email: str) -> User:
        email = (email or "").lower().strip()
        u = self.get_by_email(email)
        if u:
            u.email_verified = True
            self._save()
            return u
        return self.create_user(email, email_verified=True)

    def update_onboarding(self, user_id: str, name: str, picture: str, heard_about: str, use_cases: List[str]) -> Optional[User]:
        with self._lock:
            u = self._users.get(user_id)
            if not u:
                return None
            u.name = (name or "").strip()[:120]
            u.picture = (picture or "").strip()[:500]
            u.heard_about = (heard_about or "").strip()[:120]
            u.use_cases = [str(x).strip()[:80] for x in (use_cases or []) if str(x).strip()][:12]
            u.onboarding_completed = True
            u.onboarded_at = time.time()
            self._save()
            return u

    def create_key(self, user_id: str, name: str, scopes: List[str]) -> Tuple[str, ApiKey]:
        scopes = [s for s in (scopes or VALID_MODES) if s in VALID_MODES] or list(VALID_MODES)
        raw = _gen_key()
        rec = ApiKey(id=secrets.token_hex(8), user_id=user_id, name=(name or "key").strip()[:60],
                     key_hash=_hash(raw), prefix=_prefix(raw), scopes=scopes,
                     created_at=time.time())
        with self._lock:
            self._keys[rec.id] = rec
            self._hash_index[rec.key_hash] = rec.id
            self._save()
        return raw, rec

    def list_keys(self, user_id: str) -> List[ApiKey]:
        return [k for k in self._keys.values() if k.user_id == user_id]

    def rotate_key(self, key_id: str) -> Optional[str]:
        with self._lock:
            rec = self._keys.get(key_id)
            if not rec:
                return None
            self._hash_index.pop(rec.key_hash, None)
            raw = _gen_key()
            rec.key_hash = _hash(raw)
            rec.prefix = _prefix(raw)
            rec.revoked = False
            self._hash_index[rec.key_hash] = rec.id
            self._save()
            return raw

    def revoke_key(self, key_id: str) -> bool:
        with self._lock:
            rec = self._keys.get(key_id)
            if not rec:
                return False
            rec.revoked = True
            self._hash_index.pop(rec.key_hash, None)
            self._save()
            return True

    def validate_key(self, raw: str) -> Optional[ApiKey]:
        if not raw:
            return None
        rec = self._keys.get(self._hash_index.get(_hash(raw), ""))
        return rec if rec and not rec.revoked else None

    def _maybe_reset(self, u: User):
        if time.time() - (u.period_start or 0) >= PERIOD_SECONDS:
            u.credits_used = 0
            u.period_start = time.time()

    def charge(self, key: ApiKey, mode: str, synthesize: bool) -> Tuple[bool, str, int]:
        if mode not in key.scopes:
            return False, "scope", self._remaining(key.user_id)
        user = self._users.get(key.user_id)
        if not user:
            return False, "no_user", 0
        with self._lock:
            self._maybe_reset(user)
            cost = credits_for(mode, synthesize)
            if user.monthly_quota and user.credits_used + cost > user.monthly_quota:
                return False, "credits", max(0, user.monthly_quota - user.credits_used)
            user.credits_used += cost
            key.usage_count += 1
            key.credits_spent += cost
            key.last_used_at = time.time()
            self._save()
            return True, "ok", max(0, user.monthly_quota - user.credits_used)

    def charge_user(self, user_id: str, mode: str, synthesize: bool) -> Tuple[bool, str, int]:
        user = self._users.get(user_id)
        if not user:
            return False, "no_user", 0
        with self._lock:
            self._maybe_reset(user)
            cost = credits_for(mode, synthesize)
            if user.monthly_quota and user.credits_used + cost > user.monthly_quota:
                return False, "credits", max(0, user.monthly_quota - user.credits_used)
            user.credits_used += cost
            self._save()
            return True, "ok", max(0, user.monthly_quota - user.credits_used)

    def _remaining(self, user_id: str) -> int:
        u = self._users.get(user_id)
        return max(0, u.monthly_quota - u.credits_used) if u else 0

    def usage_breakdown(self, user_id: str) -> dict:
        keys = self.list_keys(user_id)
        user = self._users.get(user_id)
        return {
            "account": user.public() if user else None,
            "per_key": [{"id": k.id, "name": k.name, "credits_spent": k.credits_spent,
                         "usage_count": k.usage_count} for k in keys],
        }


class SupabaseAccountStore:
    """Supabase PostgREST implementation of the account-store interface."""

    def __init__(self, url: str, key: str, monthly_quota: int = 1000, timeout: int = 15):
        import httpx

        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY are required")
        self.monthly_quota = monthly_quota
        self.base_url = url.rstrip("/") + "/rest/v1"
        self._client = httpx.Client(timeout=timeout)
        self._headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, table: str, *, params: Optional[dict] = None,
                 json_body: Optional[dict] = None, prefer: str = ""):
        headers = dict(self._headers)
        if prefer:
            headers["Prefer"] = prefer
        resp = self._client.request(
            method,
            f"{self.base_url}/{table}",
            params=params or {},
            json=json_body,
            headers=headers,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"Supabase {method} {table} failed: {resp.status_code} {resp.text[:200]}")
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    def _select_one(self, table: str, params: dict) -> Optional[dict]:
        rows = self._request("GET", table, params={**params, "select": "*", "limit": "1"}) or []
        return rows[0] if rows else None

    def _insert(self, table: str, body: dict) -> dict:
        rows = self._request("POST", table, json_body=body, prefer="return=representation") or []
        return rows[0] if rows else body

    def _patch(self, table: str, params: dict, body: dict) -> Optional[dict]:
        rows = self._request("PATCH", table, params=params, json_body=body, prefer="return=representation") or []
        return rows[0] if rows else None

    def _delete(self, table: str, params: dict) -> None:
        self._request("DELETE", table, params=params)

    @staticmethod
    def _user_from_row(row: Optional[dict]) -> Optional[User]:
        if not row:
            return None
        return User(
            id=row["id"],
            email=row["email"],
            name=row.get("name") or "",
            picture=row.get("picture") or "",
            password_hash=row.get("password_hash"),
            google_sub=row.get("google_sub"),
            email_verified=bool(row.get("email_verified", False)),
            heard_about=row.get("heard_about") or "",
            use_cases=row.get("use_cases") or [],
            onboarding_completed=bool(row.get("onboarding_completed", False)),
            onboarded_at=row.get("onboarded_at"),
            created_at=float(row.get("created_at") or 0),
            monthly_quota=int(row.get("monthly_quota") or 0),
            credits_used=int(row.get("credits_used") or 0),
            period_start=float(row.get("period_start") or 0),
        )

    @staticmethod
    def _key_from_row(row: Optional[dict]) -> Optional[ApiKey]:
        if not row:
            return None
        scopes = row.get("scopes") or list(VALID_MODES)
        if isinstance(scopes, str):
            try:
                scopes = json.loads(scopes)
            except Exception:
                scopes = list(VALID_MODES)
        return ApiKey(
            id=row["id"],
            user_id=row["user_id"],
            name=row.get("name") or "key",
            key_hash=row["key_hash"],
            prefix=row.get("prefix") or "",
            scopes=list(scopes),
            created_at=float(row.get("created_at") or 0),
            last_used_at=row.get("last_used_at"),
            revoked=bool(row.get("revoked", False)),
            usage_count=int(row.get("usage_count") or 0),
            credits_spent=int(row.get("credits_spent") or 0),
        )

    def create_user(self, email: str, *, name: str = "", picture: str = "",
                    password: Optional[str] = None, google_sub: Optional[str] = None,
                    email_verified: bool = False) -> User:
        now = time.time()
        row = self._insert("account_users", {
            "id": secrets.token_hex(8),
            "email": (email or "").lower().strip(),
            "name": name,
            "picture": picture,
            "password_hash": hash_password(password) if password else None,
            "google_sub": google_sub,
            "email_verified": email_verified,
            "heard_about": "",
            "use_cases": [],
            "onboarding_completed": False,
            "onboarded_at": None,
            "created_at": now,
            "monthly_quota": self.monthly_quota,
            "credits_used": 0,
            "period_start": now,
        })
        return self._user_from_row(row)

    def get_user(self, uid: str) -> Optional[User]:
        return self._user_from_row(self._select_one("account_users", {"id": f"eq.{uid}"}))

    def get_by_email(self, email: str) -> Optional[User]:
        email = (email or "").lower().strip()
        return self._user_from_row(self._select_one("account_users", {"email": f"eq.{email}"}))

    def get_by_google(self, sub: str) -> Optional[User]:
        if not sub:
            return None
        return self._user_from_row(self._select_one("account_users", {"google_sub": f"eq.{sub}"}))

    def upsert_google_user(self, sub: str, email: str, name: str = "", picture: str = "",
                           email_verified: bool = True) -> User:
        u = self.get_by_google(sub) or self.get_by_email(email)
        if u:
            patch = {"google_sub": sub}
            if name and not u.name:
                patch["name"] = name
            if picture:
                patch["picture"] = picture
            if email_verified:
                patch["email_verified"] = True
            row = self._patch("account_users", {"id": f"eq.{u.id}"}, patch)
            return self._user_from_row(row) or self.get_user(u.id)
        return self.create_user(email, name=name, picture=picture, google_sub=sub,
                                email_verified=email_verified)

    def create_email_code(self, email: str, ttl_seconds: int = 600) -> str:
        email = (email or "").lower().strip()
        code = f"{secrets.randbelow(1_000_000):06d}"
        self._request(
            "POST",
            "account_email_codes",
            params={"on_conflict": "email"},
            json_body={
                "email": email,
                "code_hash": _hash(code),
                "expires_at": time.time() + ttl_seconds,
                "attempts": 0,
            },
            prefer="resolution=merge-duplicates,return=minimal",
        )
        return code

    def verify_email_code(self, email: str, code: str, *, max_attempts: int = 5) -> bool:
        email = (email or "").lower().strip()
        code = (code or "").strip()
        rec = self._select_one("account_email_codes", {"email": f"eq.{email}"})
        if not rec or rec.get("expires_at", 0) < time.time():
            self._delete("account_email_codes", {"email": f"eq.{email}"})
            return False
        attempts = int(rec.get("attempts") or 0) + 1
        if attempts > max_attempts:
            self._delete("account_email_codes", {"email": f"eq.{email}"})
            return False
        ok = hmac.compare_digest(rec.get("code_hash", ""), _hash(code))
        if ok:
            self._delete("account_email_codes", {"email": f"eq.{email}"})
        else:
            self._patch("account_email_codes", {"email": f"eq.{email}"}, {"attempts": attempts})
        return ok

    def get_or_create_verified_email_user(self, email: str) -> User:
        email = (email or "").lower().strip()
        u = self.get_by_email(email)
        if u:
            row = self._patch("account_users", {"id": f"eq.{u.id}"}, {"email_verified": True})
            return self._user_from_row(row) or self.get_user(u.id)
        return self.create_user(email, email_verified=True)

    def update_onboarding(self, user_id: str, name: str, picture: str, heard_about: str, use_cases: List[str]) -> Optional[User]:
        patch = {
            "name": (name or "").strip()[:120],
            "picture": (picture or "").strip()[:500],
            "heard_about": (heard_about or "").strip()[:120],
            "use_cases": [str(x).strip()[:80] for x in (use_cases or []) if str(x).strip()][:12],
            "onboarding_completed": True,
            "onboarded_at": time.time(),
        }
        row = self._patch("account_users", {"id": f"eq.{user_id}"}, patch)
        return self._user_from_row(row) or self.get_user(user_id)

    def create_key(self, user_id: str, name: str, scopes: List[str]) -> Tuple[str, ApiKey]:
        scopes = [s for s in (scopes or VALID_MODES) if s in VALID_MODES] or list(VALID_MODES)
        raw = _gen_key()
        row = self._insert("account_api_keys", {
            "id": secrets.token_hex(8),
            "user_id": user_id,
            "name": (name or "key").strip()[:60],
            "key_hash": _hash(raw),
            "prefix": _prefix(raw),
            "scopes": scopes,
            "created_at": time.time(),
            "revoked": False,
            "usage_count": 0,
            "credits_spent": 0,
        })
        return raw, self._key_from_row(row)

    def list_keys(self, user_id: str) -> List[ApiKey]:
        rows = self._request(
            "GET",
            "account_api_keys",
            params={"user_id": f"eq.{user_id}", "select": "*", "order": "created_at.desc"},
        ) or []
        return [self._key_from_row(r) for r in rows]

    def rotate_key(self, key_id: str) -> Optional[str]:
        if not self._select_one("account_api_keys", {"id": f"eq.{key_id}"}):
            return None
        raw = _gen_key()
        self._patch("account_api_keys", {"id": f"eq.{key_id}"}, {
            "key_hash": _hash(raw),
            "prefix": _prefix(raw),
            "revoked": False,
        })
        return raw

    def revoke_key(self, key_id: str) -> bool:
        if not self._select_one("account_api_keys", {"id": f"eq.{key_id}"}):
            return False
        self._patch("account_api_keys", {"id": f"eq.{key_id}"}, {"revoked": True})
        return True

    def validate_key(self, raw: str) -> Optional[ApiKey]:
        if not raw:
            return None
        row = self._select_one("account_api_keys", {"key_hash": f"eq.{_hash(raw)}", "revoked": "eq.false"})
        return self._key_from_row(row)

    def _maybe_reset(self, user: User) -> User:
        if time.time() - (user.period_start or 0) < PERIOD_SECONDS:
            return user
        row = self._patch("account_users", {"id": f"eq.{user.id}"}, {
            "credits_used": 0,
            "period_start": time.time(),
        })
        return self._user_from_row(row) or self.get_user(user.id)

    def charge(self, key: ApiKey, mode: str, synthesize: bool) -> Tuple[bool, str, int]:
        if mode not in key.scopes:
            return False, "scope", self._remaining(key.user_id)
        user = self.get_user(key.user_id)
        if not user:
            return False, "no_user", 0
        user = self._maybe_reset(user)
        cost = credits_for(mode, synthesize)
        if user.monthly_quota and user.credits_used + cost > user.monthly_quota:
            return False, "credits", max(0, user.monthly_quota - user.credits_used)
        now = time.time()
        self._patch("account_users", {"id": f"eq.{user.id}"}, {"credits_used": user.credits_used + cost})
        self._patch("account_api_keys", {"id": f"eq.{key.id}"}, {
            "usage_count": key.usage_count + 1,
            "credits_spent": key.credits_spent + cost,
            "last_used_at": now,
        })
        return True, "ok", max(0, user.monthly_quota - user.credits_used - cost)

    def charge_user(self, user_id: str, mode: str, synthesize: bool) -> Tuple[bool, str, int]:
        user = self.get_user(user_id)
        if not user:
            return False, "no_user", 0
        user = self._maybe_reset(user)
        cost = credits_for(mode, synthesize)
        if user.monthly_quota and user.credits_used + cost > user.monthly_quota:
            return False, "credits", max(0, user.monthly_quota - user.credits_used)
        self._patch("account_users", {"id": f"eq.{user.id}"}, {"credits_used": user.credits_used + cost})
        return True, "ok", max(0, user.monthly_quota - user.credits_used - cost)

    def _remaining(self, user_id: str) -> int:
        u = self.get_user(user_id)
        return max(0, u.monthly_quota - u.credits_used) if u else 0

    def usage_breakdown(self, user_id: str) -> dict:
        keys = self.list_keys(user_id)
        user = self.get_user(user_id)
        return {
            "account": user.public() if user else None,
            "per_key": [{"id": k.id, "name": k.name, "credits_spent": k.credits_spent,
                         "usage_count": k.usage_count} for k in keys],
        }

_store: Optional[object] = None


def get_account_store():
    global _store
    if _store is None:
        from config import settings
        backend = (getattr(settings, "ACCOUNT_STORE_BACKEND", "local") or "local").lower()
        if backend == "supabase":
            _store = SupabaseAccountStore(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY,
                monthly_quota=settings.ACCOUNT_MONTHLY_CREDITS,
            )
        else:
            _store = LocalAccountStore(path=settings.ACCOUNT_STORE_PATH or None,
                                       monthly_quota=settings.ACCOUNT_MONTHLY_CREDITS)
    return _store