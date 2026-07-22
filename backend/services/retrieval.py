"""
Semantic retrieval / RAG core (Problem 2).

Instead of blindly truncating scraped pages, we chunk every source into passages, embed
the passages and the query, and keep only the top passages by cosine similarity until a
token budget is filled. This fixes within-page data loss (the relevant passage survives
no matter where it sits in the page) and keeps the payload small enough for the smallest
model in the fallback chain (gpt-4o-mini, 128k).

Retrieval is ephemeral and in-memory — content is scraped fresh per query, so there is no
vector database to maintain.

Embedders are pluggable (`EMBEDDING_MODE`):
  - "local"   -> sentence-transformers MiniLM (free, no API key; needs the package)
  - "openai"  -> text-embedding-3-small (tiny, cheap; needs OPENAI_API_KEY)
  - "hashing" -> zero-dependency bag-of-words hashing (no model, crude but always works)
If "local" is selected but sentence-transformers isn't installed, we fall back to "hashing"
so the engine still runs.
"""
import logging
import re
import zlib
from dataclasses import dataclass
from typing import List, Sequence

import numpy as np

logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars/token). Avoids a tokenizer dependency."""
    return max(1, len(text) // 4)


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """Split text into ~chunk_size-char passages with overlap, preferring word boundaries."""
    text = re.sub(r"\s+", " ", (text or "")).strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks: List[str] = []
    start, n = 0, len(text)
    while start < n:
        end = min(start + chunk_size, n)
        if end < n:
            # break at the last space in the back half of the window for a cleaner cut
            space = text.rfind(" ", start + chunk_size // 2, end)
            if space != -1:
                end = space
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks


@dataclass
class Passage:
    text: str
    source_url: str
    source_title: str
    score: float = 0.0


def _normalize_rows(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    norms[norms == 0] = 1e-9
    return m / norms


def rank_by_cosine(query_vec: np.ndarray, chunk_matrix: np.ndarray) -> np.ndarray:
    """Return a cosine-similarity score per chunk row against the query vector."""
    q = np.asarray(query_vec, dtype=float).ravel()
    qn = q / (np.linalg.norm(q) or 1e-9)
    cm = _normalize_rows(np.asarray(chunk_matrix, dtype=float))
    return cm @ qn


# ---------------- embedders ----------------

class HashingEmbedder:
    """Zero-dependency bag-of-words hashing embedder. Deterministic (stable crc32 hash).

    Not semantic — purely lexical overlap — but needs nothing beyond numpy, so the engine
    is always runnable and tests are deterministic.
    """

    def __init__(self, dim: int = 256):
        self.dim = dim

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=float)
        for i, t in enumerate(texts):
            for w in re.findall(r"\w+", (t or "").lower()):
                out[i, zlib.crc32(w.encode()) % self.dim] += 1.0
        return out


class LocalEmbedder:
    """sentence-transformers MiniLM. Lazy-loaded so import never fails if absent."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def _ensure(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # lazy
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        model = self._ensure()
        return np.asarray(model.encode(list(texts), show_progress_bar=False), dtype=float)


class OpenAIEmbedder:
    """OpenAI text-embedding-3-small. Lazy client; needs OPENAI_API_KEY."""

    def __init__(self, model: str = "text-embedding-3-small", api_key: str | None = None):
        self.model = model
        self._api_key = api_key
        self._client = None

    def _ensure(self):
        if self._client is None:
            from openai import OpenAI  # lazy
            self._client = OpenAI(api_key=self._api_key) if self._api_key else OpenAI()
        return self._client

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        client = self._ensure()
        resp = client.embeddings.create(model=self.model, input=list(texts))
        return np.asarray([d.embedding for d in resp.data], dtype=float)


def get_embedder(mode: str = "local", *, openai_api_key: str | None = None):
    """Factory. Falls back to hashing if 'local' is requested but unavailable."""
    mode = (mode or "local").lower()
    if mode == "openai":
        return OpenAIEmbedder(api_key=openai_api_key)
    if mode == "hashing":
        return HashingEmbedder()
    # default: local, with graceful fallback
    try:
        import sentence_transformers  # noqa: F401
        return LocalEmbedder()
    except Exception:
        logger.warning("sentence-transformers not installed; falling back to hashing embedder")
        return HashingEmbedder()


# ---------------- retrieval ----------------

def retrieve_relevant_passages(
    query: str,
    sources: List[dict],
    embedder,
    *,
    chunk_size: int = 800,
    overlap: int = 100,
    token_budget: int = 90_000,
) -> List[Passage]:
    """
    Chunk all sources, embed against the query, and return the most relevant passages
    (highest cosine first) until the token budget is filled.

    ``sources`` is a list of dicts with at least ``content``; ``url``/``title`` optional.
    """
    chunks: List[tuple] = []  # (text, url, title)
    for s in sources or []:
        content = s.get("content") or ""
        url = s.get("url", "")
        title = s.get("title", "")
        for c in chunk_text(content, chunk_size, overlap):
            chunks.append((c, url, title))

    if not chunks:
        return []

    texts = [c[0] for c in chunks]
    chunk_vecs = np.asarray(embedder.embed(texts), dtype=float)
    query_vec = np.asarray(embedder.embed([query])[0], dtype=float)
    scores = rank_by_cosine(query_vec, chunk_vecs)

    order = np.argsort(scores)[::-1]
    selected: List[Passage] = []
    used = 0
    for idx in order:
        text, url, title = chunks[int(idx)]
        t = estimate_tokens(text)
        if selected and used + t > token_budget:
            break
        selected.append(
            Passage(text=text, source_url=url, source_title=title, score=float(scores[int(idx)]))
        )
        used += t
    return selected
