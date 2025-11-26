"""
Webhook API endpoints.

Provides endpoints for:
- Creating and managing webhooks
- Receiving webhook calls and triggering workflows
- Webhook statistics and monitoring
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Header, Request, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.core.security import limiter
from backend.core.webhooks import (
    Webhook,
    save_webhook,
    load_webhook,
    list_webhooks,
    delete_webhook,
    generate_webhook_id,
    generate_webhook_secret,
    verify_webhook_signature,
    map_payload_to_workflow_input,
)
from backend.core.engine import engine
from backend.core.models import Workflow
from backend.api.workflows import _load_workflow
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Webhooks"])


class WebhookCreateRequest(BaseModel):
    """Request to create a webhook."""
    workflow_id: str
    name: Optional[str] = None
    secret: Optional[str] = None  # If not provided, will be auto-generated
    method: str = Field(default="POST", description="HTTP method")
    headers_required: Dict[str, str] = Field(default_factory=dict)
    payload_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Map webhook payload fields to workflow input (e.g., {'query': 'body.question'})"
    )


class WebhookUpdateRequest(BaseModel):
    """Request to update a webhook."""
    name: Optional[str] = None
    enabled: Optional[bool] = None
    secret: Optional[str] = None
    method: Optional[str] = None
    headers_required: Optional[Dict[str, str]] = None
    payload_mapping: Optional[Dict[str, str]] = None


class WebhookResponse(BaseModel):
    """Webhook response model."""
    id: str
    workflow_id: str
    name: Optional[str]
    webhook_id: str
    webhook_url: str
    enabled: bool
    created_at: str
    updated_at: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    last_called_at: Optional[str]


@router.post("/webhooks", response_model=WebhookResponse)
@limiter.limit("20/minute")
async def create_webhook(
    request_body: WebhookCreateRequest,
    request: Request,
    base_url: str = Header(None, alias="X-Base-URL", description="Base URL for webhook (optional)"),
) -> WebhookResponse:
    """
    Create a webhook for a workflow.
    
    Returns the webhook URL that can be used to trigger the workflow.
    """
    # Verify workflow exists
    workflow = _load_workflow(request_body.workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow {request_body.workflow_id} not found")
    
    # Generate webhook ID and secret
    webhook_id = generate_webhook_id()
    secret = request_body.secret or generate_webhook_secret()
    
    # Create webhook
    webhook = Webhook(
        id=str(uuid.uuid4()),
        workflow_id=request_body.workflow_id,
        name=request_body.name,
        webhook_id=webhook_id,
        secret=secret,
        enabled=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        method=request_body.method,
        headers_required=request_body.headers_required,
        payload_mapping=request_body.payload_mapping,
    )
    
    save_webhook(webhook)
    logger.info(f"Created webhook {webhook_id} for workflow {request_body.workflow_id}")
    
    # Generate webhook URL
    # Default to localhost if base_url not provided
    if not base_url:
        base_url = "http://localhost:8000"
    webhook_url = f"{base_url.rstrip('/')}/api/v1/webhooks/{webhook_id}/trigger"
    
    return WebhookResponse(
        id=webhook.id,
        workflow_id=webhook.workflow_id,
        name=webhook.name,
        webhook_id=webhook.webhook_id,
        webhook_url=webhook_url,
        enabled=webhook.enabled,
        created_at=webhook.created_at.isoformat(),
        updated_at=webhook.updated_at.isoformat(),
        total_calls=webhook.total_calls,
        successful_calls=webhook.successful_calls,
        failed_calls=webhook.failed_calls,
        last_called_at=webhook.last_called_at.isoformat() if webhook.last_called_at else None,
    )


@router.get("/webhooks", response_model=List[WebhookResponse])
@limiter.limit("30/minute")
async def list_webhooks_endpoint(
    request: Request,
    workflow_id: Optional[str] = None,
    base_url: str = Header(None, alias="X-Base-URL"),
) -> List[WebhookResponse]:
    """List all webhooks, optionally filtered by workflow."""
    webhooks = list_webhooks(workflow_id=workflow_id)
    
    if not base_url:
        base_url = "http://localhost:8000"
    
    return [
        WebhookResponse(
            id=w.id,
            workflow_id=w.workflow_id,
            name=w.name,
            webhook_id=w.webhook_id,
            webhook_url=f"{base_url.rstrip('/')}/api/v1/webhooks/{w.webhook_id}/trigger",
            enabled=w.enabled,
            created_at=w.created_at.isoformat(),
            updated_at=w.updated_at.isoformat(),
            total_calls=w.total_calls,
            successful_calls=w.successful_calls,
            failed_calls=w.failed_calls,
            last_called_at=w.last_called_at.isoformat() if w.last_called_at else None,
        )
        for w in webhooks
    ]


@router.get("/webhooks/{webhook_id}", response_model=WebhookResponse)
@limiter.limit("30/minute")
async def get_webhook(
    webhook_id: str,
    request: Request,
    base_url: str = Header(None, alias="X-Base-URL"),
) -> WebhookResponse:
    """Get a webhook by ID."""
    # Find webhook by webhook_id (the URL identifier, not the internal id)
    webhooks = list_webhooks()
    webhook = next((w for w in webhooks if w.webhook_id == webhook_id), None)
    if not webhook:
        raise HTTPException(status_code=404, detail=f"Webhook {webhook_id} not found")
    
    if not base_url:
        base_url = "http://localhost:8000"
    
    return WebhookResponse(
        id=webhook.id,
        workflow_id=webhook.workflow_id,
        name=webhook.name,
        webhook_id=webhook.webhook_id,
        webhook_url=f"{base_url.rstrip('/')}/api/v1/webhooks/{webhook.webhook_id}/trigger",
        enabled=webhook.enabled,
        created_at=webhook.created_at.isoformat(),
        updated_at=webhook.updated_at.isoformat(),
        total_calls=webhook.total_calls,
        successful_calls=webhook.successful_calls,
        failed_calls=webhook.failed_calls,
        last_called_at=webhook.last_called_at.isoformat() if webhook.last_called_at else None,
    )


@router.put("/webhooks/{webhook_id}", response_model=WebhookResponse)
@limiter.limit("20/minute")
async def update_webhook(
    webhook_id: str,
    request_body: WebhookUpdateRequest,
    request: Request,
    base_url: str = Header(None, alias="X-Base-URL"),
) -> WebhookResponse:
    """Update a webhook."""
    # Find webhook by webhook_id (the URL identifier, not the internal id)
    webhooks = list_webhooks()
    webhook = next((w for w in webhooks if w.webhook_id == webhook_id), None)
    if not webhook:
        raise HTTPException(status_code=404, detail=f"Webhook {webhook_id} not found")
    
    # Update fields
    if request_body.name is not None:
        webhook.name = request_body.name
    if request_body.enabled is not None:
        webhook.enabled = request_body.enabled
    if request_body.secret is not None:
        webhook.secret = request_body.secret
    if request_body.method is not None:
        webhook.method = request_body.method
    if request_body.headers_required is not None:
        webhook.headers_required = request_body.headers_required
    if request_body.payload_mapping is not None:
        webhook.payload_mapping = request_body.payload_mapping
    
    webhook.updated_at = datetime.now()
    save_webhook(webhook)
    
    if not base_url:
        base_url = "http://localhost:8000"
    
    return WebhookResponse(
        id=webhook.id,
        workflow_id=webhook.workflow_id,
        name=webhook.name,
        webhook_id=webhook.webhook_id,
        webhook_url=f"{base_url.rstrip('/')}/api/v1/webhooks/{webhook.webhook_id}/trigger",
        enabled=webhook.enabled,
        created_at=webhook.created_at.isoformat(),
        updated_at=webhook.updated_at.isoformat(),
        total_calls=webhook.total_calls,
        successful_calls=webhook.successful_calls,
        failed_calls=webhook.failed_calls,
        last_called_at=webhook.last_called_at.isoformat() if webhook.last_called_at else None,
    )


@router.delete("/webhooks/{webhook_id}")
@limiter.limit("10/minute")
async def delete_webhook_endpoint(webhook_id: str, request: Request) -> Dict[str, str]:
    """Delete a webhook."""
    # Find webhook by webhook_id (the URL identifier, not the internal id)
    webhooks = list_webhooks()
    webhook = next((w for w in webhooks if w.webhook_id == webhook_id), None)
    if not webhook:
        raise HTTPException(status_code=404, detail=f"Webhook {webhook_id} not found")
    
    # Delete using internal id
    if not delete_webhook(webhook.id):
        raise HTTPException(status_code=500, detail="Failed to delete webhook")
    
    logger.info(f"Deleted webhook {webhook_id} (internal id: {webhook.id})")
    return {"message": f"Webhook {webhook_id} deleted successfully"}


@router.post("/webhooks/{webhook_id}/trigger")
@limiter.limit("10/minute")
async def trigger_webhook(
    webhook_id: str,
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    x_signature_256: Optional[str] = Header(None, alias="X-Signature-256"),
) -> JSONResponse:
    """
    Trigger a workflow via webhook.
    
    This endpoint receives HTTP POST requests and executes the associated workflow.
    """
    # Find webhook by webhook_id (the URL identifier, not the internal id)
    webhooks = list_webhooks()
    webhook = next((w for w in webhooks if w.webhook_id == webhook_id), None)
    if not webhook:
        raise HTTPException(status_code=404, detail=f"Webhook {webhook_id} not found")
    
    # Check if enabled
    if not webhook.enabled:
        raise HTTPException(status_code=403, detail="Webhook is disabled")
    
    # Verify signature if secret is set
    if webhook.secret:
        signature = x_signature_256 or x_signature
        if not signature:
            raise HTTPException(status_code=401, detail="Missing webhook signature")
        
        # Get request body
        body = await request.body()
        if not verify_webhook_signature(body, signature, webhook.secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    # Check required headers
    for header_name, expected_value in webhook.headers_required.items():
        actual_value = request.headers.get(header_name)
        if actual_value != expected_value:
            raise HTTPException(
                status_code=403,
                detail=f"Missing or invalid required header: {header_name}"
            )
    
    # Get payload
    try:
        payload = await request.json()
    except:
        # If not JSON, try form data or raw body
        try:
            form_data = await request.form()
            payload = dict(form_data)
        except:
            body = await request.body()
            payload = {"raw": body.decode("utf-8", errors="ignore")}
    
    # Update webhook statistics
    webhook.total_calls += 1
    webhook.last_called_at = datetime.now()
    
    try:
        # Load workflow
        workflow = _load_workflow(webhook.workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow {webhook.workflow_id} not found")
        
        # Map payload to workflow input
        workflow_input = map_payload_to_workflow_input(payload, webhook.payload_mapping)
        
        # If no mapping, use payload as input
        if not workflow_input:
            workflow_input = payload
        
        # Inject input into workflow nodes
        workflow_copy = workflow.model_copy(deep=True)
        
        # Find webhook_input nodes first (preferred)
        webhook_nodes = [n for n in workflow_copy.nodes if n.type == "webhook_input"]
        
        if webhook_nodes:
            # If webhook_input nodes exist, inject payload into them
            for node in webhook_nodes:
                # Check if this node's webhook_id matches (if configured)
                node_webhook_id = node.data.get("config", {}).get("webhook_id")
                if not node_webhook_id or node_webhook_id == webhook.webhook_id:
                    # Inject payload into webhook node
                    if "config" not in node.data:
                        node.data["config"] = {}
                    node.data["config"]["payload"] = workflow_input
                    node.data["config"]["webhook_id"] = webhook.webhook_id
                    break  # Use first matching webhook node
        else:
            # Fallback: Find other input nodes and inject data
            for node in workflow_copy.nodes:
                if node.type == "text_input":
                    # If payload has 'query' or 'text', use it
                    if "query" in workflow_input:
                        node.data["text"] = workflow_input["query"]
                    elif "text" in workflow_input:
                        node.data["text"] = workflow_input["text"]
                    elif isinstance(workflow_input, dict) and len(workflow_input) == 1:
                        # Single key-value pair, use the value
                        node.data["text"] = str(list(workflow_input.values())[0])
                    else:
                        # Use entire payload as JSON string
                        import json
                        node.data["text"] = json.dumps(workflow_input)
                elif node.type == "file_loader" and "file_id" in workflow_input:
                    node.data["file_id"] = workflow_input["file_id"]
        
        # Execute workflow
        execution_id = f"webhook_{webhook_id}_{uuid.uuid4().hex[:8]}"
        execution = await engine.execute(
            workflow=workflow_copy,
            execution_id=execution_id,
        )
        
        # Update statistics
        webhook.successful_calls += 1
        save_webhook(webhook)
        
        # Extract result from last node (usually chat/llm node)
        result = None
        if execution.results:
            # Get the last node result
            last_node_result = list(execution.results.values())[-1]
            if last_node_result.output:
                if isinstance(last_node_result.output, dict):
                    result = last_node_result.output.get("response") or last_node_result.output.get("output") or last_node_result.output
                else:
                    result = last_node_result.output
        
        return JSONResponse({
            "success": True,
            "execution_id": execution_id,
            "status": execution.status.value,
            "result": result,
            "cost": execution.total_cost,
            "duration_ms": execution.duration_ms,
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing webhook {webhook_id}: {e}", exc_info=True)
        webhook.failed_calls += 1
        save_webhook(webhook)
        
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Workflow execution failed",
                "message": str(e),
            }
        )


@router.get("/workflows/{workflow_id}/webhooks", response_model=List[WebhookResponse])
@limiter.limit("30/minute")
async def get_workflow_webhooks(
    request: Request,
    workflow_id: str,
    base_url: str = Header(None, alias="X-Base-URL"),
) -> List[WebhookResponse]:
    """Get all webhooks for a workflow."""
    webhooks = list_webhooks(workflow_id=workflow_id)
    
    if not base_url:
        base_url = "http://localhost:8000"
    
    return [
        WebhookResponse(
            id=w.id,
            workflow_id=w.workflow_id,
            name=w.name,
            webhook_id=w.webhook_id,
            webhook_url=f"{base_url.rstrip('/')}/api/v1/webhooks/{w.webhook_id}/trigger",
            enabled=w.enabled,
            created_at=w.created_at.isoformat(),
            updated_at=w.updated_at.isoformat(),
            total_calls=w.total_calls,
            successful_calls=w.successful_calls,
            failed_calls=w.failed_calls,
            last_called_at=w.last_called_at.isoformat() if w.last_called_at else None,
        )
        for w in webhooks
    ]

