"""
Cost tracking module.

This module handles:
- Recording execution costs
- Persisting costs to database
- Extracting cost metadata
"""

from datetime import datetime
from typing import Dict, Optional

from backend.core.models import NodeResult
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CostTracker:
    """Tracks and records execution costs."""

    @staticmethod
    async def record_execution_costs(
        execution_id: str,
        workflow_id: str,
        results: Dict[str, NodeResult],
        user_id: Optional[str] = None,
    ) -> None:
        """
        Record execution costs for the cost intelligence system.
        
        This method extracts cost information from node results and stores it
        in a format that can be analyzed by the cost intelligence API.
        
        Args:
            execution_id: The execution ID
            workflow_id: The workflow ID
            results: Dictionary of node results keyed by node ID
            user_id: Optional user ID for cost tracking
        """
        try:
            # Import here to avoid circular dependencies
            from backend.api import cost_intelligence
            
            # Build cost records for each node
            cost_records = []
            
            for node_id, node_result in results.items():
                # Skip nodes with no cost
                if node_result.cost <= 0.0:
                    continue
                
                # Extract node metadata from output if available
                output = node_result.output or {}
                node_type = output.get("_node_type", "unknown")
                node_config = output.get("_node_config", {})
                
                # Extract provider and model from config
                provider = node_config.get("provider")
                model = (
                    node_config.get("openai_model") or 
                    node_config.get("anthropic_model") or 
                    node_config.get("model") or
                    node_config.get("base_model")
                )
                
                # If provider is not directly in config, try to infer from model name
                if not provider and model:
                    model_str = str(model).lower()
                    if "gpt" in model_str or "o1" in model_str or "text-embedding" in model_str:
                        provider = "openai"
                    elif "claude" in model_str:
                        provider = "anthropic"
                    elif "cohere" in model_str:
                        provider = "cohere"
                
                # Build cost record
                cost_record = {
                    "node_id": node_id,
                    "node_type": node_type,
                    "cost": node_result.cost,
                    "tokens_used": node_result.tokens_used,
                    "model": model,
                    "provider": provider,
                    "config": node_config,
                    "duration_ms": node_result.duration_ms,
                    "timestamp": node_result.completed_at.isoformat() if node_result.completed_at else None,
                }
                
                cost_records.append(cost_record)
            
            # Store in cost intelligence module's history (in-memory cache)
            # The _cost_history dict is defined at module level in cost_intelligence
            cost_intelligence._cost_history[execution_id] = cost_records
            
            # Also persist to database for historical tracking
            try:
                from backend.core.cost_storage import record_cost
                
                # Convert workflow_id to UUID if needed
                # Skip if workflow_id is "unknown" or not a valid UUID
                workflow_uuid = None
                if workflow_id and workflow_id != "unknown":
                    try:
                        import uuid
                        # Only try to convert if it looks like a UUID (36 chars)
                        if len(workflow_id) == 36:
                            workflow_uuid = str(uuid.UUID(workflow_id))
                        else:
                            # Not a UUID format, skip it (set to None)
                            workflow_uuid = None
                    except (ValueError, AttributeError):
                        # Invalid UUID format, set to None
                        workflow_uuid = None
                
                # Persist each cost record to database
                for cost_record in cost_records:
                    node_id = cost_record.get("node_id")
                    node_type = cost_record.get("node_type", "unknown")
                    cost_value = cost_record.get("cost", 0.0)
                    
                    if cost_value <= 0:
                        continue
                    
                    # Determine category from node_type
                    category = "other"
                    if "embed" in node_type.lower():
                        category = "embedding"
                    elif "rerank" in node_type.lower():
                        category = "rerank"
                    elif "vector" in node_type.lower() or "search" in node_type.lower():
                        category = "vector_search"
                    elif "chat" in node_type.lower() or "llm" in node_type.lower() or "agent" in node_type.lower():
                        category = "llm"
                    
                    # Extract timestamp
                    timestamp = None
                    if cost_record.get("timestamp"):
                        try:
                            timestamp = datetime.fromisoformat(cost_record["timestamp"].replace('Z', '+00:00'))
                        except (ValueError, AttributeError):
                            pass
                    
                    # Record to database
                    record_cost(
                        execution_id=execution_id,
                        workflow_id=workflow_uuid,
                        user_id=user_id,
                        node_id=node_id or "unknown",
                        node_type=node_type,
                        cost=cost_value,
                        category=category,
                        provider=cost_record.get("provider"),
                        model=cost_record.get("model"),
                        tokens_used=cost_record.get("tokens_used"),
                        duration_ms=cost_record.get("duration_ms", 0),
                        config=cost_record.get("config"),
                        metadata=cost_record.get("metadata"),
                        timestamp=timestamp,
                    )
            except Exception as db_error:
                # Don't fail execution if database persistence fails
                logger.warning(f"Failed to persist costs to database: {db_error}", exc_info=True)
            
            logger.debug(
                f"Recorded costs for execution {execution_id}: "
                f"{len(cost_records)} nodes, total cost: ${sum(r['cost'] for r in cost_records):.4f}"
            )
            
        except Exception as e:
            # Don't fail execution if cost recording fails
            logger.warning(f"Failed to record execution costs: {e}", exc_info=True)

