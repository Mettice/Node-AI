"""
Agent Lightning Integration Helper.

Provides optional integration with Microsoft Agent Lightning for agent optimization.
This module handles the optional dependency and provides a clean interface.
"""

from typing import Any, Dict, Optional, Callable
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Try to import Agent Lightning (optional dependency)
AGENT_LIGHTNING_AVAILABLE = False
try:
    import agentlightning as agl
    AGENT_LIGHTNING_AVAILABLE = True
    logger.info("Agent Lightning available - agent optimization enabled")
except ImportError:
    logger.debug("Agent Lightning not installed - agent optimization disabled")
    agl = None


class AgentLightningWrapper:
    """
    Wrapper for Agent Lightning integration.
    
    Provides a clean interface that gracefully handles when Agent Lightning
    is not installed or disabled.
    """
    
    def __init__(self, enabled: bool = False):
        """
        Initialize Agent Lightning wrapper.
        
        Args:
            enabled: Whether Agent Lightning is enabled
        """
        self.enabled = enabled and AGENT_LIGHTNING_AVAILABLE
        self._trainer: Optional[Any] = None
        
        if self.enabled:
            logger.info("Agent Lightning wrapper initialized and enabled")
        elif enabled and not AGENT_LIGHTNING_AVAILABLE:
            logger.warning(
                "Agent Lightning requested but not installed. "
                "Install with: pip install agentlightning"
            )
    
    def emit_reward(self, reward: float, metadata: Optional[Dict[str, Any]] = None):
        """
        Emit a reward signal for agent optimization.
        
        Args:
            reward: Reward value (typically 0.0 to 1.0)
            metadata: Optional metadata about the reward
        """
        if not self.enabled:
            return
        
        try:
            if agl:
                agl.emit_reward(reward)
                if metadata:
                    logger.debug(f"Agent Lightning reward emitted: {reward}, metadata: {metadata}")
                else:
                    logger.debug(f"Agent Lightning reward emitted: {reward}")
        except Exception as e:
            logger.warning(f"Failed to emit Agent Lightning reward: {e}")
    
    def emit_task(self, task: Dict[str, Any]):
        """
        Emit a task for agent optimization.
        
        Args:
            task: Task dictionary
        """
        if not self.enabled:
            return
        
        try:
            if agl:
                agl.emit_task(task)
                logger.debug(f"Agent Lightning task emitted: {task.get('id', 'unknown')}")
        except Exception as e:
            logger.warning(f"Failed to emit Agent Lightning task: {e}")
    
    def emit_span(self, span_type: str, data: Dict[str, Any]):
        """
        Emit a span for agent optimization.
        
        Args:
            span_type: Type of span (e.g., 'llm_call', 'tool_call')
            data: Span data
        """
        if not self.enabled:
            return
        
        try:
            if agl:
                agl.emit_span(span_type, data)
                logger.debug(f"Agent Lightning span emitted: {span_type}")
        except Exception as e:
            logger.warning(f"Failed to emit Agent Lightning span: {e}")
    
    def rollout(self, func: Callable):
        """
        Decorator to mark a function for Agent Lightning rollout.
        
        Args:
            func: Function to wrap
            
        Returns:
            Wrapped function
        """
        if not self.enabled:
            return func
        
        try:
            if agl:
                return agl.rollout(func)
        except Exception as e:
            logger.warning(f"Failed to apply Agent Lightning rollout decorator: {e}")
        
        return func
    
    def create_trainer(
        self,
        algorithm: Optional[str] = "apo",
        initial_resources: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """
        Create an Agent Lightning trainer.
        
        Args:
            algorithm: Algorithm to use ('apo' for Automatic Prompt Optimization)
            initial_resources: Initial resources (prompts, etc.)
            
        Returns:
            Trainer instance or None if not enabled
        """
        if not self.enabled:
            return None
        
        try:
            if agl:
                # Map algorithm string to Agent Lightning algorithm
                if algorithm == "apo":
                    algo = agl.APO()
                else:
                    logger.warning(f"Unknown algorithm: {algorithm}, using APO")
                    algo = agl.APO()
                
                trainer = agl.Trainer(
                    algorithm=algo,
                    initial_resources=initial_resources or {},
                )
                self._trainer = trainer
                logger.info(f"Agent Lightning trainer created with algorithm: {algorithm}")
                return trainer
        except Exception as e:
            logger.error(f"Failed to create Agent Lightning trainer: {e}")
        
        return None


def get_agent_lightning_wrapper(config: Dict[str, Any]) -> AgentLightningWrapper:
    """
    Get an Agent Lightning wrapper from node config.
    
    Args:
        config: Node configuration dictionary
        
    Returns:
        AgentLightningWrapper instance
    """
    enabled = config.get("enable_agent_lightning", False)
    return AgentLightningWrapper(enabled=enabled)


def calculate_simple_reward(
    result: Dict[str, Any],
    expected_output: Optional[str] = None,
    success_criteria: Optional[Callable] = None,
) -> float:
    """
    Calculate a simple reward based on result quality.
    
    This is a basic implementation - users can provide custom reward functions.
    
    Args:
        result: Agent execution result
        expected_output: Optional expected output for comparison
        success_criteria: Optional custom function to evaluate success
        
    Returns:
        Reward value between 0.0 and 1.0
    """
    if success_criteria:
        try:
            return 1.0 if success_criteria(result) else 0.0
        except Exception as e:
            logger.warning(f"Error in custom reward function: {e}")
            return 0.5
    
    # Default: check if result has output and no errors
    has_output = bool(result.get("output"))
    has_error = bool(result.get("error"))
    
    if has_error:
        return 0.0
    elif has_output:
        return 1.0
    else:
        return 0.5

