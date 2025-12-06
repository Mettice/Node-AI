"""
BM25 Keyword Search Node for NodeAI.

This node provides BM25 (Best Matching 25) ranking for keyword-based retrieval.
BM25 is excellent for exact keyword matching and term frequency-based relevance.

BM25 complements vector search:
- Vector search: Semantic similarity (handles synonyms, context)
- BM25: Keyword matching (handles exact terms, technical terms, names)
"""

from typing import Any, Dict, List, Optional
import re
from collections import defaultdict

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None

from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.nodes.base import BaseNode
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# In-memory storage for BM25 indexes (similar to FAISS indexes)
# Key: index_id, Value: BM25Okapi instance
_bm25_indexes: Dict[str, BM25Okapi] = {}
# Key: index_id, Value: List of documents (for result retrieval)
_bm25_documents: Dict[str, List[Dict[str, Any]]] = {}


def _tokenize(text: str) -> List[str]:
    """Tokenize text into words (simple whitespace-based tokenization)."""
    # Convert to lowercase and split on whitespace
    # Remove punctuation and keep alphanumeric tokens
    tokens = re.findall(r'\b\w+\b', text.lower())
    return tokens


class BM25SearchNode(BaseNode):
    """
    BM25 Keyword Search Node.
    
    Provides BM25 ranking for keyword-based retrieval.
    BM25 is excellent for exact keyword matching and complements vector search.
    """

    node_type = "bm25_search"
    name = "BM25 Search"
    description = "Keyword-based search using BM25 ranking algorithm. Excellent for exact term matching."
    category = "retrieval"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute BM25 search.
        
        Requires:
        1. Query text (from inputs or config)
        2. Documents to search (from inputs or indexed documents)
        """
        node_id = config.get("_node_id", "bm25_search")
        query = config.get("query") or inputs.get("query") or inputs.get("text")
        
        # Validate query
        if not query:
            raise ValueError(
                "Query is required for BM25 search.\n"
                "Provide a search query string."
            )
        
        if not isinstance(query, str) or not query.strip():
            raise ValueError(
                f"Query must be a non-empty string. Got: {type(query).__name__}"
            )
        
        await self.stream_progress(node_id, 0.1, "Starting BM25 search...")
        
        # Check if rank-bm25 is installed
        if BM25Okapi is None:
            raise ImportError(
                "rank-bm25 package is not installed.\n"
                "Please install it with: pip install rank-bm25"
            )
        
        # Get documents to search
        # Option 1: From inputs (if documents are passed directly)
        documents = inputs.get("documents") or inputs.get("chunks") or []
        
        # Option 2: From indexed BM25 index (if index_id is provided)
        index_id = config.get("index_id") or inputs.get("index_id")
        
        if not documents and not index_id:
            raise ValueError(
                "No documents provided for BM25 search.\n"
                "Either provide documents/chunks in inputs, or provide an index_id "
                "to use a previously indexed BM25 index."
            )
        
        # Get configuration
        top_k = config.get("top_k", 10)
        score_threshold = config.get("score_threshold", 0.0)
        
        # Validate top_k
        try:
            top_k = int(top_k)
            if top_k < 1 or top_k > 1000:
                raise ValueError("top_k must be between 1 and 1000")
        except (ValueError, TypeError):
            raise ValueError(
                f"top_k must be an integer between 1 and 1000. Got: {top_k}"
            )
        
        await self.stream_progress(node_id, 0.3, f"Searching {len(documents) if documents else 'indexed'} documents...")
        
        # Get or create BM25 index
        if index_id and index_id in _bm25_indexes:
            # Use existing index
            bm25 = _bm25_indexes[index_id]
            indexed_documents = _bm25_documents.get(index_id, [])
            await self.stream_progress(node_id, 0.5, f"Using indexed BM25 index: {index_id}")
        elif documents:
            # Create new index from documents
            await self.stream_progress(node_id, 0.4, f"Indexing {len(documents)} documents...")
            
            # Extract text from documents
            document_texts = []
            indexed_documents = []
            
            for doc in documents:
                if isinstance(doc, str):
                    text = doc
                    doc_meta = {"text": text}
                elif isinstance(doc, dict):
                    text = doc.get("text") or doc.get("content") or str(doc)
                    doc_meta = doc.copy()
                else:
                    text = str(doc)
                    doc_meta = {"text": text}
                
                document_texts.append(text)
                indexed_documents.append(doc_meta)
            
            # Tokenize documents
            tokenized_docs = [_tokenize(text) for text in document_texts]
            
            # Create BM25 index
            bm25 = BM25Okapi(tokenized_docs)
            
            # Store index if index_id provided
            if index_id:
                _bm25_indexes[index_id] = bm25
                _bm25_documents[index_id] = indexed_documents
                await self.stream_progress(node_id, 0.5, f"Indexed and stored BM25 index: {index_id}")
            else:
                await self.stream_progress(node_id, 0.5, "BM25 index created (not stored)")
        else:
            raise ValueError(
                "No documents or valid index_id provided.\n"
                "Please provide documents to search or a valid index_id."
            )
        
        # Tokenize query
        tokenized_query = _tokenize(query)
        
        if not tokenized_query:
            logger.warning("Query tokenized to empty list, returning empty results")
            await self.stream_progress(node_id, 1.0, "No valid query terms found")
            return {
                "results": [],
                "query": query,
                "results_count": 0,
                "provider": "bm25",
            }
        
        await self.stream_progress(node_id, 0.6, f"Searching with query: {query[:50]}...")
        
        # Get BM25 scores
        scores = bm25.get_scores(tokenized_query)
        
        # Create results with scores
        results_with_scores = [
            {
                "document": doc,
                "score": float(score),
                "index": idx,
            }
            for idx, (doc, score) in enumerate(zip(indexed_documents, scores))
        ]
        
        # Filter by score threshold and sort by score
        filtered_results = [
            r for r in results_with_scores
            if r["score"] >= score_threshold
        ]
        filtered_results.sort(key=lambda x: x["score"], reverse=True)
        
        # Take top_k
        top_results = filtered_results[:top_k]
        
        await self.stream_progress(node_id, 0.9, f"Found {len(top_results)} results")
        
        # Format results (similar to vector search output format)
        formatted_results = []
        for result in top_results:
            doc = result["document"]
            text = doc.get("text") or doc.get("content") or str(doc)
            
            formatted_results.append({
                "text": text,
                "score": result["score"],
                "metadata": {k: v for k, v in doc.items() if k not in ["text", "content"]},
                "index": result["index"],
            })
        
        await self.stream_progress(node_id, 1.0, f"BM25 search complete: {len(formatted_results)} results")
        
        await self.stream_output(node_id, {
            "results": formatted_results,
            "query": query,
            "results_count": len(formatted_results),
        }, partial=False)
        
        return {
            "results": formatted_results,
            "query": query,
            "results_count": len(formatted_results),
            "provider": "bm25",
            "index_id": index_id if index_id else None,
        }

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for BM25 search configuration."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "title": "Query",
                    "description": "Search query (keywords)",
                },
                "index_id": {
                    "type": "string",
                    "title": "Index ID (Optional)",
                    "description": "ID of a previously indexed BM25 index. If not provided, documents from inputs will be indexed on-the-fly.",
                    "default": "",
                },
                "top_k": {
                    "type": "integer",
                    "title": "Top K",
                    "description": "Number of results to return",
                    "minimum": 1,
                    "maximum": 1000,
                    "default": 10,
                },
                "score_threshold": {
                    "type": "number",
                    "title": "Score Threshold",
                    "description": "Minimum BM25 score to include in results (0.0 = no threshold)",
                    "minimum": 0.0,
                    "default": 0.0,
                },
            },
            "required": ["query"],
        }

    def get_input_schema(self) -> Dict[str, Any]:
        """Return schema for node inputs."""
        return {
            "query": {
                "type": "string",
                "description": "Search query text",
                "required": False,
            },
            "text": {
                "type": "string",
                "description": "Search query text (alternative to query)",
                "required": False,
            },
            "documents": {
                "type": "array",
                "description": "List of documents to search (if not using indexed index)",
                "required": False,
            },
            "chunks": {
                "type": "array",
                "description": "List of text chunks to search (alternative to documents)",
                "required": False,
            },
            "index_id": {
                "type": "string",
                "description": "ID of a previously indexed BM25 index",
                "required": False,
            },
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for node outputs."""
        return {
            "results": {
                "type": "array",
                "description": "BM25 search results",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "score": {"type": "number"},
                        "metadata": {"type": "object"},
                        "index": {"type": "integer"},
                    },
                },
            },
            "query": {
                "type": "string",
                "description": "Search query",
            },
            "results_count": {
                "type": "integer",
                "description": "Number of results returned",
            },
            "provider": {
                "type": "string",
                "description": "Provider used (always 'bm25')",
            },
            "index_id": {
                "type": ["string", "null"],
                "description": "Index ID used (if any)",
            },
        }

    def estimate_cost(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> float:
        """Estimate cost for BM25 search."""
        # BM25 is free (local computation)
        return 0.0


# Register the node
NodeRegistry.register(
    "bm25_search",
    BM25SearchNode,
    BM25SearchNode().get_metadata(),
)

