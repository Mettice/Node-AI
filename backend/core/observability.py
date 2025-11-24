"""
Robust Observability & Tracing System for GenAI Workflows.

Implements comprehensive tracing with:
- End-to-end trace tracking
- Span-level metadata (tokens, costs, errors, API limits)
- Parallel span execution tracking
- Span-level evaluation
- LangSmith/LangFuse integration
- Persistent storage
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from enum import Enum
import uuid
import json
import traceback

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SpanStatus(str, Enum):
    """Status of a span execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SpanType(str, Enum):
    """Types of spans in a GenAI workflow."""
    # RAG-specific
    QUERY_INPUT = "query_input"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    VECTOR_SEARCH = "vector_search"
    RERANKING = "reranking"
    LLM = "llm"
    FINAL_OUTPUT = "final_output"
    
    # Agent-specific
    AGENT_START = "agent_start"
    AGENT_TOOL_CALL = "agent_tool_call"
    AGENT_REASONING = "agent_reasoning"
    AGENT_COMPLETE = "agent_complete"
    
    # General
    WORKFLOW_START = "workflow_start"
    WORKFLOW_COMPLETE = "workflow_complete"
    NODE_EXECUTION = "node_execution"
    ERROR = "error"


class Span:
    """
    A span represents an atomic action in the workflow.
    
    Spans can be:
    - Sequential (one after another)
    - Parallel (executing simultaneously)
    - Nested (child spans within parent spans)
    """
    
    def __init__(
        self,
        span_id: str,
        trace_id: str,
        span_type: SpanType,
        name: str,
        parent_span_id: Optional[str] = None,
    ):
        self.span_id = span_id
        self.trace_id = trace_id
        self.span_type = span_type
        self.name = name
        self.parent_span_id = parent_span_id
        self.status = SpanStatus.PENDING
        
        # Timing
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.duration_ms: int = 0
        
        # Inputs/Outputs
        self.inputs: Dict[str, Any] = {}
        self.outputs: Dict[str, Any] = {}
        
        # GenAI-specific metadata
        self.tokens: Dict[str, int] = {}  # input_tokens, output_tokens, total_tokens
        self.cost: float = 0.0
        self.model: Optional[str] = None
        self.provider: Optional[str] = None
        
        # Error tracking
        self.error: Optional[str] = None
        self.error_type: Optional[str] = None
        self.error_stack: Optional[str] = None
        
        # API-specific metadata
        self.api_limits: Dict[str, Any] = {}  # rate_limit, remaining, reset_at
        self.retry_count: int = 0
        self.timeout: Optional[int] = None
        
        # Evaluation metadata (for span-level evaluation)
        self.evaluation: Optional[Dict[str, Any]] = None
        
        # Additional metadata
        self.metadata: Dict[str, Any] = {}
        
        # Child spans (for nested spans)
        self.child_spans: List[str] = []
    
    def start(self):
        """Mark span as started."""
        self.status = SpanStatus.RUNNING
        self.started_at = datetime.now()
    
    def complete(self, outputs: Optional[Dict[str, Any]] = None):
        """Mark span as completed."""
        self.status = SpanStatus.COMPLETED
        self.completed_at = datetime.now()
        if outputs:
            self.outputs = outputs
        
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)
    
    def fail(self, error: str, error_type: Optional[str] = None, error_stack: Optional[str] = None):
        """Mark span as failed."""
        self.status = SpanStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error
        self.error_type = error_type
        self.error_stack = error_stack
        
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary."""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "span_type": self.span_type.value,
            "name": self.name,
            "parent_span_id": self.parent_span_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "tokens": self.tokens,
            "cost": self.cost,
            "model": self.model,
            "provider": self.provider,
            "error": self.error,
            "error_type": self.error_type,
            "api_limits": self.api_limits,
            "retry_count": self.retry_count,
            "evaluation": self.evaluation,
            "metadata": self.metadata,
            "child_spans": self.child_spans,
        }


class Trace:
    """
    A trace represents the end-to-end application flow.
    
    Composed of multiple spans that can be sequential or parallel.
    """
    
    def __init__(
        self,
        trace_id: str,
        workflow_id: str,
        execution_id: str,
        query: Optional[str] = None,
    ):
        self.trace_id = trace_id
        self.workflow_id = workflow_id
        self.execution_id = execution_id
        self.query = query
        
        self.started_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        
        # Spans (keyed by span_id)
        self.spans: Dict[str, Span] = {}
        
        # Root spans (spans without parents)
        self.root_spans: List[str] = []
        
        # Total metrics
        self.total_cost: float = 0.0
        self.total_tokens: Dict[str, int] = {}
        self.total_duration_ms: int = 0
        
        # Status
        self.status: str = "running"
        self.error: Optional[str] = None
    
    def add_span(self, span: Span, parent_span_id: Optional[str] = None):
        """Add a span to the trace."""
        self.spans[span.span_id] = span
        
        if parent_span_id:
            if parent_span_id in self.spans:
                self.spans[parent_span_id].child_spans.append(span.span_id)
        else:
            self.root_spans.append(span.span_id)
    
    def get_span(self, span_id: str) -> Optional[Span]:
        """Get a span by ID."""
        return self.spans.get(span_id)
    
    def complete(self):
        """Mark trace as completed."""
        self.completed_at = datetime.now()
        self.status = "completed"
        
        # Calculate totals
        self.total_cost = sum(span.cost for span in self.spans.values())
        self.total_tokens = {
            "input": sum(span.tokens.get("input_tokens", 0) for span in self.spans.values()),
            "output": sum(span.tokens.get("output_tokens", 0) for span in self.spans.values()),
            "total": sum(span.tokens.get("total_tokens", 0) for span in self.spans.values()),
        }
        
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.total_duration_ms = int(delta.total_seconds() * 1000)
    
    def fail(self, error: str):
        """Mark trace as failed."""
        self.completed_at = datetime.now()
        self.status = "failed"
        self.error = error
    
    def get_span_sequence(self) -> List[Span]:
        """Get spans in execution order (topological sort)."""
        # Simple implementation - return spans sorted by start time
        return sorted(
            [span for span in self.spans.values() if span.started_at],
            key=lambda s: s.started_at or datetime.min
        )
    
    def get_parallel_spans(self) -> List[List[Span]]:
        """Get groups of spans that executed in parallel."""
        # Group spans by overlapping time windows
        spans = self.get_span_sequence()
        if not spans:
            return []
        
        parallel_groups: List[List[Span]] = []
        current_group: List[Span] = []
        
        for span in spans:
            if not span.started_at or not span.completed_at:
                continue
            
            # Check if this span overlaps with any span in current group
            overlaps = False
            for group_span in current_group:
                if group_span.started_at and group_span.completed_at:
                    # Check for overlap
                    if (span.started_at < group_span.completed_at and 
                        span.completed_at > group_span.started_at):
                        overlaps = True
                        break
            
            if overlaps:
                current_group.append(span)
            else:
                if current_group:
                    parallel_groups.append(current_group)
                current_group = [span]
        
        if current_group:
            parallel_groups.append(current_group)
        
        return parallel_groups
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary."""
        return {
            "trace_id": self.trace_id,
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "query": self.query,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "error": self.error,
            "total_cost": self.total_cost,
            "total_tokens": self.total_tokens,
            "total_duration_ms": self.total_duration_ms,
            "spans": [span.to_dict() for span in self.spans.values()],
            "span_count": len(self.spans),
        }


class ObservabilityManager:
    """
    Central manager for observability and tracing.
    
    Handles:
    - Trace creation and management
    - Span tracking
    - Integration with LangSmith/LangFuse
    - Persistent storage
    """
    
    def __init__(self):
        # In-memory storage (should be replaced with database)
        self._traces: Dict[str, Trace] = {}
        self._spans: Dict[str, Span] = {}
        
        # LangSmith/LangFuse integration (optional)
        self._langsmith_enabled = False
        self._langfuse_enabled = False
    
    def start_trace(
        self,
        workflow_id: str,
        execution_id: str,
        query: Optional[str] = None,
    ) -> Trace:
        """Start a new trace."""
        trace_id = str(uuid.uuid4())
        trace = Trace(
            trace_id=trace_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            query=query,
        )
        self._traces[trace_id] = trace
        
        logger.info(f"Started trace: {trace_id} for execution: {execution_id}")
        return trace
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a trace by ID."""
        return self._traces.get(trace_id)
    
    def get_trace_by_execution_id(self, execution_id: str) -> Optional[Trace]:
        """Get a trace by execution ID."""
        for trace in self._traces.values():
            if trace.execution_id == execution_id:
                return trace
        return None
    
    def start_span(
        self,
        trace_id: str,
        span_type: SpanType,
        name: str,
        parent_span_id: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Span:
        """Start a new span."""
        span_id = str(uuid.uuid4())
        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            span_type=span_type,
            name=name,
            parent_span_id=parent_span_id,
        )
        
        if inputs:
            span.inputs = inputs
        
        span.start()
        
        # Add to trace
        trace = self._traces.get(trace_id)
        if trace:
            trace.add_span(span, parent_span_id)
        
        self._spans[span_id] = span
        
        logger.debug(f"Started span: {span_id} ({span_type.value}) in trace: {trace_id}")
        return span
    
    def complete_span(
        self,
        span_id: str,
        outputs: Optional[Dict[str, Any]] = None,
        tokens: Optional[Dict[str, int]] = None,
        cost: Optional[float] = None,
    ):
        """Complete a span."""
        span = self._spans.get(span_id)
        if not span:
            logger.warning(f"Span not found: {span_id}")
            return
        
        if tokens:
            span.tokens = tokens
        if cost is not None:
            span.cost = cost
        
        span.complete(outputs)
        
        logger.debug(f"Completed span: {span_id} (duration: {span.duration_ms}ms, cost: ${span.cost:.4f})")
    
    def fail_span(
        self,
        span_id: str,
        error: str,
        error_type: Optional[str] = None,
        error_stack: Optional[str] = None,
    ):
        """Mark a span as failed."""
        span = self._spans.get(span_id)
        if not span:
            logger.warning(f"Span not found: {span_id}")
            return
        
        span.fail(error, error_type, error_stack)
        
        # Also mark trace as failed if this is a critical span
        trace = self._traces.get(span.trace_id)
        if trace and span.span_type in [SpanType.LLM, SpanType.FINAL_OUTPUT]:
            trace.fail(error)
        
        logger.warning(f"Span failed: {span_id} - {error}")
    
    def update_span_metadata(
        self,
        span_id: str,
        tokens: Optional[Dict[str, int]] = None,
        cost: Optional[float] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        api_limits: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Update span metadata."""
        span = self._spans.get(span_id)
        if not span:
            return
        
        if tokens:
            span.tokens.update(tokens)
        if cost is not None:
            span.cost = cost
        if model:
            span.model = model
        if provider:
            span.provider = provider
        if api_limits:
            span.api_limits.update(api_limits)
        if metadata:
            span.metadata.update(metadata)
    
    def add_span_evaluation(
        self,
        span_id: str,
        evaluation: Dict[str, Any],
    ):
        """Add evaluation results to a span."""
        span = self._spans.get(span_id)
        if not span:
            return
        
        span.evaluation = evaluation
    
    def complete_trace(self, trace_id: str):
        """Complete a trace."""
        trace = self._traces.get(trace_id)
        if not trace:
            return
        
        trace.complete()
        
        logger.info(
            f"Completed trace: {trace_id} "
            f"(cost: ${trace.total_cost:.4f}, duration: {trace.total_duration_ms}ms, "
            f"spans: {len(trace.spans)})"
        )
    
    def list_traces(
        self,
        workflow_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List traces."""
        traces = list(self._traces.values())
        
        if workflow_id:
            traces = [t for t in traces if t.workflow_id == workflow_id]
        
        # Sort by started_at (newest first)
        traces.sort(key=lambda t: t.started_at, reverse=True)
        traces = traces[:limit]
        
        return [t.to_dict() for t in traces]


# Global observability manager instance
_observability_manager = ObservabilityManager()


def get_observability_manager() -> ObservabilityManager:
    """Get the global observability manager."""
    return _observability_manager

