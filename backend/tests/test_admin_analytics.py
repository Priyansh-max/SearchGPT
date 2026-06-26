"""
Tests for analytics aggregation + the server-side admin gate (Problem 5). Offline; no keys.
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from config import settings  # noqa: E402
import api.admin as admin  # noqa: E402
from services.analytics import Event, aggregate, hash_ip  # noqa: E402


def make_client():
    app = FastAPI()
    app.include_router(admin.router)
    return TestClient(app)


def configure(monkeypatch, pw="pw"):
    monkeypatch.setattr(settings, "ADMIN_USER", "boss")
    monkeypatch.setattr(settings, "ADMIN_PASSWORD_HASH", hashlib.sha256(pw.encode()).hexdigest())
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret")


# ---------- aggregation ----------

def test_aggregate_counts():
    evts = [
        Event(created_at=1.0, mode="search", provider="gemini", cached=False,
              latency_ms=100, identity_type="api_key", identity_id="k1"),
        Event(created_at=1.0, mode="search", provider="openai", cached=True,
              latency_ms=0, identity_type="api_key", identity_id="k1"),
        Event(created_at=1.0, mode="analyze", provider="gemini", cached=False,
              latency_ms=200, identity_type="anonymous", identity_id="c1"),
    ]
    agg = aggregate(evts)
    assert agg["total"] == 3
    assert agg["by_mode"]["search"] == 2
    assert agg["by_provider"]["gemini"] == 2
    assert agg["per_key_usage"]["k1"] == 2
    assert 0 < agg["cache_hit_rate"] < 1


def test_hash_ip_is_not_raw():
    h = hash_ip("203.0.113.7")
    assert h and "203.0.113.7" not in h and len(h) == 16
    assert hash_ip("") == ""


# ---------- admin gate ----------

def test_login_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_USER", "")
    monkeypatch.setattr(settings, "ADMIN_PASSWORD_HASH", "")
    monkeypatch.setattr(settings, "JWT_SECRET", "")
    r = make_client().post("/api/admin/login", json={"username": "x", "password": "y"})
    assert r.status_code == 503


def test_login_wrong_creds(monkeypatch):
    configure(monkeypatch)
    r = make_client().post("/api/admin/login", json={"username": "boss", "password": "WRONG"})
    assert r.status_code == 401


def test_analytics_requires_token(monkeypatch):
    configure(monkeypatch)
    r = make_client().get("/api/admin/analytics/summary")
    assert r.status_code == 401


def test_login_then_access_analytics(monkeypatch):
    configure(monkeypatch)
    c = make_client()
    r = c.post("/api/admin/login", json={"username": "boss", "password": "pw"})
    assert r.status_code == 200
    token = r.json()["token"]

    r2 = c.get("/api/admin/analytics/summary", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert "total" in r2.json()


def test_tampered_token_rejected(monkeypatch):
    configure(monkeypatch)
    c = make_client()
    token = c.post("/api/admin/login", json={"username": "boss", "password": "pw"}).json()["token"]
    bad = token[:-2] + ("aa" if not token.endswith("aa") else "bb")
    r = c.get("/api/admin/analytics/summary", headers={"Authorization": f"Bearer {bad}"})
    assert r.status_code == 401
