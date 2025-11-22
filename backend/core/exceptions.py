"""
Custom exceptions for NodeAI backend.

This module defines all custom exceptions used throughout the application.
These exceptions provide clear error messages and help with debugging.
"""


class NodeAIError(Exception):
    """Base exception for all NodeAI errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# ============================================
# Workflow Exceptions
# ============================================


class WorkflowError(NodeAIError):
    """Base exception for workflow-related errors."""

    pass


class WorkflowNotFoundError(WorkflowError):
    """Raised when a workflow is not found."""

    def __init__(self, workflow_id: str):
        super().__init__(f"Workflow not found: {workflow_id}")
        self.workflow_id = workflow_id


class WorkflowValidationError(WorkflowError):
    """Raised when a workflow fails validation."""

    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message, {"errors": errors or []})
        self.errors = errors or []


class WorkflowExecutionError(WorkflowError):
    """Raised when workflow execution fails."""

    def __init__(self, message: str, workflow_id: str | None = None):
        super().__init__(message, {"workflow_id": workflow_id})
        self.workflow_id = workflow_id


# ============================================
# Node Exceptions
# ============================================


class NodeError(NodeAIError):
    """Base exception for node-related errors."""

    pass


class NodeNotFoundError(NodeError):
    """Raised when a node type is not found in the registry."""

    def __init__(self, node_type: str):
        super().__init__(f"Node type not found: {node_type}")
        self.node_type = node_type


class NodeExecutionError(NodeError):
    """Raised when a node execution fails."""

    def __init__(
        self,
        message: str,
        node_id: str | None = None,
        node_type: str | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(
            message,
            {
                "node_id": node_id,
                "node_type": node_type,
                "original_error": str(original_error) if original_error else None,
            },
        )
        self.node_id = node_id
        self.node_type = node_type
        self.original_error = original_error


class NodeValidationError(NodeError):
    """Raised when node configuration is invalid."""

    def __init__(self, message: str, node_id: str | None = None, errors: list[str] | None = None):
        super().__init__(message, {"node_id": node_id, "errors": errors or []})
        self.node_id = node_id
        self.errors = errors or []


# ============================================
# Execution Exceptions
# ============================================


class ExecutionError(NodeAIError):
    """Base exception for execution-related errors."""

    pass


class ExecutionNotFoundError(ExecutionError):
    """Raised when an execution is not found."""

    def __init__(self, execution_id: str):
        super().__init__(f"Execution not found: {execution_id}")
        self.execution_id = execution_id


class ExecutionTimeoutError(ExecutionError):
    """Raised when execution times out."""

    def __init__(self, execution_id: str, timeout_seconds: int):
        super().__init__(
            f"Execution timed out after {timeout_seconds} seconds",
            {"execution_id": execution_id, "timeout_seconds": timeout_seconds},
        )
        self.execution_id = execution_id
        self.timeout_seconds = timeout_seconds


# ============================================
# Graph/Edge Exceptions
# ============================================


class GraphError(NodeAIError):
    """Base exception for graph-related errors."""

    pass


class CircularDependencyError(GraphError):
    """Raised when a workflow has circular dependencies."""

    def __init__(self, cycle: list[str]):
        cycle_str = " -> ".join(cycle)
        super().__init__(
            f"Circular dependency detected: {cycle_str}",
            {"cycle": cycle},
        )
        self.cycle = cycle


class InvalidConnectionError(GraphError):
    """Raised when nodes are connected incorrectly."""

    def __init__(self, source_id: str, target_id: str, reason: str):
        super().__init__(
            f"Invalid connection from {source_id} to {target_id}: {reason}",
            {"source_id": source_id, "target_id": target_id, "reason": reason},
        )
        self.source_id = source_id
        self.target_id = target_id
        self.reason = reason


# ============================================
# Storage Exceptions
# ============================================


class StorageError(NodeAIError):
    """Base exception for storage-related errors."""

    pass


class StorageNotFoundError(StorageError):
    """Raised when storage resource is not found."""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            f"{resource_type} not found: {resource_id}",
            {"resource_type": resource_type, "resource_id": resource_id},
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


# ============================================
# API Exceptions
# ============================================


class APIError(NodeAIError):
    """Base exception for API-related errors."""

    pass


class InvalidRequestError(APIError):
    """Raised when API request is invalid."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message, {"field": field})
        self.field = field

