"""
API key store + lifecycle (Developers section).

Real key management: create (named), list (masked), rotate, revoke, plus per-key usage and
quota. Keys are stored HASHED; the plaintext is shown exactly once at creation/rotation.

Backend: JSON file by default (KEYSTORE_PATH) so it persists for self-host and runs offline.
In-memory when no path is given (tests). A Supabase-backed store can replace this later behind
the same interface without changing callers (NEEDS KEYS).
"""
import hashlib
import json
import logging
import os
import secrets
import threading
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _gen_key() -> str:
    return "sbk_live_" + secrets.token_hex(20)  # sbk_live_ + 40 hex chars


def _prefix(raw: str) -> str:
    # display form: sbk_live_3f9a…a30 (never the full secret)
    return f"{raw[:12]}…{raw[-4:]}"


@dataclass
class ApiKeyRecord:
    id: str
    name: str
    key_hash: str
    prefix: str
    created_at: float
    last_used_at: Optional[float]
    revoked: bool
    usage_count: int
    quota: int  # 0 = unlimited

    def public(self) -> dict:
        """Masked view safe to send to the client (no hash, no secret)."""
        return {
            "id": self.id,
            "name": self.name,
            "prefix": self.prefix,
            "created_at": self.created_at,
            "last_used_at": self.last_used_at,
            "revoked": self.revoked,
            "usage_count": self.usage_count,
            "quota": self.quota,
            "remaining": (max(0, self.quota - self.usage_count) if self.quota else None),
        }


class KeyStore:
    def __init__(self, path: Optional[str] = None, default_quota: int = 0):
        self.path = path
        self.default_quota = default_quota
        self._lock = threading.Lock()
        self._keys: Dict[str, ApiKeyRecord] = {}
        self._hash_index: Dict[str, str] = {}  # key_hash -> id
        self._load()

    # ---- persistence ----
    def _load(self) -> None:
        if not self.path or not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            for rec in raw.get("keys", []):
                r = ApiKeyRecord(**rec)
                self._keys[r.id] = r
                self._hash_index[r.key_hash] = r.id
        except Exception as e:
            logger.warning(f"keystore load failed: {e}")

    def _save(self) -> None:
        if not self.path:
            return
        try:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({"keys": [asdict(r) for r in self._keys.values()]}, f, indent=2)
        except Exception as e:
            logger.warning(f"keystore save failed: {e}")

    # ---- lifecycle ----
    def create(self, name: str, quota: Optional[int] = None) -> Tuple[str, ApiKeyRecord]:
        raw = _gen_key()
        rec = ApiKeyRecord(
            id=secrets.token_hex(8),
            name=(name or "key").strip()[:60],
            key_hash=_hash_key(raw),
            prefix=_prefix(raw),
            created_at=time.time(),
            last_used_at=None,
            revoked=False,
            usage_count=0,
            quota=self.default_quota if quota is None else max(0, quota),
        )
        with self._lock:
            self._keys[rec.id] = rec
            self._hash_index[rec.key_hash] = rec.id
            self._save()
        return raw, rec  # raw shown ONCE

    def list(self) -> List[ApiKeyRecord]:
        with self._lock:
            return list(self._keys.values())

    def get(self, key_id: str) -> Optional[ApiKeyRecord]:
        return self._keys.get(key_id)

    def rotate(self, key_id: str) -> Optional[str]:
        """Issue a new secret for an existing key (keeps name + usage history)."""
        with self._lock:
            rec = self._keys.get(key_id)
            if not rec:
                return None
            self._hash_index.pop(rec.key_hash, None)
            raw = _gen_key()
            rec.key_hash = _hash_key(raw)
            rec.prefix = _prefix(raw)
            rec.revoked = False
            self._hash_index[rec.key_hash] = rec.id
            self._save()
            return raw

    def revoke(self, key_id: str) -> bool:
        with self._lock:
            rec = self._keys.get(key_id)
            if not rec:
                return False
            rec.revoked = True
            self._hash_index.pop(rec.key_hash, None)
            self._save()
            return True

    def delete(self, key_id: str) -> bool:
        with self._lock:
            rec = self._keys.pop(key_id, None)
            if not rec:
                return False
            self._hash_index.pop(rec.key_hash, None)
            self._save()
            return True

    # ---- validation / usage ----
    def validate(self, raw: str) -> Optional[ApiKeyRecord]:
        if not raw:
            return None
        rec = self._keys.get(self._hash_index.get(_hash_key(raw), ""))
        if not rec or rec.revoked:
            return None
        return rec

    def over_quota(self, rec: ApiKeyRecord) -> bool:
        return bool(rec.quota) and rec.usage_count >= rec.quota

    def record_use(self, rec: ApiKeyRecord) -> None:
        with self._lock:
            rec.usage_count += 1
            rec.last_used_at = time.time()
            self._save()


_store: Optional[KeyStore] = None


def get_keystore() -> KeyStore:
    global _store
    if _store is None:
        try:
            from config import settings
            _store = KeyStore(path=settings.KEYSTORE_PATH or None,
                              default_quota=settings.DEFAULT_KEY_QUOTA)
        except Exception:
            _store = KeyStore()
    return _store
