"""
Prompt Playground API endpoints.

This module provides endpoints for:
- Testing prompts without full workflow execution
- Prompt versioning and A/B testing
- Comparing prompt outputs side-by-side
- Exporting best prompts to workflows
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from backend.core.security import limiter
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Prompt Playground"])

# In-memory storage (will be replaced with database later)
_prompt_tests: Dict[str, Dict] = {}
_prompt_versions: Dict[str, List[Dict]] = {}


class PromptTestRequest(BaseModel):
    """Request to test a prompt."""
    prompt: str
    provider: str = "openai"  # openai, anthropic, etc.
    model: str = "gpt-3.5-turbo"
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    test_inputs: Optional[List[str]] = None  # Multiple test inputs for batch testing


class PromptTestResult(BaseModel):
    """Result of a prompt test."""
    test_id: str
    prompt: str
    provider: str
    model: str
    input_text: str
    output: str
    tokens_used: Dict[str, int]
    cost: float
    latency_ms: int
    created_at: str


class PromptVersion(BaseModel):
    """A versioned prompt."""
    version_id: str
    prompt: str
    system_prompt: Optional[str] = None
    provider: str
    model: str
    temperature: float
    max_tokens: Optional[int] = None
    test_results: List[PromptTestResult]
    average_cost: float
    average_latency_ms: int
    created_at: str
    notes: Optional[str] = None


class ABTestRequest(BaseModel):
    """Request to run A/B test between two prompts."""
    prompt_a: str
    prompt_b: str
    provider: str = "openai"
    model: str = "gpt-3.5-turbo"
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    test_inputs: List[str]  # Same inputs for both prompts


class ABTestResult(BaseModel):
    """Result of A/B test."""
    test_id: str
    prompt_a_result: PromptTestResult
    prompt_b_result: PromptTestResult
    winner: Optional[str] = None  # "a", "b", or None (tie)
    comparison_metrics: Dict[str, Any]
    created_at: str


@router.post("/prompt/test", response_model=PromptTestResult)
@limiter.limit("20/minute")
async def test_prompt(request_body: PromptTestRequest, request: Request) -> PromptTestResult:
    """
    Test a prompt with a single or multiple inputs.
    
    Returns the result for the first input (or single input).
    For batch testing, use the batch endpoint.
    """
    import time
    import os
    
    test_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Use first test input or empty string
    test_input = request_body.test_inputs[0] if request_body.test_inputs and len(request_body.test_inputs) > 0 else ""
    
    try:
        # Execute prompt based on provider
        if request_body.provider == "openai":
            output, tokens, cost = await _test_openai_prompt(
                request_body.prompt,
                test_input,
                request_body.model,
                request_body.system_prompt,
                request_body.temperature,
                request_body.max_tokens,
            )
        elif request_body.provider == "anthropic":
            output, tokens, cost = await _test_anthropic_prompt(
                request_body.prompt,
                test_input,
                request_body.model,
                request_body.system_prompt,
                request_body.temperature,
                request_body.max_tokens,
            )
        elif request_body.provider == "gemini" or request_body.provider == "google":
            output, tokens, cost = await _test_gemini_prompt(
                request_body.prompt,
                test_input,
                request_body.model,
                request_body.system_prompt,
                request_body.temperature,
                request_body.max_tokens,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported provider: {request_body.provider}"
            )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        result = PromptTestResult(
            test_id=test_id,
            prompt=request_body.prompt,
            provider=request_body.provider,
            model=request_body.model,
            input_text=test_input,
            output=output,
            tokens_used=tokens,
            cost=cost,
            latency_ms=latency_ms,
            created_at=datetime.now().isoformat(),
        )
        
        _prompt_tests[test_id] = result.dict()
        
        return result
        
    except Exception as e:
        logger.error(f"Error testing prompt: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to test prompt: {str(e)}"
        )


@router.post("/prompt/test/batch", response_model=List[PromptTestResult])
@limiter.limit("10/minute")
async def test_prompt_batch(request_body: PromptTestRequest, request: Request) -> List[PromptTestResult]:
    """Test a prompt with multiple inputs."""
    results = []
    
    if not request_body.test_inputs or len(request_body.test_inputs) == 0:
        raise HTTPException(
            status_code=400,
            detail="test_inputs is required for batch testing"
        )
    
    for test_input in request_body.test_inputs:
        # Create individual request
        single_request = PromptTestRequest(
            prompt=request_body.prompt,
            provider=request_body.provider,
            model=request_body.model,
            system_prompt=request_body.system_prompt,
            temperature=request_body.temperature,
            max_tokens=request_body.max_tokens,
            test_inputs=[test_input],
        )
        
        result = await test_prompt(single_request, request)
        results.append(result)
    
    return results


@router.post("/prompt/ab-test", response_model=ABTestResult)
@limiter.limit("10/minute")
async def ab_test_prompts(request_body: ABTestRequest, request: Request) -> ABTestResult:
    """Run A/B test between two prompts."""
    test_id = str(uuid.uuid4())
    
    # Test both prompts with all inputs
    results_a = []
    results_b = []
    
    for test_input in request_body.test_inputs:
        # Test prompt A
        request_a = PromptTestRequest(
            prompt=request_body.prompt_a,
            provider=request_body.provider,
            model=request_body.model,
            system_prompt=request_body.system_prompt,
            temperature=request_body.temperature,
            max_tokens=request_body.max_tokens,
            test_inputs=[test_input],
        )
        result_a = await test_prompt(request_a, request)
        results_a.append(result_a)
        
        # Test prompt B
        request_b = PromptTestRequest(
            prompt=request_body.prompt_b,
            provider=request_body.provider,
            model=request_body.model,
            system_prompt=request_body.system_prompt,
            temperature=request_body.temperature,
            max_tokens=request_body.max_tokens,
            test_inputs=[test_input],
        )
        result_b = await test_prompt(request_b, request)
        results_b.append(result_b)
    
    # Use first results for comparison
    prompt_a_result = results_a[0]
    prompt_b_result = results_b[0]
    
    # Calculate comparison metrics
    avg_cost_a = sum(r.cost for r in results_a) / len(results_a)
    avg_cost_b = sum(r.cost for r in results_b) / len(results_b)
    avg_latency_a = sum(r.latency_ms for r in results_a) / len(results_a)
    avg_latency_b = sum(r.latency_ms for r in results_b) / len(results_b)
    
    # Determine winner (lower cost + lower latency wins, or user preference)
    winner = None
    if avg_cost_a < avg_cost_b and avg_latency_a <= avg_latency_b:
        winner = "a"
    elif avg_cost_b < avg_cost_a and avg_latency_b <= avg_latency_a:
        winner = "b"
    # Could add quality metrics here (e.g., output length, coherence)
    
    comparison_metrics = {
        "avg_cost_a": avg_cost_a,
        "avg_cost_b": avg_cost_b,
        "avg_latency_a": avg_latency_a,
        "avg_latency_b": avg_latency_b,
        "cost_savings": abs(avg_cost_a - avg_cost_b),
        "latency_diff": abs(avg_latency_a - avg_latency_b),
    }
    
    result = ABTestResult(
        test_id=test_id,
        prompt_a_result=prompt_a_result,
        prompt_b_result=prompt_b_result,
        winner=winner,
        comparison_metrics=comparison_metrics,
        created_at=datetime.now().isoformat(),
    )
    
    return result


class PromptVersionRequest(BaseModel):
    """Request to create a prompt version."""
    prompt: str
    provider: str
    model: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    notes: Optional[str] = None


@router.post("/prompt/version")
@limiter.limit("20/minute")
async def create_prompt_version(request_body: PromptVersionRequest, request: Request) -> Dict[str, str]:
    """Create a new prompt version."""
    version_id = str(uuid.uuid4())
    
    version = PromptVersion(
        version_id=version_id,
        prompt=request_body.prompt,
        system_prompt=request_body.system_prompt,
        provider=request_body.provider,
        model=request_body.model,
        temperature=request_body.temperature,
        max_tokens=request_body.max_tokens,
        test_results=[],
        average_cost=0.0,
        average_latency_ms=0,
        created_at=datetime.now().isoformat(),
        notes=request_body.notes,
    )
    
    # Store by prompt hash or key (simplified: store by version_id)
    if "default" not in _prompt_versions:
        _prompt_versions["default"] = []
    _prompt_versions["default"].append(version.dict())
    
    return {
        "version_id": version_id,
        "message": "Prompt version created",
    }


@router.get("/prompt/versions", response_model=List[PromptVersion])
@limiter.limit("30/minute")
async def list_prompt_versions(request: Request) -> List[PromptVersion]:
    """List all prompt versions."""
    versions = _prompt_versions.get("default", [])
    return [PromptVersion(**v) for v in versions]


@router.get("/prompt/test/{test_id}", response_model=PromptTestResult)
@limiter.limit("30/minute")
async def get_prompt_test(test_id: str, request: Request) -> PromptTestResult:
    """Get a specific prompt test result."""
    if test_id not in _prompt_tests:
        raise HTTPException(status_code=404, detail=f"Test not found: {test_id}")
    
    return PromptTestResult(**_prompt_tests[test_id])


async def _test_openai_prompt(
    prompt: str,
    input_text: str,
    model: str,
    system_prompt: Optional[str],
    temperature: float,
    max_tokens: Optional[int],
) -> Tuple[str, Dict[str, int], float]:
    """Test a prompt using OpenAI."""
    import openai
    import os
    from backend.config import settings
    
    api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "openai_api_key", None)
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    
    client = openai.OpenAI(api_key=api_key)
    
    # Format prompt with input
    formatted_prompt = prompt.format(input=input_text) if "{input}" in prompt else f"{prompt}\n\n{input_text}"
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": formatted_prompt})
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    output = response.choices[0].message.content or ""
    tokens = {
        "input": response.usage.prompt_tokens,
        "output": response.usage.completion_tokens,
        "total": response.usage.total_tokens,
    }
    
    # Calculate cost using centralized pricing
    cost = _calculate_openai_cost(model, tokens["input"], tokens["output"])
    
    return output, tokens, cost


async def _test_anthropic_prompt(
    prompt: str,
    input_text: str,
    model: str,
    system_prompt: Optional[str],
    temperature: float,
    max_tokens: Optional[int],
) -> Tuple[str, Dict[str, int], float]:
    """Test a prompt using Anthropic."""
    import anthropic
    import os
    from backend.config import settings
    
    api_key = os.getenv("ANTHROPIC_API_KEY") or getattr(settings, "anthropic_api_key", None)
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    # Format prompt with input
    formatted_prompt = prompt.format(input=input_text) if "{input}" in prompt else f"{prompt}\n\n{input_text}"
    
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens or 1024,
        temperature=temperature,
        system=system_prompt or "",
        messages=[
            {"role": "user", "content": formatted_prompt}
        ],
    )
    
    output = message.content[0].text if message.content else ""
    tokens = {
        "input": message.usage.input_tokens,
        "output": message.usage.output_tokens,
        "total": message.usage.input_tokens + message.usage.output_tokens,
    }
    
    # Calculate cost using centralized pricing
    cost = _calculate_anthropic_cost(model, tokens["input"], tokens["output"])
    
    return output, tokens, cost


async def _test_gemini_prompt(
    prompt: str,
    input_text: str,
    model: str,
    system_prompt: Optional[str],
    temperature: float,
    max_tokens: Optional[int],
) -> Tuple[str, Dict[str, int], float]:
    """Test a prompt using Google Gemini."""
    try:
        from google import genai
    except ImportError:
        raise ValueError("google-genai not installed. Install with: pip install google-genai")
    
    import os
    from backend.config import settings
    
    api_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "gemini_api_key", None)
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    
    client = genai.Client(api_key=api_key)
    
    # Format prompt with input
    formatted_prompt = prompt.format(input=input_text) if "{input}" in prompt else f"{prompt}\n\n{input_text}"
    
    # Build messages
    messages = []
    if system_prompt:
        messages.append({"role": "user", "parts": [{"text": system_prompt}]})
    messages.append({"role": "user", "parts": [{"text": formatted_prompt}]})
    
    response = client.models.generate_content(
        model=model,
        contents=messages,
        config={
            "temperature": temperature,
            "max_output_tokens": max_tokens or 1024,
        },
    )
    
    output = response.text if hasattr(response, 'text') else str(response)
    
    # Estimate token usage (Gemini API doesn't always return usage)
    estimated_input_tokens = len(formatted_prompt) // 4
    estimated_output_tokens = len(output) // 4
    
    tokens = {
        "input": estimated_input_tokens,
        "output": estimated_output_tokens,
        "total": estimated_input_tokens + estimated_output_tokens,
    }
    
    # Calculate cost using centralized pricing
    from backend.utils.model_pricing import calculate_llm_cost
    cost = calculate_llm_cost("gemini", model, tokens["input"], tokens["output"])
    
    return output, tokens, cost


def _calculate_openai_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate OpenAI API cost using centralized pricing."""
    from backend.utils.model_pricing import calculate_llm_cost
    return calculate_llm_cost("openai", model, input_tokens, output_tokens)


def _calculate_anthropic_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate Anthropic API cost using centralized pricing."""
    from backend.utils.model_pricing import calculate_llm_cost
    return calculate_llm_cost("anthropic", model, input_tokens, output_tokens)

