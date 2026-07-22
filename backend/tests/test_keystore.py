"""
Tests for the API key store + lifecycle + keystore auth mode (Developers). Offline; no keys.
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from config import settings  # noqa: E402
import services.keystore as ks  # noqa: E402
from services.keystore import KeyStore  # noqa: E402
import api.admin as admin  # noqa: E402
import api.keys as keys_api  # noqa: E402
import api.v1 as v1  # noqa: E402


# ---------- store unit ----------

def test_create_and_validate():
    store = KeyStore()
    raw, rec = store.create("prod")
    assert raw.startswith("sbk_live_")
    assert store.validate(raw).id == rec.id
    # public view never leaks the secret/hash
    pub = rec.public()
    assert "key_hash" not in pub and raw not in str(pub)
    assert pub["prefix"].endswith(raw[-4:])


def test_rotate_invalidates_old_keeps_usage():
    store = KeyStore()
    raw1, rec = store.create("k")
    store.record_use(rec)
    assert rec.usage_count == 1
    raw2 = store.rotate(rec.id)
    assert store.validate(raw1) is None      # old secret dead
    assert store.validate(raw2).id == rec.id  # new secret works
    assert store.get(rec.id).usage_count == 1  # usage history kept


def test_revoke_and_delete():
    store = KeyStore()
    raw, rec = store.create("k")
    assert store.revoke(rec.id) is True
    assert store.validate(raw) is None
    assert store.delete(rec.id) is True
    assert store.get(rec.id) is None


def test_quota():
    store = KeyStore()
    raw, rec = store.create("k", quota=2)
    assert store.over_quota(rec) is False
    store.record_use(rec); store.record_use(rec)
    assert store.over_quota(rec) is True
    assert rec.public()["remaining"] == 0


def test_persistence_roundtrip(tmp_path):
    p = str(tmp_path / "ks.json")
    s1 = KeyStore(path=p)
    raw, rec = s1.create("persisted")
    s2 = KeyStore(path=p)               # reload from disk
    assert s2.validate(raw).id == rec.id


# ---------- management API (admin-gated) ----------

def _admin_client(monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_USER", "boss")
    monkeypatch.setattr(settings, "ADMIN_PASSWORD_HASH", hashlib.sha256(b"pw").hexdigest())
    monkeypatch.setattr(settings, "JWT_SECRET", "secret")
    monkeypatch.setattr(ks, "_store", KeyStore())  # fresh in-memory store
    app = FastAPI()
    app.include_router(admin.router)
    app.include_router(keys_api.router)
    c = TestClient(app)
    token = c.post("/api/admin/login", json={"username": "boss", "password": "pw"}).json()["token"]
    return c, {"Authorization": f"Bearer {token}"}


def test_key_management_requires_admin(monkeypatch):
    monkeypatch.setattr(ks, "_store", KeyStore())
    app = FastAPI(); app.include_router(keys_api.router)
    monkeypatch.setattr(settings, "JWT_SECRET", "secret")
    r = TestClient(app).get("/api/keys")
    assert r.status_code == 401


def test_key_crud_flow(monkeypatch):
    c, hdr = _admin_client(monkeypatch)
    # create
    created = c.post("/api/keys", json={"name": "prod"}, headers=hdr).json()
    assert created["key"].startswith("sbk_live_")
    kid = created["record"]["id"]
    # list (masked, no plaintext)
    listed = c.get("/api/keys", headers=hdr).json()["keys"]
    assert any(k["id"] == kid for k in listed)
    assert all("key" not in k for k in listed)
    # rotate
    rotated = c.post(f"/api/keys/{kid}/rotate", headers=hdr).json()
    assert rotated["key"] != created["key"]
    # revoke
    assert c.delete(f"/api/keys/{kid}", headers=hdr).json()["ok"] is True


# ---------- keystore auth mode on /api/v1/query ----------

async def _fake_search(query, *a, **k):
    return [{"title": "T", "url": "https://x.com", "snippet": "s", "position": 1}]


def _v1_client(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "keystore")
    monkeypatch.setattr(ks, "_store", KeyStore())
    monkeypatch.setattr(v1.web_searcher, "search", _fake_search)
    app = FastAPI(); app.include_router(v1.router)
    return TestClient(app)


def test_keystore_auth_accepts_valid_rejects_revoked(monkeypatch):
    c = _v1_client(monkeypatch)
    raw, rec = ks.get_keystore().create("k")
    ok = c.post("/api/v1/query", json={"mode": "search", "query": "hi"},
                headers={"X-API-Key": raw})
    assert ok.status_code == 200
    ks.get_keystore().revoke(rec.id)
    bad = c.post("/api/v1/query", json={"mode": "search", "query": "hi"},
                 headers={"X-API-Key": raw})
    assert bad.status_code == 401


def test_keystore_auth_enforces_quota(monkeypatch):
    c = _v1_client(monkeypatch)
    raw, rec = ks.get_keystore().create("k", quota=1)
    first = c.post("/api/v1/query", json={"mode": "search", "query": "hi"},
                   headers={"X-API-Key": raw})
    assert first.status_code == 200          # uses the 1 allowed call
    second = c.post("/api/v1/query", json={"mode": "search", "query": "hi"},
                    headers={"X-API-Key": raw})
    assert second.status_code == 429         # quota exceeded
