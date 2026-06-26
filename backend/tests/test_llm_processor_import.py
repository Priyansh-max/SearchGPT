"""
Regression test (Problem 3 / Problem 1): the LLM processor must import and construct WITHOUT
a GEMINI_API_KEY (lazy init), so the engine, tests, and self-host setup don't fail at import.
The actual Gemini/OpenAI calls still need keys at runtime (NEEDS KEYS) and are not exercised here.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_llm_processor_imports_and_is_lazy_without_keys(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # Fresh import
    for mod in ("services.llm_processor",):
        sys.modules.pop(mod, None)
    from services.llm_processor import llm_processor, LLMProcessor

    assert isinstance(llm_processor, LLMProcessor)
    # Nothing key-dependent should have been built at construction time.
    assert llm_processor.model is None
    assert llm_processor._provider_chain is None
    # Output token cap was raised from the old 2048.
    assert llm_processor._generation_config["max_output_tokens"] >= 8192


def test_ensure_model_raises_clearly_without_key(monkeypatch):
    sys.modules.pop("services.llm_processor", None)
    from services.llm_processor import LLMProcessor

    # Force an empty key AFTER import (module import re-runs load_dotenv, which would
    # otherwise restore a real key from .env). Empty => no network call, clean raise.
    monkeypatch.setenv("GEMINI_API_KEY", "")

    proc = LLMProcessor()
    try:
        proc._ensure_model()
        assert False, "expected ValueError without GEMINI_API_KEY"
    except ValueError as e:
        assert "GEMINI_API_KEY" in str(e)
