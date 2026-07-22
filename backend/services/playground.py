"""Shared playground execution for signed-in and anonymous demo lanes."""

import re

from fastapi import HTTPException

from api.v1 import QueryRequest, run_query
from config import settings
from services.accounts import VALID_MODES, credits_for, get_account_store
from services.cache import get_cache, make_cache_key
from services.concurrency import BusyError, get_manager
from services.serpapi_searcher import serpapi_searcher

DEMO_BUSY_MESSAGE = "Demo is at capacity right now. Try again in a minute, or sign in for priority access."
SIGNEDIN_BUSY_MESSAGE = "We are freeing up your workspace. Try again in a few seconds."


def _validate(body: QueryRequest) -> bool:
    if body.mode not in VALID_MODES:
        raise HTTPException(status_code=400, detail=f"invalid mode '{body.mode}'")
    if not body.query and not body.options.urls:
        raise HTTPException(status_code=400, detail="query is required")
    return body.options.synthesize or body.mode == "analyze"


def _is_image_scrape_request(body: QueryRequest) -> bool:
    if body.mode != "scrape" or body.options.urls:
        return False
    query = (body.query or "").lower()
    return bool(re.search(r"\b(scrape|extract|get|find|download|show)\b.*\b(images?|photos?|pictures?)\b", query))


def _image_query_from_scrape(query: str) -> str:
    cleaned = (query or "").lower()
    cleaned = re.sub(r"\b(can you|please|for me|scrape|extract|get|find|download|show|images?|photos?|pictures?|image urls?|of|an|a|the)\b", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        cleaned = query.strip()
    brand_terms = {"iphone", "ipad", "mac", "macbook", "ios", "app store", "apple intelligence", "apple watch"}
    if cleaned == "apple" and not any(term in query.lower() for term in brand_terms):
        cleaned = "apple fruit"
    return cleaned


async def _run_image_scrape(query: str):
    image_query = _image_query_from_scrape(query)
    images = await serpapi_searcher.search_images(image_query, num_images=8)
    sources = [
        {
            "url": item.get("source_url") or "",
            "title": item.get("title") or image_query,
            "content": "",
            "image": item.get("image") or item.get("thumbnail") or "",
            "images": [{
                "url": item.get("image") or item.get("thumbnail") or "",
                "alt": item.get("title") or image_query,
                "source_url": item.get("source_url") or "",
            }],
            "source": item.get("source") or "Google Images",
        }
        for item in images
    ]
    answer = (
        f"Found {len(images)} image results for **{image_query}**. "
        "Use the image previews and export controls below to open, copy, or download the scraped image URLs."
        if images else f"No image results were found for **{image_query}**."
    )
    return {
        "mode": "scrape",
        "query": query,
        "data": {"sources": sources, "images": images, "image_query": image_query},
        "answer": answer,
        "meta": {
            "cached": False,
            "synthesized": False,
            "provider": "serpapi_images",
            "sources_used": len(sources),
            "link_mode": False,
            "image_scrape": True,
        },
    }


async def execute_playground_query(body: QueryRequest, *, tier: str, user=None):
    synthesize = _validate(body)
    image_scrape = _is_image_scrape_request(body)
    if image_scrape:
        synthesize = False
    manager = get_manager()
    busy_message = SIGNEDIN_BUSY_MESSAGE if tier == "signedin" else DEMO_BUSY_MESSAGE

    try:
        async with manager.slot(tier):
            credits_charged = 0
            credits_remaining = None
            if user is not None:
                store = get_account_store()
                ok, reason, remaining = store.charge_user(user.id, body.mode, synthesize)
                if not ok:
                    if reason == "credits":
                        raise HTTPException(status_code=429, detail=f"monthly credits exhausted ({remaining} remaining)")
                    raise HTTPException(status_code=401, detail="invalid account")
                credits_charged = credits_for(body.mode, synthesize)
                credits_remaining = remaining

            key = make_cache_key(body.mode, body.query, {
                "synthesize": synthesize,
                "max_sources": body.options.max_sources,
                "urls": body.options.urls,
                "intent": "image_scrape" if image_scrape else "default",
            })
            cache = get_cache()
            out = None
            if settings.CACHE_ENABLED:
                hit = cache.get(key)
                if hit is not None:
                    out = {**hit, "meta": {**hit.get("meta", {}), "cached": True}}

            if out is None:
                out = await _run_image_scrape(body.query) if image_scrape else await run_query(body.mode, body.query, body.options, synthesize)
                if settings.CACHE_ENABLED:
                    cache.set(key, out)
            if not image_scrape:
                await _attach_playground_images(out, body.query, body.mode, synthesize)

            meta = {
                **out.get("meta", {}),
                "playground": True,
                "tier": "signedin" if user is not None else "demo",
                "lane_stats": manager.stats(),
            }
            if user is not None:
                meta["credits_charged"] = credits_charged
                meta["credits_remaining"] = credits_remaining
            out["meta"] = meta
            return out
    except BusyError as exc:
        raise HTTPException(status_code=429, detail=busy_message) from exc


async def _attach_playground_images(out, query: str, mode: str, synthesize: bool) -> None:
    """Playground-only visual enrichment. Keeps the public /api/v1/query path fast."""
    if not synthesize or mode not in {"search", "news"} or not query:
        return
    data = out.setdefault("data", {})
    if data.get("images"):
        return
    images = await serpapi_searcher.search_images(query, num_images=4)
    if images:
        data["images"] = images
