"""
Tests that the chat node sends each provider the model and parameters the model accepts.
The provider SDK clients are replaced with recorders, so no API keys or network are needed.
"""

import sys
import types
from types import SimpleNamespace

import pytest

import backend.nodes.llm.chat as chat_module
from backend.nodes.llm.chat import ChatNode
from backend.utils.model_catalog import get_default_model


class _AnthropicRecorder:
    calls = []

    def __init__(self, api_key=None):
        self.messages = SimpleNamespace(stream=self._stream)

    def _stream(self, **kwargs):
        _AnthropicRecorder.calls.append(kwargs)

        class _Stream:
            text_stream = iter(["Hello", " world"])

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def get_final_message(self):
                return SimpleNamespace(usage=SimpleNamespace(input_tokens=10, output_tokens=5))

        return _Stream()


class _OpenAIRecorder:
    calls = []

    def __init__(self, api_key=None):
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        _OpenAIRecorder.calls.append(kwargs)
        delta = SimpleNamespace(content="Hi")
        return iter([SimpleNamespace(choices=[SimpleNamespace(delta=delta)], usage=None)])


@pytest.fixture(autouse=True)
def stub_clients(monkeypatch):
    _AnthropicRecorder.calls.clear()
    _OpenAIRecorder.calls.clear()
    fake_anthropic = types.ModuleType("anthropic")
    fake_anthropic.Anthropic = _AnthropicRecorder
    monkeypatch.setitem(sys.modules, "anthropic", fake_anthropic)
    monkeypatch.setattr(chat_module, "OpenAI", _OpenAIRecorder)
    monkeypatch.setattr(chat_module, "resolve_api_key", lambda *args, **kwargs: "test-key")


async def _run(config):
    return await ChatNode().execute({"query": "What is RAG?", "context": ""}, config)


@pytest.mark.unit
class TestAnthropic:
    async def test_retired_default_is_upgraded(self):
        result = await _run({"provider": "anthropic", "anthropic_model": "claude-3-5-sonnet-20241022"})
        assert _AnthropicRecorder.calls[0]["model"] == "claude-sonnet-5"
        assert result["model"] == "claude-sonnet-5"
        assert result["response"] == "Hello world"

    async def test_sonnet_5_omits_temperature(self):
        await _run({"provider": "anthropic", "anthropic_model": "claude-sonnet-5", "temperature": 0.2})
        sent = _AnthropicRecorder.calls[0]
        assert "temperature" not in sent
        assert sent["max_tokens"] >= 4000

    async def test_haiku_keeps_temperature(self):
        await _run({"provider": "anthropic", "anthropic_model": "claude-haiku-4-5", "temperature": 0.2,
                    "max_tokens": 300})
        sent = _AnthropicRecorder.calls[0]
        assert sent["temperature"] == 0.2
        assert sent["max_tokens"] == 300

    async def test_no_model_uses_default(self):
        await _run({"provider": "anthropic"})
        assert _AnthropicRecorder.calls[0]["model"] == get_default_model("anthropic")

    async def test_cost_uses_registry_price(self):
        result = await _run({"provider": "anthropic", "anthropic_model": "claude-sonnet-5"})
        # 10 input + 5 output tokens at $2 / $10 per million
        assert result["cost"] == pytest.approx(10 * 2 / 1e6 + 5 * 10 / 1e6)


@pytest.mark.unit
class TestOpenAI:
    async def test_default_model_keeps_temperature(self):
        await _run({"provider": "openai", "temperature": 0.3, "max_tokens": 200})
        sent = _OpenAIRecorder.calls[0]
        assert sent["model"] == "gpt-4o-mini"
        assert sent["temperature"] == 0.3
        assert sent["max_completion_tokens"] == 200

    async def test_reasoning_model_omits_temperature(self):
        await _run({"provider": "openai", "openai_model": "gpt-5.6-sol", "temperature": 0.3, "max_tokens": 200})
        sent = _OpenAIRecorder.calls[0]
        assert "temperature" not in sent and "max_tokens" not in sent
        assert sent["max_completion_tokens"] >= 4000

    async def test_retired_model_is_upgraded(self):
        await _run({"provider": "openai", "openai_model": "o1-mini"})
        assert _OpenAIRecorder.calls[0]["model"] == "gpt-4.1-mini"


@pytest.mark.unit
def test_schema_offers_current_models_and_hides_retired():
    props = ChatNode().get_schema()["properties"]
    anthropic = props["anthropic_model"]["enum"]
    assert anthropic[0] == "claude-fable-5-1"  # current generation first
    assert "claude-3-5-sonnet-20241022" not in anthropic
    assert props["anthropic_model"]["default"] in anthropic
    assert "o1-mini" not in props["openai_model"]["enum"]
    assert props["openai_model"]["default"] in props["openai_model"]["enum"]
    assert props["gemini_model"]["default"] in props["gemini_model"]["enum"]
