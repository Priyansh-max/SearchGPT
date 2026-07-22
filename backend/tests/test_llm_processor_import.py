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


def test_configured_gemini_model_skips_model_listing(monkeypatch):
    sys.modules.pop("services.llm_processor", None)
    from services.llm_processor import LLMProcessor
    import services.llm_processor as mod

    class FakeGenAI:
        def __init__(self):
            self.configured = False
            self.listed = False
            self.model_name = None
            self.generation_config = None

        def configure(self, api_key):
            self.configured = api_key == "test-key"

        def list_models(self):
            self.listed = True
            return []

        def GenerativeModel(self, *, model_name, safety_settings, generation_config):
            self.model_name = model_name
            self.generation_config = generation_config
            return object()

    fake = FakeGenAI()
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(mod.settings, "GEMINI_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setattr(mod, "genai", fake)

    proc = LLMProcessor()
    proc._ensure_model()

    assert fake.configured is True
    assert fake.listed is False
    assert fake.model_name == "models/gemini-3.5-flash-lite"
    assert "top_k" not in fake.generation_config

