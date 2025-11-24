"""
Unified observability adapter.

Supports multiple observability backends:
- LangSmith
- LangFuse
- Internal database storage
"""

from typing import List, Optional, Dict, Any
from backend.utils.logger import get_logger
from backend.core.observability import Span, Trace
from backend.core.db_settings import get_observability_settings
from backend.config import settings

logger = get_logger(__name__)


class ObservabilityAdapter:
    """
    Unified adapter for multiple observability backends.
    
    Automatically routes traces/spans to all configured backends.
    Supports both global (env) and user-specific settings.
    """
    
    def __init__(self, user_id: Optional[str] = None):
        self.adapters: List[Any] = []
        self.user_id = user_id
        
        # Get settings (user-specific first, then fall back to env)
        observability_config = self._get_observability_config()
        
        # Add LangSmith adapter if configured
        langsmith_key = observability_config.get("langsmith_api_key")
        if langsmith_key:
            try:
                from backend.core.observability_langsmith import LangSmithAdapter
                self.adapters.append(
                    LangSmithAdapter(
                        api_key=langsmith_key,
                        project=observability_config.get("langsmith_project", "nodeflow"),
                    )
                )
                logger.debug(f"LangSmith adapter initialized for user: {user_id or 'global'}")
            except Exception as e:
                logger.warning(f"Failed to initialize LangSmith adapter: {e}")
        
        # Add LangFuse adapter if configured
        langfuse_public = observability_config.get("langfuse_public_key")
        langfuse_secret = observability_config.get("langfuse_secret_key")
        if langfuse_public and langfuse_secret:
            try:
                from backend.core.observability_langfuse import LangFuseAdapter
                self.adapters.append(
                    LangFuseAdapter(
                        public_key=langfuse_public,
                        secret_key=langfuse_secret,
                        host=observability_config.get("langfuse_host", "https://cloud.langfuse.com"),
                    )
                )
                logger.debug(f"LangFuse adapter initialized for user: {user_id or 'global'}")
            except Exception as e:
                logger.warning(f"Failed to initialize LangFuse adapter: {e}")
        
        if len(self.adapters) > 0:
            logger.debug(f"Observability adapter initialized with {len(self.adapters)} backend(s) for user: {user_id or 'global'}")
    
    def _get_observability_config(self) -> Dict[str, Any]:
        """Get observability configuration (user-specific first, then env fallback)."""
        config: Dict[str, Any] = {}
        
        # Try user-specific settings first
        if self.user_id:
            try:
                user_settings = get_observability_settings(self.user_id)
                if user_settings.get("enabled", True):
                    config.update(user_settings)
            except Exception as e:
                logger.debug(f"Failed to get user observability settings: {e}")
        
        # Fall back to environment variables if user settings not available
        if not config.get("langsmith_api_key") and settings.langsmith_api_key:
            config["langsmith_api_key"] = settings.langsmith_api_key
            config["langsmith_project"] = settings.langsmith_project
        
        if not config.get("langfuse_public_key") and settings.langfuse_public_key:
            config["langfuse_public_key"] = settings.langfuse_public_key
            config["langfuse_secret_key"] = settings.langfuse_secret_key
            config["langfuse_host"] = settings.langfuse_host
        
        return config
    
    def start_trace(
        self,
        trace_id: str,
        workflow_id: str,
        execution_id: str,
        query: Optional[str] = None,
    ) -> List[Any]:
        """Start a trace in all configured backends."""
        results = []
        for adapter in self.adapters:
            try:
                result = adapter.start_trace(trace_id, workflow_id, execution_id, query)
                if result:
                    results.append(result)
            except Exception as e:
                logger.warning(f"Failed to start trace in {type(adapter).__name__}: {e}")
        return results
    
    def log_span(self, trace_id: str, span: Span):
        """Log a span to all configured backends."""
        for adapter in self.adapters:
            try:
                adapter.log_span(trace_id, span)
            except Exception as e:
                logger.warning(f"Failed to log span in {type(adapter).__name__}: {e}")
    
    def complete_trace(self, trace_id: str, trace: Trace):
        """Complete a trace in all configured backends."""
        for adapter in self.adapters:
            try:
                adapter.complete_trace(trace_id, trace)
            except Exception as e:
                logger.warning(f"Failed to complete trace in {type(adapter).__name__}: {e}")


# Global adapter instance (for backward compatibility)
_observability_adapter: Optional[ObservabilityAdapter] = None


def get_observability_adapter(user_id: Optional[str] = None) -> ObservabilityAdapter:
    """
    Get observability adapter for a user.
    
    Args:
        user_id: Optional user ID. If provided, uses user-specific settings.
                 If None, uses global (env) settings.
    
    Returns:
        ObservabilityAdapter instance
    """
    # If user_id provided, create user-specific adapter
    if user_id:
        return ObservabilityAdapter(user_id=user_id)
    
    # Otherwise, use global adapter (backward compatibility)
    global _observability_adapter
    if _observability_adapter is None:
        _observability_adapter = ObservabilityAdapter()
    return _observability_adapter

