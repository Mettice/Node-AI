"""
Node information API endpoints.

This module provides REST API endpoints for querying available nodes
and their schemas.
"""

from typing import Dict, List

from fastapi import APIRouter, HTTPException

from backend.core.exceptions import NodeNotFoundError
from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.core.cache import get_cache
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Nodes"])

# Cache for node metadata (TTL: 1 hour)
_cache = get_cache()


@router.get("/nodes", response_model=List[NodeMetadata])
async def list_nodes() -> List[NodeMetadata]:
    """
    List all available nodes.
    
    Returns:
        List of node metadata with schemas and descriptions
    """
    # Cache node list (nodes don't change at runtime)
    cache_key = "nodes:list"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached
    
    metadata = NodeRegistry.list_all_metadata()
    _cache.set(cache_key, metadata, ttl_seconds=3600)  # 1 hour
    return metadata


@router.get("/nodes/{node_type}", response_model=NodeMetadata)
async def get_node_schema(node_type: str) -> NodeMetadata:
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
        return cached
    
    try:
        metadata = NodeRegistry.get_metadata(node_type)
        if not metadata:
            # Try to get from node instance
            node_class = NodeRegistry.get(node_type)
            node_instance = node_class()
            metadata = node_instance.get_metadata()
        
        # Cache the metadata
        _cache.set(cache_key, metadata, ttl_seconds=3600)  # 1 hour
        return metadata
    except NodeNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )


@router.get("/nodes/categories")
async def get_node_categories() -> Dict:
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
    
    return result

