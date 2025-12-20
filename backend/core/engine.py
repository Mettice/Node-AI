"""
Workflow execution engine for NodeAI.

This module is a backward-compatibility shim.
The actual implementation has been modularized into backend/core/engine/

All functionality has been split into:
- backend/core/engine/engine.py - Main orchestration
- backend/core/engine/workflow_validator.py - Validation & graph analysis
- backend/core/engine/data_collector.py - Data collection & merging
- backend/core/engine/node_executor.py - Node execution
- backend/core/engine/tracing.py - Tracing & observability
- backend/core/engine/cost_tracker.py - Cost tracking
"""

# Import from the modularized engine for backward compatibility
from backend.core.engine.engine import WorkflowEngine, engine

__all__ = ["WorkflowEngine", "engine"]
