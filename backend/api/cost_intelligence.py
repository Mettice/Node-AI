"""
Cost Intelligence API endpoints.

This module provides endpoints for:
- Analyzing workflow costs
- Suggesting cost optimizations
- Predicting future costs
- Budget management and alerts
- Cost forecasting and trends
- ROI calculations
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Cost Intelligence"])

# In-memory storage for cost analytics (will be replaced with database later)
_cost_history: Dict[str, List[Dict]] = {}
_budgets: Dict[str, Dict[str, Any]] = {}  # workflow_id -> budget config


def _get_cost_data_from_execution(execution_id: str) -> Optional[List[Dict]]:
    """
    Get cost data from execution results if not in history.
    
    Args:
        execution_id: Execution ID to get cost data for
        
    Returns:
        List of cost records or None if not found
    """
    try:
        from backend.api.execution import _executions
        execution = _executions.get(execution_id)
        
        if not execution or not execution.results:
            return None
        
        # Get workflow_id from execution metadata
        workflow_id = execution.workflow_id if hasattr(execution, 'workflow_id') and execution.workflow_id else execution_id
        
        # Convert execution results to cost records format
        execution_data = []
        for node_id, node_result in execution.results.items():
            if node_result.cost > 0:
                output = node_result.output or {}
                node_config = output.get("_node_config", {})
                model = (
                    node_config.get("openai_model") or 
                    node_config.get("anthropic_model") or 
                    node_config.get("model") or
                    node_config.get("base_model")
                )
                provider = node_config.get("provider")
                if not provider and model:
                    model_str = str(model).lower()
                    if "gpt" in model_str or "o1" in model_str or "text-embedding" in model_str:
                        provider = "openai"
                    elif "claude" in model_str:
                        provider = "anthropic"
                
                execution_data.append({
                    "workflow_id": workflow_id,  # Add workflow_id to each record
                    "execution_id": execution_id,
                    "node_id": node_id,
                    "node_type": output.get("_node_type", "unknown"),
                    "cost": node_result.cost,
                    "tokens_used": node_result.tokens_used,
                    "model": model,
                    "provider": provider,
                    "config": node_config,
                    "duration_ms": node_result.duration_ms,
                    "timestamp": node_result.completed_at.isoformat() if node_result.completed_at else None,
                })
        
        # Store in history for future requests
        if execution_data:
            _cost_history[execution_id] = execution_data
        
        return execution_data
    except Exception as e:
        logger.warning(f"Failed to get execution data: {e}")
        return None


class CostBreakdown(BaseModel):
    """Cost breakdown by node type."""
    node_type: str
    node_id: str
    cost: float
    tokens_used: Optional[Dict[str, int]] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    config: Optional[Dict] = None


class CostAnalysis(BaseModel):
    """Cost analysis for a workflow execution."""
    execution_id: str
    total_cost: float
    breakdown: List[CostBreakdown]
    top_cost_nodes: List[CostBreakdown]
    cost_by_category: Dict[str, float]
    cost_by_provider: Dict[str, float]
    cost_by_model: Dict[str, float]
    suggestions: List[Dict[str, Any]]


class CostPrediction(BaseModel):
    """Cost prediction for future runs."""
    estimated_cost_per_run: float
    estimated_cost_100_runs: float
    estimated_cost_1000_runs: float
    confidence: float  # 0.0 to 1.0
    assumptions: List[str]


class CostForecast(BaseModel):
    """Cost forecast with trends."""
    daily_costs: List[Dict[str, Any]]  # [{date, cost, runs}]
    weekly_trend: str  # "increasing", "decreasing", "stable"
    monthly_estimate: float
    projected_monthly_cost: float
    growth_rate: float  # percentage


class BudgetConfig(BaseModel):
    """Budget configuration."""
    workflow_id: str
    monthly_budget: float
    alert_threshold: float = 0.8  # Alert at 80% of budget
    enabled: bool = True


class BudgetStatus(BaseModel):
    """Current budget status."""
    workflow_id: str
    monthly_budget: float
    current_spend: float
    remaining: float
    percentage_used: float
    days_remaining: int
    projected_monthly_spend: float
    status: str  # "ok", "warning", "exceeded"
    alerts: List[str]


class ROICalculation(BaseModel):
    """ROI calculation."""
    workflow_id: str
    total_cost: float
    time_saved_hours: Optional[float] = None
    hourly_rate: Optional[float] = None
    value_generated: Optional[float] = None
    roi_percentage: float
    payback_period_days: Optional[float] = None
    break_even_runs: Optional[int] = None


class OptimizationSuggestion(BaseModel):
    """Cost optimization suggestion."""
    node_id: str
    node_type: str
    current_config: Dict
    suggested_config: Dict
    current_cost: float
    estimated_new_cost: float
    savings_percentage: float
    quality_impact: str  # "minimal", "low", "medium", "high"
    reasoning: str
    priority: str  # "low", "medium", "high"


@router.get("/cost/analyze/{execution_id}", response_model=CostAnalysis)
async def analyze_execution_cost(execution_id: str) -> CostAnalysis:
    """
    Analyze cost for a specific execution.
    
    Args:
        execution_id: Execution ID to analyze
        
    Returns:
        Cost analysis with breakdown and suggestions
    """
    # Try to get cost data from history first
    execution_data = _cost_history.get(execution_id)
    
    # If not in history, try to get from execution results
    if not execution_data:
        execution_data = _get_cost_data_from_execution(execution_id)
    
    if not execution_data:
        raise HTTPException(
            status_code=404,
            detail=f"Execution not found or has no cost data: {execution_id}. Make sure the execution completed successfully."
        )
    
    # Analyze costs
    breakdown = []
    cost_by_category = defaultdict(float)
    cost_by_provider = defaultdict(float)
    cost_by_model = defaultdict(float)
    total_cost = 0.0
    
    for node_cost in execution_data:
        breakdown.append(CostBreakdown(**node_cost))
        total_cost += node_cost["cost"]
        
        # Categorize by node type
        node_type = node_cost.get("node_type", "unknown")
        cost_by_category[node_type] += node_cost["cost"]
        
        # Categorize by provider
        provider = node_cost.get("provider", "unknown")
        cost_by_provider[provider] += node_cost["cost"]
        
        # Categorize by model
        model = node_cost.get("model", "unknown")
        if model:
            cost_by_model[model] += node_cost["cost"]
    
    # Sort by cost (highest first)
    top_cost_nodes = sorted(breakdown, key=lambda x: x.cost, reverse=True)[:5]
    
    # Generate suggestions
    suggestions = _generate_cost_suggestions(breakdown)
    
    return CostAnalysis(
        execution_id=execution_id,
        total_cost=total_cost,
        breakdown=breakdown,
        top_cost_nodes=top_cost_nodes,
        cost_by_category=dict(cost_by_category),
        cost_by_provider=dict(cost_by_provider),
        cost_by_model=dict(cost_by_model),
        suggestions=suggestions,
    )


@router.get("/cost/predict", response_model=CostPrediction)
async def predict_workflow_cost(
    execution_id: Optional[str] = Query(None, description="Use historical execution for prediction"),
    workflow_id: Optional[str] = Query(None, description="Use workflow ID for prediction"),
    num_runs: int = Query(100, description="Number of runs to predict for"),
) -> CostPrediction:
    """
    Predict cost for future workflow runs.
    
    Args:
        execution_id: Use a specific execution as baseline
        workflow_id: Use workflow ID to average historical costs
        num_runs: Number of runs to predict for
        
    Returns:
        Cost prediction with estimates
    """
    # Get baseline cost
    baseline_cost = 0.0
    
    if execution_id:
        # Use specific execution
        execution_data = _cost_history.get(execution_id)
        if execution_data:
            baseline_cost = sum(node.get("cost", 0) for node in execution_data)
    elif workflow_id:
        # Average historical costs for this workflow
        # In production, query database for all executions of this workflow
        matching_executions = [
            data for exec_id, data in _cost_history.items()
            if data and data[0].get("workflow_id") == workflow_id
        ]
        if matching_executions:
            total = sum(
                sum(node.get("cost", 0) for node in exec_data)
                for exec_data in matching_executions
            )
            baseline_cost = total / len(matching_executions)
    
    # If no baseline from history, try to get from execution
    if baseline_cost == 0 and execution_id:
        try:
            from backend.api.execution import _executions
            execution = _executions.get(execution_id)
            if execution and execution.results:
                baseline_cost = sum(node_result.cost for node_result in execution.results.values())
        except Exception as e:
            logger.warning(f"Failed to get execution data for prediction: {e}")
    
    if baseline_cost == 0:
        raise HTTPException(
            status_code=400,
            detail="No historical data available for prediction. Run the workflow first and ensure it completes successfully."
        )
    
    # Predict costs
    estimated_per_run = baseline_cost
    estimated_100 = baseline_cost * 100
    estimated_1000 = baseline_cost * 1000
    
    # Confidence based on data availability
    confidence = 0.7 if execution_id else 0.5
    
    assumptions = [
        "Costs assume similar input sizes and usage patterns",
        "No major changes to node configurations",
        "Provider pricing remains stable",
    ]
    
    return CostPrediction(
        estimated_cost_per_run=round(estimated_per_run, 4),
        estimated_cost_100_runs=round(estimated_100, 2),
        estimated_cost_1000_runs=round(estimated_1000, 2),
        confidence=confidence,
        assumptions=assumptions,
    )


@router.get("/cost/forecast/{workflow_id}", response_model=CostForecast)
async def get_cost_forecast(
    workflow_id: str,
    days: int = Query(30, description="Number of days to forecast")
) -> CostForecast:
    """
    Get cost forecast and trends for a workflow.
    
    Args:
        workflow_id: Workflow ID to forecast for
        days: Number of days to look back for trend analysis
        
    Returns:
        Cost forecast with trends
    """
    # Get historical costs for this workflow
    # In production, query database
    matching_executions = [
        (exec_id, data) for exec_id, data in _cost_history.items()
        if data and data[0].get("workflow_id") == workflow_id
    ]
    
    # If no matching executions, try to get from current execution
    if not matching_executions:
        # Try to find any execution data and check if workflow_id matches
        # This handles cases where workflow_id might be the execution_id
        for exec_id, data in _cost_history.items():
            if data:
                # Check if workflow_id matches execution_id or is in the data
                if workflow_id == exec_id or (data[0].get("workflow_id") == workflow_id):
                    matching_executions.append((exec_id, data))
                    break
    
    # If still no data, return empty forecast instead of 404
    if not matching_executions:
        return CostForecast(
            daily_costs=[],
            weekly_trend="stable",
            monthly_estimate=0.0,
            projected_monthly_cost=0.0,
            growth_rate=0.0,
        )
    
    # Group by date
    daily_costs = defaultdict(lambda: {"cost": 0.0, "runs": 0})
    
    for exec_id, exec_data in matching_executions:
        total_cost = sum(node.get("cost", 0) for node in exec_data)
        # Get date from first node's timestamp
        if exec_data and exec_data[0].get("timestamp"):
            try:
                date_str = exec_data[0]["timestamp"][:10]  # YYYY-MM-DD
                daily_costs[date_str]["cost"] += total_cost
                daily_costs[date_str]["runs"] += 1
            except Exception:
                pass
    
    # Convert to list and sort by date
    daily_list = [
        {"date": date, "cost": data["cost"], "runs": data["runs"]}
        for date, data in sorted(daily_costs.items())
    ]
    
    # Calculate trends
    if len(daily_list) >= 7:
        recent_avg = sum(d["cost"] for d in daily_list[-7:]) / 7
        older_avg = sum(d["cost"] for d in daily_list[-14:-7]) / 7 if len(daily_list) >= 14 else recent_avg
        
        if recent_avg > older_avg * 1.1:
            trend = "increasing"
        elif recent_avg < older_avg * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"
        
        growth_rate = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
    else:
        trend = "stable"
        growth_rate = 0.0
    
    # Project monthly cost
    avg_daily = sum(d["cost"] for d in daily_list) / len(daily_list) if daily_list else 0
    monthly_estimate = avg_daily * 30
    projected_monthly = avg_daily * 30 * (1 + growth_rate / 100)
    
    return CostForecast(
        daily_costs=daily_list[-days:],
        weekly_trend=trend,
        monthly_estimate=round(monthly_estimate, 2),
        projected_monthly_cost=round(projected_monthly, 2),
        growth_rate=round(growth_rate, 1),
    )


@router.post("/cost/budget", response_model=BudgetConfig)
async def set_budget(config: BudgetConfig) -> BudgetConfig:
    """Set budget for a workflow."""
    _budgets[config.workflow_id] = config.dict()
    return config


@router.get("/cost/budget/{workflow_id}", response_model=BudgetStatus)
async def get_budget_status(workflow_id: str) -> BudgetStatus:
    """Get current budget status for a workflow."""
    budget = _budgets.get(workflow_id)
    if not budget:
        # Return default budget status instead of 404
        return BudgetStatus(
            workflow_id=workflow_id,
            monthly_budget=0.0,
            current_spend=0.0,
            remaining=0.0,
            percentage_used=0.0,
            days_remaining=0,
            projected_monthly_spend=0.0,
            status="no_budget",
            alerts=[],
        )
    
    # Calculate current spend (this month)
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    matching_executions = [
        data for exec_id, data in _cost_history.items()
        if data and data[0].get("workflow_id") == workflow_id
    ]
    
    current_spend = 0.0
    for exec_data in matching_executions:
        if exec_data and exec_data[0].get("timestamp"):
            try:
                exec_date = datetime.fromisoformat(exec_data[0]["timestamp"].replace("Z", "+00:00"))
                if exec_date >= month_start:
                    current_spend += sum(node.get("cost", 0) for node in exec_data)
            except Exception:
                pass
    
    monthly_budget = budget["monthly_budget"]
    remaining = monthly_budget - current_spend
    percentage_used = (current_spend / monthly_budget * 100) if monthly_budget > 0 else 0
    
    # Calculate days remaining in month
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)
    days_remaining = (next_month - now).days
    
    # Project monthly spend
    days_elapsed = (now - month_start).days + 1
    if days_elapsed > 0:
        daily_avg = current_spend / days_elapsed
        projected_monthly = daily_avg * 30
    else:
        projected_monthly = 0
    
    # Determine status
    if current_spend >= monthly_budget:
        status = "exceeded"
    elif percentage_used >= budget["alert_threshold"] * 100:
        status = "warning"
    else:
        status = "ok"
    
    # Generate alerts
    alerts = []
    if status == "exceeded":
        alerts.append(f"Budget exceeded! Current spend: ${current_spend:.2f} of ${monthly_budget:.2f}")
    elif status == "warning":
        alerts.append(f"Approaching budget limit: {percentage_used:.1f}% used")
    
    if projected_monthly > monthly_budget * 1.1:
        alerts.append(f"Projected monthly spend (${projected_monthly:.2f}) exceeds budget by {((projected_monthly / monthly_budget - 1) * 100):.1f}%")
    
    return BudgetStatus(
        workflow_id=workflow_id,
        monthly_budget=monthly_budget,
        current_spend=round(current_spend, 2),
        remaining=round(remaining, 2),
        percentage_used=round(percentage_used, 1),
        days_remaining=days_remaining,
        projected_monthly_spend=round(projected_monthly, 2),
        status=status,
        alerts=alerts,
    )


@router.post("/cost/roi", response_model=ROICalculation)
async def calculate_roi(
    workflow_id: str,
    time_saved_hours: Optional[float] = None,
    hourly_rate: Optional[float] = None,
    value_generated: Optional[float] = None,
) -> ROICalculation:
    """
    Calculate ROI for a workflow.
    
    Args:
        workflow_id: Workflow ID
        time_saved_hours: Hours saved per run (optional)
        hourly_rate: Hourly rate for time savings (optional)
        value_generated: Direct value generated (optional)
        
    Returns:
        ROI calculation
    """
    # Get total cost for this workflow
    matching_executions = [
        data for exec_id, data in _cost_history.items()
        if data and data[0].get("workflow_id") == workflow_id
    ]
    
    total_cost = sum(
        sum(node.get("cost", 0) for node in exec_data)
        for exec_data in matching_executions
    )
    
    if total_cost == 0:
        raise HTTPException(
            status_code=400,
            detail="No cost data found for workflow. Run the workflow first."
        )
    
    # Calculate value
    value = 0.0
    if value_generated:
        value = value_generated
    elif time_saved_hours and hourly_rate:
        num_runs = len(matching_executions)
        value = time_saved_hours * hourly_rate * num_runs
    
    # Calculate ROI
    if total_cost > 0:
        roi_percentage = ((value - total_cost) / total_cost) * 100
    else:
        roi_percentage = 0.0
    
    # Calculate payback period
    if time_saved_hours and hourly_rate and total_cost > 0:
        value_per_run = time_saved_hours * hourly_rate
        if value_per_run > 0:
            payback_runs = total_cost / value_per_run
            # Assume 1 run per day for payback period
            payback_days = payback_runs
            break_even_runs = int(payback_runs) + 1
        else:
            payback_days = None
            break_even_runs = None
    else:
        payback_days = None
        break_even_runs = None
    
    return ROICalculation(
        workflow_id=workflow_id,
        total_cost=round(total_cost, 2),
        time_saved_hours=time_saved_hours,
        hourly_rate=hourly_rate,
        value_generated=value_generated,
        roi_percentage=round(roi_percentage, 1),
        payback_period_days=round(payback_days, 1) if payback_days else None,
        break_even_runs=break_even_runs,
    )


@router.get("/cost/optimize/{execution_id}", response_model=List[OptimizationSuggestion])
async def get_cost_optimizations(execution_id: str) -> List[OptimizationSuggestion]:
    """
    Get cost optimization suggestions for an execution.
    
    Args:
        execution_id: Execution ID to analyze
        
    Returns:
        List of optimization suggestions
    """
    # Try to get cost data from history first
    execution_data = _cost_history.get(execution_id)
    
    # If not in history, try to get from execution results
    if not execution_data:
        execution_data = _get_cost_data_from_execution(execution_id)
    
    if not execution_data:
        raise HTTPException(
            status_code=404,
            detail=f"Execution not found or has no cost data: {execution_id}. Make sure the execution completed successfully."
        )
    
    suggestions = []
    
    for node_cost in execution_data:
        node_type = node_cost.get("node_type")
        node_id = node_cost.get("node_id")
        current_cost = node_cost.get("cost", 0)
        config = node_cost.get("config", {})
        model = node_cost.get("model")
        provider = node_cost.get("provider")
        
        # Generate suggestions based on node type
        if node_type == "embed" and provider == "openai":
            suggestion = _suggest_embedding_optimization(
                node_id, node_type, config, model, current_cost
            )
            if suggestion:
                suggestions.append(suggestion)
        
        elif node_type == "chat" and provider == "openai":
            suggestion = _suggest_chat_optimization(
                node_id, node_type, config, model, current_cost
            )
            if suggestion:
                suggestions.append(suggestion)
    
    # Sort by priority (high savings = high priority)
    suggestions.sort(key=lambda x: x.savings_percentage, reverse=True)
    
    return suggestions


@router.post("/cost/record")
async def record_execution_costs(
    execution_id: str,
    workflow_id: str,
    costs: List[Dict],
) -> Dict[str, str]:
    """
    Record costs for an execution (called by engine after execution).
    
    This is an internal endpoint used by the execution engine.
    """
    # Merge with existing costs if any
    if execution_id in _cost_history:
        existing = _cost_history[execution_id]
        # Merge costs by node_id (update if exists, append if new)
        existing_dict = {c.get("node_id"): c for c in existing}
        for cost in costs:
            node_id = cost.get("node_id")
            if node_id:
                existing_dict[node_id] = {
                    **cost,
                    "workflow_id": workflow_id,
                    "recorded_at": datetime.now().isoformat(),
                }
        _cost_history[execution_id] = list(existing_dict.values())
    else:
        _cost_history[execution_id] = [
            {**cost, "workflow_id": workflow_id, "recorded_at": datetime.now().isoformat()}
            for cost in costs
        ]
    
    logger.info(f"Recorded costs for execution: {execution_id} (total nodes: {len(_cost_history[execution_id])})")
    
    return {"message": "Costs recorded", "execution_id": execution_id}


def _generate_cost_suggestions(breakdown: List[CostBreakdown]) -> List[Dict[str, Any]]:
    """Generate cost optimization suggestions."""
    suggestions = []
    
    # Group by node type
    by_type = defaultdict(list)
    for cost in breakdown:
        by_type[cost.node_type].append(cost)
    
    # Check for expensive embedding operations
    if "embed" in by_type:
        embed_costs = by_type["embed"]
        total_embed_cost = sum(c.cost for c in embed_costs)
        
        # Check if using expensive embedding model
        for cost in embed_costs:
            if cost.model and "large" in cost.model.lower():
                suggestions.append({
                    "type": "embedding_model",
                    "node_id": cost.node_id,
                    "message": f"Using {cost.model} for embeddings. Consider switching to text-embedding-3-small to save ~60% with minimal quality loss.",
                    "current_cost": cost.cost,
                    "estimated_savings": cost.cost * 0.6,
                    "impact": "low",
                })
    
    # Check for expensive chat operations
    if "chat" in by_type:
        chat_costs = by_type["chat"]
        for cost in chat_costs:
            if cost.model and "gpt-4" in cost.model.lower() and "turbo" not in cost.model.lower():
                suggestions.append({
                    "type": "chat_model",
                    "node_id": cost.node_id,
                    "message": f"Using {cost.model}. Consider gpt-3.5-turbo for ~90% cost savings on non-critical tasks.",
                    "current_cost": cost.cost,
                    "estimated_savings": cost.cost * 0.9,
                    "impact": "medium",
                })
    
    return suggestions


def _suggest_embedding_optimization(
    node_id: str,
    node_type: str,
    config: Dict,
    model: Optional[str],
    current_cost: float,
) -> Optional[OptimizationSuggestion]:
    """Suggest embedding model optimization."""
    if not model:
        return None
    
    # Check if using expensive model
    if "large" in model.lower():
        return OptimizationSuggestion(
            node_id=node_id,
            node_type=node_type,
            current_config=config,
            suggested_config={**config, "openai_model": "text-embedding-3-small"},
            current_cost=current_cost,
            estimated_new_cost=current_cost * 0.4,  # ~60% savings
            savings_percentage=60.0,
            quality_impact="minimal",
            reasoning="text-embedding-3-small provides similar quality at 60% lower cost for most use cases",
            priority="high" if current_cost > 0.01 else "medium",
        )
    
    return None


def _suggest_chat_optimization(
    node_id: str,
    node_type: str,
    config: Dict,
    model: Optional[str],
    current_cost: float,
) -> Optional[OptimizationSuggestion]:
    """Suggest chat model optimization."""
    if not model:
        return None
    
    # Check if using expensive model
    if "gpt-4" in model.lower() and "turbo" not in model.lower():
        return OptimizationSuggestion(
            node_id=node_id,
            node_type=node_type,
            current_config=config,
            suggested_config={**config, "openai_model": "gpt-3.5-turbo"},
            current_cost=current_cost,
            estimated_new_cost=current_cost * 0.1,  # ~90% savings
            savings_percentage=90.0,
            quality_impact="medium",
            reasoning="gpt-3.5-turbo is suitable for most tasks and costs ~90% less than GPT-4",
            priority="high" if current_cost > 0.1 else "medium",
        )
    
    return None
