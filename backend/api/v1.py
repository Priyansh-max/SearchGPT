"""
Public Data API v1 (Problem 4) — ONE endpoint, modes select the tool.

    POST /api/v1/query
    { "mode": "search|scrape|analyze|news",
      "query": "...",
      "options": { "max_sources": 10, "synthesize": false, "urls": [] } }

Always returns JSON:
    { "mode", "query", "data", "answer"?, "meta": {cached, synthesized, provider, sources_used, link_mode} }

`synthesize` is additive: false => raw `data` only (no LLM); true => also adds an `answer`
(`analyze` mode always synthesizes). Gated by `X-API-Key` honoring settings.AUTH_MODE.
Link mode: if the query contains URLs (or options.urls is set), those URLs are scraped
directly (SSRF-checked) instead of running a web search.
"""
import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from config import settings
from services.cache import get_cache, make_cache_key
from services.analytics import get_recorder, Event, hash_ip
from utils.url_utils import extract_urls, is_safe_url

# Service singletons (all import keyless after the lazy-init work)
from services.web_searcher import web_searcher
from services.content_extractor import content_extractor
from services.llm_processor import llm_processor
from services.news_searcher import NewsSearcher

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["data-api"])

news_searcher = NewsSearcher()
VALID_MODES = {"search", "scrape", "analyze", "news"}


class QueryOptions(BaseModel):
    max_sources: Optional[int] = None
    synthesize: bool = False
    urls: Optional[List[str]] = None


class QueryRequest(BaseModel):
    mode: str = "search"
    query: str = ""
    options: QueryOptions = Field(default_factory=QueryOptions)


async def verify_api_key(x_api_key: Optional[str] = Header(default=None)) -> str:
    """X-API-Key gate honoring AUTH_MODE: off | static | keystore | accounts | supabase.

    Returns an identity string (key id, 'static', or 'anonymous') used for analytics.
    """
    mode = (settings.AUTH_MODE or "static").lower()
    if mode == "off":
        return "anonymous"
    if mode == "static":
        if not settings.API_KEY:  # no key configured -> open (local dev/self-host pre-setup)
            return "anonymous"
        if x_api_key != settings.API_KEY:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")
        return "static"
    if mode == "keystore":
        from services.keystore import get_keystore
        store = get_keystore()
        rec = store.validate(x_api_key or "")
        if not rec:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")
        if store.over_quota(rec):
            raise HTTPException(status_code=429, detail="quota exceeded for this key")
        store.record_use(rec)
        return rec.id  # per-key identity for analytics
    if mode == "accounts":
        from services.accounts import get_account_store
        rec = get_account_store().validate_key(x_api_key or "")
        if not rec:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")
        return rec.id
    if mode == "supabase":
        # NEEDS KEYS: validate against the Supabase api_keys table + quota.
        raise HTTPException(status_code=501, detail="Supabase auth not configured")
    raise HTTPException(status_code=500, detail=f"unknown AUTH_MODE: {mode}")


def _max_sources(options: QueryOptions) -> int:
    req = options.max_sources or settings.MAX_SOURCES
    return max(1, min(req, settings.MAX_SOURCES))


async def _acquire_sources(query: str, options: QueryOptions):
    """Return (sources, link_mode). Link mode scrapes explicit/detected URLs (SSRF-checked);
    otherwise runs a web search and scrapes the results."""
    explicit = options.urls or []
    detected = extract_urls(query)
    targets = explicit + [u for u in detected if u not in explicit]

    if targets:
        safe = [u for u in targets if is_safe_url(u)[0]]
        sources = await content_extractor.extract_multiple_urls(safe[: _max_sources(options)])
        return sources, True

    results = await web_searcher.search(query)
    sources = await content_extractor.extract_from_search_results(results)
    return sources, False


async def run_query(mode: str, query: str, options: QueryOptions, synthesize: bool) -> Dict[str, Any]:
    meta = {"cached": False, "synthesized": False, "provider": None,
            "sources_used": 0, "link_mode": False}

    if mode == "search":
        results = await web_searcher.search(query)
        meta["sources_used"] = len(results)
        out = {"mode": mode, "query": query, "data": {"results": results}, "meta": meta}
        if synthesize:
            out["answer"] = await llm_processor.process_search_results(query, results)
            meta["synthesized"] = True
        return out

    if mode == "news":
        articles = await news_searcher.search(query)
        meta["sources_used"] = len(articles)
        out = {"mode": mode, "query": query, "data": {"articles": articles}, "meta": meta}
        if synthesize:
            out["answer"] = await llm_processor.process_news(query, articles)
            meta["synthesized"] = True
        return out

    # scrape | analyze -> acquire sources (link-mode aware)
    sources, link_mode = await _acquire_sources(query, options)
    meta["link_mode"] = link_mode
    meta["sources_used"] = len(sources)
    data = {"sources": [
        {"url": s.get("url"), "title": s.get("title"), "content": s.get("content"), "image": s.get("image") or s.get("top_image") or "", "images": s.get("images") or []}
        for s in sources
    ]}
    out = {"mode": mode, "query": query, "data": data, "meta": meta}

    if mode == "analyze":
        analysis = await llm_processor.synthesize_information(query, sources)
        out["data"] = analysis                      # summary, key_points, sources
        out["answer"] = analysis.get("summary")
        meta["synthesized"] = True
    elif synthesize:
        out["answer"] = await llm_processor.process_scraped_content(query, sources)
        meta["synthesized"] = True

    return out


@router.post("/query")
async def query_endpoint(req: QueryRequest, request: Request,
                         x_api_key: Optional[str] = Header(default=None),
                         identity: str = Depends(verify_api_key)):
    if req.mode not in VALID_MODES:
        raise HTTPException(status_code=400, detail=f"invalid mode '{req.mode}' (use {sorted(VALID_MODES)})")
    if not req.query and not (req.options.urls):
        raise HTTPException(status_code=400, detail="query is required")

    started = time.time()
    synthesize = req.options.synthesize or req.mode == "analyze"
    if (settings.AUTH_MODE or "static").lower() == "accounts":
        identity = _charge_account_key(x_api_key, req.mode, synthesize)
    key = make_cache_key(req.mode, req.query, {
        "synthesize": synthesize,
        "max_sources": req.options.max_sources,
        "urls": req.options.urls,
    })
    cache = get_cache()

    out = None
    if settings.CACHE_ENABLED:
        hit = cache.get(key)
        if hit is not None:
            out = {**hit, "meta": {**hit.get("meta", {}), "cached": True}}

    if out is None:
        out = await run_query(req.mode, req.query, req.options, synthesize)
        if settings.CACHE_ENABLED:
            cache.set(key, out)

    _record_event(request, identity, req, out, started)
    return out


def _record_event(request, identity, req, out, started) -> None:
    """Lightweight analytics record (no-op unless ANALYTICS_ENABLED). Never fails the request."""
    recorder = get_recorder()
    if not recorder.enabled:
        return
    try:
        meta = out.get("meta", {})
        ip = request.client.host if request.client else ""
        recorder.record(Event(
            created_at=time.time(),
            identity_type="api_key" if identity not in ("anonymous",) else "anonymous",
            identity_id=identity,
            ip_hash=hash_ip(ip),
            event_type="query",
            mode=req.mode,
            query_text=req.query,
            synthesize=bool(meta.get("synthesized")),
            cached=bool(meta.get("cached")),
            provider=meta.get("provider"),
            status="success",
            latency_ms=int((time.time() - started) * 1000),
        ))
    except Exception as e:  # analytics must never break the API
        logger.warning(f"analytics record failed: {e}")


def _charge_account_key(raw_key: Optional[str], mode: str, synthesize: bool) -> str:
    """Enforce hosted account key scopes and shared monthly credits."""
    from services.accounts import get_account_store
    store = get_account_store()
    rec = store.validate_key(raw_key or "")
    if not rec:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    ok, reason, remaining = store.charge(rec, mode, synthesize)
    if ok:
        return rec.id
    if reason == "scope":
        raise HTTPException(status_code=403, detail=f"key is not allowed to use mode '{mode}'")
    if reason == "credits":
        raise HTTPException(status_code=429, detail=f"monthly credits exhausted ({remaining} remaining)")
    raise HTTPException(status_code=401, detail="Invalid API key account")