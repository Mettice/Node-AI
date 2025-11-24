"""
Span-level evaluation for observability.

Evaluates individual spans for quality, performance, and cost metrics.
This enables span-level tuning as mentioned in the observability article.
"""

from typing import Any, Dict
from backend.core.observability import Span, SpanType
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SpanEvaluator:
    """
    Evaluates individual spans for quality and performance.
    
    This enables span-level evaluation rather than just end-to-end,
    allowing you to tune each piece separately.
    """
    
    def evaluate_span(self, span: Span) -> Dict[str, Any]:
        """Evaluate a span based on its type."""
        if span.span_type == SpanType.EMBEDDING:
            return self.evaluate_embedding_span(span)
        elif span.span_type == SpanType.VECTOR_SEARCH:
            return self.evaluate_vector_search_span(span)
        elif span.span_type == SpanType.RERANKING:
            return self.evaluate_reranking_span(span)
        elif span.span_type == SpanType.LLM:
            return self.evaluate_llm_span(span)
        elif span.span_type == SpanType.CHUNKING:
            return self.evaluate_chunking_span(span)
        else:
            return self.evaluate_generic_span(span)
    
    def evaluate_embedding_span(self, span: Span) -> Dict[str, Any]:
        """Evaluate embedding span quality and performance."""
        embedding_count = span.metadata.get("embedding_count", 1)
        
        evaluation = {
            "embedding_count": embedding_count,
            "embedding_dimension": span.metadata.get("dimension"),
            "embedding_time_ms": span.duration_ms,
            "embeddings_per_second": embedding_count / (span.duration_ms / 1000) if span.duration_ms > 0 else 0,
            "cost_per_embedding": span.cost / embedding_count if embedding_count > 0 else 0,
            "model": span.model,
            "provider": span.provider,
        }
        
        # Performance thresholds
        if span.duration_ms > 1000:
            evaluation["performance_warning"] = "Embedding took longer than 1s"
        if span.cost / embedding_count > 0.001:
            evaluation["cost_warning"] = "Cost per embedding is high"
        
        return evaluation
    
    def evaluate_vector_search_span(self, span: Span) -> Dict[str, Any]:
        """Evaluate vector search quality and performance."""
        results = span.outputs.get("results", [])
        results_count = len(results)
        
        # Calculate average relevance score
        scores = [r.get("score", 0.0) for r in results if isinstance(r, dict)]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        evaluation = {
            "results_count": results_count,
            "avg_relevance_score": avg_score,
            "min_relevance_score": min(scores) if scores else 0.0,
            "max_relevance_score": max(scores) if scores else 0.0,
            "search_time_ms": span.duration_ms,
            "top_k": span.metadata.get("top_k"),
            "provider": span.provider,
        }
        
        # Quality thresholds
        if avg_score < 0.5:
            evaluation["quality_warning"] = "Low average relevance score"
        if results_count == 0:
            evaluation["quality_warning"] = "No results retrieved"
        if span.duration_ms > 500:
            evaluation["performance_warning"] = "Search took longer than 500ms"
        
        return evaluation
    
    def evaluate_reranking_span(self, span: Span) -> Dict[str, Any]:
        """Evaluate reranking quality and performance."""
        results = span.outputs.get("results", [])
        reranked_count = span.metadata.get("reranked_count", len(results))
        original_count = span.metadata.get("original_count", reranked_count)
        
        # Calculate score improvement
        original_scores = [r.get("original_score", 0.0) for r in results if isinstance(r, dict)]
        rerank_scores = [r.get("rerank_score", 0.0) for r in results if isinstance(r, dict)]
        
        avg_original = sum(original_scores) / len(original_scores) if original_scores else 0.0
        avg_rerank = sum(rerank_scores) / len(rerank_scores) if rerank_scores else 0.0
        score_improvement = avg_rerank - avg_original
        
        evaluation = {
            "original_count": original_count,
            "reranked_count": reranked_count,
            "final_count": len(results),
            "avg_original_score": avg_original,
            "avg_rerank_score": avg_rerank,
            "score_improvement": score_improvement,
            "improvement_pct": (score_improvement / avg_original * 100) if avg_original > 0 else 0,
            "reranking_time_ms": span.duration_ms,
            "method": span.metadata.get("method"),
            "cost": span.cost,
        }
        
        # Quality thresholds
        if score_improvement < 0:
            evaluation["quality_warning"] = "Reranking decreased scores"
        if span.duration_ms > 1000:
            evaluation["performance_warning"] = "Reranking took longer than 1s"
        
        return evaluation
    
    def evaluate_llm_span(self, span: Span) -> Dict[str, Any]:
        """Evaluate LLM response quality and performance."""
        input_tokens = span.tokens.get("input_tokens", 0)
        output_tokens = span.tokens.get("output_tokens", 0)
        total_tokens = span.tokens.get("total_tokens", 0)
        
        # Calculate metrics
        tokens_per_second = total_tokens / (span.duration_ms / 1000) if span.duration_ms > 0 else 0
        cost_per_token = span.cost / total_tokens if total_tokens > 0 else 0
        cost_per_input_token = span.cost / input_tokens if input_tokens > 0 else 0
        cost_per_output_token = span.cost / output_tokens if output_tokens > 0 else 0
        
        evaluation = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost": span.cost,
            "cost_per_token": cost_per_token,
            "cost_per_input_token": cost_per_input_token,
            "cost_per_output_token": cost_per_output_token,
            "latency_ms": span.duration_ms,
            "tokens_per_second": tokens_per_second,
            "model": span.model,
            "provider": span.provider,
            "temperature": span.metadata.get("temperature"),
        }
        
        # Performance thresholds
        if span.duration_ms > 5000:
            evaluation["performance_warning"] = "LLM response took longer than 5s"
        if tokens_per_second < 10:
            evaluation["performance_warning"] = "Low token generation rate"
        if span.cost > 0.01:
            evaluation["cost_warning"] = "High cost per request"
        
        # Check for API limits
        if span.api_limits:
            remaining = span.api_limits.get("remaining", 0)
            if remaining < 100:
                evaluation["api_limit_warning"] = f"Low API limit remaining: {remaining}"
        
        return evaluation
    
    def evaluate_chunking_span(self, span: Span) -> Dict[str, Any]:
        """Evaluate chunking quality and performance."""
        chunks_created = span.metadata.get("chunks_created", 0)
        chunk_size = span.metadata.get("chunk_size", 0)
        chunk_overlap = span.metadata.get("chunk_overlap", 0)
        
        evaluation = {
            "chunks_created": chunks_created,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "overlap_percentage": (chunk_overlap / chunk_size * 100) if chunk_size > 0 else 0,
            "chunking_time_ms": span.duration_ms,
            "chunks_per_second": chunks_created / (span.duration_ms / 1000) if span.duration_ms > 0 else 0,
        }
        
        # Quality thresholds
        if chunk_size < 256:
            evaluation["quality_warning"] = "Chunk size is very small"
        if chunk_size > 2048:
            evaluation["quality_warning"] = "Chunk size is very large"
        if chunk_overlap == 0 and chunk_size >= 512:
            evaluation["quality_warning"] = "No overlap may cause context loss"
        
        return evaluation
    
    def evaluate_generic_span(self, span: Span) -> Dict[str, Any]:
        """Evaluate generic span."""
        return {
            "span_type": span.span_type.value,
            "duration_ms": span.duration_ms,
            "cost": span.cost,
            "status": span.status.value,
            "tokens": span.tokens,
            "model": span.model,
            "provider": span.provider,
        }

