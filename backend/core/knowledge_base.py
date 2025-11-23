"""
Knowledge Base models and core functionality.

Knowledge Bases are collections of processed files with shared configurations.
They support versioning, allowing users to reprocess files with different configs.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import uuid

from pydantic import BaseModel, Field


class ProcessingStatus(str, Enum):
    """Status of knowledge base processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEPRECATED = "deprecated"


class ChunkConfig(BaseModel):
    """Chunking configuration."""
    strategy: str = Field(default="recursive", description="Chunking strategy")
    chunk_size: int = Field(default=512, description="Chunk size in tokens")
    chunk_overlap: int = Field(default=50, description="Overlap between chunks")
    separators: List[str] = Field(default_factory=list, description="Custom separators")
    min_chunk_size: int = Field(default=100, description="Minimum chunk size")
    max_chunk_size: int = Field(default=1000, description="Maximum chunk size")
    overlap_sentences: int = Field(default=1, description="Overlap sentences")


class EmbedConfig(BaseModel):
    """Embedding configuration."""
    provider: str = Field(default="openai", description="Embedding provider")
    model: str = Field(default="text-embedding-3-small", description="Model name")
    dimensions: Optional[int] = Field(default=None, description="Embedding dimensions")
    batch_size: int = Field(default=100, description="Batch size for processing")
    use_finetuned_model: bool = Field(default=False, description="Use fine-tuned model")
    finetuned_model_id: Optional[str] = Field(default=None, description="Fine-tuned model ID")


class VectorStoreConfig(BaseModel):
    """Vector store configuration."""
    provider: str = Field(default="faiss", description="Vector store provider")
    index_type: str = Field(default="flat", description="Index type (for FAISS)")
    persist: bool = Field(default=True, description="Persist to disk")
    file_path: Optional[str] = Field(default=None, description="Storage file path")


class KnowledgeBaseVersion(BaseModel):
    """A version of a knowledge base with specific processing config."""
    id: str = Field(description="Version ID")
    kb_id: str = Field(description="Knowledge Base ID")
    version_number: int = Field(description="Version number (1, 2, 3, ...)")
    created_at: datetime = Field(description="Creation timestamp")
    
    # Files in this version
    file_ids: List[str] = Field(default_factory=list, description="File IDs in this version")
    
    # Processing configurations
    chunk_config: ChunkConfig = Field(description="Chunking configuration used")
    embed_config: EmbedConfig = Field(description="Embedding configuration used")
    vector_store_config: VectorStoreConfig = Field(description="Vector store configuration")
    
    # Vector store location
    vector_store_id: str = Field(description="Vector store identifier")
    vector_store_path: Optional[str] = Field(default=None, description="Vector store file path")
    vector_count: int = Field(default=0, description="Number of vectors stored")
    
    # Status
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING, description="Processing status")
    processing_log: Optional[str] = Field(default=None, description="Processing log/error")
    
    # Metadata
    processing_duration_ms: Optional[int] = Field(default=None, description="Processing duration")
    total_cost: float = Field(default=0.0, description="Total processing cost")
    created_by: Optional[str] = Field(default=None, description="User who created this version")


class KnowledgeBase(BaseModel):
    """Knowledge Base model - collection of processed files."""
    id: str = Field(description="Knowledge Base ID")
    name: str = Field(description="Knowledge Base name")
    description: Optional[str] = Field(default=None, description="Description")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    
    # Current active version
    current_version: int = Field(default=1, description="Current active version number")
    
    # Default processing configs (used when creating new versions)
    default_chunk_config: ChunkConfig = Field(default_factory=ChunkConfig, description="Default chunk config")
    default_embed_config: EmbedConfig = Field(default_factory=EmbedConfig, description="Default embed config")
    default_vector_store_config: VectorStoreConfig = Field(default_factory=VectorStoreConfig, description="Default vector store config")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for organization")
    is_shared: bool = Field(default=False, description="Can be used by multiple workflows")
    
    # Version history (stored separately, but referenced here)
    versions: List[KnowledgeBaseVersion] = Field(default_factory=list, description="Version history")


# Storage directory for knowledge bases
KB_STORAGE_DIR = Path("backend/data/knowledge_bases")
KB_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def get_kb_path(kb_id: str) -> Path:
    """Get file path for a knowledge base."""
    return KB_STORAGE_DIR / f"{kb_id}.json"


def save_knowledge_base(kb: KnowledgeBase) -> None:
    """Save knowledge base to disk."""
    kb_path = get_kb_path(kb.id)
    kb_dict = kb.model_dump(mode="json")
    
    # Convert datetime to ISO format
    if isinstance(kb_dict.get("created_at"), datetime):
        kb_dict["created_at"] = kb.created_at.isoformat()
    if isinstance(kb_dict.get("updated_at"), datetime):
        kb_dict["updated_at"] = kb.updated_at.isoformat()
    
    # Handle versions
    if "versions" in kb_dict:
        for version in kb_dict["versions"]:
            if isinstance(version.get("created_at"), datetime):
                version["created_at"] = version["created_at"].isoformat()
    
    with open(kb_path, "w", encoding="utf-8") as f:
        json.dump(kb_dict, f, indent=2, ensure_ascii=False)


def load_knowledge_base(kb_id: str) -> Optional[KnowledgeBase]:
    """Load knowledge base from disk."""
    kb_path = get_kb_path(kb_id)
    if not kb_path.exists():
        return None
    
    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Parse datetime strings
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
        
        # Parse versions
        if "versions" in data:
            for version in data["versions"]:
                if "created_at" in version and isinstance(version["created_at"], str):
                    version["created_at"] = datetime.fromisoformat(version["created_at"].replace("Z", "+00:00"))
                if "status" in version and isinstance(version["status"], str):
                    version["status"] = ProcessingStatus(version["status"])
        
        return KnowledgeBase(**data)
    except Exception as e:
        from backend.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.error(f"Error loading knowledge base {kb_id}: {e}")
        return None


def list_knowledge_bases() -> List[KnowledgeBase]:
    """List all knowledge bases."""
    kbs = []
    for kb_file in KB_STORAGE_DIR.glob("*.json"):
        try:
            kb_id = kb_file.stem
            kb = load_knowledge_base(kb_id)
            if kb:
                kbs.append(kb)
        except Exception as e:
            from backend.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.warning(f"Error loading knowledge base from {kb_file}: {e}")
    return kbs


def delete_knowledge_base(kb_id: str) -> bool:
    """Delete a knowledge base."""
    kb_path = get_kb_path(kb_id)
    if kb_path.exists():
        kb_path.unlink()
        return True
    return False

