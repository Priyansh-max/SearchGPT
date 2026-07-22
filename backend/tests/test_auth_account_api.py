import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import services.accounts as accounts  # noqa: E402
import api.v1 as v1  # noqa: E402
from app import app  # noqa: E402
from config import settings  # noqa: E402


def reset_store(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "SESSION_SECRET", "test-session-secret-long-enough")
    monkeypatch.setattr(settings, "RESEND_API_KEY", "")
    monkeypatch.setattr(settings, "EMAIL_FROM", "")
    monkeypatch.setattr(settings, "ACCOUNT_STORE_BACKEND", "local")
    monkeypatch.setattr(settings, "ACCOUNT_STORE_PATH", str(tmp_path / "accounts.json"))
    monkeypatch.setattr(settings, "ACCOUNT_MONTHLY_CREDITS", 10)
    accounts._store = None


def test_email_code_signin_me_and_create_key(monkeypatch, tmp_path):
    reset_store(monkeypatch, tmp_path)
    c = TestClient(app)

    start = c.post("/api/auth/email/start", json={"email": "me@example.com"})
    assert start.status_code == 200
    code = start.json()["dev_code"]

    r = c.post("/api/auth/email/verify", json={"email": "me@example.com", "code": code})
    assert r.status_code == 200
    token = r.json()["token"]

    me = c.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "me@example.com"

    bad = c.post("/api/auth/email/verify", json={"email": "me@example.com", "code": "000000"})
    assert bad.status_code == 401

    key = c.post(
        "/api/account/keys",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "prod", "scopes": ["search"]},
    )
    assert key.status_code == 200
    assert key.json()["key"].startswith("sbk_live_")

    keys = c.get("/api/account/keys", headers={"Authorization": f"Bearer {token}"})
    assert keys.status_code == 200
    assert keys.json()["keys"][0]["name"] == "prod"


async def fake_search(query, engine="google", num_results=None):
    return [{"title": "T", "url": "https://x.com", "snippet": "s", "position": 1}]


def test_account_key_can_call_query_and_scope_is_enforced(monkeypatch, tmp_path):
    reset_store(monkeypatch, tmp_path)
    monkeypatch.setattr(settings, "AUTH_MODE", "accounts")
    monkeypatch.setattr(v1.web_searcher, "search", fake_search)
    c = TestClient(app)

    start = c.post("/api/auth/email/start", json={"email": "api@example.com"})
    token = c.post(
        "/api/auth/email/verify",
        json={"email": "api@example.com", "code": start.json()["dev_code"]},
    ).json()["token"]
    raw_key = c.post(
        "/api/account/keys",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "search-only", "scopes": ["search"]},
    ).json()["key"]

    ok = c.post(
        "/api/v1/query",
        headers={"X-API-Key": raw_key},
        json={"mode": "search", "query": "hello"},
    )
    assert ok.status_code == 200
    assert ok.json()["meta"]["sources_used"] == 1

    blocked = c.post(
        "/api/v1/query",
        headers={"X-API-Key": raw_key},
        json={"mode": "news", "query": "hello"},
    )
    assert blocked.status_code == 403

def test_email_template_uses_searchbot_defaults_and_code(monkeypatch):
    import api.auth as auth

    class EmailSettings:
        AUTH_BRAND_NAME = "SearchBot"
        AUTH_PUBLIC_URL = "http://localhost:5173"
        FRONTEND_URL = "http://localhost:5173"

    monkeypatch.setattr(auth, "settings", EmailSettings())
    payload = auth._build_email_code_payload("Me@Example.com", "123456")

    assert payload["subject"] == "SearchBot sign-in code: 123456"
    assert "1 2 3 4 5 6" in payload["html"]
    assert "Me@Example.com" in payload["html"]
    assert "http://localhost:5173" in payload["html"]
    assert "Your SearchBot sign-in code is 123456." in payload["text"]


def test_email_template_brand_can_change_later(monkeypatch):
    import api.auth as auth

    class EmailSettings:
        AUTH_BRAND_NAME = "OpenContext"
        AUTH_PUBLIC_URL = "https://opencontext.live"
        FRONTEND_URL = "https://opencontext.live"

    monkeypatch.setattr(auth, "settings", EmailSettings())
    payload = auth._build_email_code_payload("me@example.com", "654321")

    assert payload["subject"] == "OpenContext sign-in code: 654321"
    assert "OpenContext" in payload["html"]
    assert "https://opencontext.live" in payload["text"]


def test_complete_onboarding_endpoint(monkeypatch, tmp_path):
    reset_store(monkeypatch, tmp_path)
    c = TestClient(app)

    start = c.post("/api/auth/email/start", json={"email": "onboard@example.com"})
    token = c.post(
        "/api/auth/email/verify",
        json={"email": "onboard@example.com", "code": start.json()["dev_code"]},
    ).json()["token"]

    r = c.post(
        "/api/account/onboarding",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Onboard User",
            "picture": "https://example.com/me.png",
            "heard_about": "LinkedIn",
            "use_cases": ["Agent web search", "Observability"],
        },
    )
    assert r.status_code == 200
    user = r.json()["user"]
    assert user["onboarding_completed"] is True
    assert user["name"] == "Onboard User"
    assert user["heard_about"] == "LinkedIn"
    assert user["use_cases"] == ["Agent web search", "Observability"]

    me = c.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["onboarding_completed"] is True


def test_signed_in_playground_query_charges_user(monkeypatch, tmp_path):
    reset_store(monkeypatch, tmp_path)
    monkeypatch.setattr(settings, "CACHE_ENABLED", False)
    monkeypatch.setattr(v1.web_searcher, "search", fake_search)
    c = TestClient(app)

    start = c.post("/api/auth/email/start", json={"email": "playground@example.com"})
    token = c.post(
        "/api/auth/email/verify",
        json={"email": "playground@example.com", "code": start.json()["dev_code"]},
    ).json()["token"]

    r = c.post(
        "/api/account/playground/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"mode": "search", "query": "demo query", "options": {"synthesize": False}},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "search"
    assert body["data"]["results"][0]["title"] == "T"
    assert body["meta"]["playground"] is True
    assert body["meta"]["credits_charged"] == 1
    assert body["meta"]["credits_remaining"] == 9

    me = c.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["credits_used"] == 1


def test_anonymous_playground_query_uses_demo_lane(monkeypatch, tmp_path):
    reset_store(monkeypatch, tmp_path)
    monkeypatch.setattr(settings, "CACHE_ENABLED", False)
    monkeypatch.setattr(v1.web_searcher, "search", fake_search)
    c = TestClient(app)

    r = c.post(
        "/api/playground/query",
        json={"mode": "search", "query": "demo query", "options": {"synthesize": False}},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["playground"] is True
    assert body["meta"]["tier"] == "demo"
    assert "credits_charged" not in body["meta"]


def test_anonymous_playground_busy_message(monkeypatch, tmp_path):
    reset_store(monkeypatch, tmp_path)
    import services.concurrency as concurrency

    monkeypatch.setattr(
        concurrency,
        "_manager",
        concurrency.ConcurrencyManager(signedin_slots=1, demo_slots=0),
    )
    c = TestClient(app)

    r = c.post(
        "/api/playground/query",
        json={"mode": "search", "query": "busy demo", "options": {"synthesize": False}},
    )

    assert r.status_code == 429
    assert r.json()["detail"] == "Demo is at capacity right now. Try again in a minute, or sign in for priority access."


def test_image_scrape_query_uses_image_search(monkeypatch, tmp_path):
    reset_store(monkeypatch, tmp_path)
    monkeypatch.setattr(settings, "CACHE_ENABLED", False)

    async def fail_search(*args, **kwargs):
        raise AssertionError("normal web search should not run for image scrape intent")

    async def fake_images(query, num_images=4):
        return [{
            "title": "Fresh apple fruit",
            "image": "https://images.example.com/apple.jpg",
            "thumbnail": "https://images.example.com/apple-thumb.jpg",
            "source_url": "https://example.com/apple",
            "source": "Example Images",
        }]

    import services.playground as playground
    monkeypatch.setattr(v1.web_searcher, "search", fail_search)
    monkeypatch.setattr(playground.serpapi_searcher, "search_images", fake_images)
    c = TestClient(app)

    r = c.post(
        "/api/playground/query",
        json={"mode": "scrape", "query": "can you scrape images of an apple for me", "options": {"synthesize": True}},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "scrape"
    assert body["data"]["image_query"] == "apple fruit"
    assert body["data"]["images"][0]["image"].endswith("apple.jpg")
    assert body["data"]["sources"][0]["images"][0]["url"].endswith("apple.jpg")
    assert body["meta"]["image_scrape"] is True
    assert body["meta"]["synthesized"] is False

