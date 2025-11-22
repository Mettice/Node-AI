"""
RAG Optimization API endpoints.

This module provides endpoints for:
- Analyzing RAG workflow configurations
- Detecting suboptimal settings (chunk size, overlap, etc.)
- Generating optimization suggestions with expected improvements
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["RAG Optimization"])

# In-memory storage for optimization analyses
_optimization_analyses: Dict[str, Dict] = {}


class OptimizationSuggestion(BaseModel):
    """A single optimization suggestion."""
    node_id: str
    node_type: str
    parameter: str  # e.g., "chunk_size", "overlap"
    current_value: Any
    suggested_value: Any
    expected_improvement: str  # e.g., "+15% accuracy"
    reasoning: str
    confidence: float  # 0.0 to 1.0


class RAGOptimizationAnalysis(BaseModel):
    """Complete RAG optimization analysis."""
    analysis_id: str
    workflow_id: str
    execution_id: Optional[str] = None
    suggestions: List[OptimizationSuggestion]
    current_metrics: Dict[str, Any]  # chunk_size, overlap, etc.
    created_at: str


class OptimizationRequest(BaseModel):
    """Request to analyze and optimize a RAG workflow."""
    workflow: Dict  # The workflow to analyze
    execution_id: Optional[str] = None  # Optional: use execution results for analysis
    evaluation_id: Optional[str] = None  # Optional: use RAG evaluation results


@router.post("/rag-optimize/analyze", response_model=RAGOptimizationAnalysis)
async def analyze_rag_workflow(request: OptimizationRequest) -> RAGOptimizationAnalysis:
    """
    Analyze a RAG workflow and generate optimization suggestions.
    
    This will:
    1. Extract current configuration (chunk size, overlap, etc.)
    2. Analyze against best practices and execution metrics
    3. Generate suggestions with expected improvements
    """
    from backend.core.models import Workflow, Node
    
    analysis_id = str(uuid.uuid4())
    
    # Parse workflow
    try:
        workflow = Workflow(**request.workflow)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid workflow format: {str(e)}"
        )
    
    # Extract current metrics from workflow nodes
    current_metrics = {}
    suggestions = []
    
    # Find chunk node
    chunk_node = None
    for node in workflow.nodes:
        if node.type == "chunk":
            chunk_node = node
            break
    
    if chunk_node:
        chunk_config = chunk_node.data.get("config", {})
        chunk_size = chunk_config.get("chunk_size", 512)
        overlap = chunk_config.get("overlap", 0)
        
        current_metrics["chunk_size"] = chunk_size
        current_metrics["overlap"] = overlap
        
        # Analyze chunk configuration
        chunk_suggestions = _analyze_chunk_config(chunk_node.id, chunk_size, overlap)
        suggestions.extend(chunk_suggestions)
    
    # Find embed node
    embed_node = None
    for node in workflow.nodes:
        if node.type == "embed":
            embed_node = node
            break
    
    if embed_node:
        embed_config = embed_node.data.get("config", {})
        model = embed_config.get("openai_model") or embed_config.get("model", "text-embedding-ada-002")
        
        current_metrics["embedding_model"] = model
        
        # Analyze embedding model
        embed_suggestions = _analyze_embedding_model(embed_node.id, model)
        suggestions.extend(embed_suggestions)
    
    # Find vector search node
    search_node = None
    for node in workflow.nodes:
        if node.type == "vector_search":
            search_node = node
            break
    
    if search_node:
        search_config = search_node.data.get("config", {})
        top_k = search_config.get("top_k", 5)
        
        current_metrics["top_k"] = top_k
        
        # Analyze search configuration
        search_suggestions = _analyze_search_config(search_node.id, top_k)
        suggestions.extend(search_suggestions)
    
    # If we have evaluation results, use them for more accurate suggestions
    if request.evaluation_id:
        try:
            from backend.api.rag_evaluation import _evaluations
            evaluation = _evaluations.get(request.evaluation_id)
            if evaluation:
                # Use evaluation metrics to refine suggestions
                accuracy = evaluation.get("accuracy", 0.0)
                avg_relevance = evaluation.get("average_relevance", 0.0)
                
                # Adjust suggestions based on actual performance
                suggestions = _refine_suggestions_with_metrics(
                    suggestions,
                    accuracy,
                    avg_relevance,
                    current_metrics,
                )
        except Exception as e:
            logger.warning(f"Could not use evaluation results: {e}")
    
    analysis = RAGOptimizationAnalysis(
        analysis_id=analysis_id,
        workflow_id=workflow.id or "unknown",
        execution_id=request.execution_id,
        suggestions=suggestions,
        current_metrics=current_metrics,
        created_at=datetime.now().isoformat(),
    )
    
    _optimization_analyses[analysis_id] = analysis.dict()
    
    logger.info(f"RAG optimization analysis completed: {analysis_id} ({len(suggestions)} suggestions)")
    
    return analysis


@router.get("/rag-optimize/{analysis_id}", response_model=RAGOptimizationAnalysis)
async def get_optimization_analysis(analysis_id: str) -> RAGOptimizationAnalysis:
    """Get optimization analysis results."""
    if analysis_id not in _optimization_analyses:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis not found: {analysis_id}"
        )
    
    return RAGOptimizationAnalysis(**_optimization_analyses[analysis_id])


def _analyze_chunk_config(node_id: str, chunk_size: int, overlap: int) -> List[OptimizationSuggestion]:
    """Analyze chunk node configuration."""
    suggestions = []
    
    # Check chunk size
    if chunk_size < 256:
        suggestions.append(OptimizationSuggestion(
            node_id=node_id,
            node_type="chunk",
            parameter="chunk_size",
            current_value=chunk_size,
            suggested_value=512,
            expected_improvement="+10-15% accuracy",
            reasoning="Chunk size of 256 is too small for most documents. 512 provides better context while maintaining relevance.",
            confidence=0.8,
        ))
    elif chunk_size > 1024:
        suggestions.append(OptimizationSuggestion(
            node_id=node_id,
            node_type="chunk",
            parameter="chunk_size",
            current_value=chunk_size,
            suggested_value=768,
            expected_improvement="+5-10% relevance",
            reasoning="Chunk size over 1024 can reduce search precision. 768 is optimal for most use cases.",
            confidence=0.7,
        ))
    elif chunk_size == 512 and overlap == 0:
        suggestions.append(OptimizationSuggestion(
            node_id=node_id,
            node_type="chunk",
            parameter="overlap",
            current_value=overlap,
            suggested_value=100,
            expected_improvement="+15% accuracy",
            reasoning="Adding 100 token overlap helps maintain context across chunk boundaries, improving answer quality.",
            confidence=0.85,
        ))
    
    # Check overlap
    if overlap == 0 and chunk_size >= 512:
        suggestions.append(OptimizationSuggestion(
            node_id=node_id,
            node_type="chunk",
            parameter="overlap",
            current_value=overlap,
            suggested_value=min(100, chunk_size // 5),
            expected_improvement="+10-15% accuracy",
            reasoning="No overlap can cause context loss at chunk boundaries. 100 tokens (or 20% of chunk size) is recommended.",
            confidence=0.8,
        ))
    elif overlap > chunk_size * 0.3:
        suggestions.append(OptimizationSuggestion(
            node_id=node_id,
            node_type="chunk",
            parameter="overlap",
            current_value=overlap,
            suggested_value=chunk_size // 5,
            expected_improvement="+5% efficiency",
            reasoning="Overlap over 30% of chunk size is excessive and wastes tokens. 20% is optimal.",
            confidence=0.75,
        ))
    
    return suggestions


def _analyze_embedding_model(node_id: str, model: str) -> List[OptimizationSuggestion]:
    """Analyze embedding model configuration."""
    suggestions = []
    
    # Check if using expensive model when cheaper one would work
    if "large" in model.lower() or "ada-002" in model.lower():
        suggestions.append(OptimizationSuggestion(
            node_id=node_id,
            node_type="embed",
            parameter="model",
            current_value=model,
            suggested_value="text-embedding-3-small",
            expected_improvement="60% cost savings with minimal quality loss",
            reasoning="text-embedding-3-small provides similar quality at 60% lower cost for most use cases.",
            confidence=0.9,
        ))
    
    return suggestions


def _analyze_search_config(node_id: str, top_k: int) -> List[OptimizationSuggestion]:
    """Analyze vector search configuration."""
    suggestions = []
    
    if top_k < 3:
        suggestions.append(OptimizationSuggestion(
            node_id=node_id,
            node_type="vector_search",
            parameter="top_k",
            current_value=top_k,
            suggested_value=5,
            expected_improvement="+10% accuracy",
            reasoning="top_k of 3 may miss relevant chunks. 5 provides better coverage while maintaining relevance.",
            confidence=0.75,
        ))
    elif top_k > 10:
        suggestions.append(OptimizationSuggestion(
            node_id=node_id,
            node_type="vector_search",
            parameter="top_k",
            current_value=top_k,
            suggested_value=5,
            expected_improvement="+5% relevance, lower cost",
            reasoning="top_k over 10 can introduce noise and increase LLM costs. 5 is optimal for most queries.",
            confidence=0.7,
        ))
    
    return suggestions


def _refine_suggestions_with_metrics(
    suggestions: List[OptimizationSuggestion],
    accuracy: float,
    avg_relevance: float,
    current_metrics: Dict,
) -> List[OptimizationSuggestion]:
    """Refine suggestions based on actual evaluation metrics."""
    refined = []
    
    for suggestion in suggestions:
        # If accuracy is low, increase confidence for chunk/overlap suggestions
        if accuracy < 0.7 and suggestion.parameter in ["chunk_size", "overlap"]:
            suggestion.confidence = min(1.0, suggestion.confidence + 0.1)
            suggestion.expected_improvement = f"+{int(suggestion.expected_improvement.split('+')[1].split('%')[0]) + 5}% accuracy"
        
        # If relevance is low, prioritize search config suggestions
        if avg_relevance < 0.6 and suggestion.parameter == "top_k":
            suggestion.confidence = min(1.0, suggestion.confidence + 0.15)
        
        refined.append(suggestion)
    
    return refined

