"""
Generic Vector Search Node for NodeAI.

This node supports multiple vector search providers:
- FAISS (in-memory search)
- Pinecone (cloud search)
- (More providers can be added later)
"""

from typing import Any, Dict, List

import faiss
import numpy as np

from backend.config import settings
from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.core.secret_resolver import resolve_api_key
from backend.nodes.base import BaseNode
from backend.nodes.storage.vector_store import _faiss_indexes, _faiss_metadata
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class VectorSearchNode(BaseNode):
    """
    Generic Vector Search Node.
    
    Supports multiple vector search providers with a dropdown selector.
    Each provider has its own configuration options.
    """

    node_type = "vector_search"
    name = "Vector Search"
    description = "Search for similar vectors using various providers (FAISS, Pinecone, etc.)"
    category = "retrieval"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the vector search node.
        
        Supports multiple providers based on config selection.
        """
        node_id = config.get("_node_id", "vector_search")
        provider = config.get("provider", "faiss")
        
        await self.stream_progress(node_id, 0.1, "Preparing search...")
        
        # Debug: Log what we received
        logger.info(f"Vector Search - Config keys: {list(config.keys())}, Inputs keys: {list(inputs.keys())}")
        logger.info(f"Vector Search - Query from config: {config.get('query')}, Query from inputs: {inputs.get('query')}")
        
        # Get query embedding
        # Can come from inputs (if embedded upstream) or needs to be embedded
        query_embedding = inputs.get("query_embedding")
        
        # Also check for embeddings from embed node
        if not query_embedding:
            embeddings = inputs.get("embeddings")
            if embeddings:
                # Handle list of embeddings (take first one)
                if isinstance(embeddings, list) and len(embeddings) > 0:
                    if isinstance(embeddings[0], list):
                        # It's a list of embeddings, take the first one
                        query_embedding = embeddings[0]
                    else:
                        # It's a single embedding
                        query_embedding = embeddings
        
        query_text = inputs.get("query") or config.get("query")
        
        if not query_embedding and not query_text:
            raise ValueError("Either query_embedding or query text must be provided")
        
        # If we have text but no embedding, embed it automatically using OpenAI
        if not query_embedding:
            await self.stream_progress(node_id, 0.2, "Embedding query text...")
            # Try to determine embedding model from inputs
            # Priority: explicit model in inputs > config > use dimension from vector store
            embedding_model = inputs.get("model") or config.get("embedding_model")
            
            # If no model specified, try to infer from vector store dimension
            if not embedding_model:
                dimension = inputs.get("dimension")
                if dimension == 1536:
                    embedding_model = "text-embedding-3-small"
                    logger.info(f"Inferred embedding model from dimension {dimension}: {embedding_model}")
                elif dimension == 3072:
                    embedding_model = "text-embedding-3-large"
                    logger.info(f"Inferred embedding model from dimension {dimension}: {embedding_model}")
                else:
                    # Default fallback
                    embedding_model = "text-embedding-3-small"
                    logger.warning(f"Unknown dimension {dimension}, defaulting to {embedding_model}")
            
            logger.info(f"Auto-embedding query using model: {embedding_model} (inputs: {list(inputs.keys())})")
            try:
                from openai import OpenAI
                user_id = config.get("_user_id")
                api_key = resolve_api_key(config, "openai_api_key", user_id=user_id) or settings.openai_api_key
                client = OpenAI(api_key=api_key)
                response = client.embeddings.create(
                    model=embedding_model,
                    input=query_text
                )
                query_embedding = response.data[0].embedding
                logger.info(f"Query embedded successfully (dimension: {len(query_embedding)})")
                await self.stream_progress(node_id, 0.3, "Query embedded successfully")
            except Exception as e:
                raise ValueError(
                    f"Failed to auto-embed query: {e}. Connect an Embed node before this node."
                )
        else:
            await self.stream_progress(node_id, 0.3, "Using provided query embedding")
        
        # Route to appropriate provider
        if provider == "faiss":
            return await self._search_faiss(query_embedding, inputs, config, node_id)
        elif provider == "pinecone":
            return await self._search_pinecone(query_embedding, query_text, inputs, config, node_id)
        elif provider == "azure_cognitive_search":
            return await self._search_azure_cognitive_search(query_embedding, query_text, inputs, config, node_id)
        else:
            raise ValueError(f"Unsupported search provider: {provider}")

    async def _search_faiss(
        self,
        query_embedding: List[float],
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Search using FAISS index."""
        # Check if using Knowledge Base mode
        kb_id = config.get("knowledge_base_id")
        kb_version = config.get("knowledge_base_version")
        version = None
        
        if kb_id:
            # Load knowledge base and get vector store ID
            from backend.core.knowledge_base import load_knowledge_base
            kb = load_knowledge_base(kb_id)
            if not kb:
                raise ValueError(f"Knowledge base '{kb_id}' not found")
            
            # Get version (default to current)
            version_number = kb_version if kb_version is not None else kb.current_version
            version = next((v for v in kb.versions if v.version_number == version_number), None)
            if not version:
                raise ValueError(f"Version {version_number} not found for knowledge base '{kb_id}'")
            
            if version.status.value != "completed":
                raise ValueError(f"Knowledge base version {version_number} is not ready (status: {version.status.value})")
            
            index_id = version.vector_store_id
            await self.stream_progress(node_id, 0.4, f"Using Knowledge Base '{kb.name}' v{version_number}...")
        else:
            # Get index_id from inputs (from vector_store node) or config
            index_id = inputs.get("index_id") or config.get("index_id")
            
            if not index_id:
                raise ValueError("index_id or knowledge_base_id is required for FAISS search. Connect a Vector Store node, set index_id in config, or use a Knowledge Base.")
        
        await self.stream_progress(node_id, 0.4, f"Loading FAISS index: {index_id}...")
        
        # Try to load from disk if not in memory
        if index_id not in _faiss_indexes:
            # Check if it's a KB vector store and try to load from disk
            if kb_id and version:
                if version.vector_store_path:
                    import os
                    if os.path.exists(version.vector_store_path):
                        await self.stream_progress(node_id, 0.45, f"Loading index from disk: {version.vector_store_path}...")
                        try:
                            index = faiss.read_index(version.vector_store_path)
                            _faiss_indexes[index_id] = index
                            # Load metadata if available
                            metadata_path = version.vector_store_path.replace(".faiss", "_metadata.json")
                            if os.path.exists(metadata_path):
                                import json
                                with open(metadata_path, "r") as f:
                                    _faiss_metadata[index_id] = json.load(f)
                            else:
                                _faiss_metadata[index_id] = []
                            logger.info(f"Loaded FAISS index from disk: {version.vector_store_path}")
                        except Exception as e:
                            logger.error(f"Failed to load index from disk: {e}")
                            raise ValueError(f"FAISS index '{index_id}' not found in memory and failed to load from disk: {e}")
                    else:
                        raise ValueError(f"FAISS index file not found: {version.vector_store_path}")
                else:
                    raise ValueError(f"FAISS index '{index_id}' not found and no file path available")
            else:
                raise ValueError(f"FAISS index '{index_id}' not found")
        
        index = _faiss_indexes[index_id]
        metadata = _faiss_metadata.get(index_id, [])
        
        await self.stream_progress(node_id, 0.5, f"Index loaded: {index.ntotal} vectors available")
        
        # Convert query to numpy array
        query_vector = np.array([query_embedding], dtype=np.float32)
        
        # Get top-k
        top_k = config.get("top_k", 5)
        score_threshold = config.get("score_threshold", 0.0)
        
        await self.stream_progress(node_id, 0.6, f"Searching for top {top_k} results...")
        
        # Search
        distances, indices = index.search(query_vector, top_k)
        
        # Build results
        results = []
        all_scores = []  # Track all scores for debugging
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:  # Invalid index
                continue
            
            # Convert distance to similarity score (for L2 distance, lower is better)
            # For cosine similarity, you'd use 1 - distance
            score = 1.0 / (1.0 + distance)  # Convert distance to similarity
            all_scores.append(score)
            
            if score < score_threshold:
                logger.info(f"Vector Search - Filtered result {i}: score={score:.4f} < threshold={score_threshold}")
                continue
            
            # Get metadata
            meta = metadata[idx] if idx < len(metadata) else {}
            
            results.append({
                "text": meta.get("text", ""),
                "score": float(score),
                "distance": float(distance),
                "index": int(idx),
                "metadata": meta,
            })
        
        # Debug: Log search summary
        logger.info(f"Vector Search - Found {len(results)} results (filtered from {len(all_scores)} candidates)")
        if all_scores:
            logger.info(f"Vector Search - Score range: min={min(all_scores):.4f}, max={max(all_scores):.4f}, threshold={score_threshold}")
        
        await self.stream_progress(node_id, 0.9, f"Found {len(results)} results")
        
        result = {
            "results": results,
            "provider": "faiss",
            "query": inputs.get("query", "") or config.get("query", ""),
            "top_k": top_k,
            "results_count": len(results),
        }
        
        await self.stream_progress(node_id, 1.0, "Search completed")
        
        return result

    async def _search_pinecone(
        self,
        query_embedding: List[float],
        query_text: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Search using Pinecone index."""
        try:
            from pinecone import Pinecone
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
        top_k = config.get("top_k", 5)
        score_threshold = config.get("score_threshold", 0.0)
        filter_metadata = config.get("filter_metadata")  # Optional metadata filter
        
        if not index_name:
            raise ValueError("Pinecone index name is required")
        
        await self.stream_progress(node_id, 0.4, f"Connecting to Pinecone index: {index_name}...")
        
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)
        
        await self.stream_progress(node_id, 0.6, f"Searching for top {top_k} results...")
        
        # Build query
        query_kwargs = {
            "vector": query_embedding,
            "top_k": top_k,
            "include_metadata": True,
        }
        
        if namespace:
            query_kwargs["namespace"] = namespace
        
        if filter_metadata:
            query_kwargs["filter"] = filter_metadata
        
        # Search
        response = index.query(**query_kwargs)
        
        # Build results
        results = []
        for match in response.matches:
            score = match.score
            
            if score < score_threshold:
                continue
            
            results.append({
                "text": match.metadata.get("text", "") if match.metadata else "",
                "score": float(score),
                "id": match.id,
                "metadata": match.metadata or {},
            })
        
        await self.stream_progress(node_id, 0.9, f"Found {len(results)} results")
        
        result = {
            "results": results,
            "provider": "pinecone",
            "query": query_text or "",
            "top_k": top_k,
            "results_count": len(results),
        }
        
        await self.stream_progress(node_id, 1.0, "Search completed")
        
        return result

    async def _search_azure_cognitive_search(
        self,
        query_embedding: List[float],
        query_text: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Search using Azure Cognitive Search."""
        try:
            from backend.integrations.azure.azure_cognitive_search import AzureCognitiveSearchProvider
        except ImportError:
            raise ValueError(
                "azure-search-documents not installed. Install it with: pip install azure-search-documents"
            )
        
        endpoint = config.get("azure_search_endpoint")
        user_id = config.get("_user_id")
        api_key = resolve_api_key(config, "azure_search_api_key", user_id=user_id) or config.get("azure_search_api_key")
        index_name = config.get("azure_search_index_name") or inputs.get("index_id")
        
        if not endpoint or not api_key or not index_name:
            raise ValueError(
                "Azure Cognitive Search requires: endpoint, api_key, and index_name"
            )
        
        top_k = config.get("top_k", 5)
        score_threshold = config.get("score_threshold", 0.0)
        search_mode = config.get("azure_search_mode", "hybrid")  # vector, hybrid, semantic
        
        await self.stream_progress(node_id, 0.4, f"Searching Azure Cognitive Search index: {index_name}...")
        
        # Initialize provider
        provider = AzureCognitiveSearchProvider(
            endpoint=endpoint,
            api_key=api_key,
            index_name=index_name,
        )
        
        # Search configuration
        search_config = {
            "search_mode": search_mode,
            "query_text": query_text,
            "filter": config.get("azure_search_filter"),
        }
        
        # Perform search
        results = await provider.search(query_embedding, top_k, search_config)
        
        # Filter by score threshold
        filtered_results = [
            r for r in results if r.get("score", 0.0) >= score_threshold
        ]
        
        await self.stream_progress(node_id, 0.9, f"Found {len(filtered_results)} results")
        
        result = {
            "results": filtered_results,
            "provider": "azure_cognitive_search",
            "query": query_text or "",
            "top_k": top_k,
            "results_count": len(filtered_results),
        }
        
        await self.stream_progress(node_id, 1.0, "Search completed")
        
        return result

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema with provider selection and dynamic config."""
        return {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "title": "Search Provider",
                    "description": "Select the vector search provider",
                    "enum": ["faiss", "pinecone", "azure_cognitive_search"],
                    "default": "faiss",
                },
                # Common config
                "query": {
                    "type": "string",
                    "title": "Query Text",
                    "description": "Search query (will be embedded if query_embedding not provided)",
                    "default": "",
                },
                "top_k": {
                    "type": "integer",
                    "title": "Top K",
                    "description": "Number of results to return",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 100,
                },
                "score_threshold": {
                    "type": "number",
                    "title": "Score Threshold",
                    "description": "Minimum similarity score (0.0 to 1.0)",
                    "default": 0.0,
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
                # Knowledge Base mode
                "knowledge_base_id": {
                    "type": "string",
                    "title": "Knowledge Base ID",
                    "description": "Use a Knowledge Base instead of index_id (optional)",
                    "default": "",
                },
                "knowledge_base_version": {
                    "type": "integer",
                    "title": "Knowledge Base Version",
                    "description": "Version number to use (defaults to current version)",
                    "default": None,
                },
                # FAISS config
                "index_id": {
                    "type": "string",
                    "title": "Index ID",
                    "description": "FAISS index identifier (from Vector Store node, or leave empty if using Knowledge Base)",
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
                "filter_metadata": {
                    "type": "object",
                    "title": "Metadata Filter (Optional)",
                    "description": "Pinecone metadata filter (JSON object)",
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
                    "description": "Name of the search index (or use index_id from Vector Store node)",
                    "default": "",
                },
                "azure_search_mode": {
                    "type": "string",
                    "title": "Search Mode",
                    "description": "Search mode: vector (vector only), hybrid (keyword + vector), or semantic (semantic + vector)",
                    "enum": ["vector", "hybrid", "semantic"],
                    "default": "hybrid",
                },
                "azure_search_filter": {
                    "type": "string",
                    "title": "Filter Expression (Optional)",
                    "description": "OData filter expression (e.g., \"metadata_author eq 'John Doe'\")",
                    "default": "",
                },
            },
            "required": ["provider"],
        }

    def get_input_schema(self) -> Dict[str, Any]:
        """Return schema for node inputs."""
        return {
            "query": {
                "type": "string",
                "description": "Search query text",
                "required": False,
            },
            "query_embedding": {
                "type": "array",
                "description": "Query embedding vector (from Embed node)",
                "required": False,
            },
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for node outputs."""
        return {
            "results": {
                "type": "array",
                "description": "Search results",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "score": {"type": "number"},
                        "metadata": {"type": "object"},
                    },
                },
            },
            "provider": {
                "type": "string",
                "description": "Provider used",
            },
            "query": {
                "type": "string",
                "description": "Search query",
            },
            "results_count": {
                "type": "integer",
                "description": "Number of results returned",
            },
        }


# Register the node
NodeRegistry.register(
    "vector_search",
    VectorSearchNode,
    VectorSearchNode().get_metadata(),
)

