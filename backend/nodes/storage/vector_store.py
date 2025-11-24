"""
Generic Vector Store Node for NodeAI.

This node supports multiple vector storage providers:
- FAISS (in-memory)
- Pinecone (cloud)
- (Chroma, Weaviate, etc. can be added later)
"""

import uuid
from pathlib import Path
from typing import Any, Dict, List

import faiss
import numpy as np

from backend.config import settings
from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.core.secret_resolver import resolve_api_key
from backend.nodes.base import BaseNode
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Global in-memory storage for FAISS indexes
# In production, you'd want to persist this or use a proper storage solution
_faiss_indexes: Dict[str, Any] = {}
_faiss_metadata: Dict[str, List[Dict[str, Any]]] = {}


class VectorStoreNode(BaseNode):
    """
    Generic Vector Store Node.
    
    Supports multiple vector storage providers with a dropdown selector.
    Each provider has its own configuration options.
    """

    node_type = "vector_store"
    name = "Vector Store"
    description = "Store vectors using various providers (FAISS, Pinecone, Chroma, etc.)"
    category = "storage"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the vector store node.
        
        Supports multiple providers based on config selection.
        """
        node_id = config.get("_node_id", "vector_store")
        provider = config.get("provider", "faiss")
        
        # Route to appropriate provider
        if provider == "gemini_file_search":
            # Gemini File Search doesn't need embeddings - it processes files directly
            return await self._store_gemini_file_search(inputs, config, node_id)
        
        # Other providers require embeddings
        embeddings = inputs.get("embeddings")
        if not embeddings:
            raise ValueError("No embeddings provided in inputs")
        
        if not isinstance(embeddings, list) or len(embeddings) == 0:
            raise ValueError("Embeddings must be a non-empty list")
        
        await self.stream_progress(node_id, 0.1, f"Preparing to store {len(embeddings)} vectors using {provider}...")
        
        if provider == "faiss":
            return await self._store_faiss(embeddings, inputs, config, node_id)
        elif provider == "pinecone":
            return await self._store_pinecone(embeddings, inputs, config, node_id)
        elif provider == "azure_cognitive_search":
            return await self._store_azure_cognitive_search(embeddings, inputs, config, node_id)
        else:
            raise ValueError(f"Unsupported storage provider: {provider}")

    async def _store_faiss(
        self,
        embeddings: List[List[float]],
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Store vectors in FAISS index."""
        index_type = config.get("faiss_index_type", "flat")
        persist = config.get("faiss_persist", False)
        file_path = config.get("faiss_file_path")
        
        await self.stream_progress(node_id, 0.2, f"Creating {index_type} index...")
        
        # Get dimension from first embedding
        dimension = len(embeddings[0])
        
        # Create or get index
        index_id = config.get("index_id") or str(uuid.uuid4())
        
        # Check if persisted index exists and can be loaded
        index_loaded = False
        if persist and file_path and Path(file_path).exists():
            try:
                await self.stream_progress(node_id, 0.2, f"Loading existing index from {file_path}...")
                index = faiss.read_index(file_path)
                
                # Load metadata if it exists
                metadata_path = file_path.replace(".faiss", "_metadata.json")
                if Path(metadata_path).exists():
                    import json
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                else:
                    metadata = []
                
                # Store in memory for faster access
                _faiss_indexes[index_id] = index
                _faiss_metadata[index_id] = metadata
                index_loaded = True
                await self.stream_log(node_id, f"Loaded existing index: {index_id} ({index.ntotal} vectors)")
            except Exception as e:
                logger.warning(f"Failed to load existing index, creating new one: {e}")
                index_loaded = False
        
        if index_id in _faiss_indexes and not index_loaded:
            # Add to existing in-memory index
            await self.stream_log(node_id, f"Adding to existing in-memory index: {index_id}")
            index = _faiss_indexes[index_id]
            metadata = _faiss_metadata.get(index_id, [])
        elif not index_loaded:
            # Create new index
            await self.stream_progress(node_id, 0.2, f"Creating new {index_type} index...")
            if index_type == "flat":
                index = faiss.IndexFlatL2(dimension)
            elif index_type == "ivf":
                nlist = config.get("faiss_nlist", 100)
                quantizer = faiss.IndexFlatL2(dimension)
                index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
            elif index_type == "hnsw":
                M = config.get("faiss_M", 32)
                index = faiss.IndexHNSWFlat(dimension, M)
            else:
                raise ValueError(f"Unsupported FAISS index type: {index_type}")
            
            _faiss_indexes[index_id] = index
            _faiss_metadata[index_id] = []
            metadata = []
            await self.stream_log(node_id, f"Created new index: {index_id}")
        
        await self.stream_progress(node_id, 0.4, "Converting embeddings to vectors...")
        
        # Convert embeddings to numpy array
        vectors = np.array(embeddings, dtype=np.float32)
        
        # Only add vectors if index was just created or if we're adding new ones
        if index.ntotal == 0 or not index_loaded:
            await self.stream_progress(node_id, 0.6, f"Adding {len(embeddings)} vectors to index...")
            # Add vectors to index
            index.add(vectors)
        else:
            # Index already has vectors - skip adding (optimization for deployed workflows)
            await self.stream_log(node_id, f"Using existing index with {index.ntotal} vectors (skipping addition)")
            # Don't add vectors - the index is already populated
        
        await self.stream_progress(node_id, 0.7, "Storing metadata...")
        
        # Store metadata (text chunks, etc.)
        chunks = inputs.get("chunks", [])
        
        if not chunks:
            logger.warning(f"No chunks found in inputs for vector store. Available keys: {list(inputs.keys())}")
        
        for i, embedding in enumerate(embeddings):
            chunk_text = chunks[i] if i < len(chunks) and chunks[i] else None
            metadata.append({
                "chunk_index": len(metadata),
                "text": chunk_text,
            })
        
        _faiss_metadata[index_id] = metadata
        
        # Persist if requested
        if persist and file_path:
            await self.stream_progress(node_id, 0.8, f"Persisting index to {file_path}...")
            import os
            import json
            os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else ".", exist_ok=True)
            faiss.write_index(index, file_path)
            # Also save metadata to JSON file
            metadata_path = file_path.replace(".faiss", "_metadata.json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved metadata to {metadata_path}")
            logger.info(f"FAISS index persisted to {file_path}")
        
        # Pass through embedding model info if available (for downstream nodes)
        result = {
            "index_id": index_id,
            "provider": "faiss",
            "vectors_stored": index.ntotal,
            "dimension": dimension,
            "index_type": index_type,
        }
        
        # Include embedding model from inputs if available
        if "model" in inputs:
            result["model"] = inputs["model"]
        if "provider" in inputs:
            result["embedding_provider"] = inputs["provider"]
        
        await self.stream_progress(node_id, 1.0, f"Stored {index.ntotal} vectors in index {index_id}")
        
        return result

    async def _store_pinecone(
        self,
        embeddings: List[List[float]],
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Store vectors in Pinecone."""
        try:
            from pinecone import Pinecone, ServerlessSpec
        except ImportError:
            raise ValueError(
                "pinecone-client not installed. Install it with: pip install pinecone-client"
            )
        
        user_id = config.get("_user_id")
        api_key = resolve_api_key(config, "pinecone_api_key", user_id=user_id) or settings.pinecone_api_key
        if not api_key:
            raise ValueError("Pinecone API key not found. Please configure it in the node settings or environment variables")
        
        index_name = config.get("pinecone_index_name")
        namespace = config.get("pinecone_namespace", "")
        create_index = config.get("pinecone_create_index", False)
        
        if not index_name:
            raise ValueError("Pinecone index name is required")
        
        await self.stream_progress(node_id, 0.2, f"Connecting to Pinecone index: {index_name}...")
        
        pc = Pinecone(api_key=api_key)
        
        # Create index if requested
        if create_index:
            dimension = len(embeddings[0])
            await self.stream_progress(node_id, 0.3, "Checking if index exists...")
            # Check if index exists
            existing_indexes = [idx.name for idx in pc.list_indexes()]
            if index_name not in existing_indexes:
                await self.stream_progress(node_id, 0.4, f"Creating new Pinecone index: {index_name}...")
                pc.create_index(
                    name=index_name,
                    dimension=dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1",
                    ),
                )
                logger.info(f"Created Pinecone index: {index_name}")
        
        # Get index
        index = pc.Index(index_name)
        
        await self.stream_progress(node_id, 0.5, "Preparing vectors for upload...")
        
        # Prepare vectors for upsert
        vectors_to_upsert = []
        chunks = inputs.get("chunks", [])
        
        for i, embedding in enumerate(embeddings):
            vector_id = str(uuid.uuid4())
            metadata = {
                "chunk_index": i,
            }
            if i < len(chunks):
                metadata["text"] = chunks[i]
            
            vectors_to_upsert.append({
                "id": vector_id,
                "values": embedding,
                "metadata": metadata,
            })
        
        # Upsert in batches
        batch_size = config.get("pinecone_batch_size", 100)
        total_batches = (len(vectors_to_upsert) + batch_size - 1) // batch_size
        
        await self.stream_progress(node_id, 0.6, f"Uploading {len(vectors_to_upsert)} vectors in {total_batches} batches...")
        
        for batch_num, i in enumerate(range(0, len(vectors_to_upsert), batch_size)):
            batch = vectors_to_upsert[i : i + batch_size]
            progress = 0.6 + (batch_num / total_batches) * 0.3
            await self.stream_progress(node_id, progress, f"Uploading batch {batch_num + 1}/{total_batches}...")
            index.upsert(vectors=batch, namespace=namespace)
        
        # Get index stats
        stats = index.describe_index_stats()
        
        result = {
            "index_id": index_name,
            "provider": "pinecone",
            "vectors_stored": len(vectors_to_upsert),
            "namespace": namespace,
            "total_vectors": stats.get("total_vector_count", 0),
        }
        
        await self.stream_progress(node_id, 1.0, f"Stored {len(vectors_to_upsert)} vectors in Pinecone")
        
        return result

    async def _store_azure_cognitive_search(
        self,
        embeddings: List[List[float]],
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Store vectors in Azure Cognitive Search."""
        try:
            from backend.integrations.azure.azure_cognitive_search import AzureCognitiveSearchProvider
        except ImportError:
            raise ValueError(
                "azure-search-documents not installed. Install it with: pip install azure-search-documents"
            )
        
        endpoint = config.get("azure_search_endpoint")
        user_id = config.get("_user_id")
        api_key = resolve_api_key(config, "azure_search_api_key", user_id=user_id) or config.get("azure_search_api_key")
        index_name = config.get("azure_search_index_name")
        
        if not endpoint or not api_key or not index_name:
            raise ValueError(
                "Azure Cognitive Search requires: endpoint, api_key, and index_name"
            )
        
        await self.stream_progress(node_id, 0.2, f"Connecting to Azure Cognitive Search index: {index_name}...")
        
        # Initialize provider
        provider = AzureCognitiveSearchProvider(
            endpoint=endpoint,
            api_key=api_key,
            index_name=index_name,
        )
        
        # Prepare metadata
        chunks = inputs.get("chunks", [])
        metadata_list = []
        for i, chunk in enumerate(chunks if chunks else [""] * len(embeddings)):
            meta = {
                "id": f"doc_{i}",
                "text": chunk if isinstance(chunk, str) else str(chunk),
            }
            # Add any additional metadata from inputs
            if "metadata" in inputs and isinstance(inputs["metadata"], list) and i < len(inputs["metadata"]):
                meta.update(inputs["metadata"][i])
            metadata_list.append(meta)
        
        # Store vectors
        await self.stream_progress(node_id, 0.4, f"Storing {len(embeddings)} vectors...")
        result = await provider.store(embeddings, metadata_list, config)
        
        await self.stream_progress(node_id, 1.0, f"Stored {result['count']} vectors in Azure Cognitive Search")
        
        return {
            "index_id": index_name,
            "provider": "azure_cognitive_search",
            "vectors_stored": result["count"],
        }

    async def _store_gemini_file_search(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Store files in Gemini File Search store."""
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise ValueError(
                "google-genai not installed. Install it with: pip install google-genai"
            )
        
        user_id = config.get("_user_id")
        api_key = resolve_api_key(config, "gemini_api_key", user_id=user_id) or settings.gemini_api_key
        if not api_key:
            raise ValueError("Gemini API key not found. Please configure it in the node settings or environment variables")
        
        # Get file information from inputs (from File Loader node)
        file_id = inputs.get("file_id")
        file_path_str = (
            inputs.get("file_path") 
            or inputs.get("text_path") 
            or inputs.get("image_path")
            or inputs.get("audio_path")
            or inputs.get("video_path")
            or inputs.get("data_path")
        )
        
        if not file_id and not file_path_str:
            raise ValueError(
                "For Gemini File Search, provide file_id or file_path from File Loader node"
            )
        
        # Get file path
        if file_path_str:
            from pathlib import Path
            file_path = Path(file_path_str)
        elif file_id:
            # Try to find file in uploads directory
            from pathlib import Path
            upload_dir = Path("uploads")
            # Try common extensions
            for ext in [".pdf", ".txt", ".docx", ".md", ".csv", ".xlsx", ".json"]:
                candidate = upload_dir / f"{file_id}{ext}"
                if candidate.exists():
                    file_path = candidate
                    break
            else:
                raise ValueError(f"File with ID {file_id} not found in uploads directory")
        else:
            raise ValueError("Could not determine file path")
        
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")
        
        await self.stream_progress(node_id, 0.2, f"Preparing to upload {file_path.name} to Gemini File Search...")
        
        client = genai.Client(api_key=api_key)
        
        # Get or create File Search store
        store_name = config.get("gemini_store_name")
        store_display_name = config.get("gemini_store_display_name", "Nodeflow File Search Store")
        
        if store_name:
            # Use existing store
            await self.stream_progress(node_id, 0.3, f"Using existing store: {store_name}")
            try:
                store = client.file_search_stores.get(name=store_name)
            except Exception as e:
                logger.warning(f"Could not get store {store_name}, creating new one: {e}")
                store = client.file_search_stores.create(config={"display_name": store_display_name})
                store_name = store.name
        else:
            # Create new store
            await self.stream_progress(node_id, 0.3, f"Creating new File Search store: {store_display_name}")
            store = client.file_search_stores.create(config={"display_name": store_display_name})
            store_name = store.name
        
        await self.stream_progress(node_id, 0.4, f"Uploading file to store...")
        
        # Prepare chunking config if provided
        chunking_config = None
        max_tokens = config.get("gemini_max_tokens_per_chunk")
        max_overlap = config.get("gemini_max_overlap_tokens")
        if max_tokens or max_overlap:
            chunking_config = {
                "white_space_config": {
                    "max_tokens_per_chunk": max_tokens or 200,
                    "max_overlap_tokens": max_overlap or 20,
                }
            }
        
        # Prepare custom metadata if provided
        custom_metadata = config.get("gemini_custom_metadata")
        metadata_list = None
        if custom_metadata and isinstance(custom_metadata, dict):
            metadata_list = []
            for key, value in custom_metadata.items():
                if isinstance(value, (int, float)):
                    metadata_list.append({"key": key, "numeric_value": value})
                else:
                    metadata_list.append({"key": key, "string_value": str(value)})
        
        # Upload file to File Search store
        upload_config = {
            "display_name": config.get("gemini_file_display_name") or file_path.name,
        }
        if chunking_config:
            upload_config["chunking_config"] = chunking_config
        if metadata_list:
            upload_config["custom_metadata"] = metadata_list
        
        try:
            operation = client.file_search_stores.upload_to_file_search_store(
                file=str(file_path),
                file_search_store_name=store_name,
                config=upload_config,
            )
            
            await self.stream_progress(node_id, 0.5, "Waiting for file processing to complete...")
            
            # Poll operation status
            import time
            max_wait_time = 300  # 5 minutes max
            start_time = time.time()
            while not operation.done:
                if time.time() - start_time > max_wait_time:
                    raise TimeoutError("File upload operation timed out")
                await self.stream_progress(
                    node_id, 
                    0.5 + (0.4 * (time.time() - start_time) / max_wait_time),
                    "Processing file (chunking, embedding, indexing)..."
                )
                time.sleep(2)
                operation = client.operations.get(operation)
            
            await self.stream_progress(node_id, 0.9, "File processing completed")
            
            # Get file name from operation result
            file_name = None
            if hasattr(operation, 'response') and operation.response:
                if hasattr(operation.response, 'file_name'):
                    file_name = operation.response.file_name
                elif isinstance(operation.response, dict) and 'file_name' in operation.response:
                    file_name = operation.response['file_name']
            
            result = {
                "index_id": store_name,  # Use store_name as index_id for compatibility
                "provider": "gemini_file_search",
                "store_name": store_name,
                "file_name": file_name or file_path.name,
                "vectors_stored": 1,  # File Search handles this internally
            }
            
            await self.stream_progress(node_id, 1.0, f"File uploaded to File Search store: {store_name}")
            
            return result
            
        except Exception as e:
            logger.error(f"Gemini File Search upload error: {e}")
            raise

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema with provider selection and dynamic config."""
        return {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "title": "Storage Provider",
                    "description": "Select the vector storage provider",
                    "enum": ["faiss", "pinecone", "azure_cognitive_search", "gemini_file_search"],
                    "default": "faiss",
                },
                # FAISS config
                "faiss_index_type": {
                    "type": "string",
                    "title": "FAISS Index Type",
                    "description": "Type of FAISS index",
                    "enum": ["flat", "ivf", "hnsw"],
                    "default": "flat",
                },
                "faiss_persist": {
                    "type": "boolean",
                    "title": "Persist to Disk",
                    "description": "Save index to disk",
                    "default": False,
                },
                "faiss_file_path": {
                    "type": "string",
                    "title": "File Path",
                    "description": "Path to save FAISS index (if persisting)",
                    "default": "./data/vectors/index.faiss",
                },
                "index_id": {
                    "type": "string",
                    "title": "Index ID (Optional)",
                    "description": "Existing index ID to add to, or leave empty to create new",
                    "default": "",
                },
                # Pinecone config
                "pinecone_index_name": {
                    "type": "string",
                    "title": "Index Name",
                    "description": "Pinecone index name",
                    "default": "",
                },
                "pinecone_namespace": {
                    "type": "string",
                    "title": "Namespace (Optional)",
                    "description": "Pinecone namespace",
                    "default": "",
                },
                "pinecone_create_index": {
                    "type": "boolean",
                    "title": "Create Index",
                    "description": "Create index if it doesn't exist",
                    "default": False,
                },
                "pinecone_batch_size": {
                    "type": "integer",
                    "title": "Batch Size",
                    "description": "Number of vectors per batch",
                    "default": 100,
                    "minimum": 1,
                    "maximum": 1000,
                },
                # Gemini File Search config
                "gemini_store_name": {
                    "type": "string",
                    "title": "File Search Store Name (Optional)",
                    "description": "Existing store name (e.g., 'fileSearchStores/my-store-123'). Leave empty to create new.",
                    "default": "",
                },
                "gemini_store_display_name": {
                    "type": "string",
                    "title": "Store Display Name",
                    "description": "Display name for the File Search store (used when creating new store)",
                    "default": "Nodeflow File Search Store",
                },
                "gemini_file_display_name": {
                    "type": "string",
                    "title": "File Display Name (Optional)",
                    "description": "Display name for the file in the store (defaults to filename)",
                    "default": "",
                },
                "gemini_max_tokens_per_chunk": {
                    "type": "integer",
                    "title": "Max Tokens Per Chunk",
                    "description": "Maximum tokens per chunk (default: 200)",
                    "default": 200,
                    "minimum": 50,
                    "maximum": 2000,
                },
                "gemini_max_overlap_tokens": {
                    "type": "integer",
                    "title": "Max Overlap Tokens",
                    "description": "Maximum overlapping tokens between chunks (default: 20)",
                    "default": 20,
                    "minimum": 0,
                    "maximum": 200,
                },
                "gemini_custom_metadata": {
                    "type": "object",
                    "title": "Custom Metadata (Optional)",
                    "description": "Key-value pairs for filtering (e.g., {\"author\": \"John Doe\", \"year\": 2024})",
                    "default": {},
                },
                # Azure Cognitive Search config
                "azure_search_endpoint": {
                    "type": "string",
                    "title": "Azure Search Endpoint",
                    "description": "Azure Cognitive Search endpoint URL (e.g., https://your-service.search.windows.net)",
                    "default": "",
                },
                "azure_search_api_key": {
                    "type": "string",
                    "title": "Azure Search API Key",
                    "description": "Azure Cognitive Search API key",
                    "default": "",
                },
                "azure_search_index_name": {
                    "type": "string",
                    "title": "Index Name",
                    "description": "Name of the search index",
                    "default": "",
                },
                "azure_search_batch_size": {
                    "type": "integer",
                    "title": "Batch Size",
                    "description": "Number of documents per batch",
                    "default": 100,
                    "minimum": 1,
                    "maximum": 1000,
                },
                "azure_search_enable_semantic": {
                    "type": "boolean",
                    "title": "Enable Semantic Search",
                    "description": "Enable semantic search capabilities (requires semantic configuration)",
                    "default": False,
                },
                "azure_search_metadata_fields": {
                    "type": "array",
                    "title": "Custom Metadata Fields (Optional)",
                    "description": "List of [field_name, field_type] pairs for custom metadata (e.g., [['author', 'string'], ['year', 'number']])",
                    "items": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "default": [],
                },
            },
            "required": ["provider"],
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for node outputs."""
        return {
            "index_id": {
                "type": "string",
                "description": "Index identifier",
            },
            "provider": {
                "type": "string",
                "description": "Storage provider used",
            },
            "vectors_stored": {
                "type": "integer",
                "description": "Number of vectors stored",
            },
        }


# Register the node
NodeRegistry.register(
    "vector_store",
    VectorStoreNode,
    VectorStoreNode().get_metadata(),
)

