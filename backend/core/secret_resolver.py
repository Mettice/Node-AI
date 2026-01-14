"""
Utility to resolve API keys from config, checking vault secrets first.
"""

from typing import Optional
from backend.core.db_secrets import get_secret_value
from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def resolve_api_key(
    config: dict,
    key_name: str,
    user_id: Optional[str] = None,
    fallback_to_settings: bool = True,
) -> Optional[str]:
    """
    Resolve an API key from config, checking vault secrets first.
    
    Priority:
    1. Check for secret_id in config (e.g., "openai_api_key_secret_id")
    2. Check for direct API key value in config (e.g., "openai_api_key")
    3. Fall back to settings if enabled
    
    Args:
        config: Node configuration dictionary
        key_name: Base key name (e.g., "openai_api_key")
        user_id: User ID for vault access (required if using secret_id)
        fallback_to_settings: Whether to fall back to environment settings
        
    Returns:
        API key value or None
    """
    # First, check for secret_id in vault
    secret_id_key = f"{key_name}_secret_id"
    secret_id = config.get(secret_id_key)
    
    # Also check nested config structure (config.config.secret_id)
    if not secret_id and isinstance(config.get("config"), dict):
        secret_id = config.get("config", {}).get(secret_id_key)
    
    if secret_id:
        if not user_id:
            logger.warning(f"Secret ID {secret_id} found but user_id is missing. Cannot retrieve from vault.")
        else:
            try:
                logger.debug(f"Attempting to retrieve {key_name} from vault (secret_id: {secret_id}, user_id: {user_id})")
                api_key = get_secret_value(secret_id, user_id)
                if api_key:
                    logger.info(f"✅ Resolved {key_name} from vault (secret_id: {secret_id})")
                    return api_key
                else:
                    logger.warning(f"Secret {secret_id} not found or empty for user {user_id}, falling back to direct value or settings")
            except Exception as e:
                logger.error(f"Failed to retrieve secret {secret_id} from vault: {e}", exc_info=True)
                logger.warning(f"Falling back to direct value or settings for {key_name}")
    else:
        logger.debug(f"No secret_id found for {key_name} (checked key: {secret_id_key})")
    
    # Second, check for direct API key value in config
    api_key = config.get(key_name)
    if api_key:
        logger.debug(f"Resolved {key_name} from config")
        return api_key
    
    # Third, fall back to settings if enabled
    if fallback_to_settings:
        # Map common key names to settings attributes
        settings_map = {
            "openai_api_key": settings.openai_api_key,
            "anthropic_api_key": settings.anthropic_api_key,
            "gemini_api_key": settings.gemini_api_key,
            "cohere_api_key": settings.cohere_api_key,
            "voyage_api_key": settings.voyage_api_key,
            "pinecone_api_key": settings.pinecone_api_key,
        }
        
        if key_name in settings_map:
            api_key = settings_map[key_name]
            if api_key:
                logger.debug(f"Resolved {key_name} from settings")
                return api_key
    
    logger.warning(f"Could not resolve {key_name} from config, vault, or settings")
    return None

