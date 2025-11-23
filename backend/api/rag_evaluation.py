"""
RAG Evaluation API endpoints.

This module provides endpoints for:
- Uploading test Q&A pairs
- Running RAG evaluation
- Getting evaluation results (accuracy, relevance, latency, cost)
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid
import time

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from pydantic import BaseModel

from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["RAG Evaluation"])

# In-memory storage for evaluations (will be replaced with database later)
_evaluations: Dict[str, Dict] = {}
_test_datasets: Dict[str, List[Dict]] = {}


class QAPair(BaseModel):
    """Question-Answer pair for evaluation."""
    question: str
    expected_answer: str
    context: Optional[str] = None  # Optional context/ground truth


class EvaluationRequest(BaseModel):
    """Request to evaluate a RAG workflow."""
    workflow: Dict  # The workflow to evaluate (full workflow object)
    test_dataset_id: str
    max_queries: Optional[int] = None  # Limit number of queries to test
    input_node_id: Optional[str] = None  # Node ID to inject question into (default: first text_input node)
    output_node_id: Optional[str] = None  # Node ID to extract answer from (default: last chat/llm node)


class EvaluationResult(BaseModel):
    """Result of a single Q&A evaluation."""
    question: str
    expected_answer: str
    actual_answer: str
    is_correct: bool
    relevance_score: float  # 0.0 to 1.0
    latency_ms: int
    cost: float
    execution_id: Optional[str] = None
    error: Optional[str] = None


class EvaluationSummary(BaseModel):
    """Summary of evaluation results."""
    evaluation_id: str
    workflow_id: str
    total_queries: int
    correct_answers: int
    accuracy: float  # 0.0 to 1.0
    average_relevance: float
    average_latency_ms: int
    total_cost: float
    cost_per_query: float
    failed_queries: int
    results: List[EvaluationResult]
    created_at: str


@router.post("/rag-eval/dataset")
async def upload_test_dataset(
    file: UploadFile = File(...),
) -> Dict[str, str]:
    """
    Upload a test dataset (JSON or JSONL file with Q&A pairs).
    
    Expected format:
    [
      {"question": "...", "expected_answer": "...", "context": "..."},
      ...
    ]
    or JSONL (one JSON object per line)
    """
    import json
    
    dataset_id = str(uuid.uuid4())
    
    try:
        # Read file content
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Try parsing as JSON first
        try:
            data = json.loads(text_content)
            if isinstance(data, list):
                qa_pairs = data
            else:
                qa_pairs = [data]
        except json.JSONDecodeError:
            # Try JSONL format (one JSON object per line)
            qa_pairs = []
            for line in text_content.strip().split('\n'):
                if line.strip():
                    qa_pairs.append(json.loads(line))
        
        # Validate format
        validated_pairs = []
        for pair in qa_pairs:
            if not isinstance(pair, dict):
                continue
            if 'question' not in pair or 'expected_answer' not in pair:
                continue
            validated_pairs.append({
                "question": pair["question"],
                "expected_answer": pair["expected_answer"],
                "context": pair.get("context"),
            })
        
        if not validated_pairs:
            raise HTTPException(
                status_code=400,
                detail="No valid Q&A pairs found in file. Expected format: [{\"question\": \"...\", \"expected_answer\": \"...\"}]"
            )
        
        # Store dataset
        _test_datasets[dataset_id] = validated_pairs
        
        logger.info(f"Uploaded test dataset: {dataset_id} ({len(validated_pairs)} pairs)")
        
        return {
            "dataset_id": dataset_id,
            "num_pairs": len(validated_pairs),
            "message": "Dataset uploaded successfully",
        }
        
    except Exception as e:
        logger.error(f"Error uploading test dataset: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse test dataset: {str(e)}"
        )


@router.get("/rag-eval/dataset/{dataset_id}")
async def get_test_dataset(dataset_id: str) -> Dict:
    """Get a test dataset."""
    if dataset_id not in _test_datasets:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
    
    return {
        "dataset_id": dataset_id,
        "pairs": _test_datasets[dataset_id],
        "num_pairs": len(_test_datasets[dataset_id]),
    }


@router.post("/rag-eval/evaluate", response_model=EvaluationSummary)
async def evaluate_rag_workflow(request: EvaluationRequest) -> EvaluationSummary:
    """
    Evaluate a RAG workflow with test Q&A pairs.
    
    This will:
    1. Load the test dataset
    2. Execute the workflow for each question
    3. Compare actual vs expected answers
    4. Calculate metrics (accuracy, relevance, latency, cost)
    """
    from backend.core.engine import engine
    from backend.core.models import Workflow, Node
    
    # Get test dataset
    if request.test_dataset_id not in _test_datasets:
        raise HTTPException(
            status_code=404,
            detail=f"Test dataset not found: {request.test_dataset_id}"
        )
    
    test_pairs = _test_datasets[request.test_dataset_id]
    
    # Limit queries if specified
    if request.max_queries:
        test_pairs = test_pairs[:request.max_queries]
    
    evaluation_id = str(uuid.uuid4())
    
    # Parse workflow
    try:
        workflow = Workflow(**request.workflow)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid workflow format: {str(e)}"
        )
    
    # Find input and output nodes
    input_node_id = request.input_node_id
    output_node_id = request.output_node_id
    
    if not input_node_id:
        # Find first text_input node
        for node in workflow.nodes:
            if node.type == "text_input":
                input_node_id = node.id
                break
    
    if not output_node_id:
        # Find last chat/llm node
        for node in reversed(workflow.nodes):
            if node.type in ["chat", "langchain_agent", "crewai_agent"]:
                output_node_id = node.id
                break
    
    if not input_node_id:
        raise HTTPException(
            status_code=400,
            detail="No input node found. Please specify input_node_id or add a text_input node."
        )
    
    if not output_node_id:
        raise HTTPException(
            status_code=400,
            detail="No output node found. Please specify output_node_id or add a chat/llm node."
        )
    
    # Execute workflow for each Q&A pair
    results: List[EvaluationResult] = []
    total_cost = 0.0
    total_latency = 0
    correct_count = 0
    total_relevance = 0.0
    failed_count = 0
    
    for idx, pair in enumerate(test_pairs):
        try:
            # Create a copy of the workflow with the question injected
            workflow_copy = workflow.model_copy(deep=True)
            
            # Inject question into input node
            for node in workflow_copy.nodes:
                if node.id == input_node_id:
                    if node.type == "text_input":
                        node.data["text"] = pair["question"]
                    break
            
            # Execute workflow
            start_time = time.time()
            execution = await engine.execute(workflow_copy, execution_id=f"{evaluation_id}-{idx}")
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Extract answer from output node
            actual_answer = ""
            if output_node_id in execution.results:
                output_result = execution.results[output_node_id]
                if output_result.output:
                    if isinstance(output_result.output, dict):
                        # Try common output fields
                        actual_answer = (
                            output_result.output.get("response") or
                            output_result.output.get("output") or
                            output_result.output.get("text") or
                            str(output_result.output)
                        )
                    else:
                        actual_answer = str(output_result.output)
            
            # Calculate relevance score using embeddings
            relevance_score = await _calculate_relevance(
                pair["expected_answer"],
                actual_answer,
                pair.get("context"),
            )
            
            # Check if answer is correct (simple string similarity for now)
            is_correct = _check_answer_correctness(
                pair["expected_answer"],
                actual_answer,
            )
            
            if is_correct:
                correct_count += 1
            
            total_relevance += relevance_score
            total_cost += execution.total_cost
            total_latency += latency_ms
            
            result = EvaluationResult(
                question=pair["question"],
                expected_answer=pair["expected_answer"],
                actual_answer=actual_answer,
                is_correct=is_correct,
                relevance_score=relevance_score,
                latency_ms=latency_ms,
                cost=execution.total_cost,
                execution_id=execution.id,
            )
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error evaluating Q&A pair {idx}: {e}", exc_info=True)
            failed_count += 1
            result = EvaluationResult(
                question=pair["question"],
                expected_answer=pair["expected_answer"],
                actual_answer="",
                is_correct=False,
                relevance_score=0.0,
                latency_ms=0,
                cost=0.0,
                error=str(e),
            )
            results.append(result)
    
    evaluation = EvaluationSummary(
        evaluation_id=evaluation_id,
        workflow_id=workflow.id or "unknown",
        total_queries=len(test_pairs),
        correct_answers=correct_count,
        accuracy=correct_count / len(test_pairs) if test_pairs else 0.0,
        average_relevance=total_relevance / len(test_pairs) if test_pairs else 0.0,
        average_latency_ms=total_latency // len(test_pairs) if test_pairs else 0,
        total_cost=total_cost,
        cost_per_query=total_cost / len(test_pairs) if test_pairs else 0.0,
        failed_queries=failed_count,
        results=results,
        created_at=datetime.now().isoformat(),
    )
    
    _evaluations[evaluation_id] = evaluation.dict()
    
    logger.info(f"RAG evaluation completed: {evaluation_id} ({correct_count}/{len(test_pairs)} correct)")
    
    return evaluation


@router.get("/rag-eval/{evaluation_id}", response_model=EvaluationSummary)
async def get_evaluation(evaluation_id: str) -> EvaluationSummary:
    """Get evaluation results."""
    if evaluation_id not in _evaluations:
        raise HTTPException(
            status_code=404,
            detail=f"Evaluation not found: {evaluation_id}"
        )
    
    return EvaluationSummary(**_evaluations[evaluation_id])


@router.get("/rag-eval", response_model=List[EvaluationSummary])
async def list_evaluations(
    workflow_id: Optional[str] = None,
) -> List[EvaluationSummary]:
    """List all evaluations, optionally filtered by workflow."""
    evaluations = list(_evaluations.values())
    
    if workflow_id:
        evaluations = [e for e in evaluations if e.get("workflow_id") == workflow_id]
    
    # Sort by created_at (newest first)
    evaluations.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return [EvaluationSummary(**e) for e in evaluations]


class ABTestRequest(BaseModel):
    """Request to run A/B test between two workflow configurations."""
    workflow_a: Dict  # First workflow configuration
    workflow_b: Dict  # Second workflow configuration
    test_dataset_id: str
    max_queries: Optional[int] = None
    input_node_id: Optional[str] = None
    output_node_id: Optional[str] = None
    test_name: Optional[str] = None  # Optional name for the test


class ABTestResult(BaseModel):
    """Result of an A/B test comparison."""
    test_id: str
    test_name: Optional[str]
    workflow_a_id: str
    workflow_b_id: str
    evaluation_a: EvaluationSummary
    evaluation_b: EvaluationSummary
    comparison: Dict[str, Any]  # Differences between A and B
    winner: Optional[str]  # "a", "b", or "tie"
    created_at: str


@router.post("/rag-eval/ab-test", response_model=ABTestResult)
async def run_ab_test(request: ABTestRequest) -> ABTestResult:
    """
    Run an A/B test comparing two workflow configurations.
    
    This will:
    1. Evaluate both workflows with the same test dataset
    2. Compare results (accuracy, relevance, latency, cost)
    3. Determine which configuration performs better
    """
    from backend.core.engine import engine
    from backend.core.models import Workflow
    
    # Evaluate workflow A
    workflow_a = Workflow(**request.workflow_a)
    eval_request_a = EvaluationRequest(
        workflow=request.workflow_a,
        test_dataset_id=request.test_dataset_id,
        max_queries=request.max_queries,
        input_node_id=request.input_node_id,
        output_node_id=request.output_node_id,
    )
    evaluation_a = await evaluate_rag_workflow(eval_request_a)
    
    # Evaluate workflow B
    workflow_b = Workflow(**request.workflow_b)
    eval_request_b = EvaluationRequest(
        workflow=request.workflow_b,
        test_dataset_id=request.test_dataset_id,
        max_queries=request.max_queries,
        input_node_id=request.input_node_id,
        output_node_id=request.output_node_id,
    )
    evaluation_b = await evaluate_rag_workflow(eval_request_b)
    
    # Compare results
    comparison = {
        "accuracy_diff": evaluation_b.accuracy - evaluation_a.accuracy,
        "relevance_diff": evaluation_b.average_relevance - evaluation_a.average_relevance,
        "latency_diff_ms": evaluation_b.average_latency_ms - evaluation_a.average_latency_ms,
        "cost_diff": evaluation_b.cost_per_query - evaluation_a.cost_per_query,
        "cost_diff_pct": ((evaluation_b.cost_per_query - evaluation_a.cost_per_query) / evaluation_a.cost_per_query * 100) if evaluation_a.cost_per_query > 0 else 0,
    }
    
    # Determine winner (weighted scoring: accuracy 40%, relevance 30%, latency 20%, cost 10%)
    score_a = (
        evaluation_a.accuracy * 0.4 +
        evaluation_a.average_relevance * 0.3 +
        (1 - min(evaluation_a.average_latency_ms / 10000, 1)) * 0.2 +  # Normalize latency (10s = 0)
        (1 - min(evaluation_a.cost_per_query / 1.0, 1)) * 0.1  # Normalize cost ($1 = 0)
    )
    score_b = (
        evaluation_b.accuracy * 0.4 +
        evaluation_b.average_relevance * 0.3 +
        (1 - min(evaluation_b.average_latency_ms / 10000, 1)) * 0.2 +
        (1 - min(evaluation_b.cost_per_query / 1.0, 1)) * 0.1
    )
    
    winner = None
    if abs(score_a - score_b) < 0.01:  # Within 1% = tie
        winner = "tie"
    elif score_b > score_a:
        winner = "b"
    else:
        winner = "a"
    
    test_id = str(uuid.uuid4())
    result = ABTestResult(
        test_id=test_id,
        test_name=request.test_name,
        workflow_a_id=workflow_a.id or "a",
        workflow_b_id=workflow_b.id or "b",
        evaluation_a=evaluation_a,
        evaluation_b=evaluation_b,
        comparison=comparison,
        winner=winner,
        created_at=datetime.now().isoformat(),
    )
    
    # Store A/B test result
    if not hasattr(run_ab_test, '_ab_tests'):
        run_ab_test._ab_tests = {}
    run_ab_test._ab_tests[test_id] = result.dict()
    
    logger.info(f"A/B test completed: {test_id} (winner: {winner})")
    return result


@router.get("/rag-eval/ab-tests", response_model=List[ABTestResult])
async def list_ab_tests() -> List[ABTestResult]:
    """List all A/B tests."""
    if not hasattr(run_ab_test, '_ab_tests'):
        return []
    
    tests = list(run_ab_test._ab_tests.values())
    tests.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return [ABTestResult(**t) for t in tests]


@router.get("/rag-eval/quality-trends")
async def get_quality_trends(
    workflow_id: Optional[str] = None,
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
) -> Dict[str, Any]:
    """
    Get quality trends over time for evaluations.
    
    Returns daily averages of accuracy, relevance, latency, and cost.
    """
    from datetime import timedelta
    
    evaluations = list(_evaluations.values())
    
    if workflow_id:
        evaluations = [e for e in evaluations if e.get("workflow_id") == workflow_id]
    
    # Filter by date range
    cutoff_date = datetime.now() - timedelta(days=days)
    filtered_evals = []
    for e in evaluations:
        try:
            eval_date = datetime.fromisoformat(e.get("created_at", "").replace("Z", "+00:00"))
            if eval_date >= cutoff_date:
                filtered_evals.append(e)
        except:
            continue
    
    # Group by day
    daily_data: Dict[str, Dict[str, List[float]]] = {}
    for eval_data in filtered_evals:
        try:
            eval_date = datetime.fromisoformat(eval_data.get("created_at", "").replace("Z", "+00:00"))
            day_key = eval_date.strftime("%Y-%m-%d")
            
            if day_key not in daily_data:
                daily_data[day_key] = {
                    "accuracy": [],
                    "relevance": [],
                    "latency": [],
                    "cost": [],
                }
            
            summary = EvaluationSummary(**eval_data)
            daily_data[day_key]["accuracy"].append(summary.accuracy)
            daily_data[day_key]["relevance"].append(summary.average_relevance)
            daily_data[day_key]["latency"].append(summary.average_latency_ms)
            daily_data[day_key]["cost"].append(summary.cost_per_query)
        except:
            continue
    
    # Calculate daily averages
    trends = []
    for day_key in sorted(daily_data.keys()):
        data = daily_data[day_key]
        trends.append({
            "date": day_key,
            "avg_accuracy": sum(data["accuracy"]) / len(data["accuracy"]) if data["accuracy"] else 0,
            "avg_relevance": sum(data["relevance"]) / len(data["relevance"]) if data["relevance"] else 0,
            "avg_latency_ms": sum(data["latency"]) / len(data["latency"]) if data["latency"] else 0,
            "avg_cost_per_query": sum(data["cost"]) / len(data["cost"]) if data["cost"] else 0,
            "evaluation_count": len(data["accuracy"]),
        })
    
    return {
        "workflow_id": workflow_id,
        "days": days,
        "trends": trends,
    }


async def _calculate_relevance(
    expected: str,
    actual: str,
    context: Optional[str] = None,
) -> float:
    """
    Calculate relevance score between expected and actual answers.
    
    Uses embedding similarity (cosine similarity) if available,
    otherwise falls back to simple text similarity.
    """
    try:
        # Try to use embeddings for better relevance scoring
        from sentence_transformers import SentenceTransformer
        import numpy as np
        
        # Load model (cache it if possible)
        if not hasattr(_calculate_relevance, '_model'):
            _calculate_relevance._model = SentenceTransformer('all-MiniLM-L6-v2')
        
        model = _calculate_relevance._model
        
        # Encode both texts
        embeddings = model.encode([expected, actual])
        
        # Calculate cosine similarity
        similarity = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )
        
        # Normalize to 0-1 range (cosine similarity is already -1 to 1)
        return float((similarity + 1) / 2)
        
    except ImportError:
        # Fallback to simple text similarity if sentence-transformers not available
        logger.warning("sentence-transformers not available, using simple text similarity")
        return _simple_text_similarity(expected, actual)
    except Exception as e:
        logger.warning(f"Error calculating embedding similarity: {e}, using fallback")
        return _simple_text_similarity(expected, actual)


def _simple_text_similarity(text1: str, text2: str) -> float:
    """Simple text similarity based on word overlap."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0


def _check_answer_correctness(expected: str, actual: str) -> bool:
    """
    Check if the actual answer matches the expected answer.
    
    Uses fuzzy matching to handle variations in phrasing.
    """
    # Normalize both strings
    expected_norm = expected.lower().strip()
    actual_norm = actual.lower().strip()
    
    # Exact match
    if expected_norm == actual_norm:
        return True
    
    # Check if expected is contained in actual (for longer answers)
    if expected_norm in actual_norm:
        return True
    
    # Check word overlap (if >80% words match, consider correct)
    words_expected = set(expected_norm.split())
    words_actual = set(actual_norm.split())
    
    if words_expected and words_actual:
        overlap = len(words_expected.intersection(words_actual))
        similarity = overlap / len(words_expected)
        return similarity >= 0.8
    
    return False

