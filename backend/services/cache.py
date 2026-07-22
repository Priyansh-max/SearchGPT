"""
Result cache (Problem 1 — highest-leverage free win).

A repeated query within the TTL returns the cached result and skips BOTH the scrape and the
LLM call — cutting latency, cost, and rate-limit pressure. Keyed by (mode + normalized query
+ options), so semantically identical requests collide.

In-memory + thread-safe by default (fine for a single engine box and for self-host). The clock
is injectable so expiry is testable without sleeping. A Supabase-backed implementation can be
added later for multi-box hosted deployments without changing callers.
"""
import hashlib
import json
import re
import threading
import time
from typing import Any, Callable, Optional


def make_cache_key(mode: str, query: str, options: Optional[dict] = None) -> str:
    """Stable key from mode + normalized query + sorted options."""
    norm_query = re.sub(r"\s+", " ", (query or "").strip().lower())
    payload = {
        "mode": (mode or "").lower(),
        "query": norm_query,
        "options": options or {},
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


class TTLCache:
    def __init__(
        self,
        default_ttl: int = 3600,
        max_entries: int = 1000,
        *,
        time_fn: Callable[[], float] = time.monotonic,
    ):
        self.default_ttl = default_ttl
        self.max_entries = max_entries
        self._time = time_fn
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if self._time() >= expires_at:
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = self.default_ttl if ttl is None else ttl
        with self._lock:
            # simple capacity guard: drop the soonest-to-expire entry
            if key not in self._store and len(self._store) >= self.max_entries:
                oldest = min(self._store, key=lambda k: self._store[k][0])
                self._store.pop(oldest, None)
            self._store[key] = (self._time() + ttl, value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)


# Module-level instance, configured lazily from settings to avoid import-time coupling.
_default_cache: Optional[TTLCache] = None


def get_cache() -> TTLCache:
    global _default_cache
    if _default_cache is None:
        try:
            from config import settings
            ttl = settings.CACHE_TTL
        except Exception:
            ttl = 3600
        _default_cache = TTLCache(default_ttl=ttl)
    return _default_cache
