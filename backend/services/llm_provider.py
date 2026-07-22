"""
LLM provider chain with fallback (Problem 3).

One `generate_with_fallback()` entry point tries providers in order and returns the first
usable answer, so a Gemini rate-limit (or 5xx/timeout/empty/blocked response) transparently
fails over to OpenAI. The caller does its own last-resort non-LLM formatting if everything
here raises.

Fail-over triggers: rate-limit (429), server errors, timeouts, and empty/blocked responses.
On rate-limit we fail over immediately (no slow backoff) — retrying a rate-limited provider in
a couple seconds usually fails again, and we have a working alternative.

Which provider answered is returned in `GenResult.provider` so it can be logged for analytics
(Problem 5).
"""
import logging
from dataclasses import dataclass
from typing import List, Optional, Protocol, Sequence

logger = logging.getLogger(__name__)


class ProviderError(Exception):
    """Raised by a provider when it could not return a usable answer."""

    def __init__(self, message: str, *, rate_limited: bool = False, provider: Optional[str] = None):
        super().__init__(message)
        self.rate_limited = rate_limited
        self.provider = provider


def _short_error(err: Exception, limit: int = 180) -> str:
    text = str(err).replace("\n", " ").strip()
    return text[:limit] + ("..." if len(text) > limit else "")


@dataclass
class GenResult:
    text: str
    provider: str


class LLMProvider(Protocol):
    name: str
    async def generate(self, prompt: str, *, json_mode: bool = False,
                       max_output_tokens: int = 8192) -> str: ...


def _looks_rate_limited(err: Exception) -> bool:
    s = str(err).lower()
    return "429" in s or "rate limit" in s or "quota" in s or "resource exhausted" in s


async def generate_with_fallback(
    prompt: str,
    providers: Sequence[LLMProvider],
    *,
    json_mode: bool = False,
    max_output_tokens: Optional[int] = None,
) -> GenResult:
    """Try each provider in order; return the first non-empty answer. Raise if all fail."""
    if not providers:
        raise ProviderError("no LLM providers configured")

    last_exc: Optional[Exception] = None
    for p in providers:
        try:
            text = await p.generate(prompt, json_mode=json_mode, max_output_tokens=max_output_tokens)
            if text and text.strip():
                return GenResult(text=text, provider=p.name)
            last_exc = ProviderError(f"{p.name} returned empty/blocked response", provider=p.name)
            logger.warning("LLM provider '%s' returned empty/blocked; trying next", p.name)
        except ProviderError as e:
            last_exc = e
            logger.warning("LLM provider '%s' failed (%s); trying next", p.name, _short_error(e))
        except Exception as e:  # SDK-specific errors → normalize
            last_exc = ProviderError(str(e), rate_limited=_looks_rate_limited(e), provider=p.name)
            logger.warning("LLM provider '%s' errored (%s); trying next", p.name, _short_error(e))

    raise last_exc or ProviderError("all providers failed")


# ---------------- concrete providers (lazy; never imported unless used) ----------------

class GeminiProvider:
    name = "gemini"

    def __init__(self, model):
        # `model` is a configured google.generativeai.GenerativeModel
        self.model = model

    async def generate(self, prompt: str, *, json_mode: bool = False,
                       max_output_tokens: Optional[int] = None) -> str:
        try:
            # Only override per-call when needed; otherwise use the model's baked-in
            # generation_config (temperature/top_p/top_k/max_output_tokens).
            cfg = {}
            if max_output_tokens is not None:
                cfg["max_output_tokens"] = max_output_tokens
            if json_mode:
                cfg["response_mime_type"] = "application/json"
            kwargs = {"generation_config": cfg} if cfg else {}
            resp = await self.model.generate_content_async(prompt, **kwargs)
            return getattr(resp, "text", "") or ""
        except Exception as e:
            raise ProviderError(str(e), rate_limited=_looks_rate_limited(e), provider=self.name)


class OpenAIProvider:
    name = "openai"

    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        self.model = model
        self._api_key = api_key
        self._client = None

    def _ensure(self):
        if self._client is None:
            from openai import AsyncOpenAI  # lazy
            self._client = AsyncOpenAI(api_key=self._api_key) if self._api_key else AsyncOpenAI()
        return self._client

    async def generate(self, prompt: str, *, json_mode: bool = False,
                       max_output_tokens: Optional[int] = None) -> str:
        try:
            client = self._ensure()
            kwargs = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_output_tokens or 8192,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            resp = await client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""
        except Exception as e:
            raise ProviderError(str(e), rate_limited=_looks_rate_limited(e), provider=self.name)


def build_provider_chain(*, gemini_model=None, openai_model: Optional[str] = None,
                         openai_api_key: Optional[str] = None) -> List[LLMProvider]:
    """Assemble the ordered chain. OpenAI is included only if a key is configured."""
    chain: List[LLMProvider] = []
    if gemini_model is not None:
        chain.append(GeminiProvider(gemini_model))
    if openai_api_key:
        chain.append(OpenAIProvider(model=openai_model or "gpt-4o-mini", api_key=openai_api_key))
    return chain
