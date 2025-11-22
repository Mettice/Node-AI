"""
Centralized Model Pricing Configuration

This module provides a unified interface for model pricing across all providers.
Supports embedding models, reranking models, and LLM models.

Designed to be modular and easily extensible for new providers.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class ModelType(Enum):
    """Model type categories."""
    EMBEDDING = "embedding"
    RERANKING = "reranking"
    LLM = "llm"


class Provider(Enum):
    """Supported providers."""
    VOYAGE_AI = "voyage_ai"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    GEMINI = "gemini"


@dataclass
class RateLimit:
    """Rate limit configuration for a model."""
    tpm: int  # Tokens per minute
    rpm: int  # Requests per minute


@dataclass
class ModelPricing:
    """Pricing information for a model."""
    model_id: str
    provider: Provider
    model_type: ModelType
    price_per_1k_tokens: Optional[float] = None  # For embedding/LLM models
    price_per_1k_units: Optional[float] = None  # For reranking (units = query + documents)
    dimension: Optional[int] = None  # For embedding models
    max_tokens: Optional[int] = None  # Max tokens per request
    max_batch_size: Optional[int] = None  # Max batch size
    rate_limit: Optional[RateLimit] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# VOYAGE AI MODELS
# ============================================================================

VOYAGE_AI_EMBEDDING_MODELS: Dict[str, ModelPricing] = {
    "voyage-3-large": ModelPricing(
        model_id="voyage-3-large",
        provider=Provider.VOYAGE_AI,
        model_type=ModelType.EMBEDDING,
        price_per_1k_tokens=0.10,  # $0.10 per 1K tokens
        dimension=1024,
        max_tokens=8192,
        max_batch_size=128,
        rate_limit=RateLimit(tpm=3_000_000, rpm=2000),
        description="High-quality embedding model with 1024 dimensions",
    ),
    "voyage-context-3": ModelPricing(
        model_id="voyage-context-3",
        provider=Provider.VOYAGE_AI,
        model_type=ModelType.EMBEDDING,
        price_per_1k_tokens=0.10,  # $0.10 per 1K tokens
        dimension=1024,
        max_tokens=8192,
        max_batch_size=128,
        rate_limit=RateLimit(tpm=3_000_000, rpm=2000),
        description="Context-aware embedding model",
    ),
    "voyage-code-3": ModelPricing(
        model_id="voyage-code-3",
        provider=Provider.VOYAGE_AI,
        model_type=ModelType.EMBEDDING,
        price_per_1k_tokens=0.10,  # $0.10 per 1K tokens
        dimension=1024,
        max_tokens=8192,
        max_batch_size=128,
        rate_limit=RateLimit(tpm=3_000_000, rpm=2000),
        description="Code-specific embedding model",
    ),
    "voyage-3.5": ModelPricing(
        model_id="voyage-3.5",
        provider=Provider.VOYAGE_AI,
        model_type=ModelType.EMBEDDING,
        price_per_1k_tokens=0.10,  # $0.10 per 1K tokens
        dimension=1024,
        max_tokens=8192,
        max_batch_size=128,
        rate_limit=RateLimit(tpm=8_000_000, rpm=2000),
        description="Latest general-purpose embedding model",
    ),
    "voyage-3.5-lite": ModelPricing(
        model_id="voyage-3.5-lite",
        provider=Provider.VOYAGE_AI,
        model_type=ModelType.EMBEDDING,
        price_per_1k_tokens=0.05,  # $0.05 per 1K tokens (estimated, cheaper than 3.5)
        dimension=1024,
        max_tokens=8192,
        max_batch_size=128,
        rate_limit=RateLimit(tpm=16_000_000, rpm=2000),
        description="Lighter, faster version of voyage-3.5",
    ),
    "voyage-multimodal-3": ModelPricing(
        model_id="voyage-multimodal-3",
        provider=Provider.VOYAGE_AI,
        model_type=ModelType.EMBEDDING,
        price_per_1k_tokens=0.15,  # $0.15 per 1K tokens (estimated, multimodal is more expensive)
        dimension=1024,
        max_tokens=8192,
        max_batch_size=128,
        rate_limit=RateLimit(tpm=2_000_000, rpm=2000),
        description="Multimodal embedding model for text and images",
    ),
    # Voyage 1 & 2 Series (legacy)
    "voyage-2": ModelPricing(
        model_id="voyage-2",
        provider=Provider.VOYAGE_AI,
        model_type=ModelType.EMBEDDING,
        price_per_1k_tokens=0.10,  # $0.10 per 1K tokens
        dimension=1024,
        max_tokens=8192,
        max_batch_size=128,
        rate_limit=RateLimit(tpm=3_000_000, rpm=2000),
        description="Voyage 2 series embedding model",
    ),
    "voyage-1": ModelPricing(
        model_id="voyage-1",
        provider=Provider.VOYAGE_AI,
        model_type=ModelType.EMBEDDING,
        price_per_1k_tokens=0.10,  # $0.10 per 1K tokens
        dimension=1024,
        max_tokens=8192,
        max_batch_size=128,
        rate_limit=RateLimit(tpm=3_000_000, rpm=2000),
        description="Voyage 1 series embedding model",
    ),
}

VOYAGE_AI_RERANKING_MODELS: Dict[str, ModelPricing] = {
    "rerank-2.5-lite": ModelPricing(
        model_id="rerank-2.5-lite",
        provider=Provider.VOYAGE_AI,
        model_type=ModelType.RERANKING,
        price_per_1k_units=0.20,  # $0.20 per 1K units (1 unit = 1 query + 1 document)
        rate_limit=RateLimit(tpm=4_000_000, rpm=2000),
        description="Lighter reranking model, faster and cheaper",
    ),
    "rerank-2-lite": ModelPricing(
        model_id="rerank-2-lite",
        provider=Provider.VOYAGE_AI,
        model_type=ModelType.RERANKING,
        price_per_1k_units=0.20,  # $0.20 per 1K units
        rate_limit=RateLimit(tpm=4_000_000, rpm=2000),
        description="Lighter reranking model (v2)",
    ),
    "rerank-lite-1": ModelPricing(
        model_id="rerank-lite-1",
        provider=Provider.VOYAGE_AI,
        model_type=ModelType.RERANKING,
        price_per_1k_units=0.20,  # $0.20 per 1K units
        rate_limit=RateLimit(tpm=4_000_000, rpm=2000),
        description="Lighter reranking model (v1)",
    ),
    "rerank-2.5": ModelPricing(
        model_id="rerank-2.5",
        provider=Provider.VOYAGE_AI,
        model_type=ModelType.RERANKING,
        price_per_1k_units=0.30,  # $0.30 per 1K units (higher quality, more expensive)
        rate_limit=RateLimit(tpm=2_000_000, rpm=2000),
        description="High-quality reranking model",
    ),
    "rerank-2": ModelPricing(
        model_id="rerank-2",
        provider=Provider.VOYAGE_AI,
        model_type=ModelType.RERANKING,
        price_per_1k_units=0.30,  # $0.30 per 1K units
        rate_limit=RateLimit(tpm=2_000_000, rpm=2000),
        description="High-quality reranking model (v2)",
    ),
    "rerank-1": ModelPricing(
        model_id="rerank-1",
        provider=Provider.VOYAGE_AI,
        model_type=ModelType.RERANKING,
        price_per_1k_units=0.30,  # $0.30 per 1K units
        rate_limit=RateLimit(tpm=2_000_000, rpm=2000),
        description="High-quality reranking model (v1)",
    ),
}

# Combine all Voyage AI models
VOYAGE_AI_MODELS = {**VOYAGE_AI_EMBEDDING_MODELS, **VOYAGE_AI_RERANKING_MODELS}


# ============================================================================
# OPENAI MODELS
# ============================================================================

OPENAI_EMBEDDING_MODELS: Dict[str, ModelPricing] = {
    "text-embedding-3-small": ModelPricing(
        model_id="text-embedding-3-small",
        provider=Provider.OPENAI,
        model_type=ModelType.EMBEDDING,
        # $0.02 per 1M tokens = $0.02 / 1000 = $0.00002 per 1K tokens
        price_per_1k_tokens=0.02 / 1000,  # $0.00002 per 1K tokens
        dimension=1536,  # Default dimension, can be reduced with dimensions parameter
        max_tokens=8192,
        max_batch_size=2048,  # OpenAI supports large batches
        description="Fast, efficient embedding model with 1536 dimensions (default)",
        metadata={
            # $0.01 per 1M tokens = $0.01 / 1000 = $0.00001 per 1K tokens for batch
            "batch_price_per_1k_tokens": 0.01 / 1000,
            "pages_per_dollar": 62500,  # ~62,500 pages per dollar
            "mteb_performance": 62.3,
            "price_per_1m_tokens": 0.02,  # Original pricing per 1M tokens
            "batch_price_per_1m_tokens": 0.01,  # Batch pricing per 1M tokens
        },
    ),
    "text-embedding-3-large": ModelPricing(
        model_id="text-embedding-3-large",
        provider=Provider.OPENAI,
        model_type=ModelType.EMBEDDING,
        # $0.13 per 1M tokens = $0.13 / 1000 = $0.00013 per 1K tokens
        price_per_1k_tokens=0.13 / 1000,  # $0.00013 per 1K tokens
        dimension=3072,  # Default dimension, can be reduced with dimensions parameter
        max_tokens=8192,
        max_batch_size=2048,
        description="High-quality embedding model with 3072 dimensions (default)",
        metadata={
            # $0.065 per 1M tokens = $0.065 / 1000 = $0.000065 per 1K tokens for batch
            "batch_price_per_1k_tokens": 0.065 / 1000,
            "pages_per_dollar": 9615,  # ~9,615 pages per dollar
            "mteb_performance": 64.6,
            "price_per_1m_tokens": 0.13,  # Original pricing per 1M tokens
            "batch_price_per_1m_tokens": 0.065,  # Batch pricing per 1M tokens
        },
    ),
    "text-embedding-ada-002": ModelPricing(
        model_id="text-embedding-ada-002",
        provider=Provider.OPENAI,
        model_type=ModelType.EMBEDDING,
        # $0.10 per 1M tokens = $0.10 / 1000 = $0.0001 per 1K tokens
        price_per_1k_tokens=0.10 / 1000,  # $0.0001 per 1K tokens
        dimension=1536,
        max_tokens=8192,
        max_batch_size=2048,
        description="Legacy embedding model with 1536 dimensions",
        metadata={
            # $0.05 per 1M tokens = $0.05 / 1000 = $0.00005 per 1K tokens for batch
            "batch_price_per_1k_tokens": 0.05 / 1000,
            "pages_per_dollar": 12500,  # ~12,500 pages per dollar
            "mteb_performance": 61.0,
            "price_per_1m_tokens": 0.10,  # Original pricing per 1M tokens
            "batch_price_per_1m_tokens": 0.05,  # Batch pricing per 1M tokens
        },
    ),
}

# Import LLM models from separate module
# Use delayed import to avoid circular dependency
OPENAI_LLM_MODELS: Dict[str, ModelPricing] = {}
ANTHROPIC_LLM_MODELS: Dict[str, ModelPricing] = {}
GEMINI_MODELS: Dict[str, ModelPricing] = {}

def _load_llm_models():
    """Load LLM models from separate modules (called after base classes are defined)."""
    global OPENAI_LLM_MODELS, ANTHROPIC_LLM_MODELS, GEMINI_MODELS
    import importlib
    import sys
    import os
    
    # Get the current module's directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # Try multiple import strategies
        llm_pricing = None
        try:
            # Strategy 1: Relative import (when running as package)
            from . import llm_pricing
        except ImportError:
            try:
                # Strategy 2: Absolute import (when running from project root)
                from backend.utils import llm_pricing
            except ImportError:
                # Strategy 3: Direct file import (when running from backend directory)
                import importlib.util
                spec = importlib.util.spec_from_file_location("llm_pricing", os.path.join(current_dir, "llm_pricing.py"))
                if spec and spec.loader:
                    llm_pricing = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(llm_pricing)
        
        if llm_pricing:
            OPENAI_LLM_MODELS = getattr(llm_pricing, 'OPENAI_LLM_MODELS', {})
            ANTHROPIC_LLM_MODELS = getattr(llm_pricing, 'ANTHROPIC_LLM_MODELS', {})
    except (ImportError, AttributeError, Exception) as e:
        # Use print instead of logger to avoid circular import
        print(f"Warning: Failed to import LLM models: {e}")
        OPENAI_LLM_MODELS = {}
        ANTHROPIC_LLM_MODELS = {}
    
    try:
        # Try multiple import strategies
        gemini_pricing = None
        try:
            # Strategy 1: Relative import (when running as package)
            from . import gemini_pricing
        except ImportError:
            try:
                # Strategy 2: Absolute import (when running from project root)
                from backend.utils import gemini_pricing
            except ImportError:
                # Strategy 3: Direct file import (when running from backend directory)
                import importlib.util
                spec = importlib.util.spec_from_file_location("gemini_pricing", os.path.join(current_dir, "gemini_pricing.py"))
                if spec and spec.loader:
                    gemini_pricing = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(gemini_pricing)
        
        if gemini_pricing:
            GEMINI_MODELS = getattr(gemini_pricing, 'GEMINI_MODELS', {})
    except (ImportError, AttributeError, Exception) as e:
        # Use print instead of logger to avoid circular import
        print(f"Warning: Failed to import Gemini models: {e}")
        GEMINI_MODELS = {}

# Load LLM models after all base classes are defined
_load_llm_models()

# Combine all OpenAI models (embeddings + LLMs)
# Note: OPENAI_LLM_MODELS is populated by _load_llm_models() above
OPENAI_MODELS = {**OPENAI_EMBEDDING_MODELS, **OPENAI_LLM_MODELS}

# Anthropic models (LLMs only for now)
# Note: ANTHROPIC_LLM_MODELS is populated by _load_llm_models() above
ANTHROPIC_MODELS = ANTHROPIC_LLM_MODELS

# Gemini models (embeddings + LLMs)
# Note: GEMINI_MODELS is populated by _load_llm_models() above
# GEMINI_MODELS is already a combined dict from gemini_pricing.py

# Verify models were loaded (for debugging)
if len(OPENAI_LLM_MODELS) == 0:
    import sys
    print("WARNING: OpenAI LLM models not loaded! Check import errors above.", file=sys.stderr)
if len(ANTHROPIC_LLM_MODELS) == 0:
    import sys
    print("WARNING: Anthropic LLM models not loaded! Check import errors above.", file=sys.stderr)
if len(GEMINI_MODELS) == 0:
    import sys
    print("WARNING: Gemini models not loaded! Check import errors above.", file=sys.stderr)


# ============================================================================
# COHERE MODELS
# ============================================================================

COHERE_EMBEDDING_MODELS: Dict[str, ModelPricing] = {
    "embed-v4.0": ModelPricing(
        model_id="embed-v4.0",
        provider=Provider.COHERE,
        model_type=ModelType.EMBEDDING,
        price_per_1k_tokens=0.10 / 1000,  # Estimated: $0.10 per 1M tokens (needs verification)
        dimension=1536,  # Default dimension, can be 256, 512, 1024, or 1536
        max_tokens=128000,  # 128k context length
        max_batch_size=96,  # Cohere's typical batch limit
        description="Latest model supporting text, images, and mixed content (PDFs). Flexible dimensions.",
        metadata={
            "supported_dimensions": [256, 512, 1024, 1536],
            "modalities": ["text", "images", "mixed"],
        },
    ),
    "embed-english-v3.0": ModelPricing(
        model_id="embed-english-v3.0",
        provider=Provider.COHERE,
        model_type=ModelType.EMBEDDING,
        price_per_1k_tokens=0.10 / 1000,  # Estimated: $0.10 per 1M tokens (needs verification)
        dimension=1024,
        max_tokens=512,
        max_batch_size=96,
        description="English-only embedding model with 1024 dimensions",
        metadata={
            "modalities": ["text", "images"],
            "language": "english",
        },
    ),
    "embed-english-light-v3.0": ModelPricing(
        model_id="embed-english-light-v3.0",
        provider=Provider.COHERE,
        model_type=ModelType.EMBEDDING,
        price_per_1k_tokens=0.05 / 1000,  # Estimated: $0.05 per 1M tokens (lighter = cheaper)
        dimension=384,
        max_tokens=512,
        max_batch_size=96,
        description="Faster, lighter English-only embedding model with 384 dimensions",
        metadata={
            "modalities": ["text", "images"],
            "language": "english",
        },
    ),
    "embed-multilingual-v3.0": ModelPricing(
        model_id="embed-multilingual-v3.0",
        provider=Provider.COHERE,
        model_type=ModelType.EMBEDDING,
        price_per_1k_tokens=0.10 / 1000,  # Estimated: $0.10 per 1M tokens (needs verification)
        dimension=1024,
        max_tokens=512,
        max_batch_size=96,
        description="Multilingual embedding model with 1024 dimensions",
        metadata={
            "modalities": ["text", "images"],
            "language": "multilingual",
        },
    ),
    "embed-multilingual-light-v3.0": ModelPricing(
        model_id="embed-multilingual-light-v3.0",
        provider=Provider.COHERE,
        model_type=ModelType.EMBEDDING,
        price_per_1k_tokens=0.05 / 1000,  # Estimated: $0.05 per 1M tokens (lighter = cheaper)
        dimension=384,
        max_tokens=512,
        max_batch_size=96,
        description="Faster, lighter multilingual embedding model with 384 dimensions",
        metadata={
            "modalities": ["text", "images"],
            "language": "multilingual",
        },
    ),
}

COHERE_RERANKING_MODELS: Dict[str, ModelPricing] = {
    "rerank-v3.5": ModelPricing(
        model_id="rerank-v3.5",
        provider=Provider.COHERE,
        model_type=ModelType.RERANKING,
        price_per_1k_units=0.20 / 1000,  # Estimated: $0.20 per 1K units (needs verification)
        max_tokens=4096,  # 4k context length
        description="Latest rerank model for documents and semi-structured data (JSON). State-of-the-art performance in English and non-English languages.",
        metadata={
            "modalities": ["text"],
            "language": "multilingual",
        },
    ),
    "rerank-english-v3.0": ModelPricing(
        model_id="rerank-english-v3.0",
        provider=Provider.COHERE,
        model_type=ModelType.RERANKING,
        price_per_1k_units=0.20 / 1000,  # Estimated: $0.20 per 1K units (needs verification)
        max_tokens=4096,  # 4k context length
        description="English-only rerank model for documents and semi-structured data (JSON)",
        metadata={
            "modalities": ["text"],
            "language": "english",
        },
    ),
    "rerank-multilingual-v3.0": ModelPricing(
        model_id="rerank-multilingual-v3.0",
        provider=Provider.COHERE,
        model_type=ModelType.RERANKING,
        price_per_1k_units=0.20 / 1000,  # Estimated: $0.20 per 1K units (needs verification)
        max_tokens=4096,  # 4k context length
        description="Multilingual rerank model for non-English documents and semi-structured data (JSON)",
        metadata={
            "modalities": ["text"],
            "language": "multilingual",
        },
    ),
}

# Combine all Cohere models
COHERE_MODELS = {**COHERE_EMBEDDING_MODELS, **COHERE_RERANKING_MODELS}


# ============================================================================
# PRICING REGISTRY
# ============================================================================

# Central registry of all models by provider
MODEL_REGISTRY: Dict[Provider, Dict[str, ModelPricing]] = {
    Provider.VOYAGE_AI: VOYAGE_AI_MODELS,
    Provider.OPENAI: OPENAI_MODELS,
    Provider.ANTHROPIC: ANTHROPIC_MODELS,
    Provider.COHERE: COHERE_MODELS,
    Provider.GEMINI: GEMINI_MODELS,
}


# ============================================================================
# COST CALCULATION FUNCTIONS
# ============================================================================

def get_model_pricing(provider: str, model_id: str) -> Optional[ModelPricing]:
    """
    Get pricing information for a model.
    
    Args:
        provider: Provider name (e.g., "voyage_ai", "openai")
        model_id: Model identifier (e.g., "voyage-3.5", "text-embedding-3-small")
    
    Returns:
        ModelPricing object or None if not found
    """
    try:
        provider_enum = Provider(provider.lower())
    except ValueError:
        # Try to match by name
        provider_map = {
            "voyage": Provider.VOYAGE_AI,
            "voyageai": Provider.VOYAGE_AI,
            "voyage_ai": Provider.VOYAGE_AI,
            "openai": Provider.OPENAI,
            "anthropic": Provider.ANTHROPIC,
            "cohere": Provider.COHERE,
            "huggingface": Provider.HUGGINGFACE,
            "gemini": Provider.GEMINI,
            "google": Provider.GEMINI,  # Alias for Google Gemini
        }
        provider_enum = provider_map.get(provider.lower())
        if not provider_enum:
            return None
    
    models = MODEL_REGISTRY.get(provider_enum, {})
    return models.get(model_id)


def calculate_embedding_cost(
    provider: str,
    model_id: str,
    num_tokens: int,
    use_batch_pricing: bool = False,
) -> float:
    """
    Calculate cost for embedding operation.
    
    Args:
        provider: Provider name
        model_id: Model identifier
        num_tokens: Number of tokens to embed
        use_batch_pricing: Whether to use batch pricing (if available)
    
    Returns:
        Cost in USD
    """
    pricing = get_model_pricing(provider, model_id)
    if not pricing or pricing.model_type != ModelType.EMBEDDING:
        return 0.0
    
    # Check if batch pricing is available and requested
    if use_batch_pricing and pricing.metadata and "batch_price_per_1k_tokens" in pricing.metadata:
        price_per_1k = pricing.metadata["batch_price_per_1k_tokens"]
    elif pricing.price_per_1k_tokens is not None:
        price_per_1k = pricing.price_per_1k_tokens
    else:
        return 0.0
    
    cost = (num_tokens / 1000) * price_per_1k
    return round(cost, 6)


def calculate_reranking_cost(
    provider: str,
    model_id: str,
    num_units: int,  # 1 unit = 1 query + 1 document
) -> float:
    """
    Calculate cost for reranking operation.
    
    Args:
        provider: Provider name
        model_id: Model identifier
        num_units: Number of units (1 query + N documents = 1 + N units)
    
    Returns:
        Cost in USD
    """
    pricing = get_model_pricing(provider, model_id)
    if not pricing or pricing.model_type != ModelType.RERANKING:
        return 0.0
    
    if pricing.price_per_1k_units is None:
        return 0.0
    
    cost = (num_units / 1000) * pricing.price_per_1k_units
    return round(cost, 6)


def estimate_tokens_from_text(text: str) -> int:
    """
    Estimate number of tokens from text.
    Rough approximation: 1 token ≈ 4 characters.
    
    Args:
        text: Input text
    
    Returns:
        Estimated token count
    """
    return len(text) // 4


def estimate_tokens_from_texts(texts: List[str]) -> int:
    """
    Estimate total tokens from multiple texts.
    
    Args:
        texts: List of input texts
    
    Returns:
        Total estimated token count
    """
    return sum(estimate_tokens_from_text(text) for text in texts)


def get_available_models(
    provider: Optional[str] = None,
    model_type: Optional[ModelType] = None,
) -> List[ModelPricing]:
    """
    Get list of available models, optionally filtered by provider and/or type.
    
    Args:
        provider: Optional provider filter (e.g., "openai", "anthropic", "gemini")
        model_type: Optional model type filter
    
    Returns:
        List of ModelPricing objects
    """
    all_models = []
    
    # Normalize provider name
    normalized_provider = None
    if provider:
        provider_lower = provider.lower()
        # Handle aliases
        if provider_lower in ["google"]:
            normalized_provider = "gemini"
        else:
            normalized_provider = provider_lower
    
    for prov, models in MODEL_REGISTRY.items():
        # Check provider match
        if normalized_provider:
            # Try exact match first
            if prov.value != normalized_provider:
                # Try enum name match (e.g., "OPENAI" -> "openai")
                if prov.name.lower() != normalized_provider:
                    continue
        
        for model in models.values():
            # Check model type match
            if model_type and model.model_type != model_type:
                continue
            all_models.append(model)
    
    return all_models


def get_model_info(provider: str, model_id: str) -> Optional[Dict[str, Any]]:
    """
    Get model information as a dictionary.
    
    Args:
        provider: Provider name
        model_id: Model identifier
    
    Returns:
        Dictionary with model information or None
    """
    pricing = get_model_pricing(provider, model_id)
    if not pricing:
        return None
    
    return {
        "model_id": pricing.model_id,
        "provider": pricing.provider.value,
        "model_type": pricing.model_type.value,
        "price_per_1k_tokens": pricing.price_per_1k_tokens,
        "price_per_1k_units": pricing.price_per_1k_units,
        "dimension": pricing.dimension,
        "max_tokens": pricing.max_tokens,
        "max_batch_size": pricing.max_batch_size,
        "rate_limit": {
            "tpm": pricing.rate_limit.tpm if pricing.rate_limit else None,
            "rpm": pricing.rate_limit.rpm if pricing.rate_limit else None,
        } if pricing.rate_limit else None,
        "description": pricing.description,
        "metadata": pricing.metadata,
    }


# ============================================================================
# HELPER FUNCTIONS FOR NODES
# ============================================================================

def calculate_embedding_cost_from_texts(
    provider: str,
    model_id: str,
    texts: List[str],
    use_batch_pricing: bool = False,
) -> float:
    """
    Convenience function to calculate embedding cost from text list.
    
    Args:
        provider: Provider name
        model_id: Model identifier
        texts: List of texts to embed
        use_batch_pricing: Whether to use batch pricing (if available)
    
    Returns:
        Cost in USD
    """
    num_tokens = estimate_tokens_from_texts(texts)
    return calculate_embedding_cost(provider, model_id, num_tokens, use_batch_pricing)


def calculate_reranking_cost_from_query_and_docs(
    provider: str,
    model_id: str,
    query: str,
    num_documents: int,
) -> float:
    """
    Convenience function to calculate reranking cost from query and documents.
    
    Args:
        provider: Provider name
        model_id: Model identifier
        query: Search query
        num_documents: Number of documents to rerank
    
    Returns:
        Cost in USD
    """
    # For reranking: 1 unit = 1 query + 1 document
    # So total units = 1 (query) + num_documents
    num_units = 1 + num_documents
    return calculate_reranking_cost(provider, model_id, num_units)


# ============================================================================
# LLM COST CALCULATION FUNCTIONS
# ============================================================================

def calculate_llm_cost(
    provider: str,
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    use_cached_input: bool = False,
    cache_type: Optional[str] = None,  # "5m", "1h", or "hit" for Anthropic
    use_batch: bool = False,
    use_long_context: bool = False,  # For Anthropic 1M context window
) -> float:
    """
    Calculate cost for LLM models based on input and output tokens.
    
    Args:
        provider: Provider name (e.g., "openai", "anthropic")
        model_id: Model identifier (e.g., "gpt-5.1", "claude-sonnet-4-5")
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        use_cached_input: Whether to use cached input pricing (if available)
        cache_type: Cache type for Anthropic ("5m", "1h", "hit", or None for base)
        use_batch: Whether to use batch pricing (50% discount for Anthropic)
        use_long_context: Whether to use long context pricing (>200K tokens for Anthropic)
    
    Returns:
        Cost in USD
    """
    pricing = get_model_pricing(provider, model_id)
    if not pricing or pricing.model_type != ModelType.LLM:
        return 0.0
    
    metadata = pricing.metadata or {}
    
    # Handle Anthropic-specific pricing
    if provider.lower() == "anthropic":
        # Check for long context pricing first (>200K tokens)
        if use_long_context and input_tokens > 200000:
            input_price_per_1k = metadata.get("long_context_input_price_per_1k_tokens", 0.0)
            output_price_per_1k = metadata.get("long_context_output_price_per_1k_tokens", 0.0)
        # Check for batch pricing
        elif use_batch:
            input_price_per_1k = metadata.get("batch_input_price_per_1m_tokens", 0.0) / 1000
            output_price_per_1k = metadata.get("batch_output_price_per_1m_tokens", 0.0) / 1000
        # Check for cache pricing
        elif use_cached_input and cache_type:
            if cache_type == "5m":
                input_price_per_1k = metadata.get("cached_input_price_per_1m_tokens_5m", 0.0) / 1000
            elif cache_type == "1h":
                input_price_per_1k = metadata.get("cached_input_price_per_1m_tokens_1h", 0.0) / 1000
            elif cache_type == "hit":
                input_price_per_1k = metadata.get("cache_hit_price_per_1m_tokens", 0.0) / 1000
            else:
                input_price_per_1k = metadata.get("input_price_per_1k_tokens", 0.0)
            output_price_per_1k = metadata.get("output_price_per_1k_tokens", 0.0)
        # Default cached pricing (cache hit)
        elif use_cached_input:
            input_price_per_1k = metadata.get("cached_input_price_per_1k_tokens", 0.0)
            output_price_per_1k = metadata.get("output_price_per_1k_tokens", 0.0)
        # Base pricing
        else:
            input_price_per_1k = metadata.get("input_price_per_1k_tokens", 0.0)
            output_price_per_1k = metadata.get("output_price_per_1k_tokens", 0.0)
    elif provider.lower() == "gemini" or provider.lower() == "google":
        # Handle Gemini-specific pricing (similar to Anthropic with cache and batch)
        # Check for long context pricing first (>200K tokens for 2.5 Pro)
        if use_long_context and input_tokens > 200000 and metadata.get("input_price_per_1m_tokens_long"):
            input_price_per_1k = metadata.get("input_price_per_1m_tokens_long", 0.0) / 1000
            output_price_per_1k = metadata.get("output_price_per_1m_tokens_long", 0.0) / 1000
        # Check for batch pricing
        elif use_batch:
            input_price_per_1k = metadata.get("batch_input_price_per_1m_tokens", 0.0) / 1000
            output_price_per_1k = metadata.get("batch_output_price_per_1m_tokens", 0.0) / 1000
        # Check for cache pricing
        elif use_cached_input:
            input_price_per_1k = metadata.get("cached_input_price_per_1k_tokens", 0.0)
            if not input_price_per_1k:
                # Fallback to cache price per 1M tokens
                input_price_per_1k = metadata.get("cache_price_per_1m_tokens_text", 0.0) / 1000
            output_price_per_1k = metadata.get("output_price_per_1k_tokens", 0.0)
        # Base pricing (default to text pricing)
        else:
            input_price_per_1k = metadata.get("input_price_per_1k_tokens", 0.0)
            if not input_price_per_1k:
                # Fallback to input price per 1M tokens (text)
                input_price_per_1k = metadata.get("input_price_per_1m_tokens_text", 0.0) / 1000
                if not input_price_per_1k:
                    input_price_per_1k = metadata.get("input_price_per_1m_tokens", 0.0) / 1000
            output_price_per_1k = metadata.get("output_price_per_1k_tokens", 0.0)
    else:
        # OpenAI and other providers
        if use_cached_input and metadata.get("cached_input_price_per_1k_tokens") is not None:
            input_price_per_1k = metadata["cached_input_price_per_1k_tokens"]
        else:
            input_price_per_1k = metadata.get("input_price_per_1k_tokens", 0.0)
        
        output_price_per_1k = metadata.get("output_price_per_1k_tokens", 0.0)
    
    # Calculate cost
    input_cost = (input_tokens / 1000) * input_price_per_1k
    output_cost = (output_tokens / 1000) * output_price_per_1k
    
    total_cost = input_cost + output_cost
    return round(total_cost, 6)


def calculate_llm_cost_from_texts(
    provider: str,
    model_id: str,
    input_text: str,
    estimated_output_tokens: int = 500,
    use_cached_input: bool = False,
) -> float:
    """
    Convenience function to calculate LLM cost from input text.
    
    Args:
        provider: Provider name
        model_id: Model identifier
        input_text: Input text (will be tokenized)
        estimated_output_tokens: Estimated number of output tokens
        use_cached_input: Whether to use cached input pricing
    
    Returns:
        Cost in USD
    """
    input_tokens = estimate_tokens_from_text(input_text)
    return calculate_llm_cost(provider, model_id, input_tokens, estimated_output_tokens, use_cached_input)

