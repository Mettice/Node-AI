"""
Azure Cognitive Search Integration

Provides vector store functionality using Azure Cognitive Search.
Supports hybrid search (keyword + vector) and semantic search.
"""

from typing import Any, Dict, List, Optional

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    VectorSearch,
    VectorSearchAlgorithmConfiguration,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
)

from backend.core.provider_registry import VectorStoreProvider
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class AzureCognitiveSearchProvider(VectorStoreProvider):
    """
    Azure Cognitive Search vector store provider.
    
    Supports:
    - Vector search
    - Hybrid search (keyword + vector)
    - Semantic search
    - Filtering and faceting
    """

    def __init__(self, endpoint: str, api_key: str, index_name: str):
        """
        Initialize Azure Cognitive Search provider.
        
        Args:
            endpoint: Azure Cognitive Search endpoint URL
            api_key: Azure Cognitive Search API key
            index_name: Name of the search index
        """
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.index_name = index_name
        self.credential = AzureKeyCredential(api_key)
        self.index_client = SearchIndexClient(endpoint=self.endpoint, credential=self.credential)
        self.search_client: Optional[SearchClient] = None

    async def _ensure_index_exists(self, dimension: int, config: Dict[str, Any]) -> None:
        """Ensure the search index exists, create if it doesn't."""
        try:
            # Check if index exists
            self.index_client.get_index(self.index_name)
            logger.info(f"Index '{self.index_name}' already exists")
        except Exception:
            # Index doesn't exist, create it
            logger.info(f"Creating index '{self.index_name}' with dimension {dimension}")
            await self._create_index(dimension, config)

    async def _create_index(self, dimension: int, config: Dict[str, Any]) -> None:
        """Create a new search index with vector support."""
        # Define fields
        fields = [
            SearchField(name="id", type=SearchFieldDataType.String, key=True),
            SearchField(name="content", type=SearchFieldDataType.String, searchable=True),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=dimension,
                vector_search_profile_name="default-vector-profile",
            ),
            SearchField(name="metadata", type=SearchFieldDataType.String, filterable=True),
        ]

        # Add custom metadata fields if specified
        metadata_fields = config.get("metadata_fields", [])
        for field_name, field_type in metadata_fields:
            fields.append(
                SearchField(
                    name=f"metadata_{field_name}",
                    type=SearchFieldDataType.String if field_type == "string" else SearchFieldDataType.Double,
                    filterable=True,
                )
            )

        # Vector search configuration
        vector_search = VectorSearch(
            algorithms=[
                VectorSearchAlgorithmConfiguration(
                    name="default-algorithm",
                    kind="hnsw",
                    hnsw_parameters=HnswAlgorithmConfiguration(
                        m=4,  # Number of bi-directional links
                        ef_construction=400,  # Size of dynamic candidate list
                        ef_search=500,  # Size of dynamic candidate list for search
                        metric="cosine",
                    ),
                )
            ],
            profiles=[
                VectorSearchProfile(
                    name="default-vector-profile",
                    algorithm_configuration_name="default-algorithm",
                )
            ],
        )

        # Semantic search configuration (optional)
        semantic_config = None
        if config.get("enable_semantic_search", False):
            semantic_config = SemanticSearch(
                configurations=[
                    SemanticConfiguration(
                        name="default-semantic-config",
                        prioritized_fields=SemanticPrioritizedFields(
                            title_field=SemanticField(field_name="content"),
                            content_fields=[SemanticField(field_name="content")],
                        ),
                    )
                ]
            )

        # Create index
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search,
            semantic_search=semantic_config,
        )

        self.index_client.create_index(index)
        logger.info(f"Created index '{self.index_name}'")

    async def store(
        self, embeddings: List[List[float]], metadata: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Store vectors with metadata in Azure Cognitive Search.
        
        Args:
            embeddings: List of embedding vectors
            metadata: List of metadata dictionaries
            config: Configuration dictionary
            
        Returns:
            Dictionary with store_id and count
        """
        if not embeddings:
            raise ValueError("No embeddings provided")

        dimension = len(embeddings[0])
        
        # Ensure index exists
        await self._ensure_index_exists(dimension, config)

        # Initialize search client
        if not self.search_client:
            self.search_client = SearchClient(
                endpoint=self.endpoint, index_name=self.index_name, credential=self.credential
            )

        # Prepare documents
        documents = []
        for i, (embedding, meta) in enumerate(zip(embeddings, metadata)):
            doc = {
                "id": meta.get("id", f"doc_{i}"),
                "content": meta.get("text", meta.get("content", "")),
                "content_vector": embedding,
                "metadata": str(meta),
            }
            
            # Add custom metadata fields
            for key, value in meta.items():
                if key not in ["id", "text", "content"]:
                    doc[f"metadata_{key}"] = value
            
            documents.append(doc)

        # Upload documents in batches
        batch_size = config.get("batch_size", 100)
        uploaded_count = 0
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            result = self.search_client.upload_documents(documents=batch)
            
            # Count successful uploads
            for r in result:
                if r.succeeded:
                    uploaded_count += 1
                else:
                    logger.warning(f"Failed to upload document {r.key}: {r.error_message}")

        return {
            "store_id": self.index_name,
            "count": uploaded_count,
            "provider": "azure_cognitive_search",
        }

    async def search(
        self, query_embedding: List[float], top_k: int, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in Azure Cognitive Search.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            config: Configuration dictionary
            
        Returns:
            List of search results with metadata
        """
        if not self.search_client:
            self.search_client = SearchClient(
                endpoint=self.endpoint, index_name=self.index_name, credential=self.credential
            )

        # Build search options
        search_mode = config.get("search_mode", "vector")  # "vector", "hybrid", or "semantic"
        query_text = config.get("query_text", "")
        filter_expression = config.get("filter", None)

        # Import VectorQuery for proper type
        from azure.search.documents.models import VectorizedQuery
        
        # Create vector query
        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=top_k,
            fields="content_vector",
        )
        
        # Vector search
        if search_mode == "vector":
            search_results = self.search_client.search(
                search_text="*",  # Required but not used for vector-only search
                vector_queries=[vector_query],
                top=top_k,
                filter=filter_expression,
            )
        # Hybrid search (keyword + vector)
        elif search_mode == "hybrid":
            search_results = self.search_client.search(
                search_text=query_text or "*",
                vector_queries=[vector_query],
                top=top_k,
                filter=filter_expression,
            )
        # Semantic search
        elif search_mode == "semantic":
            search_results = self.search_client.search(
                search_text=query_text or "*",
                vector_queries=[vector_query],
                semantic_configuration_name="default-semantic-config",
                top=top_k,
                filter=filter_expression,
            )
        else:
            raise ValueError(f"Unsupported search mode: {search_mode}")

        # Format results
        results = []
        for result in search_results:
            results.append({
                "id": result.get("id"),
                "text": result.get("content", ""),
                "score": result.get("@search.score", 0.0),
                "metadata": eval(result.get("metadata", "{}")) if isinstance(result.get("metadata"), str) else result.get("metadata", {}),
            })

        return results

    async def delete(self, ids: List[str], config: Dict[str, Any]) -> bool:
        """
        Delete vectors by IDs.
        
        Args:
            ids: List of document IDs to delete
            config: Configuration dictionary
            
        Returns:
            True if successful
        """
        if not self.search_client:
            self.search_client = SearchClient(
                endpoint=self.endpoint, index_name=self.index_name, credential=self.credential
            )

        # Prepare documents for deletion
        documents = [{"id": doc_id} for doc_id in ids]
        
        result = self.search_client.delete_documents(documents=documents)
        
        # Check if all deletions succeeded
        all_succeeded = all(r.succeeded for r in result)
        
        if not all_succeeded:
            failed = [r.key for r in result if not r.succeeded]
            logger.warning(f"Failed to delete documents: {failed}")
        
        return all_succeeded

