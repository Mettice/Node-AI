"""
Gemini Model Pricing Configuration

This module contains pricing information for Google Gemini models including:
- Embedding models
- LLM/Chat models (Gemini 2.5 Pro, 2.5 Flash, etc.)

Separated from model_pricing.py for better organization as the model list grows.
"""

from typing import Dict, Optional, Any
try:
    # Try relative import first (when running as module)
    from .model_pricing import (
        ModelPricing,
        ModelType,
        Provider,
        RateLimit,
    )
except ImportError:
    # Fallback to absolute import (when running directly)
    from backend.utils.model_pricing import (
        ModelPricing,
        ModelType,
        Provider,
        RateLimit,
    )


# ============================================================================
# GEMINI EMBEDDING MODELS
# ============================================================================

GEMINI_EMBEDDING_MODELS: Dict[str, ModelPricing] = {
    "gemini-embedding-001": ModelPricing(
        model_id="gemini-embedding-001",
        provider=Provider.GEMINI,
        model_type=ModelType.EMBEDDING,
        price_per_1k_tokens=0.15 / 1000,  # $0.15 per 1M tokens = $0.00015 per 1K tokens
        dimension=3072,  # Default, supports 128-3072 with MRL
        max_tokens=2048,  # Input token limit
        max_batch_size=100,  # Reasonable batch size
        description="Gemini embedding model with flexible dimensions (128-3072), optimized for various tasks",
        metadata={
            "price_per_1m_tokens": 0.15,
            "batch_price_per_1m_tokens": 0.075,  # 50% discount for batch
            "batch_price_per_1k_tokens": 0.075 / 1000,
            "supported_dimensions": [128, 256, 512, 768, 1024, 1536, 2048, 3072],
            "recommended_dimensions": [768, 1536, 3072],
            "mrl_technique": True,  # Matryoshka Representation Learning
            "task_types": [
                "SEMANTIC_SIMILARITY",
                "CLASSIFICATION",
                "CLUSTERING",
                "RETRIEVAL_DOCUMENT",
                "RETRIEVAL_QUERY",
                "CODE_RETRIEVAL_QUERY",
                "QUESTION_ANSWERING",
                "FACT_VERIFICATION",
            ],
            "mteb_scores": {
                2048: 68.16,
                1536: 68.17,
                768: 67.99,
                512: 67.55,
                256: 66.19,
                128: 63.31,
            },
        },
    ),
    "gemini-embedding-exp-03-07": ModelPricing(
        model_id="gemini-embedding-exp-03-07",
        provider=Provider.GEMINI,
        model_type=ModelType.EMBEDDING,
        price_per_1k_tokens=0.15 / 1000,
        dimension=3072,
        max_tokens=2048,
        max_batch_size=100,
        description="Experimental Gemini embedding model (deprecating in Oct 2025)",
        metadata={
            "price_per_1m_tokens": 0.15,
            "batch_price_per_1m_tokens": 0.075,
            "batch_price_per_1k_tokens": 0.075 / 1000,
            "deprecated": True,
            "deprecation_date": "October 2025",
        },
    ),
}


# ============================================================================
# GEMINI LLM MODELS
# ============================================================================

GEMINI_LLM_MODELS: Dict[str, ModelPricing] = {
    # Gemini 2.5 Pro
    "gemini-2.5-pro": ModelPricing(
        model_id="gemini-2.5-pro",
        provider=Provider.GEMINI,
        model_type=ModelType.LLM,
        price_per_1k_tokens=None,
        max_tokens=1000000,  # 1M context window
        description="State-of-the-art multipurpose model, excels at coding and complex reasoning tasks",
        metadata={
            "input_price_per_1m_tokens_standard": 1.25,  # <= 200k tokens
            "input_price_per_1m_tokens_long": 2.50,  # > 200k tokens
            "output_price_per_1m_tokens_standard": 10.00,  # <= 200k tokens
            "output_price_per_1m_tokens_long": 15.00,  # > 200k tokens
            "cache_price_per_1m_tokens_standard": 0.125,  # <= 200k tokens
            "cache_price_per_1m_tokens_long": 0.25,  # > 200k tokens
            "cache_storage_price_per_1m_tokens_per_hour": 4.50,
            "batch_input_price_per_1m_tokens": 0.625,  # 50% discount
            "batch_output_price_per_1m_tokens": 5.00,  # 50% discount
            "input_price_per_1k_tokens": 1.25 / 1000,  # Default to standard
            "output_price_per_1k_tokens": 10.00 / 1000,
            "cached_input_price_per_1k_tokens": 0.125 / 1000,
            "context_window": 1000000,  # 1M tokens
            "category": "frontier",
            "features": ["coding", "reasoning", "multimodal"],
            "grounding_google_search": {
                "free_rpd": 1500,
                "paid_per_1k_prompts": 35.00,
            },
            "grounding_google_maps": {
                "free_rpd": 10000,
                "paid_per_1k_prompts": 25.00,
            },
        },
    ),
    
    # Gemini 2.5 Flash
    "gemini-2.5-flash": ModelPricing(
        model_id="gemini-2.5-flash",
        provider=Provider.GEMINI,
        model_type=ModelType.LLM,
        price_per_1k_tokens=None,
        max_tokens=1000000,  # 1M context window
        description="First hybrid reasoning model with 1M token context window and thinking budgets",
        metadata={
            "input_price_per_1m_tokens_text": 0.30,
            "input_price_per_1m_tokens_audio": 1.00,
            "output_price_per_1m_tokens": 2.50,
            "cache_price_per_1m_tokens_text": 0.03,
            "cache_price_per_1m_tokens_audio": 0.10,
            "cache_storage_price_per_1m_tokens_per_hour": 1.00,
            "batch_input_price_per_1m_tokens": 0.15,  # 50% discount
            "batch_output_price_per_1m_tokens": 1.25,  # 50% discount
            "input_price_per_1k_tokens": 0.30 / 1000,  # Default to text
            "output_price_per_1k_tokens": 2.50 / 1000,
            "cached_input_price_per_1k_tokens": 0.03 / 1000,
            "context_window": 1000000,  # 1M tokens
            "category": "standard",
            "features": ["reasoning", "multimodal", "thinking_budgets"],
            "grounding_google_search": {
                "free_rpd": 1500,  # Shared with Flash-Lite
                "paid_per_1k_prompts": 35.00,
            },
            "grounding_google_maps": {
                "free_rpd": 1500,
                "paid_per_1k_prompts": 25.00,
            },
        },
    ),
    
    # Gemini 2.5 Flash Preview
    "gemini-2.5-flash-preview-09-2025": ModelPricing(
        model_id="gemini-2.5-flash-preview-09-2025",
        provider=Provider.GEMINI,
        model_type=ModelType.LLM,
        price_per_1k_tokens=None,
        max_tokens=1000000,
        description="Latest model based on 2.5 Flash, optimized for large scale processing and agentic use cases",
        metadata={
            "input_price_per_1m_tokens_text": 0.30,
            "input_price_per_1m_tokens_audio": 1.00,
            "output_price_per_1m_tokens": 2.50,
            "cache_price_per_1m_tokens_text": 0.03,
            "cache_price_per_1m_tokens_audio": 0.10,
            "cache_storage_price_per_1m_tokens_per_hour": 1.00,
            "batch_input_price_per_1m_tokens": 0.15,
            "batch_output_price_per_1m_tokens": 1.25,
            "input_price_per_1k_tokens": 0.30 / 1000,
            "output_price_per_1k_tokens": 2.50 / 1000,
            "cached_input_price_per_1k_tokens": 0.03 / 1000,
            "context_window": 1000000,
            "category": "standard",
            "features": ["reasoning", "multimodal", "agentic", "preview"],
            "grounding_google_search": {
                "free_rpd": 1500,  # Shared with Flash-Lite
                "paid_per_1k_prompts": 35.00,
            },
        },
    ),
    
    # Gemini 2.5 Flash-Lite
    "gemini-2.5-flash-lite": ModelPricing(
        model_id="gemini-2.5-flash-lite",
        provider=Provider.GEMINI,
        model_type=ModelType.LLM,
        price_per_1k_tokens=None,
        max_tokens=1000000,
        description="Smallest and most cost-effective model, built for at scale usage",
        metadata={
            "input_price_per_1m_tokens_text": 0.10,
            "input_price_per_1m_tokens_audio": 0.30,
            "output_price_per_1m_tokens": 0.40,
            "cache_price_per_1m_tokens_text": 0.01,
            "cache_price_per_1m_tokens_audio": 0.03,
            "cache_storage_price_per_1m_tokens_per_hour": 1.00,
            "batch_input_price_per_1m_tokens": 0.05,  # 50% discount
            "batch_output_price_per_1m_tokens": 0.20,  # 50% discount
            "input_price_per_1k_tokens": 0.10 / 1000,
            "output_price_per_1k_tokens": 0.40 / 1000,
            "cached_input_price_per_1k_tokens": 0.01 / 1000,
            "context_window": 1000000,
            "category": "standard",
            "features": ["cost_effective", "multimodal", "at_scale"],
            "grounding_google_search": {
                "free_rpd": 500,  # Shared with Flash
                "paid_per_1k_prompts": 35.00,
            },
            "grounding_google_maps": {
                "free_rpd": 500,
                "paid_per_1k_prompts": 25.00,
            },
        },
    ),
    
    # Gemini 2.5 Flash-Lite Preview
    "gemini-2.5-flash-lite-preview-09-2025": ModelPricing(
        model_id="gemini-2.5-flash-lite-preview-09-2025",
        provider=Provider.GEMINI,
        model_type=ModelType.LLM,
        price_per_1k_tokens=None,
        max_tokens=1000000,
        description="Latest model based on Gemini 2.5 Flash-Lite, optimized for cost-efficiency and high throughput",
        metadata={
            "input_price_per_1m_tokens_text": 0.10,
            "input_price_per_1m_tokens_audio": 0.30,
            "output_price_per_1m_tokens": 0.40,
            "cache_price_per_1m_tokens_text": 0.01,
            "cache_price_per_1m_tokens_audio": 0.03,
            "cache_storage_price_per_1m_tokens_per_hour": 1.00,
            "batch_input_price_per_1m_tokens": 0.05,
            "batch_output_price_per_1m_tokens": 0.20,
            "input_price_per_1k_tokens": 0.10 / 1000,
            "output_price_per_1k_tokens": 0.40 / 1000,
            "cached_input_price_per_1k_tokens": 0.01 / 1000,
            "context_window": 1000000,
            "category": "standard",
            "features": ["cost_effective", "multimodal", "preview"],
            "grounding_google_search": {
                "free_rpd": 500,  # Shared with Flash
                "paid_per_1k_prompts": 35.00,
            },
        },
    ),
    
    # Gemini 2.0 Flash
    "gemini-2.0-flash": ModelPricing(
        model_id="gemini-2.0-flash",
        provider=Provider.GEMINI,
        model_type=ModelType.LLM,
        price_per_1k_tokens=None,
        max_tokens=1000000,
        description="Most balanced multimodal model with great performance across all tasks, built for the era of Agents",
        metadata={
            "input_price_per_1m_tokens_text": 0.10,
            "input_price_per_1m_tokens_audio": 0.70,
            "output_price_per_1m_tokens": 0.40,
            "cache_price_per_1m_tokens_text": 0.025,
            "cache_price_per_1m_tokens_audio": 0.175,
            "cache_storage_price_per_1m_tokens_per_hour": 1.00,
            "image_generation_price_per_image": 0.039,
            "image_generation_price_per_1m_tokens": 30.00,  # For image output
            "input_price_per_1k_tokens": 0.10 / 1000,
            "output_price_per_1k_tokens": 0.40 / 1000,
            "cached_input_price_per_1k_tokens": 0.025 / 1000,
            "context_window": 1000000,
            "category": "standard",
            "features": ["multimodal", "agents", "image_generation"],
            "grounding_google_search": {
                "free_rpd": 500,
                "paid_per_1k_prompts": 35.00,
            },
            "grounding_google_maps": {
                "free_rpd": 500,
                "paid_per_1k_prompts": 25.00,
            },
        },
    ),
    
    # Gemini 2.0 Flash-Lite
    "gemini-2.0-flash-lite": ModelPricing(
        model_id="gemini-2.0-flash-lite",
        provider=Provider.GEMINI,
        model_type=ModelType.LLM,
        price_per_1k_tokens=None,
        max_tokens=1000000,
        description="Smallest and most cost-effective model, built for at scale usage",
        metadata={
            "input_price_per_1m_tokens": 0.075,
            "output_price_per_1m_tokens": 0.30,
            "input_price_per_1k_tokens": 0.075 / 1000,
            "output_price_per_1k_tokens": 0.30 / 1000,
            "context_window": 1000000,
            "category": "standard",
            "features": ["cost_effective", "at_scale"],
        },
    ),
    
    # Gemini 2.0 Flash Experimental
    "gemini-2.0-flash-exp": ModelPricing(
        model_id="gemini-2.0-flash-exp",
        provider=Provider.GEMINI,
        model_type=ModelType.LLM,
        price_per_1k_tokens=None,
        max_tokens=8192,  # 8K output limit
        description="Experimental Gemini 2.0 Flash model (not suitable for production)",
        metadata={
            "input_price_per_1m_tokens_text": 0.10,
            "input_price_per_1m_tokens_audio": 0.70,
            "output_price_per_1m_tokens": 0.40,
            "input_price_per_1k_tokens": 0.10 / 1000,
            "output_price_per_1k_tokens": 0.40 / 1000,
            "context_window": 1000000,
            "category": "experimental",
            "features": ["multimodal", "experimental", "thinking_experimental"],
            "deprecated": False,
        },
    ),
    
    # Gemini 2.0 Flash Image Preview
    "gemini-2.0-flash-preview-image-generation": ModelPricing(
        model_id="gemini-2.0-flash-preview-image-generation",
        provider=Provider.GEMINI,
        model_type=ModelType.LLM,
        price_per_1k_tokens=None,
        max_tokens=8192,
        description="Gemini 2.0 Flash model with image generation capabilities",
        metadata={
            "input_price_per_1m_tokens": 0.10,
            "output_price_per_1m_tokens": 0.40,
            "image_generation_price_per_image": 0.039,
            "input_price_per_1k_tokens": 0.10 / 1000,
            "output_price_per_1k_tokens": 0.40 / 1000,
            "context_window": 32768,
            "category": "preview",
            "features": ["multimodal", "image_generation", "preview"],
        },
    ),
    
    # Gemini 3 Pro Preview
    "gemini-3-pro-preview": ModelPricing(
        model_id="gemini-3-pro-preview",
        provider=Provider.GEMINI,
        model_type=ModelType.LLM,
        price_per_1k_tokens=None,
        max_tokens=65536,  # 65K output limit
        description="Our most intelligent model for multimodal understanding, agentic and vibe-coding",
        metadata={
            "input_price_per_1m_tokens": 1.25,  # Estimated based on 2.5 Pro
            "output_price_per_1m_tokens": 10.00,  # Estimated
            "input_price_per_1k_tokens": 1.25 / 1000,
            "output_price_per_1k_tokens": 10.00 / 1000,
            "context_window": 1048576,  # 1M tokens
            "category": "frontier",
            "features": ["multimodal", "agentic", "coding", "thinking", "preview"],
            "grounding_google_search": {
                "free_rpd": 1500,
                "paid_per_1k_prompts": 35.00,
            },
        },
    ),
    
    # Gemini 3 Pro Image Preview
    "gemini-3-pro-image-preview": ModelPricing(
        model_id="gemini-3-pro-image-preview",
        provider=Provider.GEMINI,
        model_type=ModelType.LLM,
        price_per_1k_tokens=None,
        max_tokens=32768,  # 32K output limit
        description="Gemini 3 Pro model with image generation capabilities",
        metadata={
            "input_price_per_1m_tokens": 1.25,
            "output_price_per_1m_tokens": 10.00,
            "image_generation_price_per_image": 0.05,  # Estimated
            "input_price_per_1k_tokens": 1.25 / 1000,
            "output_price_per_1k_tokens": 10.00 / 1000,
            "context_window": 65536,
            "category": "frontier",
            "features": ["multimodal", "image_generation", "preview"],
        },
    ),
    
    # Gemini 3 Flash Preview
    "gemini-3-flash-preview": ModelPricing(
        model_id="gemini-3-flash-preview",
        provider=Provider.GEMINI,
        model_type=ModelType.LLM,
        price_per_1k_tokens=None,
        max_tokens=65536,  # 65K output limit
        description="Our most intelligent model built for speed, combining frontier intelligence with superior search and grounding",
        metadata={
            "input_price_per_1m_tokens_text": 0.30,  # Estimated based on 2.5 Flash
            "input_price_per_1m_tokens_audio": 1.00,
            "output_price_per_1m_tokens": 2.50,
            "input_price_per_1k_tokens": 0.30 / 1000,
            "output_price_per_1k_tokens": 2.50 / 1000,
            "context_window": 1048576,  # 1M tokens
            "category": "standard",
            "features": ["multimodal", "thinking", "preview"],
            "grounding_google_search": {
                "free_rpd": 1500,
                "paid_per_1k_prompts": 35.00,
            },
        },
    ),
    
    # Gemini 2.5 Flash Image
    "gemini-2.5-flash-image": ModelPricing(
        model_id="gemini-2.5-flash-image",
        provider=Provider.GEMINI,
        model_type=ModelType.LLM,
        price_per_1k_tokens=None,
        max_tokens=32768,  # 32K output limit
        description="Gemini 2.5 Flash model with image generation capabilities",
        metadata={
            "input_price_per_1m_tokens": 0.30,
            "output_price_per_1m_tokens": 2.50,
            "image_generation_price_per_image": 0.039,
            "input_price_per_1k_tokens": 0.30 / 1000,
            "output_price_per_1k_tokens": 2.50 / 1000,
            "context_window": 65536,
            "category": "standard",
            "features": ["multimodal", "image_generation"],
        },
    ),
    
    # Gemini 2.5 Flash Native Audio Preview
    "gemini-2.5-flash-native-audio-preview-12-2025": ModelPricing(
        model_id="gemini-2.5-flash-native-audio-preview-12-2025",
        provider=Provider.GEMINI,
        model_type=ModelType.LLM,
        price_per_1k_tokens=None,
        max_tokens=8192,  # 8K output limit
        description="Gemini 2.5 Flash model with native audio generation and live API support",
        metadata={
            "input_price_per_1m_tokens": 0.30,
            "output_price_per_1m_tokens": 2.50,
            "audio_generation_price_per_1k_tokens": 1.00,  # Estimated
            "input_price_per_1k_tokens": 0.30 / 1000,
            "output_price_per_1k_tokens": 2.50 / 1000,
            "context_window": 131072,  # 131K tokens
            "category": "preview",
            "features": ["multimodal", "audio_generation", "live_api", "thinking", "preview"],
        },
    ),
    "gemini-2.5-flash-native-audio-preview-09-2025": ModelPricing(
        model_id="gemini-2.5-flash-native-audio-preview-09-2025",
        provider=Provider.GEMINI,
        model_type=ModelType.LLM,
        price_per_1k_tokens=None,
        max_tokens=8192,
        description="Gemini 2.5 Flash model with native audio generation (older preview)",
        metadata={
            "input_price_per_1m_tokens": 0.30,
            "output_price_per_1m_tokens": 2.50,
            "audio_generation_price_per_1k_tokens": 1.00,
            "input_price_per_1k_tokens": 0.30 / 1000,
            "output_price_per_1k_tokens": 2.50 / 1000,
            "context_window": 131072,
            "category": "preview",
            "features": ["multimodal", "audio_generation", "live_api", "thinking", "preview"],
        },
    ),
    
    # Gemini 2.5 Flash TTS
    "gemini-2.5-flash-preview-tts": ModelPricing(
        model_id="gemini-2.5-flash-preview-tts",
        provider=Provider.GEMINI,
        model_type=ModelType.LLM,
        price_per_1k_tokens=None,
        max_tokens=16384,  # 16K output limit
        description="Gemini 2.5 Flash model optimized for text-to-speech",
        metadata={
            "input_price_per_1m_tokens": 0.30,
            "output_price_per_1m_tokens": 2.50,
            "audio_generation_price_per_1k_tokens": 1.00,
            "input_price_per_1k_tokens": 0.30 / 1000,
            "output_price_per_1k_tokens": 2.50 / 1000,
            "context_window": 8192,
            "category": "preview",
            "features": ["tts", "audio_generation", "preview"],
        },
    ),
    
    # Gemini 2.5 Pro TTS
    "gemini-2.5-pro-preview-tts": ModelPricing(
        model_id="gemini-2.5-pro-preview-tts",
        provider=Provider.GEMINI,
        model_type=ModelType.LLM,
        price_per_1k_tokens=None,
        max_tokens=16384,  # 16K output limit
        description="Gemini 2.5 Pro model optimized for text-to-speech",
        metadata={
            "input_price_per_1m_tokens": 1.25,
            "output_price_per_1m_tokens": 10.00,
            "audio_generation_price_per_1k_tokens": 2.00,  # Estimated
            "input_price_per_1k_tokens": 1.25 / 1000,
            "output_price_per_1k_tokens": 10.00 / 1000,
            "context_window": 8192,
            "category": "preview",
            "features": ["tts", "audio_generation", "preview"],
        },
    ),
}

# Combine all Gemini models
GEMINI_MODELS = {**GEMINI_EMBEDDING_MODELS, **GEMINI_LLM_MODELS}

