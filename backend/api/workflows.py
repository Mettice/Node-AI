"""
Workflow management API endpoints.

This module provides REST API endpoints for saving, loading, and managing workflows.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Header, Request
from pydantic import BaseModel, Field

from backend.core.models import Workflow, Node, Edge, ExecutionResponse
from backend.core.engine import engine
from backend.core.exceptions import WorkflowValidationError, WorkflowExecutionError
from backend.core.deployment import DeploymentManager
from backend.core.security import validate_workflow_id, validate_node_id, limiter
from backend.core.cache import get_cache
from backend.core.workflow_permissions import (
    require_user_id,
    check_workflow_ownership,
    can_modify_workflow,
    filter_workflows_by_user,
    add_owner_to_workflow,
    get_user_id_from_request,
)
from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Workflows"])

# Cache for workflows (TTL: 5 minutes)
_cache = get_cache()

# Workflow storage directory - use settings to ensure correct path
WORKFLOWS_DIR = settings.workflows_dir
WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)


class WorkflowCreateRequest(BaseModel):
    """Request model for creating a workflow."""
    name: str
    description: Optional[str] = None
    nodes: List[Dict]
    edges: List[Dict]
    tags: List[str] = []
    is_template: bool = False


class WorkflowUpdateRequest(BaseModel):
    """Request model for updating a workflow."""
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[Dict]] = None
    edges: Optional[List[Dict]] = None
    tags: Optional[List[str]] = None
    is_template: Optional[bool] = None


class WorkflowListItem(BaseModel):
    """Workflow list item (metadata only)."""
    id: str
    name: str
    description: Optional[str]
    tags: List[str]
    is_template: bool
    is_deployed: bool = False
    created_at: str
    updated_at: str


class WorkflowListResponse(BaseModel):
    """Response model for listing workflows."""
    workflows: List[WorkflowListItem]
    total: int


def _get_workflow_path(workflow_id: str) -> Path:
    """Get the file path for a workflow."""
    return WORKFLOWS_DIR / f"{workflow_id}.json"


def _load_workflow(workflow_id: str) -> Optional[Workflow]:
    """Load a workflow from disk (with caching)."""
    # Check cache first
    cache_key = f"workflow:{workflow_id}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached
    
    workflow_path = _get_workflow_path(workflow_id)
    if not workflow_path.exists():
        return None
    
    try:
        with open(workflow_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Parse datetime strings if present
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
        if "deployed_at" in data and isinstance(data["deployed_at"], str):
            data["deployed_at"] = datetime.fromisoformat(data["deployed_at"].replace("Z", "+00:00"))
        
        # Ensure nodes and edges are properly formatted
        # Position should be a dict with x and y, not a Position object
        if "nodes" in data:
            for node in data["nodes"]:
                if "position" in node and isinstance(node["position"], dict):
                    # Position is already a dict, which is correct
                    pass
                elif hasattr(node.get("position"), "x"):
                    # Convert Position object to dict
                    pos = node["position"]
                    node["position"] = {"x": pos.x, "y": pos.y}
        
        workflow = Workflow(**data)
        # Cache the workflow (TTL: 5 minutes)
        _cache.set(cache_key, workflow, ttl_seconds=300)
        return workflow
    except Exception as e:
        logger.error(f"Error loading workflow {workflow_id}: {e}")
        return None


def _save_workflow(workflow: Workflow) -> None:
    """Save a workflow to disk and invalidate cache."""
    if not workflow.id:
        workflow.id = str(uuid.uuid4())
    
    workflow_path = _get_workflow_path(workflow.id)
    
    # Convert to dict and handle datetime serialization
    workflow_dict = workflow.model_dump()
    if workflow.created_at:
        workflow_dict["created_at"] = workflow.created_at.isoformat()
    if workflow.updated_at:
        workflow_dict["updated_at"] = workflow.updated_at.isoformat()
    if workflow.deployed_at:
        workflow_dict["deployed_at"] = workflow.deployed_at.isoformat()
    
    with open(workflow_path, "w", encoding="utf-8") as f:
        json.dump(workflow_dict, f, indent=2, ensure_ascii=False)
    
    # Invalidate cache
    cache_key = f"workflow:{workflow.id}"
    _cache.delete(cache_key)
    
    logger.info(f"Saved workflow {workflow.id} to {workflow_path}")


def _list_workflows() -> List[Workflow]:
    """List all workflows from disk."""
    workflows = []
    for workflow_file in WORKFLOWS_DIR.glob("*.json"):
        try:
            with open(workflow_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Parse datetime strings if present
            if "created_at" in data and isinstance(data["created_at"], str):
                data["created_at"] = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            if "updated_at" in data and isinstance(data["updated_at"], str):
                data["updated_at"] = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
            if "deployed_at" in data and isinstance(data["deployed_at"], str):
                data["deployed_at"] = datetime.fromisoformat(data["deployed_at"].replace("Z", "+00:00"))
            
            workflows.append(Workflow(**data))
        except Exception as e:
            logger.error(f"Error loading workflow from {workflow_file}: {e}")
    return workflows


@router.post("/workflows", response_model=Workflow)
@limiter.limit("20/minute")
async def create_workflow(request: Request, workflow_request: WorkflowCreateRequest) -> Workflow:
    """
    Create a new workflow.
    
    Args:
        workflow_request: Workflow creation request
        request: FastAPI request object for auth
        
    Returns:
        Created workflow with ID
        
    Raises:
        HTTPException: If workflow validation fails or user is not authenticated
    """
    # Require authentication for non-public workflows
    user_id = None
    if not workflow_request.is_template:
        user_id = require_user_id(request)
    
    try:
        # Convert dicts to Node and Edge objects
        nodes = [Node(**node) for node in workflow_request.nodes]
        edges = [Edge(**edge) for edge in workflow_request.edges]
        
        # Validate workflow structure using engine
        workflow = Workflow(
            id=str(uuid.uuid4()),
            name=workflow_request.name,
            description=workflow_request.description,
            nodes=nodes,
            edges=edges,
            tags=workflow_request.tags,
            is_template=workflow_request.is_template,
            owner_id=user_id,  # Set owner
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        # Validate workflow
        engine._validate_workflow(workflow)
        
        # Save workflow
        _save_workflow(workflow)
        
        logger.info(f"Created workflow {workflow.id}: {workflow.name} for user {user_id or 'public'}")
        return workflow
        
    except Exception as e:
        logger.error(f"Error creating workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Failed to create workflow",
                "message": str(e),
            },
        )


@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    is_template: Optional[bool] = None,
) -> WorkflowListResponse:
    """
    List workflows accessible to the current user.
    
    Args:
        limit: Maximum number of workflows to return
        offset: Number of workflows to skip
        is_template: Filter by template status
        
    Returns:
        List of workflows (metadata only)
    """
    try:
        # Get current user ID (optional - unauthenticated users can still see templates)
        user_id = get_user_id_from_request(request)
        
        all_workflows = _list_workflows()
        
        # Filter by user permissions - only show:
        # 1. Public templates
        # 2. Workflows owned by the current user
        # 3. Legacy workflows without owner_id (for backward compatibility)
        if user_id:
            # Authenticated user - show their workflows + templates
            all_workflows = [
                w for w in all_workflows
                if w.is_template or w.owner_id == user_id or w.owner_id is None
            ]
        else:
            # Unauthenticated user - show only templates
            all_workflows = [w for w in all_workflows if w.is_template]
            logger.debug("Showing only public templates to unauthenticated user")
        
        # Filter by template status if specified
        if is_template is not None:
            all_workflows = [w for w in all_workflows if w.is_template == is_template]
        
        # Sort by updated_at (newest first)
        all_workflows.sort(key=lambda w: w.updated_at or w.created_at or datetime.min, reverse=True)
        
        # Apply pagination
        total = len(all_workflows)
        workflows = all_workflows[offset:offset + limit]
        
        # Convert to list items (metadata only)
        workflow_items = [
            WorkflowListItem(
                id=w.id or "",
                name=w.name,
                description=w.description,
                tags=w.tags,
                is_template=w.is_template,
                is_deployed=w.is_deployed,
                created_at=(w.created_at or datetime.now()).isoformat(),
                updated_at=(w.updated_at or datetime.now()).isoformat(),
            )
            for w in workflows
        ]
        
        logger.info(f"Listed {len(workflow_items)} workflows for user {user_id or 'anonymous'} (total: {total})")
        return WorkflowListResponse(workflows=workflow_items, total=total)
        
    except Exception as e:
        logger.error(f"Error listing workflows: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to list workflows",
                "message": str(e),
            },
        )


@router.get("/workflows/{workflow_id}", response_model=Workflow)
async def get_workflow(workflow_id: str, request: Request) -> Workflow:
    """
    Get a workflow by ID.
    
    Args:
        workflow_id: The workflow ID
        request: FastAPI request object for auth
        
    Returns:
        Full workflow object
        
    Raises:
        HTTPException: If workflow not found or access denied
    """
    workflow = _load_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow {workflow_id} not found",
        )
    
    # Check permissions
    user_id = get_user_id_from_request(request)
    if user_id:
        # Authenticated user - check ownership
        check_workflow_ownership(
            workflow.owner_id,
            user_id,
            workflow_id,
            workflow.is_template,
        )
    else:
        # Unauthenticated user - only allow templates
        if not workflow.is_template:
            raise HTTPException(
                status_code=401,
                detail="Authentication required to access this workflow",
            )
    
    return workflow


@router.put("/workflows/{workflow_id}", response_model=Workflow)
@limiter.limit("30/minute")
async def update_workflow(
    workflow_id: str,
    request: Request,
    workflow_request: WorkflowUpdateRequest,
) -> Workflow:
    """
    Update a workflow.
    
    Args:
        workflow_id: The workflow ID
        workflow_request: Workflow update request
        request: FastAPI request object for auth
        
    Returns:
        Updated workflow
        
    Raises:
        HTTPException: If workflow not found, validation fails, or access denied
    """
    # Require authentication
    user_id = require_user_id(request)
    
    workflow = _load_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow {workflow_id} not found",
        )
    
    # Check modification permission
    can_modify_workflow(workflow.owner_id, user_id, workflow_id)
    
    try:
        # Update fields
        if workflow_request.name is not None:
            workflow.name = workflow_request.name
        if workflow_request.description is not None:
            workflow.description = workflow_request.description
        if workflow_request.nodes is not None:
            workflow.nodes = [Node(**node) for node in workflow_request.nodes]
        if workflow_request.edges is not None:
            workflow.edges = [Edge(**edge) for edge in workflow_request.edges]
        if workflow_request.tags is not None:
            workflow.tags = workflow_request.tags
        if workflow_request.is_template is not None:
            workflow.is_template = workflow_request.is_template
        
        workflow.updated_at = datetime.now()
        
        # Validate workflow
        engine._validate_workflow(workflow)
        
        # Save workflow
        _save_workflow(workflow)
        
        logger.info(f"Updated workflow {workflow_id}")
        return workflow
        
    except Exception as e:
        logger.error(f"Error updating workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Failed to update workflow",
                "message": str(e),
            },
        )


@router.delete("/workflows/{workflow_id}")
@limiter.limit("10/minute")
async def delete_workflow(workflow_id: str, request: Request) -> Dict[str, str]:
    """
    Delete a workflow.
    
    Args:
        workflow_id: The workflow ID
        request: FastAPI request object for auth
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If workflow not found or access denied
    """
    # Require authentication
    user_id = require_user_id(request)
    
    # Load workflow to check ownership
    workflow = _load_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow {workflow_id} not found",
        )
    
    # Check modification permission
    can_modify_workflow(workflow.owner_id, user_id, workflow_id)
    
    try:
        workflow_path = _get_workflow_path(workflow_id)
        workflow_path.unlink()
        
        # Clear cache
        cache_key = f"workflow:{workflow_id}"
        _cache.delete(cache_key)
        
        logger.info(f"Deleted workflow {workflow_id} by user {user_id}")
        return {"message": f"Workflow {workflow_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to delete workflow",
                "message": str(e),
            },
        )


@router.post("/workflows/{workflow_id}/deploy", response_model=Workflow)
async def deploy_workflow(workflow_id: str) -> Workflow:
    """
    Deploy a workflow, making it available for queries.
    
    Args:
        workflow_id: The workflow ID to deploy
        
    Returns:
        Deployed workflow
        
    Raises:
        HTTPException: If workflow not found or validation fails
    """
    workflow = _load_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow {workflow_id} not found",
        )
    
    try:
        # Validate workflow before deployment
        engine._validate_workflow(workflow)
        
        # Ensure vector stores are configured for persistence
        # This allows them to be reused across queries
        for node in workflow.nodes:
            if node.type == "vector_store":
                config = node.data.get("config", {})
                if config.get("provider") == "faiss":
                    # Enable persistence if not already set
                    if not config.get("faiss_persist", False):
                        config["faiss_persist"] = True
                    
                    # Set a deployment-specific path if not set
                    if not config.get("faiss_file_path"):
                        from backend.config import settings
                        vector_dir = settings.vectors_dir / (workflow_id or "default")
                        vector_dir.mkdir(parents=True, exist_ok=True)
                        config["faiss_file_path"] = str(vector_dir / f"{node.id}.faiss")
                    
                    # Set index_id if not set (for consistency)
                    if not config.get("index_id"):
                        config["index_id"] = f"{workflow_id}_{node.id}"
        
        # Mark as deployed
        workflow.is_deployed = True
        workflow.deployed_at = datetime.now()
        workflow.updated_at = datetime.now()
        
        # Save workflow with updated configs
        _save_workflow(workflow)
        
        # Create deployment version
        workflow_dict = workflow.model_dump()
        deployment_version = DeploymentManager.create_deployment_version(
            workflow_id=workflow_id,
            workflow_snapshot=workflow_dict,
            description=f"Deployment of {workflow.name}",
        )
        
        logger.info(f"Deployed workflow {workflow_id} as version {deployment_version.version_number}")
        return workflow
        
    except WorkflowValidationError as e:
        logger.error(f"Workflow validation failed for deployment: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Workflow validation failed",
                "message": str(e),
                "errors": e.errors,
            },
        )
    except Exception as e:
        logger.error(f"Error deploying workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to deploy workflow",
                "message": str(e),
            },
        )


@router.post("/workflows/{workflow_id}/undeploy", response_model=Workflow)
async def undeploy_workflow(workflow_id: str) -> Workflow:
    """
    Undeploy a workflow, making it unavailable for queries.
    
    Args:
        workflow_id: The workflow ID to undeploy
        
    Returns:
        Undeployed workflow
        
    Raises:
        HTTPException: If workflow not found
    """
    workflow = _load_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow {workflow_id} not found",
        )
    
    try:
        # Mark as undeployed
        workflow.is_deployed = False
        workflow.updated_at = datetime.now()
        
        # Deactivate active deployment
        active = DeploymentManager.get_active_deployment(workflow_id)
        if active:
            from backend.core.deployment import DeploymentStatus
            active.status = DeploymentStatus.INACTIVE
        
        # Save workflow
        _save_workflow(workflow)
        
        logger.info(f"Undeployed workflow {workflow_id}")
        return workflow
    except Exception as e:
        logger.error(f"Error undeploying workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to undeploy workflow",
                "message": str(e),
            },
        )


@router.get("/workflows/{workflow_id}/deployments")
async def list_deployment_versions(workflow_id: str) -> Dict[str, Any]:
    """
    List all deployment versions for a workflow.
    
    Args:
        workflow_id: The workflow ID
        
    Returns:
        List of deployment versions
    """
    versions = DeploymentManager.list_deployment_versions(workflow_id)
    return {
        "workflow_id": workflow_id,
        "versions": [v.to_dict() for v in versions],
        "total": len(versions),
    }


@router.get("/workflows/{workflow_id}/deployments/{version_number}")
async def get_deployment_version(workflow_id: str, version_number: int) -> Dict[str, Any]:
    """
    Get a specific deployment version.
    
    Args:
        workflow_id: The workflow ID
        version_number: The version number
        
    Returns:
        Deployment version details
    """
    version = DeploymentManager.get_deployment_version(workflow_id, version_number)
    if not version:
        raise HTTPException(
            status_code=404,
            detail=f"Deployment version {version_number} not found for workflow {workflow_id}",
        )
    return version.to_dict()


@router.post("/workflows/{workflow_id}/deployments/{version_number}/rollback")
async def rollback_deployment(workflow_id: str, version_number: int) -> Dict[str, Any]:
    """
    Rollback to a previous deployment version.
    
    Args:
        workflow_id: The workflow ID
        version_number: The version number to rollback to
        
    Returns:
        Rolled back deployment version
    """
    version = DeploymentManager.rollback_to_version(workflow_id, version_number)
    if not version:
        raise HTTPException(
            status_code=404,
            detail=f"Deployment version {version_number} not found or cannot be rolled back",
        )
    
    # Restore workflow from deployment snapshot
    workflow = Workflow(**version.workflow_snapshot)
    workflow.is_deployed = True
    workflow.updated_at = datetime.now()
    _save_workflow(workflow)
    
    logger.info(f"Rolled back workflow {workflow_id} to version {version_number}")
    return {
        "message": f"Rolled back to version {version_number}",
        "deployment": version.to_dict(),
        "workflow": workflow.model_dump(),
    }


@router.get("/workflows/{workflow_id}/deployments/health")
async def get_deployment_health(workflow_id: str) -> Dict[str, Any]:
    """
    Get health metrics for the active deployment.
    
    Args:
        workflow_id: The workflow ID
        
    Returns:
        Deployment health metrics
    """
    health = DeploymentManager.get_deployment_health(workflow_id)
    return health


class WorkflowQueryRequest(BaseModel):
    """Request model for querying a deployed workflow."""
    input: Dict[str, Any] = Field(
        default_factory=dict,
        description="Input data to pass to the workflow (e.g., query, file_id, etc.)"
    )


@router.post("/workflows/{workflow_id}/query", response_model=ExecutionResponse)
async def query_workflow(
    workflow_id: str,
    query_request: WorkflowQueryRequest,
    http_request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> ExecutionResponse:
    """
    Query a deployed workflow.
    
    This endpoint loads a deployed workflow and executes it with the provided input data.
    The input data is merged with node configurations (e.g., query text, file_id).
    
    Args:
        workflow_id: The deployed workflow ID
        request: Query request with input data
        
    Returns:
        Execution response with results and costs
        
    Raises:
        HTTPException: If workflow not found, not deployed, or execution fails
    """
    # Load workflow
    workflow = _load_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow {workflow_id} not found",
        )
    
    # Check if workflow is deployed
    if not workflow.is_deployed:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Workflow not deployed",
                "message": f"Workflow {workflow_id} must be deployed before it can be queried. Use POST /workflows/{workflow_id}/deploy to deploy it.",
            },
        )
    
    # Optional: Validate API key if provided
    # For now, API keys are optional but can be used for access control
    api_key_obj = None
    if x_api_key:
        from backend.core.api_keys import validate_api_key
        from backend.core.usage_tracking import check_rate_limit, check_cost_limit
        api_key_obj = validate_api_key(x_api_key)
        if api_key_obj:
            # If API key is associated with a workflow, verify it matches
            if api_key_obj.workflow_id and api_key_obj.workflow_id != workflow_id:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "API key not authorized",
                        "message": f"API key is associated with a different workflow",
                    },
                )
            
            # Check rate limit
            allowed, error_msg = check_rate_limit(api_key_obj.key_id, api_key_obj.rate_limit)
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "message": error_msg,
                    },
                )
            
            # Check cost limit
            allowed, error_msg = check_cost_limit(api_key_obj.key_id, api_key_obj.cost_limit)
            if not allowed:
                raise HTTPException(
                    status_code=402,
                    detail={
                        "error": "Cost limit exceeded",
                        "message": error_msg,
                    },
                )
        # Note: We don't require API keys yet, but validate if provided
    
    try:
        # Create a copy of the workflow with merged input data
        # Merge query input with node configs
        # OPTIMIZATION: Skip file processing nodes if vector store already exists
        merged_nodes = []
        vector_store_ready = {}  # Track which vector stores are ready
        
        # First pass: Check which vector stores already exist
        for node in workflow.nodes:
            if node.type == "vector_store":
                config = node.data.get("config", {})
                if config.get("provider") == "faiss":
                    file_path = config.get("faiss_file_path")
                    if file_path and Path(file_path).exists():
                        # Vector store exists, mark as ready
                        index_id = config.get("index_id") or f"{workflow_id}_{node.id}"
                        vector_store_ready[index_id] = True
                        logger.info(f"Vector store {index_id} already exists, will skip file processing")
        
        # Second pass: Merge configs and mark nodes to skip if vector store is ready
        for node in workflow.nodes:
            # Create a copy of the node's data/config
            merged_data = node.data.copy()
            config = merged_data.get("config", {})
            
            # Merge input data into node config based on node type
            if node.type == "vector_search" or node.type == "search":
                # For search nodes, inject query from input
                if "query" in query_request.input:
                    config["query"] = query_request.input["query"]
            elif node.type == "chat" or node.type == "llm":
                # For chat/LLM nodes, inject query from input
                if "query" in query_request.input:
                    config["query"] = query_request.input["query"]
            elif node.type == "file_loader":
                # For file loader, inject file_id from input
                if "file_id" in query_request.input:
                    config["file_id"] = query_request.input["file_id"]
            
            # OPTIMIZATION: Skip file processing if vector store is ready
            # Check if this node feeds into a ready vector store
            if node.type in ["file_loader", "chunk", "embed"]:
                # Check if any downstream vector store is ready
                # We'll mark it to skip by setting a flag
                # The actual skipping happens in node execution
                target_index_id = None
                # Find connected vector_store node
                for edge in workflow.edges:
                    if edge.source == node.id:
                        target_node = next((n for n in workflow.nodes if n.id == edge.target), None)
                        if target_node and target_node.type == "vector_store":
                            target_config = target_node.data.get("config", {})
                            target_index_id = target_config.get("index_id") or f"{workflow_id}_{target_node.id}"
                            break
                
                if target_index_id and vector_store_ready.get(target_index_id):
                    # Mark to skip processing
                    config["_skip_if_store_exists"] = True
                    config["_target_index_id"] = target_index_id
                    logger.info(f"Marking {node.type} node {node.id} to skip (vector store ready)")
            
            # Also merge any other input fields that match node config keys
            for key, value in query_request.input.items():
                if key not in config:  # Don't override existing config
                    config[key] = value
            
            merged_data["config"] = config
            
            # Create new node with merged data
            merged_node = Node(
                id=node.id,
                type=node.type,
                position=node.position,
                data=merged_data,
            )
            merged_nodes.append(merged_node)
        
        # Create workflow with merged nodes
        query_workflow = Workflow(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            nodes=merged_nodes,
            edges=workflow.edges,
            tags=workflow.tags,
            is_template=workflow.is_template,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at,
            is_deployed=workflow.is_deployed,
            deployed_at=workflow.deployed_at,
        )
        
        # Execute workflow
        import uuid
        execution_id = str(uuid.uuid4())
        # Get user ID for observability
        user_id = get_user_id_from_request(http_request)
        
        execution = await engine.execute(
            workflow=query_workflow,
            execution_id=execution_id,
            user_id=user_id,
        )
        
        # Record metrics asynchronously (don't block response)
        try:
            from backend.api.metrics import record_execution
            import asyncio
            asyncio.create_task(record_execution(
                execution_id=execution_id,
                execution=execution,
                workflow_version=None,  # TODO: Add version tracking
            ))
        except Exception as e:
            logger.warning(f"Failed to record metrics for execution {execution_id}: {e}")
        
        # Record API key usage if API key was used
        if api_key_obj:
            try:
                from backend.core.usage_tracking import record_usage
                record_usage(
                    key_id=api_key_obj.key_id,
                    workflow_id=workflow_id,
                    execution_id=execution_id,
                    cost=execution.total_cost,
                    duration_ms=execution.duration_ms,
                    status=execution.status.value,
                )
            except Exception as e:
                logger.warning(f"Failed to record API key usage: {e}")
        
        # Record deployment metrics
        success = execution.status.value == "completed"
        DeploymentManager.record_query_metrics(
            workflow_id=workflow_id,
            success=success,
            response_time_ms=execution.duration_ms,
            cost=execution.total_cost,
        )
        
        # Convert to ExecutionResponse
        return ExecutionResponse(
            execution_id=execution_id,
            status=execution.status,
            started_at=execution.started_at.isoformat(),
            completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
            total_cost=execution.total_cost,
            duration_ms=execution.duration_ms,
            results=execution.results,
        )
        
    except WorkflowValidationError as e:
        logger.error(f"Workflow validation failed during query: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Workflow validation failed",
                "message": str(e),
                "errors": e.errors,
            },
        )
    except WorkflowExecutionError as e:
        logger.error(f"Workflow execution failed during query: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Workflow execution failed",
                "message": str(e),
            },
        )
    except Exception as e:
        logger.error(f"Unexpected error during workflow query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": str(e),
            },
        )

