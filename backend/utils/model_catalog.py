"""
Model lifecycle, defaults and request compatibility.

model_pricing.MODEL_REGISTRY knows which models exist and what they cost. This module adds
what the registry cannot express on its own:

- Lifecycle: provider shutdown dates and replacements. Retired models are hidden from model
  pickers, and a saved workflow that still names one is upgraded to a working model instead
  of failing at run time.
- Defaults per provider and model type, so nodes stop hardcoding their own.
- Request options that differ between model families (temperature support, which token
  limit parameter to send, minimum output budget for models that think before answering).

Sources, checked 2026-09-19:
- Anthropic: models overview (current, legacy, deprecated and retired models)
- OpenAI: https://developers.openai.com/api/docs/deprecations
- Google: https://ai.google.dev/gemini-api/docs/deprecations
Update MODEL_LIFECYCLE when providers announce new deprecations.
"""

from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from backend.utils.logger import get_logger

logger = get_logger(__name__)

LIFECYCLE_CHECKED_ON = "2026-09-19"

# provider -> model_id -> (shutdown date, replacement recommended by the provider, upgrade target)
#
# shutdown date: ISO date, or None when the provider deprecated the model without a date.
#   Past date -> "retired" (API calls fail). Future date or None -> "deprecated" (still works).
# replacement: what the provider recommends; shown to users.
# upgrade target: model a retired model is swapped for at run time, when it differs from the
#   replacement. Used where the provider's recommendation has not been verified with the way
#   NodeAI calls the API yet (OpenAI's gpt-5.6 family through Chat Completions).
Lifecycle = Tuple[Optional[str], Optional[str], Optional[str]]

MODEL_LIFECYCLE: Dict[str, Dict[str, Lifecycle]] = {
    "openai": {
        # Shut down
        "chatgpt-4o-latest": ("2026-02-17", "gpt-5.6-sol", "gpt-4.1"),
        "codex-mini-latest": ("2026-02-12", "gpt-5.6-terra", "gpt-4.1-mini"),
        "computer-use-preview": ("2026-07-23", "gpt-5.6-terra", "gpt-4.1"),
        "gpt-4o-search-preview": ("2026-07-23", "gpt-5.6-terra", "gpt-4.1"),
        "gpt-4o-mini-search-preview": ("2026-07-23", "gpt-5.6-terra", "gpt-4.1-mini"),
        "gpt-5-chat-latest": ("2026-07-23", "gpt-5.6-sol", "gpt-4.1"),
        "gpt-5-codex": ("2026-07-23", "gpt-5.6-sol", "gpt-4.1"),
        "gpt-5.1-chat-latest": ("2026-07-23", "gpt-5.6-sol", "gpt-4.1"),
        "gpt-5.1-codex": ("2026-07-23", "gpt-5.6-sol", "gpt-4.1"),
        "gpt-5.1-codex-max": ("2026-07-23", "gpt-5.6-sol", "gpt-4.1"),
        "gpt-5.1-codex-mini": ("2026-07-23", "gpt-5.6-terra", "gpt-4.1-mini"),
        "gpt-5.2-codex": ("2026-07-23", "gpt-5.6-sol", "gpt-4.1"),
        "gpt-5.2-chat-latest": ("2026-08-10", "gpt-5.6-sol", "gpt-4.1"),
        "gpt-5.3-chat-latest": ("2026-08-10", "gpt-5.6-sol", "gpt-4.1"),
        "o3-deep-research": ("2026-07-23", "gpt-5.6-sol", "gpt-4.1"),
        "o4-mini-deep-research": ("2026-07-23", "gpt-5.6-sol", "gpt-4.1"),
        "gpt-4o-audio-preview": ("2026-05-07", "gpt-audio-1.5", None),
        "gpt-4o-mini-audio-preview": ("2026-05-07", "gpt-audio-1.5", None),
        "gpt-4o-realtime-preview": ("2026-05-07", "gpt-realtime-2.1", None),
        "gpt-4o-mini-realtime-preview": ("2026-05-07", "gpt-realtime-2.1-mini", None),
        "gpt-4-turbo-preview": ("2026-03-26", "gpt-4.1", None),
        "gpt-4-0125-preview": ("2026-03-26", "gpt-4.1", None),
        "gpt-4-1106-preview": ("2026-03-26", "gpt-4.1", None),
        "o1-mini": ("2025-10-27", "gpt-5.6-terra", "gpt-4.1-mini"),
        "o1-preview": ("2025-07-28", "gpt-5.6-sol", "gpt-4.1"),
        "gpt-4.5-preview": ("2025-07-14", "gpt-4.1", None),
        "gpt-4-32k": ("2025-06-06", "gpt-4o", None),
        "gpt-4-vision-preview": ("2024-12-06", "gpt-4o", None),
        # Shutdown scheduled
        "gpt-3.5-turbo-instruct": ("2026-09-28", "gpt-5.6-terra", "gpt-4.1-mini"),
        "gpt-3.5-turbo": ("2026-10-23", "gpt-5.6-terra", "gpt-4.1-mini"),
        "gpt-4": ("2026-10-23", "gpt-5.6-sol", "gpt-4.1"),
        "gpt-4-turbo": ("2026-10-23", "gpt-5.6-sol", "gpt-4.1"),
        "gpt-4.1-nano": ("2026-10-23", "gpt-5.6-luna", "gpt-4.1-mini"),
        "gpt-4o-2024-05-13": ("2026-10-23", "gpt-5.6-sol", "gpt-4o"),
        "o1": ("2026-10-23", "gpt-5.6-sol", "gpt-4.1"),
        "o1-pro": ("2026-10-23", "gpt-5.6-sol", "gpt-4.1"),
        "o3-mini": ("2026-10-23", "gpt-5.6-sol", "gpt-4.1-mini"),
        "o4-mini": ("2026-10-23", "gpt-5.6-terra", "gpt-4.1-mini"),
        "gpt-5": ("2026-12-11", "gpt-5.6-sol", "gpt-4.1"),
        "gpt-5-mini": ("2026-12-11", "gpt-5.6-terra", "gpt-4.1-mini"),
        "gpt-5-nano": ("2026-12-11", "gpt-5.6-luna", "gpt-4.1-mini"),
        "gpt-5-pro": ("2026-12-11", "gpt-5.6-sol", "gpt-4.1"),
        "o3": ("2026-12-11", "gpt-5.6-sol", "gpt-4.1"),
        "o3-pro": ("2026-12-11", "gpt-5.6-sol", "gpt-4.1"),
        "gpt-audio": ("2027-01-20", "gpt-audio-1.5", None),
        "gpt-audio-mini": ("2027-01-20", "gpt-audio-1.5", None),
        "gpt-realtime": ("2027-01-20", "gpt-realtime-2.1", None),
        "gpt-realtime-mini": ("2027-01-20", "gpt-realtime-2.1-mini", None),
    },
    "anthropic": {
        # Retired
        "claude-opus-4-1": ("2026-08-05", "claude-opus-5", None),
        "claude-opus-4-1-20250805": ("2026-08-05", "claude-opus-5", None),
        "claude-3-haiku-20240307": ("2026-04-19", "claude-haiku-4-5", None),
        "claude-3-7-sonnet-20250219": ("2026-02-19", "claude-sonnet-5", None),
        "claude-3-7-sonnet-latest": ("2026-02-19", "claude-sonnet-5", None),
        "claude-3-5-haiku-20241022": ("2026-02-19", "claude-haiku-4-5", None),
        "claude-3-5-haiku-latest": ("2026-02-19", "claude-haiku-4-5", None),
        "claude-3-opus-20240229": ("2026-01-05", "claude-opus-5", None),
        "claude-3-opus-latest": ("2026-01-05", "claude-opus-5", None),
        "claude-3-5-sonnet-20241022": ("2025-10-28", "claude-sonnet-5", None),
        "claude-3-5-sonnet-20240620": ("2025-10-28", "claude-sonnet-5", None),
        "claude-3-5-sonnet-latest": ("2025-10-28", "claude-sonnet-5", None),
        "claude-3-sonnet-20240229": ("2025-07-21", "claude-sonnet-5", None),
        # Misspelled IDs that earlier versions of the registry offered. The API never
        # accepted them; kept so workflows that saved one are upgraded instead of failing.
        "claude-haiku-3-20240307": ("2024-03-07", "claude-haiku-4-5", None),
        "claude-haiku-3-5-20241022": ("2024-10-22", "claude-haiku-4-5", None),
        "claude-opus-3-20240229": ("2024-02-29", "claude-opus-5", None),
        "claude-sonnet-3-7-20240229": ("2024-02-29", "claude-sonnet-5", None),
        # Deprecated, no shutdown date announced
        "claude-sonnet-4-0": (None, "claude-sonnet-5", None),
        "claude-sonnet-4-20250514": (None, "claude-sonnet-5", None),
        "claude-opus-4-0": (None, "claude-opus-5", None),
        "claude-opus-4-20250514": (None, "claude-opus-5", None),
    },
    "gemini": {
        # Shut down
        "gemini-2.0-flash": ("2026-06-01", "gemini-3.6-flash", None),
        "gemini-2.0-flash-001": ("2026-06-01", "gemini-3.6-flash", None),
        "gemini-2.0-flash-lite": ("2026-06-01", "gemini-3.1-flash-lite", None),
        "gemini-2.0-flash-lite-001": ("2026-06-01", "gemini-3.1-flash-lite", None),
        "gemini-2.0-flash-preview-image-generation": ("2025-11-14", "gemini-3.1-flash-image", None),
        "gemini-2.5-flash-preview-09-2025": ("2026-02-17", "gemini-3.6-flash", None),
        "gemini-2.5-flash-preview-09-25": ("2026-02-17", "gemini-3.6-flash", None),
        "gemini-2.5-flash-lite-preview-09-2025": ("2026-03-31", "gemini-3.1-flash-lite", None),
        "gemini-3-pro-preview": ("2026-03-09", "gemini-3.1-pro-preview", None),
        "gemini-3-pro-image-preview": ("2026-06-25", "gemini-3-pro-image", None),
        "gemini-embedding-exp-03-07": ("2025-10-30", "gemini-embedding-2", None),
        "text-embedding-004": ("2026-01-14", "gemini-embedding-2", None),
        # Shutdown scheduled or replacement announced
        "gemini-2.5-flash-image": ("2026-10-02", "gemini-3.1-flash-image", None),
        "gemini-embedding-001": ("2028-05-14", "gemini-embedding-2", None),
        "gemini-3-flash-preview": (None, "gemini-3.6-flash", None),
        "gemini-2.5-flash-native-audio-preview-12-2025": (None, "gemini-3.8-live", None),
        "gemini-2.5-flash-preview-tts": (None, "gemini-3.1-flash-tts-preview", None),
        "gemini-2.5-pro-preview-tts": (None, "gemini-3.1-flash-tts-preview", None),
        # Experimental model missing from Google's deprecation table; treat as deprecated
        "gemini-2.0-flash-exp": (None, "gemini-3.6-flash", None),
    },
}

# Default model per provider and model type. Deliberately not always the newest model:
# each default has been used with NodeAI's request code, or has compatibility handled by
# llm_request_options below.
DEFAULT_MODELS: Dict[str, Dict[str, str]] = {
    "openai": {"llm": "gpt-4o-mini", "embedding": "text-embedding-3-small"},
    "anthropic": {"llm": "claude-sonnet-5"},
    "gemini": {"llm": "gemini-2.5-flash", "embedding": "gemini-embedding-001"},
    "cohere": {"embedding": "embed-english-v3.0", "reranking": "rerank-v3.5"},
    "voyage_ai": {"embedding": "voyage-3.5", "reranking": "rerank-2.5"},
}

_PROVIDER_ALIASES = {"google": "gemini", "voyage": "voyage_ai", "voyageai": "voyage_ai", "claude": "anthropic"}

# Models that think before answering by default. Their output limit covers the thinking too,
# so a small limit (the chat node's default is 500) can leave nothing for the answer.
MIN_OUTPUT_TOKENS_FOR_THINKING_MODELS = 4000


def _provider_key(provider: str) -> str:
    key = (provider or "").lower()
    return _PROVIDER_ALIASES.get(key, key)


def get_model_lifecycle(provider: str, model_id: str, today: Optional[date] = None) -> Dict[str, Any]:
    """
    Return the lifecycle of a model: status ("active", "deprecated" or "retired"),
    shutdown_date and replacement.
    """
    entry = MODEL_LIFECYCLE.get(_provider_key(provider), {}).get(model_id)
    if not entry:
        return {"status": "active", "shutdown_date": None, "replacement": None}

    shutdown, replacement, _ = entry
    today = today or date.today()
    retired = shutdown is not None and date.fromisoformat(shutdown) <= today
    return {
        "status": "retired" if retired else "deprecated",
        "shutdown_date": shutdown,
        "replacement": replacement,
    }


def is_retired(provider: str, model_id: str, today: Optional[date] = None) -> bool:
    return get_model_lifecycle(provider, model_id, today)["status"] == "retired"


def resolve_model(provider: str, model_id: Optional[str], model_type: str = "llm",
                  today: Optional[date] = None) -> str:
    """
    Return the model to actually call.

    Falls back to the provider default when no model is given, and upgrades retired LLMs to
    their replacement so saved workflows keep running. Retired embedding models are never
    swapped: vectors from a different model are not comparable with an existing index, so
    silently switching would corrupt search results. Those are returned unchanged and the
    provider's error surfaces instead.
    """
    key = _provider_key(provider)
    if not model_id:
        return get_default_model(key, model_type)

    current = model_id
    for _ in range(5):  # follow replacement chains, bounded
        entry = MODEL_LIFECYCLE.get(key, {}).get(current)
        if not entry or not is_retired(key, current, today):
            break
        if model_type != "llm":
            logger.warning(
                f"{key} model '{current}' was shut down on {entry[0]}. Not replacing it automatically: "
                f"{model_type} models are not interchangeable. Recommended replacement: {entry[1]}"
            )
            return current
        _, replacement, upgrade_target = entry
        target = upgrade_target or replacement
        if not target:
            break
        logger.warning(
            f"{key} model '{current}' was shut down on {entry[0]}; using '{target}' instead. "
            f"Update the node's model setting to stop this warning."
        )
        current = target
    return current


def list_model_ids(provider: str, model_type: str = "llm") -> List[str]:
    """
    Model IDs for a picker: retired models and duplicate aliases removed, current generation
    first, then older active models, deprecated models last.
    """
    from backend.utils.model_pricing import ModelType, get_available_models

    models = get_available_models(provider=_provider_key(provider), model_type=ModelType(model_type))
    models = [m for m in models if not (m.metadata or {}).get("is_alias", False)]

    def order(indexed):
        index, model = indexed
        deprecated = get_model_lifecycle(provider, model.model_id)["status"] == "deprecated"
        current = bool((model.metadata or {}).get("current_generation"))
        return (deprecated, not current, index)

    return [m.model_id for _, m in sorted(enumerate(models), key=order)]


def get_default_model(provider: str, model_type: str = "llm") -> str:
    key = _provider_key(provider)
    try:
        return DEFAULT_MODELS[key][model_type]
    except KeyError:
        raise ValueError(f"No default {model_type} model configured for provider '{provider}'")


def _is_openai_reasoning_model(model: str) -> bool:
    m = model.lower()
    return m.startswith(("o1", "o3", "o4", "gpt-5", "gpt-6"))


def _anthropic_rejects_sampling(model: str) -> bool:
    """Claude models from Opus 4.7 / Sonnet 5 on return 400 when temperature or top_p is sent."""
    m = model.lower()
    return m.startswith(("claude-opus-4-7", "claude-opus-4-8", "claude-opus-5",
                         "claude-sonnet-5", "claude-fable", "claude-mythos"))


def _anthropic_thinks_by_default(model: str) -> bool:
    """These run adaptive thinking when the request does not configure thinking."""
    m = model.lower()
    return m.startswith(("claude-opus-5", "claude-sonnet-5", "claude-fable", "claude-mythos"))


def llm_request_options(provider: str, model: str, temperature: Optional[float],
                        max_tokens: Optional[int]) -> Dict[str, Any]:
    """
    Sampling and output-limit arguments for a chat request, adjusted for the model family.

    Returns keyword arguments to merge into the provider SDK call. Parameters a model rejects
    are left out rather than sent, since sending them fails the whole request.
    """
    key = _provider_key(provider)
    options: Dict[str, Any] = {}

    if key == "openai":
        # Fine-tuned models ("ft:gpt-4o-mini:org:name:id") follow their base model's rules
        if model.lower().startswith("ft:"):
            model = model.split(":")[1]
        if _is_openai_reasoning_model(model):
            # Reasoning models only accept the default temperature, take
            # max_completion_tokens, and spend part of that budget on reasoning.
            if max_tokens is not None:
                options["max_completion_tokens"] = max(max_tokens, MIN_OUTPUT_TOKENS_FOR_THINKING_MODELS)
        else:
            if temperature is not None:
                options["temperature"] = temperature
            if max_tokens is not None:
                legacy = model.lower().startswith(("gpt-3.5", "gpt-4-", "gpt-4.1")) or model.lower() == "gpt-4"
                options["max_tokens" if legacy else "max_completion_tokens"] = max_tokens
        return options

    if key == "anthropic":
        if temperature is not None and not _anthropic_rejects_sampling(model):
            options["temperature"] = temperature
        if max_tokens is not None:
            if _anthropic_thinks_by_default(model):
                max_tokens = max(max_tokens, MIN_OUTPUT_TOKENS_FOR_THINKING_MODELS)
            options["max_tokens"] = max_tokens
        return options

    # Other providers: pass through unchanged
    if temperature is not None:
        options["temperature"] = temperature
    if max_tokens is not None:
        options["max_tokens"] = max_tokens
    return options
