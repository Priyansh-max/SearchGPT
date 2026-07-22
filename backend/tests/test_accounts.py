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


def test_account_store_can_select_supabase_backend(monkeypatch):
    import services.accounts as accounts_module
    from config import settings

    accounts_module._store = None
    monkeypatch.setattr(settings, "ACCOUNT_STORE_BACKEND", "supabase")
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_KEY", "service-role-key")
    monkeypatch.setattr(settings, "ACCOUNT_MONTHLY_CREDITS", 123)

    try:
        store = accounts_module.get_account_store()
        assert isinstance(store, accounts_module.SupabaseAccountStore)
        assert store.monthly_quota == 123
        assert store.base_url == "https://example.supabase.co/rest/v1"
    finally:
        accounts_module._store = None


def test_supabase_backend_requires_credentials(monkeypatch):
    import pytest
    import services.accounts as accounts_module
    from config import settings

    accounts_module._store = None
    monkeypatch.setattr(settings, "ACCOUNT_STORE_BACKEND", "supabase")
    monkeypatch.setattr(settings, "SUPABASE_URL", "")
    monkeypatch.setattr(settings, "SUPABASE_KEY", "")

    try:
        with pytest.raises(ValueError):
            accounts_module.get_account_store()
    finally:
        accounts_module._store = None


def test_update_onboarding_marks_user_complete():
    s = LocalAccountStore(monthly_quota=1000)
    u = s.create_user("a@b.com")
    updated = s.update_onboarding(
        u.id,
        "Ada Lovelace",
        "https://example.com/avatar.png",
        "Twitter",
        ["Deep research", "API access"],
    )
    assert updated.onboarding_completed is True
    assert updated.name == "Ada Lovelace"
    assert updated.picture == "https://example.com/avatar.png"
    assert updated.heard_about == "Twitter"
    assert updated.use_cases == ["Deep research", "API access"]
    assert updated.public()["onboarding_completed"] is True
