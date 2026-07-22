"""
Tests for the result cache (Problem 1). Deterministic — uses an injected fake clock,
so expiry is tested without sleeping.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.cache import TTLCache, make_cache_key  # noqa: E402


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, secs):
        self.t += secs


# ---------- key normalization ----------

def test_key_normalizes_whitespace_and_case():
    a = make_cache_key("search", "  Best   Laptops 2026 ")
    b = make_cache_key("search", "best laptops 2026")
    assert a == b


def test_key_varies_by_mode_and_options():
    assert make_cache_key("search", "q") != make_cache_key("scrape", "q")
    assert make_cache_key("search", "q", {"synthesize": True}) != make_cache_key(
        "search", "q", {"synthesize": False}
    )


# ---------- hit / miss / expiry ----------

def test_set_then_get_hit():
    c = TTLCache(default_ttl=100, time_fn=FakeClock())
    c.set("k", {"answer": 42})
    assert c.get("k") == {"answer": 42}


def test_miss_returns_none():
    c = TTLCache(time_fn=FakeClock())
    assert c.get("nope") is None


def test_expiry():
    clock = FakeClock()
    c = TTLCache(default_ttl=10, time_fn=clock)
    c.set("k", "v")
    clock.advance(9)
    assert c.get("k") == "v"      # still fresh
    clock.advance(2)              # now 11 > 10
    assert c.get("k") is None     # expired
    assert len(c) == 0           # and evicted on access


def test_capacity_eviction():
    clock = FakeClock()
    c = TTLCache(default_ttl=100, max_entries=2, time_fn=clock)
    c.set("a", 1, ttl=10)
    c.set("b", 2, ttl=100)
    c.set("c", 3, ttl=100)        # should evict "a" (soonest to expire)
    assert c.get("a") is None
    assert c.get("b") == 2
    assert c.get("c") == 3


def test_clear():
    c = TTLCache(time_fn=FakeClock())
    c.set("k", "v")
    c.clear()
    assert c.get("k") is None
