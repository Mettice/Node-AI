"""
Knowledge Base API endpoints.

Provides CRUD operations for knowledge bases, versioning, and processing.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.core.knowledge_base import (
    KnowledgeBase,
    KnowledgeBaseVersion,
    ChunkConfig,
    EmbedConfig,
    VectorStoreConfig,
    ProcessingStatus,
    save_knowledge_base,
    load_knowledge_base,
    list_knowledge_bases,
    delete_knowledge_base,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/knowledge-bases", tags=["Knowledge Bases"])


# Request/Response models
class KnowledgeBaseCreateRequest(BaseModel):
    """Request to create a knowledge base."""
    name: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_shared: bool = False
    default_chunk_config: Optional[ChunkConfig] = None
    default_embed_config: Optional[EmbedConfig] = None
    default_vector_store_config: Optional[VectorStoreConfig] = None


class KnowledgeBaseUpdateRequest(BaseModel):
    """Request to update a knowledge base."""
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_shared: Optional[bool] = None
    default_chunk_config: Optional[ChunkConfig] = None
    default_embed_config: Optional[EmbedConfig] = None
    default_vector_store_config: Optional[VectorStoreConfig] = None


class KnowledgeBaseListItem(BaseModel):
    """Knowledge base list item (summary)."""
    id: str
    name: str
    description: Optional[str]
    current_version: int
    file_count: int
    vector_count: int
    created_at: str
    updated_at: str
    tags: List[str]
    is_shared: bool


class KnowledgeBaseListResponse(BaseModel):
    """Response for listing knowledge bases."""
    knowledge_bases: List[KnowledgeBaseListItem]
    total: int


class ProcessKnowledgeBaseRequest(BaseModel):
    """Request to process files in a knowledge base."""
    file_ids: List[str] = Field(description="File IDs to process")
    create_new_version: bool = Field(default=True, description="Create new version or replace current")
    chunk_config: Optional[ChunkConfig] = None
    embed_config: Optional[EmbedConfig] = None
    vector_store_config: Optional[VectorStoreConfig] = None


@router.post("", response_model=KnowledgeBase)
async def create_knowledge_base(request: KnowledgeBaseCreateRequest) -> KnowledgeBase:
    """Create a new knowledge base."""
    try:
        kb = KnowledgeBase(
            id=str(uuid.uuid4()),
            name=request.name,
            description=request.description,
            tags=request.tags,
            is_shared=request.is_shared,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            default_chunk_config=request.default_chunk_config or ChunkConfig(),
            default_embed_config=request.default_embed_config or EmbedConfig(),
            default_vector_store_config=request.default_vector_store_config or VectorStoreConfig(),
        )
        
        save_knowledge_base(kb)
        logger.info(f"Created knowledge base: {kb.id} ({kb.name})")
        return kb
    except Exception as e:
        logger.error(f"Error creating knowledge base: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create knowledge base: {e}")


@router.get("", response_model=KnowledgeBaseListResponse)
async def list_knowledge_bases_endpoint() -> KnowledgeBaseListResponse:
    """List all knowledge bases."""
    try:
        kbs = list_knowledge_bases()
        
        # Convert to list items
        items = []
        for kb in kbs:
            # Get file count and vector count from current version
            file_count = 0
            vector_count = 0
            if kb.versions:
                current_version = next(
                    (v for v in kb.versions if v.version_number == kb.current_version),
                    None
                )
                if current_version:
                    file_count = len(current_version.file_ids)
                    vector_count = current_version.vector_count
            
            items.append(KnowledgeBaseListItem(
                id=kb.id,
                name=kb.name,
                description=kb.description,
                current_version=kb.current_version,
                file_count=file_count,
                vector_count=vector_count,
                created_at=kb.created_at.isoformat(),
                updated_at=kb.updated_at.isoformat(),
                tags=kb.tags,
                is_shared=kb.is_shared,
            ))
        
        return KnowledgeBaseListResponse(
            knowledge_bases=items,
            total=len(items)
        )
    except Exception as e:
        logger.error(f"Error listing knowledge bases: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list knowledge bases: {e}")


@router.get("/{kb_id}", response_model=KnowledgeBase)
async def get_knowledge_base(kb_id: str) -> KnowledgeBase:
    """Get a knowledge base by ID."""
    kb = load_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail=f"Knowledge base {kb_id} not found")
    return kb


@router.put("/{kb_id}", response_model=KnowledgeBase)
async def update_knowledge_base(
    kb_id: str,
    request: KnowledgeBaseUpdateRequest,
) -> KnowledgeBase:
    """Update a knowledge base."""
    kb = load_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail=f"Knowledge base {kb_id} not found")
    
    try:
        if request.name is not None:
            kb.name = request.name
        if request.description is not None:
            kb.description = request.description
        if request.tags is not None:
            kb.tags = request.tags
        if request.is_shared is not None:
            kb.is_shared = request.is_shared
        if request.default_chunk_config is not None:
            kb.default_chunk_config = request.default_chunk_config
        if request.default_embed_config is not None:
            kb.default_embed_config = request.default_embed_config
        if request.default_vector_store_config is not None:
            kb.default_vector_store_config = request.default_vector_store_config
        
        kb.updated_at = datetime.now()
        save_knowledge_base(kb)
        
        logger.info(f"Updated knowledge base: {kb_id}")
        return kb
    except Exception as e:
        logger.error(f"Error updating knowledge base {kb_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update knowledge base: {e}")


@router.delete("/{kb_id}")
async def delete_knowledge_base_endpoint(kb_id: str) -> Dict[str, str]:
    """Delete a knowledge base."""
    kb = load_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail=f"Knowledge base {kb_id} not found")
    
    try:
        # TODO: Also delete associated vector stores
        delete_knowledge_base(kb_id)
        logger.info(f"Deleted knowledge base: {kb_id}")
        return {"message": f"Knowledge base {kb_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting knowledge base {kb_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete knowledge base: {e}")


@router.post("/{kb_id}/process", response_model=KnowledgeBaseVersion)
async def process_knowledge_base(
    kb_id: str,
    request: ProcessKnowledgeBaseRequest,
) -> KnowledgeBaseVersion:
    """
    Process files in a knowledge base (chunk, embed, store).
    
    This creates a new version or replaces the current version.
    """
    kb = load_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail=f"Knowledge base {kb_id} not found")
    
    try:
        # Determine version number
        if request.create_new_version:
            new_version_number = kb.current_version + 1
        else:
            # Mark current version as deprecated
            if kb.versions:
                for version in kb.versions:
                    if version.version_number == kb.current_version:
                        version.status = ProcessingStatus.DEPRECATED
            new_version_number = kb.current_version
        
        # Use provided configs or defaults
        chunk_config = request.chunk_config or kb.default_chunk_config
        embed_config = request.embed_config or kb.default_embed_config
        vector_store_config = request.vector_store_config or kb.default_vector_store_config
        
        # Generate vector store ID
        vector_store_id = f"kb_{kb_id}_v{new_version_number}"
        
        # Create version
        version = KnowledgeBaseVersion(
            id=str(uuid.uuid4()),
            kb_id=kb_id,
            version_number=new_version_number,
            created_at=datetime.now(),
            file_ids=request.file_ids,
            chunk_config=chunk_config,
            embed_config=embed_config,
            vector_store_config=vector_store_config,
            vector_store_id=vector_store_id,
            status=ProcessingStatus.PENDING,
        )
        
        # Add version to KB
        kb.versions.append(version)
        kb.current_version = new_version_number
        kb.updated_at = datetime.now()
        save_knowledge_base(kb)
        
        # Start async processing task
        import asyncio
        from backend.core.kb_processor import process_knowledge_base_async
        
        # Process in background
        asyncio.create_task(process_knowledge_base_async(kb_id, version))
        
        logger.info(f"Created version {new_version_number} for knowledge base {kb_id}, processing started")
        return version
        
    except Exception as e:
        logger.error(f"Error processing knowledge base {kb_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process knowledge base: {e}")


@router.get("/{kb_id}/versions", response_model=List[KnowledgeBaseVersion])
async def list_knowledge_base_versions(kb_id: str) -> List[KnowledgeBaseVersion]:
    """List all versions of a knowledge base."""
    kb = load_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail=f"Knowledge base {kb_id} not found")
    
    return kb.versions


@router.get("/{kb_id}/versions/{version_number}", response_model=KnowledgeBaseVersion)
async def get_knowledge_base_version(
    kb_id: str,
    version_number: int,
) -> KnowledgeBaseVersion:
    """Get a specific version of a knowledge base."""
    kb = load_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail=f"Knowledge base {kb_id} not found")
    
    version = next(
        (v for v in kb.versions if v.version_number == version_number),
        None
    )
    if not version:
        raise HTTPException(
            status_code=404,
            detail=f"Version {version_number} not found for knowledge base {kb_id}"
        )
    
    return version


class VersionComparisonResponse(BaseModel):
    """Response for version comparison."""
    version1: KnowledgeBaseVersion
    version2: KnowledgeBaseVersion
    differences: Dict[str, Any]


@router.get("/{kb_id}/versions/compare")
async def compare_versions(
    kb_id: str,
    version1: int = Query(..., description="First version number"),
    version2: int = Query(..., description="Second version number"),
) -> VersionComparisonResponse:
    """
    Compare two versions of a knowledge base.
    
    Returns differences in configurations, files, and metadata.
    """
    kb = load_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail=f"Knowledge base {kb_id} not found")
    
    v1 = next((v for v in kb.versions if v.version_number == version1), None)
    v2 = next((v for v in kb.versions if v.version_number == version2), None)
    
    if not v1:
        raise HTTPException(status_code=404, detail=f"Version {version1} not found")
    if not v2:
        raise HTTPException(status_code=404, detail=f"Version {version2} not found")
    
    # Calculate differences
    differences: Dict[str, Any] = {}
    
    # Compare chunk config
    chunk_diff = {}
    if v1.chunk_config.chunk_size != v2.chunk_config.chunk_size:
        chunk_diff["chunk_size"] = {"v1": v1.chunk_config.chunk_size, "v2": v2.chunk_config.chunk_size}
    if v1.chunk_config.chunk_overlap != v2.chunk_config.chunk_overlap:
        chunk_diff["chunk_overlap"] = {"v1": v1.chunk_config.chunk_overlap, "v2": v2.chunk_config.chunk_overlap}
    if v1.chunk_config.strategy != v2.chunk_config.strategy:
        chunk_diff["strategy"] = {"v1": v1.chunk_config.strategy, "v2": v2.chunk_config.strategy}
    if chunk_diff:
        differences["chunk_config"] = chunk_diff
    
    # Compare embed config
    embed_diff = {}
    if v1.embed_config.provider != v2.embed_config.provider:
        embed_diff["provider"] = {"v1": v1.embed_config.provider, "v2": v2.embed_config.provider}
    if v1.embed_config.model != v2.embed_config.model:
        embed_diff["model"] = {"v1": v1.embed_config.model, "v2": v2.embed_config.model}
    if embed_diff:
        differences["embed_config"] = embed_diff
    
    # Compare vector store config
    vs_diff = {}
    if v1.vector_store_config.provider != v2.vector_store_config.provider:
        vs_diff["provider"] = {"v1": v1.vector_store_config.provider, "v2": v2.vector_store_config.provider}
    if vs_diff:
        differences["vector_store_config"] = vs_diff
    
    # Compare files
    files_v1 = set(v1.file_ids)
    files_v2 = set(v2.file_ids)
    if files_v1 != files_v2:
        differences["files"] = {
            "added": list(files_v2 - files_v1),
            "removed": list(files_v1 - files_v2),
            "v1_count": len(files_v1),
            "v2_count": len(files_v2),
        }
    
    # Compare metadata
    metadata_diff = {}
    if v1.vector_count != v2.vector_count:
        metadata_diff["vector_count"] = {"v1": v1.vector_count, "v2": v2.vector_count}
    if v1.total_cost != v2.total_cost:
        metadata_diff["total_cost"] = {"v1": v1.total_cost, "v2": v2.total_cost}
    if metadata_diff:
        differences["metadata"] = metadata_diff
    
    return VersionComparisonResponse(
        version1=v1,
        version2=v2,
        differences=differences,
    )


@router.post("/{kb_id}/versions/{version_number}/rollback")
async def rollback_to_version(
    kb_id: str,
    version_number: int,
) -> KnowledgeBase:
    """
    Rollback knowledge base to a specific version.
    
    This sets the specified version as the current version.
    """
    kb = load_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail=f"Knowledge base {kb_id} not found")
    
    version = next(
        (v for v in kb.versions if v.version_number == version_number),
        None
    )
    if not version:
        raise HTTPException(
            status_code=404,
            detail=f"Version {version_number} not found for knowledge base {kb_id}"
        )
    
    if version.status != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot rollback to version {version_number}: version is not completed (status: {version.status})"
        )
    
    # Update current version
    kb.current_version = version_number
    kb.updated_at = datetime.now()
    save_knowledge_base(kb)
    
    logger.info(f"Rolled back knowledge base {kb_id} to version {version_number}")
    return kb

