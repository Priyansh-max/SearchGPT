"""
TestClient tests for the single Data API endpoint (Problem 4).

Service singletons are monkeypatched with async fakes, so no keys / network / LLM calls.
Covers: auth modes, envelope shape, data-only-skips-LLM, synthesize adds answer, and caching.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from config import settings  # noqa: E402
import api.v1 as v1  # noqa: E402


def make_client():
    app = FastAPI()
    app.include_router(v1.router)
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_cache():
    v1.get_cache().clear()
    yield
    v1.get_cache().clear()


# ---------- fakes ----------

async def fake_search(query, *a, **k):
    return [{"title": "T1", "url": "https://x.com", "snippet": "snippet", "position": 1}]


class LLMCallSpy:
    def __init__(self):
        self.called = False

    async def __call__(self, *a, **k):
        self.called = True
        return "SYNTHESIZED ANSWER"


# ---------- auth ----------

def test_static_auth_rejects_missing_key(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "static")
    monkeypatch.setattr(settings, "API_KEY", "secret123")
    monkeypatch.setattr(v1.web_searcher, "search", fake_search)
    r = make_client().post("/api/v1/query", json={"mode": "search", "query": "hi"})
    assert r.status_code == 401


def test_static_auth_rejects_wrong_key(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "static")
    monkeypatch.setattr(settings, "API_KEY", "secret123")
    monkeypatch.setattr(v1.web_searcher, "search", fake_search)
    r = make_client().post("/api/v1/query", json={"mode": "search", "query": "hi"},
                           headers={"X-API-Key": "wrong"})
    assert r.status_code == 401


def test_static_auth_accepts_good_key(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "static")
    monkeypatch.setattr(settings, "API_KEY", "secret123")
    monkeypatch.setattr(v1.web_searcher, "search", fake_search)
    r = make_client().post("/api/v1/query", json={"mode": "search", "query": "hi"},
                           headers={"X-API-Key": "secret123"})
    assert r.status_code == 200


def test_auth_off_allows_no_key(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "off")
    monkeypatch.setattr(v1.web_searcher, "search", fake_search)
    r = make_client().post("/api/v1/query", json={"mode": "search", "query": "hi"})
    assert r.status_code == 200


# ---------- envelope + behavior ----------

def test_envelope_shape_and_data_only_skips_llm(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "off")
    monkeypatch.setattr(v1.web_searcher, "search", fake_search)
    spy = LLMCallSpy()
    monkeypatch.setattr(v1.llm_processor, "process_search_results", spy)

    r = make_client().post("/api/v1/query", json={"mode": "search", "query": "hi"})
    body = r.json()
    assert body["mode"] == "search"
    assert body["query"] == "hi"
    assert "results" in body["data"]
    assert body["meta"]["cached"] is False
    assert body["meta"]["synthesized"] is False
    assert "answer" not in body            # data-only
    assert spy.called is False             # LLM NOT called without synthesize


def test_synthesize_adds_answer_and_calls_llm(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "off")
    monkeypatch.setattr(v1.web_searcher, "search", fake_search)
    spy = LLMCallSpy()
    monkeypatch.setattr(v1.llm_processor, "process_search_results", spy)

    r = make_client().post("/api/v1/query",
                           json={"mode": "search", "query": "hi", "options": {"synthesize": True}})
    body = r.json()
    assert body["answer"] == "SYNTHESIZED ANSWER"
    assert body["meta"]["synthesized"] is True
    assert spy.called is True


def test_invalid_mode_rejected(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "off")
    r = make_client().post("/api/v1/query", json={"mode": "bogus", "query": "hi"})
    assert r.status_code == 400


def test_cache_hit_on_second_call(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "off")
    monkeypatch.setattr(settings, "CACHE_ENABLED", True)

    calls = {"n": 0}

    async def counting_search(query, *a, **k):
        calls["n"] += 1
        return [{"title": "T", "url": "https://x.com", "snippet": "s", "position": 1}]

    monkeypatch.setattr(v1.web_searcher, "search", counting_search)
    client = make_client()

    r1 = client.post("/api/v1/query", json={"mode": "search", "query": "same"})
    r2 = client.post("/api/v1/query", json={"mode": "search", "query": "same"})
    assert r1.json()["meta"]["cached"] is False
    assert r2.json()["meta"]["cached"] is True
    assert calls["n"] == 1                 # second call served from cache, no re-search
