"""
Node information API endpoints.

This module provides REST API endpoints for querying available nodes
and their schemas.
"""

from typing import Dict, List

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from backend.core.exceptions import NodeNotFoundError
from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.core.cache import get_cache
from backend.core.security import limiter
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Nodes"])

# Cache for node metadata (TTL: 1 hour)
_cache = get_cache()


@router.get("/nodes")
@limiter.limit("5/minute")
async def list_nodes(request: Request) -> JSONResponse:
    """
    List all available nodes.
    
    Returns:
        List of node metadata with schemas and descriptions
    """
    # Cache node list (nodes don't change at runtime)
    cache_key = "nodes:list"
    cached = _cache.get(cache_key)
    if cached is not None:
        return JSONResponse(content=cached)
    
    metadata = NodeRegistry.list_all_metadata()
    # Convert NodeMetadata objects to dict for JSON serialization
    metadata_dicts = [item.model_dump() if hasattr(item, 'model_dump') else item for item in metadata]
    _cache.set(cache_key, metadata_dicts, ttl_seconds=3600)  # 1 hour
    return JSONResponse(content=metadata_dicts)


@router.get("/nodes/categories")
@limiter.limit("5/minute")
async def get_node_categories(request: Request) -> JSONResponse:
    """
    Get all node categories.
    
    Returns:
        Dictionary with categories and their node counts
    """
    categories = NodeRegistry.get_categories()
    
    result = {}
    for category in categories:
        nodes = NodeRegistry.get_by_category(category)
        result[category] = {
            "count": len(nodes),
            "nodes": nodes,
        }
    
    return JSONResponse(content=result)


@router.get("/nodes/{node_type}")
@limiter.limit("30/minute")
async def get_node_schema(node_type: str, request: Request) -> JSONResponse:
    """
    Get schema for a specific node type.
    
    Args:
        node_type: The node type identifier (e.g., 'text_input', 'chunk')
        
    Returns:
        Node metadata with full schema
        
    Raises:
        HTTPException: If node type not found
    """
    # Cache node schema (schemas don't change at runtime)
    cache_key = f"nodes:schema:{node_type}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return JSONResponse(content=cached)
    
    try:
        metadata = NodeRegistry.get_metadata(node_type)
        if not metadata:
            # Try to get from node instance
            node_class = NodeRegistry.get(node_type)
            node_instance = node_class()
            metadata = node_instance.get_metadata()
        
        # Convert NodeMetadata to dict for JSON serialization
        metadata_dict = metadata.model_dump() if hasattr(metadata, 'model_dump') else metadata
        # Cache the metadata
        _cache.set(cache_key, metadata_dict, ttl_seconds=3600)  # 1 hour
        return JSONResponse(content=metadata_dict)
    except NodeNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

