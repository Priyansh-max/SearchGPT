"""
Tests for the multi-user account model: users, shared credit pool, scoped keys, charging.
Offline; no keys.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.accounts import (  # noqa: E402
    LocalAccountStore, credits_for, verify_password, hash_password, VALID_MODES,
)


# ---- users / auth ----

def test_create_user_and_lookup():
    s = LocalAccountStore(monthly_quota=1000)
    u = s.create_user("Me@Example.com", name="Me", password="secret")
    assert u.email == "me@example.com"           # normalized
    assert s.get_by_email("me@example.com").id == u.id
    assert verify_password("secret", u.password_hash)
    assert not verify_password("wrong", u.password_hash)


def test_google_upsert_links_by_email():
    s = LocalAccountStore()
    u1 = s.create_user("x@e.com", name="X")
    u2 = s.upsert_google_user("google-sub-1", "x@e.com", name="X G")
    assert u2.id == u1.id and u2.google_sub == "google-sub-1"   # linked, not duplicated
    u3 = s.upsert_google_user("google-sub-1", "x@e.com")
    assert u3.id == u1.id


# ---- scoped keys ----

def test_create_scoped_key_and_validate():
    s = LocalAccountStore()
    u = s.create_user("a@b.com")
    raw, key = s.create_key(u.id, "limited", ["search", "news"])
    assert set(key.scopes) == {"search", "news"}
    assert s.validate_key(raw).id == key.id
    assert "key_hash" not in key.public()


def test_invalid_scopes_default_to_all():
    s = LocalAccountStore()
    u = s.create_user("a@b.com")
    _, key = s.create_key(u.id, "k", ["bogus"])
    assert set(key.scopes) == set(VALID_MODES)


# ---- charging: scope + shared pool ----

def test_charge_enforces_scope():
    s = LocalAccountStore(monthly_quota=1000)
    u = s.create_user("a@b.com")
    raw, key = s.create_key(u.id, "search-only", ["search"])
    ok, reason, _ = s.charge(key, "analyze", synthesize=False)
    assert not ok and reason == "scope"
    ok2, _, _ = s.charge(key, "search", synthesize=False)
    assert ok2


def test_credits_shared_across_keys():
    s = LocalAccountStore(monthly_quota=10)
    u = s.create_user("a@b.com")
    _, k1 = s.create_key(u.id, "k1", ["search"])
    _, k2 = s.create_key(u.id, "k2", ["search"])
    # search costs 1 each; spend 6 on k1, 4 on k2 -> pool exhausted at 10
    for _ in range(6):
        assert s.charge(k1, "search", False)[0]
    for _ in range(4):
        assert s.charge(k2, "search", False)[0]
    ok, reason, remaining = s.charge(k1, "search", False)
    assert not ok and reason == "credits" and remaining == 0
    assert s.get_user(u.id).credits_used == 10


def test_synthesize_costs_more():
    assert credits_for("search", False) == 1
    assert credits_for("search", True) == 1 + 2
    assert credits_for("analyze", True) == 3 + 2


def test_usage_breakdown_for_graph():
    s = LocalAccountStore(monthly_quota=100)
    u = s.create_user("a@b.com")
    _, k1 = s.create_key(u.id, "k1", ["search"])
    _, k2 = s.create_key(u.id, "k2", ["analyze"])
    s.charge(k1, "search", False)            # 1 credit
    s.charge(k2, "analyze", True)            # 5 credits
    bd = s.usage_breakdown(u.id)
    spent = {row["name"]: row["credits_spent"] for row in bd["per_key"]}
    assert spent["k1"] == 1 and spent["k2"] == 5
    assert bd["account"]["credits_used"] == 6
    assert bd["account"]["credits_remaining"] == 94


def test_monthly_reset(monkeypatch):
    s = LocalAccountStore(monthly_quota=5)
    u = s.create_user("a@b.com")
    _, k = s.create_key(u.id, "k", ["search"])
    for _ in range(5):
        s.charge(k, "search", False)
    assert s.charge(k, "search", False)[0] is False     # exhausted
    # simulate the period rolling over
    s.get_user(u.id).period_start = time.time() - (31 * 24 * 3600)
    assert s.charge(k, "search", False)[0] is True       # reset, allowed again
    assert s.get_user(u.id).credits_used == 1


def test_persistence(tmp_path):
    p = str(tmp_path / "acc.json")
    s1 = LocalAccountStore(path=p)
    u = s1.create_user("a@b.com", password="pw")
    raw, k = s1.create_key(u.id, "k", ["search"])
    s2 = LocalAccountStore(path=p)
    assert s2.get_by_email("a@b.com").id == u.id
    assert s2.validate_key(raw).id == k.id
