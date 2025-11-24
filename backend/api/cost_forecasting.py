"""
API endpoints for cost forecasting.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from backend.core.cost_forecasting import get_cost_forecaster
from backend.core.user_context import get_user_id_from_request
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Cost Forecasting"])


class CostForecastRequest(BaseModel):
    """Request model for cost forecasting."""
    workflow_id: str = Field(description="Workflow ID to forecast for")
    expected_queries: int = Field(ge=1, description="Expected number of queries")
    days: int = Field(default=30, ge=1, le=365, description="Forecast period in days")


class CostForecastResponse(BaseModel):
    """Response model for cost forecast."""
    workflow_id: str
    expected_queries: int
    forecast_period_days: int
    avg_cost_per_query: float
    forecasted_total_cost: float
    forecasted_daily_cost: float
    forecasted_monthly_cost: float
    confidence: str
    sample_size: int
    message: Optional[str] = None


@router.post("/cost-forecast", response_model=CostForecastResponse)
async def forecast_cost(request: Request, forecast_request: CostForecastRequest):
    """
    Forecast cost for a workflow based on historical data.
    
    Returns cost predictions based on historical execution traces.
    """
    user_id = get_user_id_from_request(request)
    
    try:
        forecaster = get_cost_forecaster()
        forecast = forecaster.forecast_cost(
            workflow_id=forecast_request.workflow_id,
            expected_queries=forecast_request.expected_queries,
            days=forecast_request.days,
            user_id=user_id,
        )
        return CostForecastResponse(**forecast)
    except Exception as e:
        logger.error(f"Failed to forecast cost: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to forecast cost")


@router.get("/cost-forecast/{workflow_id}/trends")
async def get_cost_trends(
    request: Request,
    workflow_id: str,
    days: int = Query(default=30, ge=1, le=365),
):
    """
    Get cost trends for a workflow over time.
    
    Returns daily and weekly cost aggregations.
    """
    user_id = get_user_id_from_request(request)
    
    try:
        forecaster = get_cost_forecaster()
        trends = forecaster.analyze_cost_trends(
            workflow_id=workflow_id,
            days=days,
            user_id=user_id,
        )
        return trends
    except Exception as e:
        logger.error(f"Failed to get cost trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get cost trends")


@router.get("/cost-forecast/{workflow_id}/breakdown")
async def get_cost_breakdown(
    request: Request,
    workflow_id: str,
    days: int = Query(default=30, ge=1, le=365),
):
    """
    Get cost breakdown by span type for a workflow.
    
    Shows which parts of the workflow are most expensive.
    """
    user_id = get_user_id_from_request(request)
    
    try:
        forecaster = get_cost_forecaster()
        breakdown = forecaster.get_cost_breakdown(
            workflow_id=workflow_id,
            days=days,
            user_id=user_id,
        )
        return breakdown
    except Exception as e:
        logger.error(f"Failed to get cost breakdown: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get cost breakdown")

