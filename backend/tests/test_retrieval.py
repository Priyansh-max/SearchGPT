"""
Tests for the RAG core (Problem 2): chunking + cosine retrieval.

Uses the zero-dependency HashingEmbedder so ranking is deterministic and offline
(no model download, no API keys).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.retrieval import (  # noqa: E402
    chunk_text,
    estimate_tokens,
    retrieve_relevant_passages,
    HashingEmbedder,
)


# ---------- chunking ----------

def test_chunk_short_text_single_chunk():
    assert chunk_text("a short sentence", chunk_size=800) == ["a short sentence"]


def test_chunk_empty():
    assert chunk_text("", 800) == []
    assert chunk_text(None, 800) == []


def test_chunk_long_text_splits_with_overlap():
    text = " ".join([f"word{i}" for i in range(400)])  # well over 800 chars
    chunks = chunk_text(text, chunk_size=200, overlap=40)
    assert len(chunks) > 1
    # every chunk respects (roughly) the size bound
    assert all(len(c) <= 220 for c in chunks)
    # reconstruction covers the start and end content
    assert chunks[0].startswith("word0")
    assert "word399" in chunks[-1]


def test_estimate_tokens():
    assert estimate_tokens("a" * 400) == 100


# ---------- retrieval ----------

def _sources():
    return [
        {"url": "https://a.com", "title": "A",
         "content": "Photosynthesis lets plants convert sunlight into chemical energy."},
        {"url": "https://b.com", "title": "B",
         "content": "The stock market rallied today as tech shares climbed sharply."},
        {"url": "https://c.com", "title": "C",
         "content": "Quantum computers use qubits and superposition to perform computation."},
    ]


def test_retrieval_ranks_relevant_source_first():
    passages = retrieve_relevant_passages(
        "how do quantum computers work with qubits",
        _sources(),
        HashingEmbedder(),
        chunk_size=800,
    )
    assert passages, "expected at least one passage"
    # the quantum source should rank top by lexical overlap
    assert passages[0].source_url == "https://c.com"


def test_retrieval_respects_token_budget():
    # tiny budget → only the single best passage comes back
    passages = retrieve_relevant_passages(
        "quantum qubits superposition",
        _sources(),
        HashingEmbedder(),
        chunk_size=800,
        token_budget=1,  # forces just one (first is always admitted)
    )
    assert len(passages) == 1
    assert passages[0].source_url == "https://c.com"


def test_retrieval_empty_sources():
    assert retrieve_relevant_passages("anything", [], HashingEmbedder()) == []


def test_passages_carry_provenance_and_score():
    passages = retrieve_relevant_passages(
        "photosynthesis sunlight plants", _sources(), HashingEmbedder()
    )
    top = passages[0]
    assert top.source_url == "https://a.com"
    assert top.source_title == "A"
    assert isinstance(top.score, float)
