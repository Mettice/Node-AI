"""
LLM Configuration Mixin for AI-Native Nodes

This mixin provides consistent LLM configuration patterns across all AI-native nodes.
"""

from typing import Dict, Any, List
from backend.core.secret_resolver import resolve_api_key
from backend.utils.model_pricing import calculate_llm_cost
from backend.utils.model_catalog import get_default_model, list_model_ids, llm_request_options, resolve_model
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class LLMConfigMixin:
    """Mixin for consistent LLM configuration across AI-native nodes."""

    def _get_openai_model_list(self) -> List[str]:
        return list_model_ids("openai")

    def _get_anthropic_model_list(self) -> List[str]:
        return list_model_ids("anthropic")

    def _get_gemini_model_list(self) -> List[str]:
        return list_model_ids("gemini")

    def _get_llm_schema_section(self) -> Dict[str, Any]:
        """Get the standard LLM configuration schema section.
        
        This matches the schema pattern used in CrewAI and Advanced NLP nodes
        for consistency across the codebase.
        """
        return {
            # Provider selection (matches CrewAI pattern)
            "provider": {
                "type": "string",
                "enum": ["openai", "anthropic", "gemini"],
                "default": "openai",
                "title": "Provider",
                "description": "LLM provider to use",
            },
            # Fallback model field (matches CrewAI pattern)
            "model": {
                "type": "string",
                "default": get_default_model("openai"),
                "title": "Model",
                "description": "Model to use (fallback if provider-specific model not set)",
            },
            # OpenAI configuration
            "openai_model": {
                "type": "string",
                "enum": self._get_openai_model_list(),
                "default": get_default_model("openai"),
                "title": "OpenAI Model",
                "description": "OpenAI model to use",
            },
            "openai_api_key": {
                "type": "string",
                "title": "OpenAI API Key",
                "description": "OpenAI API key (optional, uses vault secret or environment variable if not provided)",
            },
            # Anthropic configuration
            "anthropic_model": {
                "type": "string",
                "enum": self._get_anthropic_model_list(),
                "default": get_default_model("anthropic"),
                "title": "Anthropic Model", 
                "description": "Anthropic model to use",
            },
            "anthropic_api_key": {
                "type": "string",
                "title": "Anthropic API Key",
                "description": "Anthropic API key (optional, uses vault secret or environment variable if not provided)",
            },
            # Gemini configuration
            "gemini_model": {
                "type": "string",
                "enum": self._get_gemini_model_list(),
                "default": get_default_model("gemini"),
                "title": "Gemini Model",
                "description": "Google Gemini model to use",
            },
            "gemini_api_key": {
                "type": "string", 
                "title": "Gemini API Key",
                "description": "Google Gemini API key (optional, uses vault secret or environment variable if not provided)",
            },
            # Common parameters
            "temperature": {
                "type": "number",
                "default": 0.1,
                "minimum": 0,
                "maximum": 2,
                "title": "Temperature",
                "description": "Sampling temperature for response randomness",
            },
        }

    def _resolve_llm_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve LLM configuration with provider-specific model and API key."""
        provider = config.get("provider", "openai")
        user_id = config.get("_user_id")
        
        # Handle provider-specific model selection
        if provider == "openai":
            model = resolve_model("openai", config.get("openai_model") or config.get("model"))
            api_key = resolve_api_key(config, "openai_api_key", user_id=user_id)
            if not api_key:
                raise ValueError("OpenAI API key not found. Please configure it in the node settings or environment variables.")
        elif provider == "anthropic":
            model = resolve_model("anthropic", config.get("anthropic_model") or config.get("model"))
            api_key = resolve_api_key(config, "anthropic_api_key", user_id=user_id)
            if not api_key:
                raise ValueError("Anthropic API key not found. Please configure it in the node settings or environment variables.")
        elif provider == "gemini":
            model = resolve_model("gemini", config.get("gemini_model") or config.get("model"))
            api_key = resolve_api_key(config, "gemini_api_key", user_id=user_id)
            if not api_key:
                raise ValueError("Gemini API key not found. Please configure it in the node settings or environment variables.")
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        temperature = config.get("temperature", 0.1)
        
        return {
            "provider": provider,
            "model": model,
            "api_key": api_key,
            "temperature": temperature
        }

    async def _call_llm(self, prompt: str, llm_config: Dict[str, Any], max_tokens: int = 2000) -> str:
        """Call LLM with consistent pattern across providers."""
        provider = llm_config["provider"]
        model = llm_config["model"]
        api_key = llm_config["api_key"]
        temperature = llm_config["temperature"]
        
        if provider == "openai":
            import openai
            client = openai.AsyncOpenAI(api_key=api_key)
            
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **llm_request_options("openai", model, temperature, max_tokens),
            )
            
            return response.choices[0].message.content
            
        elif provider == "anthropic":
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=api_key)
            
            response = await client.messages.create(
                model=model,
                **llm_request_options("anthropic", model, temperature, max_tokens),
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Models that think first return thinking blocks before the text
            return "".join(block.text for block in response.content if block.type == "text")
            
        elif provider == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                
                model_obj = genai.GenerativeModel(model)
                response = await model_obj.generate_content_async(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    )
                )
                
                return response.text
            except ImportError:
                raise ValueError("google-generativeai not installed. Install with: pip install google-generativeai")
                
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _estimate_llm_cost(self, prompt: str, response: str, llm_config: Dict[str, Any]) -> float:
        """Estimate LLM cost using centralized pricing."""
        try:
            provider = llm_config["provider"]
            model = llm_config["model"]
            
            input_tokens = len(prompt.split()) * 1.3  # Rough token estimation
            output_tokens = len(response.split()) * 1.3
            
            return calculate_llm_cost(
                provider=provider,
                model_id=model,
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens)
            )
        except Exception as e:
            logger.warning(f"Failed to calculate LLM cost: {e}")
            return 0.01  # Fallback cost estimate