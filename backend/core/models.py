"""
Data models for NodeAI backend.

This module defines all Pydantic models used for workflows, nodes, edges,
executions, and related data structures.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, computed_field


# ============================================
# Enums
# ============================================


class ExecutionStatus(str, Enum):
    """Execution status values."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeStatus(str, Enum):
    """Node execution status values."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# ============================================
# Position & Geometry
# ============================================


class Position(BaseModel):
    """2D position coordinates for nodes on canvas."""

    x: float = Field(description="X coordinate")
    y: float = Field(description="Y coordinate")


# ============================================
# Node Models
# ============================================


class Node(BaseModel):
    """Represents a single node in a workflow."""

    id: str = Field(description="Unique node identifier")
    type: str = Field(description="Node type (e.g., 'text_input', 'chunk', 'openai_embed')")
    position: Position = Field(description="Node position on canvas")
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Node configuration and data",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "node-1",
                "type": "text_input",
                "position": {"x": 100, "y": 200},
                "data": {"text": "Hello world"},
            }
        }


# ============================================
# Edge Models
# ============================================


class Edge(BaseModel):
    """Represents a connection between two nodes."""

    id: str = Field(description="Unique edge identifier")
    source: str = Field(description="Source node ID")
    target: str = Field(description="Target node ID")
    sourceHandle: Optional[str] = Field(
        default=None,
        description="Source handle identifier (for multiple outputs)",
    )
    targetHandle: Optional[str] = Field(
        default=None,
        description="Target handle identifier (for multiple inputs)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "edge-1",
                "source": "node-1",
                "target": "node-2",
                "sourceHandle": None,
                "targetHandle": None,
            }
        }


# ============================================
# Workflow Models
# ============================================


class Workflow(BaseModel):
    """Represents a complete workflow with nodes and edges."""

    id: Optional[str] = Field(default=None, description="Workflow ID (generated if not provided)")
    name: str = Field(description="Workflow name")
    description: Optional[str] = Field(default=None, description="Workflow description")
    nodes: List[Node] = Field(default_factory=list, description="List of nodes in the workflow")
    edges: List[Edge] = Field(default_factory=list, description="List of edges connecting nodes")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    tags: List[str] = Field(default_factory=list, description="Workflow tags")
    is_template: bool = Field(default=False, description="Whether this is a template workflow")
    is_deployed: bool = Field(default=False, description="Whether this workflow is deployed")
    deployed_at: Optional[datetime] = Field(default=None, description="Deployment timestamp")
    owner_id: Optional[str] = Field(default=None, description="User ID of the workflow owner")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "workflow-1",
                "name": "Simple RAG",
                "description": "Basic RAG workflow",
                "nodes": [
                    {
                        "id": "node-1",
                        "type": "text_input",
                        "position": {"x": 100, "y": 100},
                        "data": {"text": "Hello"},
                    }
                ],
                "edges": [],
                "tags": ["rag", "basic"],
                "is_template": False,
            }
        }


# ============================================
# Execution Models
# ============================================


class NodeResult(BaseModel):
    """Result of a single node execution."""

    node_id: str = Field(description="Node ID")
    status: NodeStatus = Field(description="Execution status")
    output: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Node output data",
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")
    cost: float = Field(default=0.0, description="Cost in USD")
    duration_ms: int = Field(default=0, description="Execution duration in milliseconds")
    started_at: datetime = Field(description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    tokens_used: Optional[Dict[str, int]] = Field(
        default=None,
        description="Token usage (input, output, total)",
    )


class ExecutionStep(BaseModel):
    """A single step in the execution trace."""

    node_id: str = Field(description="Node ID")
    timestamp: datetime = Field(description="Step timestamp")
    action: str = Field(description="Action type (started, completed, error)")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Additional step data")


class Execution(BaseModel):
    """Represents a workflow execution."""

    id: str = Field(description="Unique execution identifier")
    workflow_id: str = Field(description="Workflow ID that was executed")
    status: ExecutionStatus = Field(description="Execution status")
    started_at: datetime = Field(description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    total_cost: float = Field(default=0.0, description="Total cost in USD")
    results: Dict[str, NodeResult] = Field(
        default_factory=dict,
        description="Results for each node (keyed by node ID)",
    )
    trace: List[ExecutionStep] = Field(
        default_factory=list,
        description="Execution trace (step-by-step timeline)",
    )
    error: Optional[str] = Field(default=None, description="Error message if execution failed")

    @computed_field
    @property
    def duration_ms(self) -> int:
        """Calculate total execution duration in milliseconds."""
        if self.completed_at and self.started_at:
            # Execution completed - return final duration
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() * 1000)
        elif self.started_at and self.status == ExecutionStatus.RUNNING:
            # Execution still running - return current duration
            from datetime import datetime
            delta = datetime.now() - self.started_at
            return int(delta.total_seconds() * 1000)
        return 0

    class Config:
        json_schema_extra = {
            "example": {
                "id": "exec-1",
                "workflow_id": "workflow-1",
                "status": "completed",
                "started_at": "2025-11-09T12:00:00Z",
                "completed_at": "2025-11-09T12:00:05Z",
                "total_cost": 0.05,
                "results": {},
                "trace": [],
            }
        }


# ============================================
# Execution Request/Response Models
# ============================================


class ExecutionRequest(BaseModel):
    """Request to execute a workflow."""

    workflow: Workflow = Field(description="Workflow to execute")
    async_execution: bool = Field(
        default=False,
        description="Whether to execute asynchronously",
    )
    timeout_seconds: Optional[int] = Field(
        default=None,
        description="Execution timeout in seconds",
    )
    use_intelligent_routing: Optional[bool] = Field(
        default=None,
        description="Use intelligent data routing (LLM-powered semantic mapping). If None, uses global setting.",
    )


class ExecutionResponse(BaseModel):
    """Response from workflow execution."""

    execution_id: str = Field(description="Execution ID")
    status: ExecutionStatus = Field(description="Current execution status")
    started_at: str = Field(description="Start timestamp")
    completed_at: Optional[str] = Field(default=None, description="Completion timestamp")
    total_cost: float = Field(default=0.0, description="Total cost in USD")
    duration_ms: int = Field(default=0, description="Execution duration in milliseconds")
    results: Optional[Dict[str, NodeResult]] = Field(
        default=None,
        description="Node execution results"
    )


# ============================================
# Node Metadata Models
# ============================================


class NodeInputSchema(BaseModel):
    """Schema for node input."""

    name: str = Field(description="Input name")
    type: str = Field(description="Input type (e.g., 'string', 'array', 'object')")
    description: Optional[str] = Field(default=None, description="Input description")
    required: bool = Field(default=True, description="Whether input is required")


class NodeOutputSchema(BaseModel):
    """Schema for node output."""

    name: str = Field(description="Output name")
    type: str = Field(description="Output type")
    description: Optional[str] = Field(default=None, description="Output description")


class NodeMetadata(BaseModel):
    """Metadata about a node type."""

    type: str = Field(description="Node type identifier")
    name: str = Field(description="Display name")
    description: str = Field(description="Node description")
    category: str = Field(description="Node category (input, processing, embedding, etc.)")
    icon: Optional[str] = Field(default=None, description="Icon identifier")
    inputs: List[NodeInputSchema] = Field(
        default_factory=list,
        description="Input schemas",
    )
    outputs: List[NodeOutputSchema] = Field(
        default_factory=list,
        description="Output schemas",
    )
    config_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration JSON schema",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "text_input",
                "name": "Text Input",
                "description": "Input text for processing",
                "category": "input",
                "icon": "text",
                "inputs": [],
                "outputs": [
                    {"name": "text", "type": "string", "description": "Input text"},
                ],
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "title": "Text",
                            "description": "Enter text to process",
                        }
                    },
                    "required": ["text"],
                },
            }
        }

