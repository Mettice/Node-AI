"""
Workflow permission system.

This module provides permission checking for workflow operations,
ensuring users can only access and modify their own workflows.
"""

from typing import Optional
from fastapi import HTTPException, status, Request
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def get_user_id_from_request(request: Request) -> Optional[str]:
    """
    Extract user ID from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User ID if authenticated, None otherwise
    """
    return getattr(request.state, "user_id", None)


def require_user_id(request: Request) -> str:
    """
    Require user authentication and return user ID.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If user is not authenticated
    """
    user_id = get_user_id_from_request(request)
    
    if not user_id:
        logger.warning("Unauthenticated access attempt to protected workflow endpoint")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in to access workflows.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


def check_workflow_ownership(
    workflow_owner_id: Optional[str],
    current_user_id: str,
    workflow_id: str,
    is_template: bool = False,
) -> None:
    """
    Check if user has permission to access a workflow.
    
    Args:
        workflow_owner_id: Owner ID from workflow metadata
        current_user_id: Current authenticated user ID
        workflow_id: Workflow ID for logging
        is_template: Whether the workflow is a public template
        
    Raises:
        HTTPException: If user doesn't have permission
    """
    # Public templates are accessible to everyone
    if is_template:
        return
    
    # If workflow has no owner (legacy workflows), allow access but log warning
    if not workflow_owner_id:
        logger.warning(
            f"Workflow {workflow_id} has no owner_id set. "
            f"Allowing access to user {current_user_id}. "
            f"Consider migrating legacy workflows."
        )
        return
    
    # Check if user is the owner
    if workflow_owner_id != current_user_id:
        logger.warning(
            f"User {current_user_id} attempted to access workflow {workflow_id} "
            f"owned by {workflow_owner_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this workflow.",
        )


def can_modify_workflow(
    workflow_owner_id: Optional[str],
    current_user_id: str,
    workflow_id: str,
) -> None:
    """
    Check if user has permission to modify a workflow.
    
    Args:
        workflow_owner_id: Owner ID from workflow metadata
        current_user_id: Current authenticated user ID
        workflow_id: Workflow ID for logging
        
    Raises:
        HTTPException: If user doesn't have permission
    """
    # If workflow has no owner (legacy workflows), allow modification but log warning
    if not workflow_owner_id:
        logger.warning(
            f"Workflow {workflow_id} has no owner_id set. "
            f"Allowing modification by user {current_user_id}. "
            f"Consider migrating legacy workflows."
        )
        return
    
    # Check if user is the owner
    if workflow_owner_id != current_user_id:
        logger.warning(
            f"User {current_user_id} attempted to modify workflow {workflow_id} "
            f"owned by {workflow_owner_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this workflow. Only the owner can make changes.",
        )


def filter_workflows_by_user(workflows: list, user_id: str) -> list:
    """
    Filter workflows to only show those accessible by the user.
    
    Args:
        workflows: List of workflow metadata dictionaries
        user_id: Current user ID
        
    Returns:
        Filtered list of workflows
    """
    filtered = []
    
    for workflow in workflows:
        # Include public templates
        if workflow.get("is_template", False):
            filtered.append(workflow)
            continue
        
        # Include workflows owned by the user
        owner_id = workflow.get("owner_id")
        if not owner_id:
            # Legacy workflows without owner_id - include them for now
            # (Can be migrated later)
            logger.debug(f"Including legacy workflow without owner_id: {workflow.get('id')}")
            filtered.append(workflow)
        elif owner_id == user_id:
            filtered.append(workflow)
    
    return filtered


def add_owner_to_workflow(workflow_data: dict, user_id: str) -> dict:
    """
    Add owner_id to workflow data.
    
    Args:
        workflow_data: Workflow data dictionary
        user_id: Owner user ID
        
    Returns:
        Workflow data with owner_id added
    """
    workflow_data["owner_id"] = user_id
    return workflow_data

