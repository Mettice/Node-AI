"""
Knowledge Base Processing Pipeline.

Processes files in a knowledge base: chunk, embed, and store vectors.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.core.knowledge_base import (
    KnowledgeBase,
    KnowledgeBaseVersion,
    ProcessingStatus,
    ChunkConfig,
    EmbedConfig,
    VectorStoreConfig,
    load_knowledge_base,
    save_knowledge_base,
)
from backend.core.node_registry import NodeRegistry
from backend.nodes.input.file_loader import FileLoaderNode
from backend.nodes.processing.chunk import ChunkNode
from backend.nodes.embedding.embed import EmbedNode
from backend.nodes.storage.vector_store import VectorStoreNode
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class KnowledgeBaseProcessor:
    """Processes files in a knowledge base."""

    def __init__(self):
        self.file_loader = FileLoaderNode()
        self.chunk_node = ChunkNode()
        self.embed_node = EmbedNode()
        self.vector_store = VectorStoreNode()

    async def process_knowledge_base(
        self,
        kb_id: str,
        version: KnowledgeBaseVersion,
    ) -> KnowledgeBaseVersion:
        """
        Process files in a knowledge base version.
        
        Steps:
        1. Load files and extract text
        2. Chunk text
        3. Create embeddings
        4. Store in vector store
        
        Returns updated version with processing results.
        """
        start_time = time.time()
        version.status = ProcessingStatus.PROCESSING
        version.processing_log = "Starting processing..."
        
        # Update KB to save version status
        kb = load_knowledge_base(kb_id)
        if not kb:
            raise ValueError(f"Knowledge base {kb_id} not found")
        
        # Save initial status
        save_knowledge_base(kb)
        
        try:
            all_chunks = []
            all_embeddings = []
            total_cost = 0.0
            
            # Step 1: Load and extract text from all files
            logger.info(f"Loading {len(version.file_ids)} files for KB {kb_id} version {version.version_number}")
            version.processing_log = f"Loading {len(version.file_ids)} files..."
            
            for file_id in version.file_ids:
                try:
                    # Load file
                    file_inputs = {}
                    file_config = {
                        "file_id": file_id,
                        "include_base64": False,
                        "_node_id": f"file_loader_{file_id}",
                    }
                    
                    file_result = await self.file_loader.execute(file_inputs, file_config)
                    text = file_result.get("text", "")
                    
                    if not text or not text.strip():
                        error_msg = f"No text extracted from file {file_id}. "
                        error_msg += "The file may be empty, corrupted, or in an unsupported format."
                        logger.warning(error_msg)
                        version.processing_log = f"Warning: {error_msg}"
                        continue
                    
                    # Step 2: Chunk text
                    chunk_inputs = {"text": text}
                    chunk_config = {
                        "strategy": version.chunk_config.strategy,
                        "chunk_size": version.chunk_config.chunk_size,
                        "chunk_overlap": version.chunk_config.chunk_overlap,
                        "separators": version.chunk_config.separators,
                        "min_chunk_size": version.chunk_config.min_chunk_size,
                        "max_chunk_size": version.chunk_config.max_chunk_size,
                        "overlap_sentences": version.chunk_config.overlap_sentences,
                        "_node_id": f"chunk_{file_id}",
                    }
                    
                    chunk_result = await self.chunk_node.execute(chunk_inputs, chunk_config)
                    chunks = chunk_result.get("chunks", [])
                    
                    if not chunks:
                        logger.warning(f"No chunks created from file {file_id}")
                        continue
                    
                    # Store chunks with metadata
                    for i, chunk_text in enumerate(chunks):
                        all_chunks.append({
                            "text": chunk_text,
                            "file_id": file_id,
                            "kb_id": kb_id,
                            "version": version.version_number,
                            "chunk_index": len(all_chunks) + i,
                        })
                    logger.info(f"Created {len(chunks)} chunks from file {file_id}")
                    
                except Exception as e:
                    logger.error(f"Error processing file {file_id}: {e}", exc_info=True)
                    version.processing_log = f"Error processing file {file_id}: {str(e)}"
                    # Continue with other files
                    continue
            
            if not all_chunks:
                error_msg = "No chunks created from any files. This usually means:\n"
                error_msg += "1. Files were empty or couldn't be read\n"
                error_msg += "2. Text extraction failed (check file format)\n"
                error_msg += "3. Chunking produced no valid chunks\n"
                error_msg += f"Processed {len(version.file_ids)} file(s) but no text was extracted."
                raise ValueError(error_msg)
            
            # Step 3: Create embeddings
            logger.info(f"Creating embeddings for {len(all_chunks)} chunks")
            version.processing_log = f"Creating embeddings for {len(all_chunks)} chunks..."
            
            # Extract text from chunks for embedding
            chunk_texts = [chunk["text"] for chunk in all_chunks]
            
            # Double-check we have text to embed
            if not chunk_texts or not any(chunk_texts):
                raise ValueError("No text or chunks provided in inputs - all chunks are empty")
            
            logger.info(f"Preparing to embed {len(chunk_texts)} chunks, first chunk length: {len(chunk_texts[0]) if chunk_texts else 0}")
            
            # Embed node expects "text" or "chunks" key, not "texts"
            # Use "chunks" since we have a list of text chunks
            embed_inputs = {"chunks": chunk_texts}
            embed_config = {
                "provider": version.embed_config.provider,
                "model": version.embed_config.model,
                "batch_size": version.embed_config.batch_size,
                "use_finetuned_model": version.embed_config.use_finetuned_model,
                "finetuned_model_id": version.embed_config.finetuned_model_id,
                "_node_id": "embed_kb",
            }
            
            logger.info(f"Embed config: provider={embed_config['provider']}, model={embed_config['model']}, batch_size={embed_config['batch_size']}")
            logger.debug(f"Embed inputs keys: {list(embed_inputs.keys())}, chunks count: {len(embed_inputs['chunks'])}")
            
            embed_result = await self.embed_node.execute(embed_inputs, embed_config)
            all_embeddings = embed_result.get("embeddings", [])
            embed_cost = embed_result.get("cost", 0.0)
            total_cost += embed_cost
            
            if not all_embeddings:
                raise ValueError("No embeddings created")
            
            if len(all_embeddings) != len(all_chunks):
                raise ValueError(f"Mismatch: {len(all_chunks)} chunks but {len(all_embeddings)} embeddings")
            
            # Step 4: Store in vector store
            logger.info(f"Storing {len(all_embeddings)} vectors")
            version.processing_log = f"Storing {len(all_embeddings)} vectors..."
            
            # Set vector store path
            if not version.vector_store_path:
                vector_store_dir = Path("backend/data/vectors")
                vector_store_dir.mkdir(parents=True, exist_ok=True)
                version.vector_store_path = str(vector_store_dir / f"{version.vector_store_id}.faiss")
            
            # Vector store expects chunks as list of strings
            chunk_texts_for_store = [chunk["text"] for chunk in all_chunks]
            
            store_inputs = {
                "embeddings": all_embeddings,
                "chunks": chunk_texts_for_store,  # Vector store expects "chunks" key
            }
            store_config = {
                "provider": version.vector_store_config.provider,
                "index_id": version.vector_store_id,
                "faiss_index_type": version.vector_store_config.index_type,
                "faiss_persist": version.vector_store_config.persist,
                "faiss_file_path": version.vector_store_path,
                "_node_id": "vector_store_kb",
            }
            
            store_result = await self.vector_store.execute(store_inputs, store_config)
            vectors_stored = store_result.get("vectors_stored", len(all_embeddings))
            
            # Update version with results
            version.vector_count = vectors_stored
            version.total_cost = total_cost
            version.status = ProcessingStatus.COMPLETED
            version.processing_log = f"Successfully processed {len(version.file_ids)} files, created {len(all_chunks)} chunks, stored {vectors_stored} vectors"
            version.processing_duration_ms = int((time.time() - start_time) * 1000)
            
            logger.info(f"KB {kb_id} version {version.version_number} processed successfully: {vectors_stored} vectors stored")
            
        except Exception as e:
            logger.error(f"Error processing KB {kb_id} version {version.version_number}: {e}", exc_info=True)
            version.status = ProcessingStatus.FAILED
            version.processing_log = f"Processing failed: {str(e)}"
            version.processing_duration_ms = int((time.time() - start_time) * 1000)
        
        # Update KB with version changes
        kb = load_knowledge_base(kb_id)
        if kb:
            # Update the version in the KB
            for i, v in enumerate(kb.versions):
                if v.id == version.id:
                    kb.versions[i] = version
                    break
            kb.updated_at = datetime.now()
            save_knowledge_base(kb)
        
        return version


# Global processor instance
_processor = KnowledgeBaseProcessor()


async def process_knowledge_base_async(kb_id: str, version: KnowledgeBaseVersion) -> KnowledgeBaseVersion:
    """Async wrapper for processing a knowledge base."""
    return await _processor.process_knowledge_base(kb_id, version)

