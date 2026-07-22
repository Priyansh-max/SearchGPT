"""
Tests that the LLM processor's context builder uses RAG retrieval (Problem 2) and that the
search service imports without a SERPAPI_KEY (Problem 1 import-safety). Offline; no keys.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import settings  # noqa: E402


def test_build_context_selects_relevant_passages(monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDING_MODE", "hashing")  # deterministic, offline
    from services.llm_processor import LLMProcessor

    proc = LLMProcessor()
    sources = [
        {"url": "https://a.com", "title": "A",
         "content": "Quantum computers use qubits and superposition for computation."},
        {"url": "https://b.com", "title": "B",
         "content": "The local bakery sells fresh sourdough bread every morning."},
    ]
    ctx = proc._build_context("how do qubits and superposition work", sources)
    assert "qubits" in ctx.lower()
    assert "https://a.com" in ctx          # provenance preserved for citations


def test_build_context_respects_max_sources(monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDING_MODE", "hashing")
    monkeypatch.setattr(settings, "MAX_SOURCES", 1)
    from services.llm_processor import LLMProcessor

    proc = LLMProcessor()
    sources = [
        {"url": "https://a.com", "title": "A", "content": "alpha alpha alpha"},
        {"url": "https://b.com", "title": "B", "content": "beta beta beta"},
    ]
    ctx = proc._build_context("alpha", sources)
    # only the first source is considered when MAX_SOURCES=1
    assert "https://b.com" not in ctx


def test_serpapi_imports_without_key(monkeypatch):
    monkeypatch.setattr(settings, "SERPAPI_KEY", "", raising=False)
    sys.modules.pop("services.serpapi_searcher", None)
    from services.serpapi_searcher import SerpApiSearcher

    s = SerpApiSearcher()  # must NOT raise
    assert s is not None
