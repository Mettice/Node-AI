"""
Cost forecasting based on historical trace data.

Provides cost prediction and analysis based on historical workflow execution data.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from backend.core.observability import get_observability_manager
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CostForecaster:
    """Forecast costs based on trace history."""
    
    def forecast_cost(
        self,
        workflow_id: str,
        expected_queries: int,
        days: int = 30,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Forecast cost for expected queries over a time period.
        
        Args:
            workflow_id: Workflow ID to forecast for
            expected_queries: Expected number of queries
            days: Number of days to forecast for
            user_id: Optional user ID to filter traces
            
        Returns:
            Forecast dictionary with predictions and confidence
        """
        # Get historical traces
        traces = self._get_historical_traces(workflow_id, user_id=user_id)
        
        if not traces:
            return {
                "workflow_id": workflow_id,
                "expected_queries": expected_queries,
                "forecast_period_days": days,
                "avg_cost_per_query": 0.0,
                "forecasted_total_cost": 0.0,
                "forecasted_daily_cost": 0.0,
                "forecasted_monthly_cost": 0.0,
                "confidence": "none",
                "sample_size": 0,
                "message": "No historical data available",
            }
        
        # Calculate statistics
        costs = [trace.get("total_cost", 0.0) for trace in traces if trace.get("total_cost")]
        
        if not costs:
            return {
                "workflow_id": workflow_id,
                "expected_queries": expected_queries,
                "forecast_period_days": days,
                "avg_cost_per_query": 0.0,
                "forecasted_total_cost": 0.0,
                "forecasted_daily_cost": 0.0,
                "forecasted_monthly_cost": 0.0,
                "confidence": "none",
                "sample_size": len(traces),
                "message": "No cost data in historical traces",
            }
        
        avg_cost = statistics.mean(costs)
        median_cost = statistics.median(costs)
        min_cost = min(costs)
        max_cost = max(costs)
        std_dev = statistics.stdev(costs) if len(costs) > 1 else 0.0
        
        # Calculate forecasts
        forecasted_total = avg_cost * expected_queries
        forecasted_daily = forecasted_total / days if days > 0 else 0.0
        forecasted_monthly = forecasted_daily * 30
        
        # Determine confidence based on sample size and variance
        confidence = self._calculate_confidence(len(costs), std_dev, avg_cost)
        
        # Calculate percentiles for range estimates
        sorted_costs = sorted(costs)
        p25 = sorted_costs[len(sorted_costs) // 4] if len(sorted_costs) >= 4 else median_cost
        p75 = sorted_costs[3 * len(sorted_costs) // 4] if len(sorted_costs) >= 4 else median_cost
        
        return {
            "workflow_id": workflow_id,
            "expected_queries": expected_queries,
            "forecast_period_days": days,
            "avg_cost_per_query": avg_cost,
            "median_cost_per_query": median_cost,
            "min_cost_per_query": min_cost,
            "max_cost_per_query": max_cost,
            "std_dev": std_dev,
            "forecasted_total_cost": forecasted_total,
            "forecasted_daily_cost": forecasted_daily,
            "forecasted_monthly_cost": forecasted_monthly,
            "forecast_range": {
                "p25": p25 * expected_queries,
                "p50": median_cost * expected_queries,
                "p75": p75 * expected_queries,
            },
            "confidence": confidence,
            "sample_size": len(costs),
            "historical_data": {
                "total_traces": len(traces),
                "date_range": {
                    "oldest": min(t.get("started_at") for t in traces if t.get("started_at")),
                    "newest": max(t.get("started_at") for t in traces if t.get("started_at")),
                },
            },
        }
    
    def analyze_cost_trends(
        self,
        workflow_id: str,
        days: int = 30,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze cost trends over time.
        
        Args:
            workflow_id: Workflow ID to analyze
            days: Number of days to look back
            user_id: Optional user ID to filter traces
            
        Returns:
            Trend analysis with daily/weekly aggregations
        """
        traces = self._get_historical_traces(workflow_id, days=days, user_id=user_id)
        
        if not traces:
            return {
                "workflow_id": workflow_id,
                "period_days": days,
                "daily_costs": [],
                "weekly_costs": [],
                "trend": "insufficient_data",
                "message": "No historical data available",
            }
        
        # Group by date
        daily_costs: Dict[str, List[float]] = defaultdict(list)
        for trace in traces:
            if trace.get("started_at") and trace.get("total_cost"):
                date_str = trace["started_at"][:10]  # YYYY-MM-DD
                daily_costs[date_str].append(trace["total_cost"])
        
        # Calculate daily averages
        daily_avg = {
            date: statistics.mean(costs) if costs else 0.0
            for date, costs in daily_costs.items()
        }
        
        # Calculate weekly averages
        weekly_costs: Dict[str, List[float]] = defaultdict(list)
        for date, cost in daily_avg.items():
            date_obj = datetime.fromisoformat(date)
            week_start = date_obj - timedelta(days=date_obj.weekday())
            week_key = week_start.strftime("%Y-%W")
            weekly_costs[week_key].append(cost)
        
        weekly_avg = {
            week: statistics.mean(costs) if costs else 0.0
            for week, costs in weekly_costs.items()
        }
        
        # Determine trend
        if len(daily_avg) >= 7:
            recent_days = sorted(daily_avg.items())[-7:]
            older_days = sorted(daily_avg.items())[-14:-7] if len(daily_avg) >= 14 else []
            
            if older_days:
                recent_avg = statistics.mean([c for _, c in recent_days])
                older_avg = statistics.mean([c for _, c in older_days])
                
                if recent_avg > older_avg * 1.1:
                    trend = "increasing"
                elif recent_avg < older_avg * 0.9:
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "workflow_id": workflow_id,
            "period_days": days,
            "daily_costs": [
                {"date": date, "avg_cost": cost, "query_count": len(daily_costs[date])}
                for date, cost in sorted(daily_avg.items())
            ],
            "weekly_costs": [
                {"week": week, "avg_cost": cost}
                for week, cost in sorted(weekly_avg.items())
            ],
            "trend": trend,
            "total_queries": len(traces),
            "total_cost": sum(t.get("total_cost", 0.0) for t in traces),
        }
    
    def get_cost_breakdown(
        self,
        workflow_id: str,
        days: int = 30,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get cost breakdown by span type.
        
        Args:
            workflow_id: Workflow ID
            days: Number of days to look back
            user_id: Optional user ID to filter traces
            
        Returns:
            Cost breakdown by span type
        """
        traces = self._get_historical_traces(workflow_id, days=days, user_id=user_id)
        
        if not traces:
            return {
                "workflow_id": workflow_id,
                "period_days": days,
                "breakdown": {},
                "total_cost": 0.0,
            }
        
        # Aggregate costs by span type
        span_costs: Dict[str, List[float]] = defaultdict(list)
        total_cost = 0.0
        
        for trace in traces:
            total_cost += trace.get("total_cost", 0.0)
            spans = trace.get("spans", [])
            for span in spans:
                span_type = span.get("span_type", "unknown")
                cost = span.get("cost", 0.0)
                if cost > 0:
                    span_costs[span_type].append(cost)
        
        # Calculate statistics per span type
        breakdown = {}
        for span_type, costs in span_costs.items():
            breakdown[span_type] = {
                "total_cost": sum(costs),
                "avg_cost": statistics.mean(costs),
                "count": len(costs),
                "percentage": (sum(costs) / total_cost * 100) if total_cost > 0 else 0.0,
            }
        
        return {
            "workflow_id": workflow_id,
            "period_days": days,
            "breakdown": breakdown,
            "total_cost": total_cost,
            "total_queries": len(traces),
        }
    
    def _get_historical_traces(
        self,
        workflow_id: str,
        days: int = 90,
        user_id: Optional[str] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Get historical traces for a workflow."""
        try:
            manager = get_observability_manager()
            traces = manager.list_traces(workflow_id=workflow_id, limit=limit)
            
            # Filter by date if specified
            if days > 0:
                cutoff_date = datetime.now() - timedelta(days=days)
                traces = [
                    t for t in traces
                    if t.get("started_at") and datetime.fromisoformat(t["started_at"]) >= cutoff_date
                ]
            
            return traces
        except Exception as e:
            logger.warning(f"Failed to get historical traces: {e}")
            return []
    
    def _calculate_confidence(
        self,
        sample_size: int,
        std_dev: float,
        avg_cost: float,
    ) -> str:
        """Calculate confidence level based on sample size and variance."""
        if sample_size < 10:
            return "low"
        elif sample_size < 50:
            return "medium"
        elif sample_size < 100:
            # Check coefficient of variation
            cv = (std_dev / avg_cost) if avg_cost > 0 else float('inf')
            if cv > 0.5:
                return "medium"
            return "high"
        else:
            cv = (std_dev / avg_cost) if avg_cost > 0 else float('inf')
            if cv > 0.3:
                return "medium"
            return "high"


# Global forecaster instance
_forecaster = CostForecaster()


def get_cost_forecaster() -> CostForecaster:
    """Get the global cost forecaster."""
    return _forecaster

