"""
Hybrid Retrieval Node for NodeAI.

This node combines vector search (semantic similarity) with knowledge graph
queries (structured relationships) for comprehensive retrieval in Hybrid RAG systems.

Based on the insight: "Author networks, citations, and institutional collaborations
aren't semantic similarities. They're structured relationships that don't live in embeddings."
"""

from typing import Any, Dict, List, Optional
import math

from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.nodes.base import BaseNode
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class HybridRetrievalNode(BaseNode):
    """
    Hybrid Retrieval Node.
    
    Combines vector search (semantic similarity) with knowledge graph queries
    (structured relationships) and fuses the results intelligently.
    """

    node_type = "hybrid_retrieval"
    name = "Hybrid Retrieval"
    description = "Combine vector search and knowledge graph queries for comprehensive retrieval"
    category = "retrieval"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute hybrid retrieval.
        
        Combines results from:
        1. Vector search (semantic similarity)
        2. Knowledge graph queries (structured relationships)
        3. Fuses results using chosen method
        """
        node_id = config.get("_node_id", "hybrid_retrieval")
        query = config.get("query") or inputs.get("query")
        
        # Validate query
        if not query:
            raise ValueError(
                "Query is required for hybrid retrieval.\n"
                "Provide a search query string."
            )
        
        if not isinstance(query, str) or not query.strip():
            raise ValueError(
                f"Query must be a non-empty string. Got: {type(query).__name__}"
            )
        
        await self.stream_progress(node_id, 0.1, "Starting hybrid retrieval...")
        
        # Get fusion method and weights
        fusion_method = config.get("fusion_method", "reciprocal_rank")
        vector_weight = config.get("vector_weight", 0.7)
        graph_weight = config.get("graph_weight", 0.3)
        top_k = config.get("top_k", 10)
        
        # Validate fusion method
        valid_methods = ["reciprocal_rank", "weighted", "simple_merge"]
        if fusion_method not in valid_methods:
            raise ValueError(
                f"Invalid fusion_method: '{fusion_method}'. "
                f"Valid methods are: {', '.join(valid_methods)}"
            )
        
        # Validate weights
        try:
            vector_weight = float(vector_weight)
            graph_weight = float(graph_weight)
        except (ValueError, TypeError):
            raise ValueError(
                f"vector_weight and graph_weight must be numbers. "
                f"Got: vector_weight={vector_weight}, graph_weight={graph_weight}"
            )
        
        if vector_weight < 0 or graph_weight < 0:
            raise ValueError(
                f"Weights must be non-negative. "
                f"Got: vector_weight={vector_weight}, graph_weight={graph_weight}"
            )
        
        # Validate top_k
        try:
            top_k = int(top_k)
            if top_k < 1 or top_k > 1000:
                raise ValueError("top_k must be between 1 and 1000")
        except (ValueError, TypeError):
            raise ValueError(
                f"top_k must be an integer between 1 and 1000. Got: {top_k}"
            )
        
        # Normalize weights
        total_weight = vector_weight + graph_weight
        if total_weight > 0:
            vector_weight = vector_weight / total_weight
            graph_weight = graph_weight / total_weight
        elif fusion_method == "weighted":
            # If both weights are 0, default to equal weights
            vector_weight = 0.5
            graph_weight = 0.5
            logger.warning("Both weights are 0, using equal weights (0.5 each)")
        
        vector_results = []
        graph_results = []
        
        # Step 1: Vector search (if enabled and results available)
        # Check if we have vector search results from upstream node
        vector_search_config = config.get("vector_search_config", {})
        if vector_search_config.get("enabled", True):
            await self.stream_progress(node_id, 0.2, "Extracting vector search results...")
            try:
                vector_results = await self._extract_vector_results(inputs, config)
                await self.stream_progress(node_id, 0.5, f"Vector search: {len(vector_results)} results")
            except Exception as e:
                logger.warning(f"Failed to extract vector search results: {e}")
                if vector_search_config.get("required", False):
                    raise ValueError(
                        f"Vector search is required but failed: {str(e)}\n"
                        "Please ensure a Vector Search node is connected upstream."
                    )
                # Continue without vector results if not required
        
        # Step 2: Graph query (if enabled and results available)
        # Check if we have graph query results from upstream node
        graph_query_config = config.get("graph_query_config", {})
        if graph_query_config.get("enabled", True):
            await self.stream_progress(node_id, 0.6, "Extracting graph query results...")
            try:
                graph_results = await self._extract_graph_results(inputs, config)
                await self.stream_progress(node_id, 0.8, f"Graph query: {len(graph_results)} results")
            except Exception as e:
                logger.warning(f"Failed to extract graph query results: {e}")
                if graph_query_config.get("required", False):
                    raise ValueError(
                        f"Graph query is required but failed: {str(e)}\n"
                        "Please ensure a Knowledge Graph node is connected upstream."
                    )
                # Continue without graph results if not required
        
        # Validate we have at least one source of results
        if not vector_results and not graph_results:
            raise ValueError(
                "No results found from either vector search or graph query.\n"
                "Please ensure at least one of the following is connected:\n"
                "1. Vector Search node (for semantic similarity)\n"
                "2. Knowledge Graph node (for relationship queries)\n"
                "Or enable at least one source in the configuration."
            )
        
        # Step 3: Fuse results
        await self.stream_progress(node_id, 0.9, f"Fusing {len(vector_results)} vector + {len(graph_results)} graph results...")
        try:
            fused_results = self._fuse_results(
                vector_results,
                graph_results,
                fusion_method,
                vector_weight,
                graph_weight,
                top_k,
            )
        except Exception as e:
            raise ValueError(
                f"Failed to fuse results: {str(e)}\n"
                f"Fusion method: {fusion_method}\n"
                "Please check your configuration and try again."
            ) from e
        
        await self.stream_progress(node_id, 1.0, f"Hybrid retrieval complete: {len(fused_results)} results")
        await self.stream_output(node_id, {
            "results": fused_results,
            "vector_count": len(vector_results),
            "graph_count": len(graph_results),
            "fused_count": len(fused_results),
        }, partial=False)
        
        return {
            "results": fused_results,
            "vector_results": vector_results,
            "graph_results": graph_results,
            "vector_count": len(vector_results),
            "graph_count": len(graph_results),
            "fused_count": len(fused_results),
            "fusion_method": fusion_method,
        }

    def _extract_vector_results(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Extract vector search results from inputs.
        
        The workflow engine merges outputs from upstream nodes.
        Vector Search node outputs: {"results": [...], "provider": "...", "results_count": N}
        
        We identify vector results by:
        1. Presence of "provider" key (faiss, pinecone, etc.)
        2. Result structure (has "score", "text", "metadata")
        """
        # Check for vector search output structure
        if "provider" in inputs:
            # This looks like Vector Search node output
            if "results" in inputs and isinstance(inputs["results"], list):
                results = inputs["results"]
                # Verify these are vector results (have score, text, metadata)
                if results and isinstance(results[0], dict):
                    if "score" in results[0] or "distance" in results[0]:
                        return results
        
        # Check if "results" contains vector-like results
        if "results" in inputs:
            results = inputs["results"]
            if isinstance(results, list) and results:
                first_result = results[0]
                if isinstance(first_result, dict):
                    # Vector results typically have: score, text, metadata, distance
                    # Graph results typically have: node_id, labels, properties, relationship_type
                    has_vector_keys = any(key in first_result for key in ["score", "distance", "text", "metadata"])
                    has_graph_keys = any(key in first_result for key in ["node_id", "labels", "relationship_type"])
                    
                    # If it has vector keys but not graph keys, it's vector results
                    if has_vector_keys and not has_graph_keys:
                        return results
        
        # Check for explicit vector search results key
        if "vector_search_results" in inputs:
            results = inputs["vector_search_results"]
            if isinstance(results, dict) and "results" in results:
                return results["results"]
            elif isinstance(results, list):
                return results
        
        # If not found, return empty list
        logger.debug("No vector search results found in inputs")
        return []

    def _extract_graph_results(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Extract graph query results from inputs.
        
        The workflow engine merges outputs from upstream nodes.
        Knowledge Graph node outputs: {"results": [...], "count": N, "operation": "query"}
        
        We identify graph results by:
        1. Presence of "operation" key with value "query"
        2. Result structure (has "node_id", "labels", "properties", "relationship_type")
        """
        # Check for Knowledge Graph output structure
        if "operation" in inputs and inputs.get("operation") == "query":
            # This looks like Knowledge Graph node output
            if "results" in inputs and isinstance(inputs["results"], list):
                results = inputs["results"]
                # Verify these are graph results
                if results and isinstance(results[0], dict):
                    if any(key in results[0] for key in ["node_id", "labels", "properties", "relationship_type"]):
                        return results
        
        # Check if "results" contains graph-like results
        if "results" in inputs:
            results = inputs["results"]
            if isinstance(results, list) and results:
                first_result = results[0]
                if isinstance(first_result, dict):
                    # Graph results typically have: node_id, labels, properties, relationship_type
                    # Vector results typically have: score, text, metadata, distance
                    has_graph_keys = any(key in first_result for key in ["node_id", "labels", "properties", "relationship_type"])
                    has_vector_keys = any(key in first_result for key in ["score", "distance", "text", "metadata"])
                    
                    # If it has graph keys but not vector keys, it's graph results
                    if has_graph_keys and not has_vector_keys:
                        return results
        
        # Check for explicit graph query results key
        if "graph_query_results" in inputs:
            results = inputs["graph_query_results"]
            if isinstance(results, dict) and "results" in results:
                return results["results"]
            elif isinstance(results, list):
                return results
        
        # If not found, return empty list
        logger.debug("No graph query results found in inputs")
        return []

    def _fuse_results(
        self,
        vector_results: List[Dict[str, Any]],
        graph_results: List[Dict[str, Any]],
        fusion_method: str,
        vector_weight: float,
        graph_weight: float,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        Fuse results from vector search and graph query.
        
        Methods:
        - reciprocal_rank: Reciprocal Rank Fusion (RRF)
        - weighted: Weighted combination of scores
        - simple_merge: Simple merge with deduplication
        """
        if fusion_method == "reciprocal_rank":
            return self._reciprocal_rank_fusion(vector_results, graph_results, top_k)
        elif fusion_method == "weighted":
            return self._weighted_fusion(vector_results, graph_results, vector_weight, graph_weight, top_k)
        elif fusion_method == "simple_merge":
            return self._simple_merge(vector_results, graph_results, top_k)
        else:
            logger.warning(f"Unknown fusion method: {fusion_method}, using simple_merge")
            return self._simple_merge(vector_results, graph_results, top_k)

    def _reciprocal_rank_fusion(
        self,
        vector_results: List[Dict[str, Any]],
        graph_results: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF).
        
        RRF score = sum(1 / (k + rank)) for each result set
        where k is a constant (typically 60)
        """
        k = 60  # RRF constant
        scores: Dict[str, Dict[str, Any]] = {}
        
        # Process vector results
        for rank, result in enumerate(vector_results, start=1):
            result_id = self._get_result_id(result)
            rrf_score = 1.0 / (k + rank)
            
            if result_id not in scores:
                scores[result_id] = {
                    "result": result,
                    "rrf_score": 0.0,
                    "sources": [],
                }
            
            scores[result_id]["rrf_score"] += rrf_score
            scores[result_id]["sources"].append("vector")
        
        # Process graph results
        for rank, result in enumerate(graph_results, start=1):
            result_id = self._get_result_id(result)
            rrf_score = 1.0 / (k + rank)
            
            if result_id not in scores:
                scores[result_id] = {
                    "result": result,
                    "rrf_score": 0.0,
                    "sources": [],
                }
            
            scores[result_id]["rrf_score"] += rrf_score
            scores[result_id]["sources"].append("graph")
        
        # Sort by RRF score and return top_k
        sorted_results = sorted(
            scores.values(),
            key=lambda x: x["rrf_score"],
            reverse=True,
        )[:top_k]
        
        # Format results
        fused = []
        for item in sorted_results:
            result = item["result"].copy()
            result["hybrid_score"] = item["rrf_score"]
            result["sources"] = item["sources"]
            fused.append(result)
        
        return fused

    def _weighted_fusion(
        self,
        vector_results: List[Dict[str, Any]],
        graph_results: List[Dict[str, Any]],
        vector_weight: float,
        graph_weight: float,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Weighted combination of scores."""
        scores: Dict[str, Dict[str, Any]] = {}
        
        # Normalize vector scores (assume they're in [0, 1] range)
        max_vector_score = max(
            (r.get("score", 0.0) for r in vector_results),
            default=1.0,
        )
        if max_vector_score == 0:
            max_vector_score = 1.0
        
        # Process vector results
        for result in vector_results:
            result_id = self._get_result_id(result)
            normalized_score = (result.get("score", 0.0) / max_vector_score) * vector_weight
            
            if result_id not in scores:
                scores[result_id] = {
                    "result": result,
                    "weighted_score": 0.0,
                    "sources": [],
                }
            
            scores[result_id]["weighted_score"] += normalized_score
            scores[result_id]["sources"].append("vector")
        
        # Normalize graph scores (assume they're in [0, 1] range)
        max_graph_score = max(
            (r.get("score", 0.0) for r in graph_results),
            default=1.0,
        )
        if max_graph_score == 0:
            max_graph_score = 1.0
        
        # Process graph results
        for result in graph_results:
            result_id = self._get_result_id(result)
            normalized_score = (result.get("score", 0.0) / max_graph_score) * graph_weight
            
            if result_id not in scores:
                scores[result_id] = {
                    "result": result,
                    "weighted_score": 0.0,
                    "sources": [],
                }
            
            scores[result_id]["weighted_score"] += normalized_score
            scores[result_id]["sources"].append("graph")
        
        # Sort by weighted score and return top_k
        sorted_results = sorted(
            scores.values(),
            key=lambda x: x["weighted_score"],
            reverse=True,
        )[:top_k]
        
        # Format results
        fused = []
        for item in sorted_results:
            result = item["result"].copy()
            result["hybrid_score"] = item["weighted_score"]
            result["sources"] = item["sources"]
            fused.append(result)
        
        return fused

    def _simple_merge(
        self,
        vector_results: List[Dict[str, Any]],
        graph_results: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Simple merge with deduplication."""
        seen_ids = set()
        merged = []
        
        # Add vector results first
        for result in vector_results:
            result_id = self._get_result_id(result)
            if result_id not in seen_ids:
                result_copy = result.copy()
                result_copy["sources"] = ["vector"]
                merged.append(result_copy)
                seen_ids.add(result_id)
        
        # Add graph results
        for result in graph_results:
            result_id = self._get_result_id(result)
            if result_id not in seen_ids:
                result_copy = result.copy()
                result_copy["sources"] = ["graph"]
                merged.append(result_copy)
                seen_ids.add(result_id)
            else:
                # Update existing result to include graph source
                for item in merged:
                    if self._get_result_id(item) == result_id:
                        if "sources" not in item:
                            item["sources"] = []
                        if "graph" not in item["sources"]:
                            item["sources"].append("graph")
                        break
        
        return merged[:top_k]

    def _get_result_id(self, result: Dict[str, Any]) -> str:
        """Extract unique ID from result for deduplication."""
        # Try various ID fields
        for key in ["id", "node_id", "document_id", "paper_id", "entity_id", "text"]:
            if key in result:
                return str(result[key])
        
        # Fallback: use hash of result
        import hashlib
        result_str = str(sorted(result.items()))
        return hashlib.md5(result_str.encode()).hexdigest()

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for hybrid retrieval configuration."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "title": "Query",
                    "description": "Search query",
                },
                "fusion_method": {
                    "type": "string",
                    "title": "Fusion Method",
                    "description": "Method to fuse vector and graph results",
                    "enum": ["reciprocal_rank", "weighted", "simple_merge"],
                    "default": "reciprocal_rank",
                },
                "vector_weight": {
                    "type": "number",
                    "title": "Vector Weight",
                    "description": "Weight for vector search results (0.0-1.0)",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.7,
                },
                "graph_weight": {
                    "type": "number",
                    "title": "Graph Weight",
                    "description": "Weight for graph query results (0.0-1.0)",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.3,
                },
                "top_k": {
                    "type": "integer",
                    "title": "Top K",
                    "description": "Number of final results to return",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 10,
                },
                "vector_search_config": {
                    "type": "object",
                    "title": "Vector Search Config",
                    "description": "Configuration for vector search (results should come from upstream Vector Search node)",
                    "properties": {
                        "enabled": {
                            "type": "boolean",
                            "title": "Enabled",
                            "description": "Enable vector search",
                            "default": True,
                        },
                    },
                    "default": {"enabled": True},
                },
                "graph_query_config": {
                    "type": "object",
                    "title": "Graph Query Config",
                    "description": "Configuration for graph queries (results should come from upstream Knowledge Graph node)",
                    "properties": {
                        "enabled": {
                            "type": "boolean",
                            "title": "Enabled",
                            "description": "Enable graph queries",
                            "default": True,
                        },
                    },
                    "default": {"enabled": True},
                },
            },
            "required": ["query"],
        }

    def estimate_cost(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> float:
        """Estimate cost for hybrid retrieval."""
        # Cost is primarily from upstream nodes (vector search, graph query)
        # This node just fuses results, so minimal cost
        return 0.0


# Register the node
NodeRegistry.register(
    "hybrid_retrieval",
    HybridRetrievalNode,
    HybridRetrievalNode().get_metadata(),
)

