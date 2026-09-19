"""
Tests for the model registry lifecycle, defaults and request compatibility.
"""

from datetime import date

import pytest

from backend.utils.model_catalog import (
    DEFAULT_MODELS,
    MIN_OUTPUT_TOKENS_FOR_THINKING_MODELS,
    MODEL_LIFECYCLE,
    get_default_model,
    get_model_lifecycle,
    llm_request_options,
    resolve_model,
)
from backend.utils.model_pricing import (
    ModelType,
    calculate_llm_cost,
    get_available_models,
    get_model_pricing,
)

TODAY = date(2026, 9, 19)


def _ids(provider, model_type=ModelType.LLM, **kwargs):
    return {m.model_id for m in get_available_models(provider=provider, model_type=model_type, **kwargs)}


@pytest.mark.unit
class TestLifecycle:
    def test_past_shutdown_is_retired(self):
        info = get_model_lifecycle("anthropic", "claude-3-5-sonnet-20241022", TODAY)
        assert info == {"status": "retired", "shutdown_date": "2025-10-28", "replacement": "claude-sonnet-5"}

    def test_future_shutdown_is_deprecated(self):
        assert get_model_lifecycle("openai", "gpt-3.5-turbo", TODAY)["status"] == "deprecated"

    def test_status_flips_on_shutdown_date(self):
        assert get_model_lifecycle("openai", "gpt-3.5-turbo", date(2026, 10, 23))["status"] == "retired"

    def test_unlisted_model_is_active(self):
        assert get_model_lifecycle("openai", "gpt-4o-mini", TODAY)["status"] == "active"

    def test_google_is_an_alias_for_gemini(self):
        assert get_model_lifecycle("google", "gemini-2.0-flash", TODAY)["status"] == "retired"


@pytest.mark.unit
class TestAvailableModels:
    def test_retired_models_are_hidden(self):
        # Shut down before any possible test date
        assert "o1-mini" not in _ids("openai")
        assert "claude-3-5-sonnet-20241022" not in _ids("anthropic")

    def test_retired_models_available_on_request(self):
        assert "o1-mini" in _ids("openai", include_retired=True)

    def test_misspelled_claude_ids_are_gone(self):
        ids = _ids("anthropic", include_retired=True)
        for bogus in ("claude-haiku-3-20240307", "claude-sonnet-3-7-20240229",
                      "claude-opus-3-20240229", "claude-haiku-3-5-20241022"):
            assert bogus not in ids

    @pytest.mark.parametrize("provider,model_id", [
        ("anthropic", "claude-opus-5"), ("anthropic", "claude-sonnet-5"), ("anthropic", "claude-fable-5-1"),
        ("openai", "gpt-5.6-sol"), ("openai", "gpt-6-astra"),
        ("gemini", "gemini-3.8-flash"), ("gemini", "gemini-3.1-pro-preview"),
    ])
    def test_current_models_are_listed(self, provider, model_id):
        assert model_id in _ids(provider)

    def test_new_models_cost_matches_provider_price(self):
        # 1M input + 1M output tokens
        assert calculate_llm_cost("anthropic", "claude-sonnet-5", 1_000_000, 1_000_000) == pytest.approx(12.00)
        assert calculate_llm_cost("openai", "gpt-5.6-sol", 1_000_000, 1_000_000) == pytest.approx(24.00)


@pytest.mark.unit
class TestResolveModel:
    def test_missing_model_uses_default(self):
        assert resolve_model("anthropic", None) == get_default_model("anthropic")

    def test_active_model_unchanged(self):
        assert resolve_model("openai", "gpt-4o-mini", today=TODAY) == "gpt-4o-mini"

    def test_deprecated_model_still_used(self):
        assert resolve_model("openai", "gpt-3.5-turbo", today=TODAY) == "gpt-3.5-turbo"

    def test_retired_llm_is_upgraded(self):
        assert resolve_model("anthropic", "claude-3-5-sonnet-20241022", today=TODAY) == "claude-sonnet-5"

    def test_upgrade_target_overrides_replacement(self):
        # OpenAI recommends gpt-5.6-terra; NodeAI upgrades to a model verified with its request code
        assert resolve_model("openai", "o1-mini", today=TODAY) == "gpt-4.1-mini"

    def test_misspelled_claude_id_is_upgraded(self):
        assert resolve_model("anthropic", "claude-haiku-3-20240307", today=TODAY) == "claude-haiku-4-5"

    def test_retired_embedding_model_is_not_swapped(self):
        assert resolve_model("gemini", "gemini-embedding-exp-03-07", model_type="embedding",
                             today=TODAY) == "gemini-embedding-exp-03-07"


@pytest.mark.unit
class TestRegistryConsistency:
    def test_defaults_exist_and_are_not_ending_soon(self):
        for provider, by_type in DEFAULT_MODELS.items():
            for model_type, model_id in by_type.items():
                assert get_model_pricing(provider, model_id), f"default {provider}/{model_id} not in registry"
                info = get_model_lifecycle(provider, model_id, TODAY)
                assert info["status"] != "retired", model_id
                # A deprecated default is tolerated only with a distant shutdown date
                # (gemini-embedding-001 shuts down 2028-05-14; changing an embedding default
                # changes vector dimensions for new knowledge bases).
                if info["status"] == "deprecated":
                    assert info["shutdown_date"] and date.fromisoformat(info["shutdown_date"]) > date(2027, 9, 19), model_id

    def test_llm_upgrade_targets_exist_and_are_active(self):
        for provider, models in MODEL_LIFECYCLE.items():
            for model_id, (_, replacement, upgrade_target) in models.items():
                target = upgrade_target or replacement
                pricing = get_model_pricing(provider, model_id)
                is_llm = pricing is None or pricing.model_type == ModelType.LLM
                if not is_llm or target is None:
                    continue
                # Upgrade targets for chat models must be callable today
                if get_model_pricing(provider, target) is None:
                    continue  # non-chat replacement (audio, image, TTS models)
                assert get_model_lifecycle(provider, target, TODAY)["status"] == "active", \
                    f"{provider}/{model_id} upgrades to non-active {target}"

    def test_chat_model_upgrade_targets_are_in_registry(self):
        chat_models = ["gpt-3.5-turbo", "gpt-4", "o1", "o3-mini", "gpt-5", "chatgpt-4o-latest",
                       "claude-3-5-sonnet-20241022", "claude-opus-4-1", "gemini-2.0-flash", "gemini-3-pro-preview"]
        for model_id in chat_models:
            provider = "openai" if model_id.startswith(("gpt", "o", "chatgpt")) else (
                "anthropic" if model_id.startswith("claude") else "gemini")
            target = resolve_model(provider, model_id, today=date(2030, 1, 1))
            assert get_model_pricing(provider, target), f"{model_id} -> {target} missing from registry"


@pytest.mark.unit
class TestRequestOptions:
    def test_classic_openai_model_keeps_temperature(self):
        assert llm_request_options("openai", "gpt-4o-mini", 0.7, 500) == {
            "temperature": 0.7, "max_completion_tokens": 500}

    def test_legacy_openai_model_uses_max_tokens(self):
        assert llm_request_options("openai", "gpt-4.1", 0.2, 300) == {"temperature": 0.2, "max_tokens": 300}

    @pytest.mark.parametrize("model", ["o1", "o3-mini", "gpt-5", "gpt-5.6-sol", "gpt-6-astra"])
    def test_openai_reasoning_models_drop_temperature(self, model):
        assert llm_request_options("openai", model, 0.7, 500) == {
            "max_completion_tokens": MIN_OUTPUT_TOKENS_FOR_THINKING_MODELS}

    def test_fine_tuned_openai_model_follows_base_model(self):
        assert llm_request_options("openai", "ft:gpt-4o-mini-2024-07-18:acme:support:abc123", 0.3, 200) == {
            "temperature": 0.3, "max_completion_tokens": 200}
        assert llm_request_options("openai", "ft:gpt-3.5-turbo-0125:acme::xyz", 0.3, 200) == {
            "temperature": 0.3, "max_tokens": 200}

    def test_older_claude_keeps_temperature(self):
        assert llm_request_options("anthropic", "claude-haiku-4-5", 0.7, 500) == {
            "temperature": 0.7, "max_tokens": 500}

    @pytest.mark.parametrize("model", ["claude-sonnet-5", "claude-opus-5", "claude-fable-5-1"])
    def test_thinking_claude_models_drop_temperature_and_raise_budget(self, model):
        assert llm_request_options("anthropic", model, 0.7, 500) == {
            "max_tokens": MIN_OUTPUT_TOKENS_FOR_THINKING_MODELS}

    def test_opus_4_8_drops_temperature_without_raising_budget(self):
        assert llm_request_options("anthropic", "claude-opus-4-8", 0.7, 500) == {"max_tokens": 500}

    def test_large_budget_is_kept(self):
        assert llm_request_options("anthropic", "claude-opus-5", None, 20_000) == {"max_tokens": 20_000}
