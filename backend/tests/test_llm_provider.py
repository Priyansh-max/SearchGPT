"""
Tests for the LLM fallback chain (Problem 3).

Uses fake providers (no SDKs, no keys). Async tests run via asyncio.run so no
pytest-asyncio plugin is required.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.llm_provider import (  # noqa: E402
    generate_with_fallback,
    ProviderError,
    build_provider_chain,
)


class FakeProvider:
    def __init__(self, name, *, result=None, raises=None, rate_limited=False):
        self.name = name
        self._result = result
        self._raises = raises
        self._rate_limited = rate_limited
        self.calls = 0

    async def generate(self, prompt, *, json_mode=False, max_output_tokens=8192):
        self.calls += 1
        if self._raises is not None:
            raise ProviderError(self._raises, rate_limited=self._rate_limited, provider=self.name)
        return self._result


def run(coro):
    return asyncio.run(coro)


def test_primary_success_no_fallback():
    primary = FakeProvider("gemini", result="answer A")
    secondary = FakeProvider("openai", result="answer B")
    res = run(generate_with_fallback("q", [primary, secondary]))
    assert res.text == "answer A"
    assert res.provider == "gemini"
    assert secondary.calls == 0  # never touched


def test_falls_over_on_rate_limit():
    primary = FakeProvider("gemini", raises="429 quota exceeded", rate_limited=True)
    secondary = FakeProvider("openai", result="fallback answer")
    res = run(generate_with_fallback("q", [primary, secondary]))
    assert res.text == "fallback answer"
    assert res.provider == "openai"
    assert primary.calls == 1 and secondary.calls == 1


def test_falls_over_on_empty_response():
    primary = FakeProvider("gemini", result="   ")  # blocked/empty
    secondary = FakeProvider("openai", result="real answer")
    res = run(generate_with_fallback("q", [primary, secondary]))
    assert res.provider == "openai"


def test_falls_over_on_server_error():
    primary = FakeProvider("gemini", raises="500 internal error")
    secondary = FakeProvider("openai", result="ok")
    res = run(generate_with_fallback("q", [primary, secondary]))
    assert res.provider == "openai"


def test_all_fail_raises():
    primary = FakeProvider("gemini", raises="429", rate_limited=True)
    secondary = FakeProvider("openai", raises="500")
    try:
        run(generate_with_fallback("q", [primary, secondary]))
        assert False, "expected ProviderError"
    except ProviderError:
        pass


def test_no_providers_raises():
    try:
        run(generate_with_fallback("q", []))
        assert False, "expected ProviderError"
    except ProviderError:
        pass


# ---------- chain assembly ----------

def test_chain_excludes_openai_without_key():
    chain = build_provider_chain(gemini_model=object())
    assert [p.name for p in chain] == ["gemini"]


def test_chain_includes_openai_with_key():
    chain = build_provider_chain(gemini_model=object(), openai_api_key="sk-test")
    assert [p.name for p in chain] == ["gemini", "openai"]


def test_chain_gemini_only_when_no_model_no_key():
    assert build_provider_chain() == []
