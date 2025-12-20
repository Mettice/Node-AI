"""
LLM Configuration Mixin for AI-Native Nodes

This mixin provides consistent LLM configuration patterns across all AI-native nodes.
"""

from typing import Dict, Any, List
from backend.core.secret_resolver import resolve_api_key
from backend.utils.model_pricing import get_available_models, ModelType, calculate_llm_cost
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class LLMConfigMixin:
    """Mixin for consistent LLM configuration across AI-native nodes."""

    def _get_openai_model_list(self) -> List[str]:
        """Get list of available OpenAI LLM models from pricing system."""
        try:
            models = get_available_models(provider="openai", model_type=ModelType.LLM)
            model_list = [model.model_id for model in models if not (model.metadata or {}).get("deprecated", False)]
            if not model_list:
                logger.warning("No OpenAI LLM models found in pricing system, using fallback list")
                return ["gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"]
            return model_list
        except Exception as e:
            logger.warning(f"Failed to get OpenAI models: {e}")
            return ["gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"]

    def _get_anthropic_model_list(self) -> List[str]:
        """Get list of available Anthropic LLM models from pricing system."""
        try:
            models = get_available_models(provider="anthropic", model_type=ModelType.LLM)
            model_list = [model.model_id for model in models if not (model.metadata or {}).get("deprecated", False)]
            if not model_list:
                logger.warning("No Anthropic LLM models found in pricing system, using fallback list")
                return ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"]
            return model_list
        except Exception as e:
            logger.warning(f"Failed to get Anthropic models: {e}")
            return ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"]

    def _get_gemini_model_list(self) -> List[str]:
        """Get list of available Gemini LLM models from pricing system."""
        try:
            models = get_available_models(provider="gemini", model_type=ModelType.LLM)
            model_list = [model.model_id for model in models if not (model.metadata or {}).get("deprecated", False)]
            if not model_list:
                logger.warning("No Gemini LLM models found in pricing system, using fallback list")
                return ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"]
            return model_list
        except Exception as e:
            logger.warning(f"Failed to get Gemini models: {e}")
            return ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"]

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
                "default": "gpt-4o-mini",
                "title": "Model",
                "description": "Model to use (fallback if provider-specific model not set)",
            },
            # OpenAI configuration
            "openai_model": {
                "type": "string",
                "enum": self._get_openai_model_list(),
                "default": "gpt-4o-mini",
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
                "default": "claude-3-5-sonnet-20241022",
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
                "default": "gemini-2.0-flash-exp",
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
            model = config.get("openai_model") or config.get("model", "gpt-4o-mini")
            api_key = resolve_api_key(config, "openai_api_key", user_id=user_id)
            if not api_key:
                raise ValueError("OpenAI API key not found. Please configure it in the node settings or environment variables.")
        elif provider == "anthropic":
            model = config.get("anthropic_model") or config.get("model", "claude-3-5-sonnet-20241022")
            api_key = resolve_api_key(config, "anthropic_api_key", user_id=user_id)
            if not api_key:
                raise ValueError("Anthropic API key not found. Please configure it in the node settings or environment variables.")
        elif provider == "gemini":
            model = config.get("gemini_model") or config.get("model", "gemini-2.0-flash-exp")
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
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        elif provider == "anthropic":
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=api_key)
            
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
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