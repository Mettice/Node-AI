"""
Workflow execution API endpoints.

This module provides REST API endpoints for executing workflows
and retrieving execution results.
"""

import asyncio
import uuid
from typing import Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from backend.core.engine import engine
from backend.core.exceptions import WorkflowExecutionError, WorkflowValidationError
from backend.core.models import Execution, ExecutionRequest, ExecutionResponse, ExecutionStatus, Workflow
from backend.core.streaming import stream_manager
from backend.core.security import limiter
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Execution"])

# In-memory storage for executions (will be replaced with database later)
_executions: Dict[str, Execution] = {}


@router.post("/workflows/execute", response_model=ExecutionResponse)
@limiter.limit("10/minute")
async def execute_workflow(request: ExecutionRequest, http_request: Request) -> ExecutionResponse:
    """
    Execute a workflow.
    
    This endpoint accepts a workflow and executes it, returning
    the execution ID and initial status.
    
    Args:
        request: Execution request containing workflow and options
        
    Returns:
        Execution response with execution ID and status
        
    Raises:
        HTTPException: If workflow validation or execution fails
    """
    try:
        # Generate execution ID
        execution_id = str(uuid.uuid4())
        
        logger.info(f"Received workflow execution request: {execution_id}")
        
        # Create placeholder execution immediately so GET endpoint works
        from datetime import datetime
        from backend.core.models import Execution
        placeholder_execution = Execution(
            id=execution_id,
            workflow_id=request.workflow.id or "unknown",
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now(),
        )
        _executions[execution_id] = placeholder_execution
        
        # Start workflow execution in background
        # This allows the frontend to connect to SSE stream before execution completes
        async def execute_in_background():
            try:
                execution = await engine.execute(
                    workflow=request.workflow,
                    execution_id=execution_id,
                )
                
                # Update stored execution with results
                _executions[execution_id] = execution
                logger.info(f"Execution {execution_id} completed successfully")
                
                # Record metrics asynchronously (don't block)
                try:
                    from backend.api.metrics import record_execution
                    await record_execution(
                        execution_id=execution_id,
                        execution=execution,
                        workflow_version=None,  # TODO: Add version tracking
                    )
                except Exception as metrics_error:
                    logger.error(f"Failed to record metrics: {metrics_error}")
                    
            except Exception as e:
                logger.error(f"Background execution failed for {execution_id}: {e}", exc_info=True)
                # Update with error execution
                from backend.core.models import Execution
                from datetime import datetime
                _executions[execution_id] = Execution(
                    id=execution_id,
                    workflow_id=request.workflow.id or "unknown",
                    status=ExecutionStatus.FAILED,
                    started_at=placeholder_execution.started_at,
                    completed_at=datetime.now(),
                    error=str(e),
                )
        
        # Start execution in background
        asyncio.create_task(execute_in_background())
        
        # Return immediately so frontend can connect to stream
        # The execution will populate _executions when it completes
        return ExecutionResponse(
            execution_id=execution_id,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now().isoformat(),
        )
        
    except WorkflowValidationError as e:
        logger.error(f"Workflow validation failed: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Workflow validation failed",
                "message": str(e),
                "errors": e.errors,
            },
        )
    except WorkflowExecutionError as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Workflow execution failed",
                "message": str(e),
            },
        )
    except Exception as e:
        logger.error(f"Unexpected error during workflow execution: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": str(e),
            },
        )


@router.get("/executions/{execution_id}", response_model=Execution)
async def get_execution(execution_id: str) -> Execution:
    """
    Get execution details by ID.
    
    Args:
        execution_id: The execution ID
        
    Returns:
        Execution object with full details
        
    Raises:
        HTTPException: If execution not found
    """
    if execution_id not in _executions:
        raise HTTPException(
            status_code=404,
            detail=f"Execution {execution_id} not found",
        )
    
    return _executions[execution_id]


@router.get("/executions/{execution_id}/trace")
async def get_execution_trace(execution_id: str) -> Dict:
    """
    Get execution trace (step-by-step timeline).
    
    Args:
        execution_id: The execution ID
        
    Returns:
        Execution trace with all steps
        
    Raises:
        HTTPException: If execution not found
    """
    if execution_id not in _executions:
        raise HTTPException(
            status_code=404,
            detail=f"Execution {execution_id} not found",
        )
    
    execution = _executions[execution_id]
    
    return {
        "execution_id": execution_id,
        "status": execution.status.value,
        "trace": [step.model_dump() for step in execution.trace],
        "total_cost": execution.total_cost,
        "duration_ms": execution.duration_ms,
    }


@router.get("/executions")
async def list_executions(limit: int = 10, offset: int = 0) -> Dict:
    """
    List all executions.
    
    Args:
        limit: Maximum number of executions to return
        offset: Number of executions to skip
        
    Returns:
        List of executions with pagination
    """
    executions_list = list(_executions.values())
    
    # Sort by started_at (most recent first)
    executions_list.sort(key=lambda e: e.started_at, reverse=True)
    
    # Paginate
    paginated = executions_list[offset : offset + limit]
    
    return {
        "executions": [exec.model_dump() for exec in paginated],
        "total": len(executions_list),
        "limit": limit,
        "offset": offset,
    }


@router.get("/executions/{execution_id}/stream")
async def stream_execution(execution_id: str):
    """
    Stream execution events using Server-Sent Events (SSE).
    
    This endpoint provides real-time updates about workflow execution,
    including node progress, agent actions, and intermediate outputs.
    
    Args:
        execution_id: The execution ID to stream
        
    Returns:
        SSE stream of execution events
    """
    async def event_generator():
        """Generate SSE events from stream."""
        try:
            # Send initial connection event
            yield "event: connected\ndata: {\"execution_id\": \"" + execution_id + "\"}\n\n"
            
            # Track node events for logging
            started_nodes = set()
            completed_nodes = set()
            
            # Subscribe to stream - keep it open until execution is truly complete
            logger.info(f"Starting to stream events for execution {execution_id}")
            async for event in stream_manager.subscribe(execution_id):
                logger.debug(f"Streaming event: {event.event_type.value} for node {event.node_id}")
                yield event.to_sse()
                
                # Track node starts for logging
                if event.event_type.value == "node_started":
                    if event.node_id:
                        started_nodes.add(event.node_id)
                        logger.info(f"Node {event.node_id} started. Total nodes started: {len(started_nodes)}")
                
                # Track node completions for logging
                if event.event_type.value in ["node_completed", "node_failed"]:
                    if event.node_id:
                        completed_nodes.add(event.node_id)
                        logger.info(f"Node {event.node_id} completed. Completed: {len(completed_nodes)}/{len(started_nodes)}. Stream will stay open for more events.")
                
                # ONLY close stream when we receive the workflow completion log event
                # This event is sent AFTER all nodes have completed execution
                # Do NOT close based on execution status or node counts - those are unreliable
                if event.event_type.value == "log" and event.node_id == "workflow":
                    message = (event.data.get("message", "") or "").lower()
                    if "completed" in message or "failed" in message:
                        # Workflow completion event - this is the ONLY reliable signal
                        # Wait a bit for any final events to be sent, then close
                        logger.info(f"Workflow completion event received: {event.data.get('message')}. All {len(started_nodes)} nodes completed. Closing stream.")
                        await asyncio.sleep(0.5)  # Small delay to ensure final events are sent
                        yield "event: complete\ndata: {\"message\": \"Execution stream complete\"}\n\n"
                        break
                    
        except Exception as e:
            logger.error(f"Error in SSE stream: {e}", exc_info=True)
            yield f"event: error\ndata: {{\"error\": \"{str(e)}\"}}\n\n"
        finally:
            # Clean up stream - but only after a delay to ensure all events are sent
            await asyncio.sleep(1.0)  # Wait a bit before removing stream
            await stream_manager.remove_stream(execution_id)
            logger.info(f"Stream {execution_id} cleaned up")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )

