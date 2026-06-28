"""
User accounts + shared credit pool + scoped API keys (Developers, multi-user model).

Replaces the single-owner keystore for the hosted model:
- A signed-in USER has a monthly credit allowance shared across ALL their keys.
- Each API KEY carries SCOPES (which of the 4 modes it may call) and tracks how many credits
  it has spent (for the per-key graph). Usage deducts from the account pool, not the key.

Storage is abstracted: LocalAccountStore (JSON file / in-memory) for self-host + dev and tests;
a SupabaseStore with the same interface is added when Supabase creds are provided (NEEDS KEYS).
Auth (Google OAuth / email+password) lives in the auth API layer; this module is pure data.
"""
import hashlib
import json
import os
import secrets
import threading
import time
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple

VALID_MODES = ["search", "scrape", "analyze", "news"]

# Credit cost per call (configurable). Synthesize adds a surcharge (LLM tokens).
CREDIT_COSTS = {"search": 1, "news": 1, "scrape": 2, "analyze": 3}
SYNTH_SURCHARGE = 2
PERIOD_SECONDS = 30 * 24 * 3600  # ~monthly window


def credits_for(mode: str, synthesize: bool) -> int:
    return CREDIT_COSTS.get(mode, 1) + (SYNTH_SURCHARGE if synthesize else 0)


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _gen_key() -> str:
    return "sbk_live_" + secrets.token_hex(20)


def _prefix(raw: str) -> str:
    return f"{raw[:12]}…{raw[-4:]}"


def hash_password(pw: str) -> str:
    """bcrypt if available, else salted sha256 fallback (prefixed so verify can tell)."""
    try:
        import bcrypt
        return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
    except Exception:
        salt = secrets.token_hex(8)
        return "sha256$" + salt + "$" + hashlib.sha256((salt + pw).encode()).hexdigest()


def verify_password(pw: str, stored: str) -> bool:
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
    created_at: float = 0.0
    monthly_quota: int = 1000
    credits_used: int = 0
    period_start: float = 0.0

    def public(self) -> dict:
        return {
            "id": self.id, "email": self.email, "name": self.name, "picture": self.picture,
            "monthly_quota": self.monthly_quota, "credits_used": self.credits_used,
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
            "id": self.id, "name": self.name, "prefix": self.prefix, "scopes": self.scopes,
            "created_at": self.created_at, "last_used_at": self.last_used_at,
            "revoked": self.revoked, "usage_count": self.usage_count,
            "credits_spent": self.credits_spent,
        }


class LocalAccountStore:
    def __init__(self, path: Optional[str] = None, monthly_quota: int = 1000):
        self.path = path
        self.monthly_quota = monthly_quota
        self._lock = threading.Lock()
        self._users: Dict[str, User] = {}
        self._keys: Dict[str, ApiKey] = {}
        self._hash_index: Dict[str, str] = {}  # key_hash -> key_id
        self._load()

    # ---- persistence ----
    def _load(self):
        if not self.path or not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for u in data.get("users", []):
                self._users[u["id"]] = User(**u)
            for k in data.get("keys", []):
                rec = ApiKey(**k)
                self._keys[rec.id] = rec
                if not rec.revoked:
                    self._hash_index[rec.key_hash] = rec.id
        except Exception:
            pass

    def _save(self):
        if not self.path:
            return
        try:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({"users": [asdict(u) for u in self._users.values()],
                           "keys": [asdict(k) for k in self._keys.values()]}, f, indent=2)
        except Exception:
            pass

    # ---- users ----
    def create_user(self, email: str, *, name: str = "", picture: str = "",
                    password: Optional[str] = None, google_sub: Optional[str] = None) -> User:
        u = User(
            id=secrets.token_hex(8), email=email.lower().strip(), name=name, picture=picture,
            password_hash=hash_password(password) if password else None,
            google_sub=google_sub, created_at=time.time(),
            monthly_quota=self.monthly_quota, credits_used=0, period_start=time.time(),
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

    def upsert_google_user(self, sub: str, email: str, name: str = "", picture: str = "") -> User:
        u = self.get_by_google(sub) or self.get_by_email(email)
        if u:
            u.google_sub = sub
            if name and not u.name:
                u.name = name
            if picture:
                u.picture = picture
            self._save()
            return u
        return self.create_user(email, name=name, picture=picture, google_sub=sub)

    def _maybe_reset(self, u: User):
        if time.time() - (u.period_start or 0) >= PERIOD_SECONDS:
            u.credits_used = 0
            u.period_start = time.time()

    # ---- keys ----
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

    # ---- charging (scope + shared credit pool) ----
    def charge(self, key: ApiKey, mode: str, synthesize: bool) -> Tuple[bool, str, int]:
        """Returns (ok, reason, remaining). Enforces scope, then the account credit pool."""
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


_store: Optional[LocalAccountStore] = None


def get_account_store():
    global _store
    if _store is None:
        try:
            from config import settings
            _store = LocalAccountStore(path=settings.ACCOUNT_STORE_PATH or None,
                                       monthly_quota=settings.ACCOUNT_MONTHLY_CREDITS)
        except Exception:
            _store = LocalAccountStore()
    return _store
