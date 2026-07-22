"""
Analytics events recorder (Problem 5).

One append-only event per request. In-memory store by default (and whenever Supabase isn't
configured), so self-host collects nothing unless ANALYTICS_ENABLED is set. A Supabase
write-through can be added later without changing callers (NEEDS KEYS).

Identities: API users by their key id; playground visitors by an anonymous client_id. IPs are
stored HASHED, never raw.
"""
import hashlib
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Event:
    created_at: float
    identity_type: str = "anonymous"   # 'api_key' | 'anonymous'
    identity_id: str = ""
    ip_hash: str = ""
    geo_country: str = ""
    event_type: str = "query"          # 'query' | 'session_start' | 'heartbeat'
    mode: str = ""
    query_text: str = ""
    synthesize: bool = False
    cached: bool = False
    provider: Optional[str] = None
    status: str = "success"
    latency_ms: int = 0
    session_id: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def hash_ip(ip: Optional[str], salt: str = "") -> str:
    if not ip:
        return ""
    return hashlib.sha256((salt + ip).encode()).hexdigest()[:16]


class InMemoryEventStore:
    def __init__(self, max_events: int = 10_000):
        self.max_events = max_events
        self._events: List[Event] = []

    def add(self, event: Event) -> None:
        self._events.append(event)
        if len(self._events) > self.max_events:
            self._events = self._events[-self.max_events:]

    def all(self) -> List[Event]:
        return list(self._events)

    def clear(self) -> None:
        self._events.clear()


def aggregate(events: List[Event]) -> Dict[str, Any]:
    n = len(events)
    by_day: Dict[str, int] = defaultdict(int)
    for e in events:
        # bucket by integer day (caller can format); avoids importing datetime here
        day = int(e.created_at // 86400)
        by_day[str(day)] += 1
    return {
        "total": n,
        "by_mode": dict(Counter(e.mode for e in events if e.mode)),
        "by_provider": dict(Counter(e.provider for e in events if e.provider)),
        "by_identity_type": dict(Counter(e.identity_type for e in events)),
        "per_key_usage": dict(Counter(
            e.identity_id for e in events if e.identity_type == "api_key" and e.identity_id
        )),
        "cache_hit_rate": (sum(1 for e in events if e.cached) / n) if n else 0.0,
        "avg_latency_ms": (sum(e.latency_ms for e in events) / n) if n else 0.0,
        "queries_by_day": dict(by_day),
    }


class AnalyticsRecorder:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.store = InMemoryEventStore()

    def record(self, event: Event) -> None:
        if not self.enabled:
            return
        self.store.add(event)
        # NEEDS KEYS: when SUPABASE_URL/KEY are set, also write-through to Supabase here.

    def aggregate(self) -> Dict[str, Any]:
        return aggregate(self.store.all())

    def clear(self) -> None:
        self.store.clear()


_recorder: Optional[AnalyticsRecorder] = None


def get_recorder() -> AnalyticsRecorder:
    global _recorder
    if _recorder is None:
        try:
            from config import settings
            _recorder = AnalyticsRecorder(enabled=settings.ANALYTICS_ENABLED)
        except Exception:
            _recorder = AnalyticsRecorder(enabled=False)
    return _recorder
