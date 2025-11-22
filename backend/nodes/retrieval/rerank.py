"""
Reranking Node for NodeAI.

This node reranks search results to improve relevance before sending to LLM.
Supports multiple reranking methods: Cohere, Cross-Encoder, and LLM-based.
"""

from typing import Any, Dict, List, Optional
from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.nodes.base import BaseNode
from backend.utils.logger import get_logger
from backend.utils.model_pricing import (
    calculate_reranking_cost_from_query_and_docs,
    get_model_pricing,
)

logger = get_logger(__name__)


class RerankNode(BaseNode):
    """
    Reranking Node.
    
    Reranks search results to improve relevance and reduce noise.
    Critical for production RAG pipelines to improve quality and reduce costs.
    """

    node_type = "rerank"
    name = "Rerank"
    description = "Rerank search results by relevance to improve quality and reduce LLM costs."
    category = "retrieval"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the reranking node.
        
        Reranks search results using the specified method.
        """
        node_id = config.get("_node_id", "rerank")
        
        await self.stream_progress(node_id, 0.1, "Preparing reranking...")
        
        # Get inputs - Vector Search outputs results in a "results" field
        search_results = inputs.get("results") or []
        query = inputs.get("query") or inputs.get("text") or ""
        
        # Also check if results is nested (e.g., from Vector Search output)
        if not search_results and isinstance(inputs.get("results"), dict):
            search_results = inputs.get("results", {}).get("results", [])
        
        if not search_results:
            raise ValueError("No search results provided. Connect a Vector Search node first.")
        
        if not query:
            raise ValueError("No query provided. Query is required for reranking.")
        
        if not isinstance(search_results, list):
            raise ValueError(f"Search results must be a list, got {type(search_results)}")
        
        await self.stream_progress(node_id, 0.2, f"Reranking {len(search_results)} results...")
        
        # Get configuration
        method = config.get("method", "cohere")
        top_n = config.get("top_n", 3)
        min_score = config.get("min_score", 0.0)
        model = config.get("model", "rerank-english-v3.0")
        
        # Normalize search results format
        # Vector Search outputs: [{"text": "...", "score": 0.9, "metadata": {...}}, ...]
        # Handle both formats: list of dicts with 'text' or 'content', or list of strings
        normalized_results = []
        for i, result in enumerate(search_results):
            if isinstance(result, str):
                normalized_results.append({
                    "text": result,
                    "metadata": {},
                    "score": 0.0,
                    "index": i,
                })
            elif isinstance(result, dict):
                # Try multiple possible text fields
                text = (
                    result.get("text") or 
                    result.get("content") or 
                    result.get("chunk") or 
                    result.get("document") or
                    ""
                )
                if not text and "metadata" in result:
                    # Sometimes text is in metadata
                    text = result.get("metadata", {}).get("text") or result.get("metadata", {}).get("content") or ""
                
                if not text:
                    logger.warning(f"Result at index {i} has no text field, skipping")
                    continue
                    
                normalized_results.append({
                    "text": text,
                    "metadata": result.get("metadata", {}),
                    "score": result.get("score", result.get("similarity", 0.0)),
                    "index": i,
                })
            else:
                logger.warning(f"Skipping invalid result at index {i}: {type(result)}")
        
        if not normalized_results:
            raise ValueError("No valid search results to rerank.")
        
        await self.stream_progress(node_id, 0.3, f"Using {method} reranking method...")
        
        # Rerank based on method
        if method == "cohere":
            reranked = await self._rerank_cohere(normalized_results, query, model, node_id)
        elif method == "voyage_ai" or method == "voyageai":
            voyage_model = config.get("voyage_model", "rerank-2.5")
            reranked = await self._rerank_voyage_ai(normalized_results, query, voyage_model, node_id)
        elif method == "cross_encoder":
            reranked = await self._rerank_cross_encoder(normalized_results, query, node_id)
        elif method == "llm":
            reranked = await self._rerank_llm(normalized_results, query, config, node_id)
        else:
            raise ValueError(f"Unknown reranking method: {method}")
        
        await self.stream_progress(node_id, 0.8, f"Reranked {len(reranked)} results")
        
        # Filter by min_score and take top_n
        filtered = [r for r in reranked if r["rerank_score"] >= min_score]
        top_results = filtered[:top_n]
        
        await self.stream_progress(node_id, 0.9, f"Selected top {len(top_results)} results")
        
        # Calculate cost
        cost = self._estimate_cost(len(normalized_results), method, config)
        
        await self.stream_progress(node_id, 1.0, "Reranking complete")
        
        return {
            "results": top_results,
            "reranked_count": len(reranked),
            "filtered_count": len(filtered),
            "top_n": len(top_results),
            "query": query,
            "method": method,
            "cost": cost,
            "metadata": {
                "original_count": len(search_results),
                "reranked_count": len(reranked),
                "filtered_count": len(filtered),
                "final_count": len(top_results),
                "method": method,
                "model": (
                    model if method == "cohere" 
                    else config.get("voyage_model") if method in ["voyage_ai", "voyageai"]
                    else None
                ),
            },
        }
    
    async def _rerank_cohere(
        self,
        results: List[Dict[str, Any]],
        query: str,
        model: str,
        node_id: str,
    ) -> List[Dict[str, Any]]:
        """Rerank using Cohere API."""
        try:
            import cohere
        except ImportError:
            raise ImportError(
                "Cohere reranking requires the cohere package. Install with: pip install cohere"
            )
        
        # Get API key from environment
        import os
        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            raise ValueError(
                "COHERE_API_KEY environment variable not set. "
                "Get your API key from https://dashboard.cohere.com/api-keys"
            )
        
        await self.stream_progress(node_id, 0.4, "Connecting to Cohere API...")
        
        client = cohere.Client(api_key)
        
        # Extract texts for reranking
        texts = [r["text"] for r in results]
        
        await self.stream_progress(node_id, 0.5, "Sending to Cohere for reranking...")
        
        try:
            response = client.rerank(
                model=model,
                query=query,
                documents=texts,
                top_n=len(texts),  # Get all reranked
            )
            
            # Map results back with rerank scores
            reranked = []
            for result in response.results:
                original_idx = result.index
                original_result = results[original_idx].copy()
                original_result["rerank_score"] = result.relevance_score
                original_result["rerank_rank"] = result.index
                reranked.append(original_result)
            
            # Sort by rerank score (descending)
            reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
            
            await self.stream_progress(node_id, 0.7, "Cohere reranking complete")
            
            return reranked
            
        except Exception as e:
            logger.error(f"Cohere reranking failed: {e}")
            raise ValueError(f"Cohere reranking failed: {str(e)}")
    
    async def _rerank_cross_encoder(
        self,
        results: List[Dict[str, Any]],
        query: str,
        node_id: str,
    ) -> List[Dict[str, Any]]:
        """Rerank using local Cross-Encoder model."""
        try:
            from sentence_transformers import CrossEncoder
        except ImportError:
            raise ImportError(
                "Cross-Encoder reranking requires sentence-transformers. "
                "Install with: pip install sentence-transformers"
            )
        
        await self.stream_progress(node_id, 0.4, "Loading Cross-Encoder model...")
        
        # Use a good cross-encoder model for reranking
        model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
        model = CrossEncoder(model_name)
        
        await self.stream_progress(node_id, 0.5, "Computing relevance scores...")
        
        # Prepare pairs for scoring
        pairs = [[query, r["text"]] for r in results]
        
        # Get scores (this is synchronous, but we're in async context)
        scores = model.predict(pairs)
        
        await self.stream_progress(node_id, 0.6, "Sorting by relevance...")
        
        # Add scores and sort
        reranked = []
        for i, result in enumerate(results):
            result_copy = result.copy()
            result_copy["rerank_score"] = float(scores[i])
            result_copy["rerank_rank"] = i
            reranked.append(result_copy)
        
        # Sort by score (descending)
        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        
        await self.stream_progress(node_id, 0.7, "Cross-Encoder reranking complete")
        
        return reranked
    
    async def _rerank_llm(
        self,
        results: List[Dict[str, Any]],
        query: str,
        config: Dict[str, Any],
        node_id: str,
    ) -> List[Dict[str, Any]]:
        """Rerank using LLM-based relevance scoring."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("LLM reranking requires openai package. Install with: pip install openai")
        
        await self.stream_progress(node_id, 0.4, "Preparing LLM reranking...")
        
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        client = OpenAI(api_key=api_key)
        model = config.get("llm_model", "gpt-4o-mini")
        
        await self.stream_progress(node_id, 0.5, "Scoring results with LLM...")
        
        # Create prompt for LLM to score relevance
        results_text = "\n\n".join([
            f"[{i+1}] {r['text'][:500]}"  # Truncate for token efficiency
            for i, r in enumerate(results)
        ])
        
        prompt = f"""You are a relevance scorer. Given a query and search results, score each result from 0.0 to 1.0 based on relevance.

Query: {query}

Results:
{results_text}

Return ONLY a JSON array of scores, one per result, in order. Example: [0.9, 0.3, 0.7, 0.1, ...]
"""
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a relevance scorer. Return only JSON arrays of scores."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=500,
            )
            
            # Parse scores
            import json
            scores_text = response.choices[0].message.content.strip()
            # Remove markdown code blocks if present
            if scores_text.startswith("```"):
                scores_text = scores_text.split("```")[1]
                if scores_text.startswith("json"):
                    scores_text = scores_text[4:]
            scores_text = scores_text.strip()
            
            scores = json.loads(scores_text)
            
            if len(scores) != len(results):
                logger.warning(f"LLM returned {len(scores)} scores for {len(results)} results. Using first {len(scores)}")
                scores = scores[:len(results)]
            
            # Add scores and sort
            reranked = []
            for i, result in enumerate(results):
                result_copy = result.copy()
                result_copy["rerank_score"] = float(scores[i]) if i < len(scores) else 0.0
                result_copy["rerank_rank"] = i
                reranked.append(result_copy)
            
            # Sort by score (descending)
            reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
            
            await self.stream_progress(node_id, 0.7, "LLM reranking complete")
            
            return reranked
            
        except Exception as e:
            logger.error(f"LLM reranking failed: {e}")
            raise ValueError(f"LLM reranking failed: {str(e)}")
    
    async def _rerank_voyage_ai(
        self,
        results: List[Dict[str, Any]],
        query: str,
        model: str,
        node_id: str,
    ) -> List[Dict[str, Any]]:
        """Rerank using Voyage AI API."""
        try:
            import voyageai
        except ImportError:
            raise ImportError(
                "Voyage AI reranking requires the voyageai package. Install with: pip install voyageai"
            )
        
        # Get API key from environment
        import os
        api_key = os.getenv("VOYAGE_API_KEY")
        if not api_key:
            raise ValueError(
                "VOYAGE_API_KEY environment variable not set. "
                "Get your API key from https://www.voyageai.com/"
            )
        
        await self.stream_progress(node_id, 0.4, "Connecting to Voyage AI API...")
        
        client = voyageai.Client(api_key=api_key)
        
        # Extract texts for reranking
        texts = [r["text"] for r in results]
        
        await self.stream_progress(node_id, 0.5, f"Sending {len(texts)} documents to Voyage AI for reranking...")
        
        try:
            response = client.rerank(
                query=query,
                documents=texts,
                model=model,
                top_k=len(texts),  # Get all reranked
            )
            
            # Map results back with rerank scores
            reranked = []
            for result in response.results:
                original_idx = result.index
                original_result = results[original_idx].copy()
                original_result["rerank_score"] = result.relevance_score
                original_result["rerank_rank"] = result.index
                reranked.append(original_result)
            
            # Sort by rerank score (descending)
            reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
            
            await self.stream_progress(node_id, 0.7, "Voyage AI reranking complete")
            
            return reranked
            
        except Exception as e:
            logger.error(f"Voyage AI reranking failed: {e}")
            raise ValueError(f"Voyage AI reranking failed: {str(e)}")

    def _estimate_cost(self, num_results: int, method: str, config: Dict[str, Any]) -> float:
        """Estimate cost for reranking operation using centralized pricing."""
        if method == "voyage_ai" or method == "voyageai":
            # Use centralized pricing system
            voyage_model = config.get("voyage_model", "rerank-2.5")
            # For reranking: 1 unit = 1 query + 1 document
            # We estimate query as 1 unit, so total = 1 + num_results
            return calculate_reranking_cost_from_query_and_docs(
                "voyage_ai", voyage_model, "", num_results
            )
        elif method == "cohere":
            # Use centralized pricing for Cohere
            cohere_model = config.get("model", "rerank-english-v3.0")
            # For reranking: 1 unit = 1 query + 1 document
            return calculate_reranking_cost_from_query_and_docs(
                "cohere", cohere_model, "", num_results
            )
        elif method == "cross_encoder":
            # Local model - no API cost
            return 0.0
        elif method == "llm":
            # Estimate based on tokens
            # Rough estimate: ~50 tokens per result for scoring
            model = config.get("llm_model", "gpt-4o-mini")
            tokens = 100 + (num_results * 50)  # Base prompt + per result
            
            # Pricing (approximate)
            if "gpt-4o-mini" in model.lower():
                cost = (tokens / 1000000) * 0.15  # $0.15 per 1M input tokens
            elif "gpt-4" in model.lower():
                cost = (tokens / 1000000) * 30.0  # $30 per 1M input tokens
            else:
                cost = (tokens / 1000000) * 0.15  # Default to mini pricing
            
            return round(cost, 6)
        return 0.0
    
    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for reranking configuration."""
        return {
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "title": "Reranking Method",
                    "description": "Method to use for reranking",
                    "enum": ["cohere", "voyage_ai", "cross_encoder", "llm"],
                    "default": "cohere",
                },
                "top_n": {
                    "type": "integer",
                    "title": "Top N Results",
                    "description": "Number of top results to keep after reranking",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 50,
                },
                "min_score": {
                    "type": "number",
                    "title": "Minimum Relevance Score",
                    "description": "Minimum rerank score to include (0.0 to 1.0)",
                    "default": 0.0,
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
                "model": {
                    "type": "string",
                    "title": "Cohere Model (Cohere only)",
                    "description": "Cohere rerank model to use",
                    "enum": [
                        "rerank-v3.5",
                        "rerank-english-v3.0",
                        "rerank-multilingual-v3.0",
                    ],
                    "default": "rerank-english-v3.0",
                },
                "llm_model": {
                    "type": "string",
                    "title": "LLM Model (LLM method only)",
                    "description": "OpenAI model to use for LLM-based reranking",
                    "default": "gpt-4o-mini",
                },
                # Voyage AI config
                "voyage_model": {
                    "type": "string",
                    "title": "Voyage AI Model (Voyage AI method only)",
                    "description": "Voyage AI rerank model to use",
                    "enum": [
                        "rerank-2.5-lite",
                        "rerank-2-lite",
                        "rerank-lite-1",
                        "rerank-2.5",
                        "rerank-2",
                        "rerank-1",
                    ],
                    "default": "rerank-2.5",
                },
            },
            "required": ["method"],
        }
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Return schema for node inputs."""
        return {
            "results": {
                "type": "array",
                "description": "Search results from Vector Search node",
            },
            "query": {
                "type": "string",
                "description": "Original search query",
            },
        }
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for node outputs."""
        return {
            "results": {
                "type": "array",
                "description": "Reranked and filtered search results",
            },
            "reranked_count": {
                "type": "integer",
                "description": "Number of results after reranking",
            },
            "filtered_count": {
                "type": "integer",
                "description": "Number of results after filtering by min_score",
            },
            "top_n": {
                "type": "integer",
                "description": "Number of final results returned",
            },
            "query": {
                "type": "string",
                "description": "Original query used for reranking",
            },
            "method": {
                "type": "string",
                "description": "Reranking method used",
            },
            "cost": {
                "type": "number",
                "description": "Estimated cost of reranking operation",
            },
            "metadata": {
                "type": "object",
                "description": "Reranking metadata and statistics",
            },
        }


# Register the node
NodeRegistry.register(
    RerankNode.node_type,
    RerankNode,
    RerankNode().get_metadata(),
)

