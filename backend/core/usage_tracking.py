"""
Usage Tracking for API Keys

Tracks requests, costs, and rate limiting per API key.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import json
from collections import defaultdict

from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Storage for usage tracking
USAGE_DIR = Path("backend/data/api_usage")
USAGE_DIR.mkdir(parents=True, exist_ok=True)


class UsageRecord:
    """A single usage record for an API key."""
    
    def __init__(
        self,
        key_id: str,
        timestamp: datetime,
        workflow_id: str,
        execution_id: str,
        cost: float,
        duration_ms: int,
        status: str,
    ):
        self.key_id = key_id
        self.timestamp = timestamp
        self.workflow_id = workflow_id
        self.execution_id = execution_id
        self.cost = cost
        self.duration_ms = duration_ms
        self.status = status
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "key_id": self.key_id,
            "timestamp": self.timestamp.isoformat(),
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "cost": self.cost,
            "duration_ms": self.duration_ms,
            "status": self.status,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "UsageRecord":
        """Create from dictionary."""
        return cls(
            key_id=data["key_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            workflow_id=data["workflow_id"],
            execution_id=data["execution_id"],
            cost=data["cost"],
            duration_ms=data["duration_ms"],
            status=data["status"],
        )


def record_usage(
    key_id: str,
    workflow_id: str,
    execution_id: str,
    cost: float,
    duration_ms: int,
    status: str = "completed",
) -> None:
    """Record a usage event for an API key."""
    record = UsageRecord(
        key_id=key_id,
        timestamp=datetime.now(),
        workflow_id=workflow_id,
        execution_id=execution_id,
        cost=cost,
        duration_ms=duration_ms,
        status=status,
    )
    
    # Append to daily log file
    today = datetime.now().date()
    log_file = USAGE_DIR / f"{key_id}_{today.isoformat()}.jsonl"
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict()) + "\n")
    except Exception as e:
        logger.error(f"Error recording usage for key {key_id}: {e}")


def get_usage_stats(
    key_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict:
    """
    Get usage statistics for an API key.
    
    Returns:
        Dictionary with total_requests, total_cost, requests_today, cost_today
    """
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)  # Last 30 days
    if not end_date:
        end_date = datetime.now()
    
    total_requests = 0
    total_cost = 0.0
    requests_today = 0
    cost_today = 0.0
    last_used_at = None
    
    today = datetime.now().date()
    start_date_only = start_date.date()
    end_date_only = end_date.date()
    
    # Iterate through date range
    current_date = start_date_only
    while current_date <= end_date_only:
        log_file = USAGE_DIR / f"{key_id}_{current_date.isoformat()}.jsonl"
        
        if log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        record_data = json.loads(line)
                        record = UsageRecord.from_dict(record_data)
                        
                        # Check if within time range
                        if start_date <= record.timestamp <= end_date:
                            total_requests += 1
                            total_cost += record.cost
                            
                            # Check if today
                            if record.timestamp.date() == today:
                                requests_today += 1
                                cost_today += record.cost
                            
                            # Track last used
                            if not last_used_at or record.timestamp > last_used_at:
                                last_used_at = record.timestamp
            except Exception as e:
                logger.error(f"Error reading usage log {log_file}: {e}")
        
        # Move to next day
        current_date += timedelta(days=1)
    
    return {
        "total_requests": total_requests,
        "total_cost": total_cost,
        "requests_today": requests_today,
        "cost_today": cost_today,
        "last_used_at": last_used_at.isoformat() if last_used_at else None,
    }


def check_rate_limit(key_id: str, rate_limit: Optional[int]) -> tuple[bool, Optional[str]]:
    """
    Check if API key has exceeded rate limit.
    
    Args:
        key_id: The API key ID
        rate_limit: Rate limit (requests per hour), None for no limit
        
    Returns:
        Tuple of (allowed, error_message)
    """
    if not rate_limit:
        return True, None
    
    # Count requests in the last hour
    one_hour_ago = datetime.now() - timedelta(hours=1)
    stats = get_usage_stats(key_id, start_date=one_hour_ago)
    
    requests_last_hour = stats["total_requests"]
    
    if requests_last_hour >= rate_limit:
        return False, f"Rate limit exceeded: {rate_limit} requests per hour"
    
    return True, None


def check_cost_limit(key_id: str, cost_limit: Optional[float]) -> tuple[bool, Optional[str]]:
    """
    Check if API key has exceeded cost limit.
    
    Args:
        key_id: The API key ID
        cost_limit: Cost limit (dollars per month), None for no limit
        
    Returns:
        Tuple of (allowed, error_message)
    """
    if not cost_limit:
        return True, None
    
    # Get cost for current month
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    stats = get_usage_stats(key_id, start_date=month_start)
    
    cost_this_month = stats["total_cost"]
    
    if cost_this_month >= cost_limit:
        return False, f"Cost limit exceeded: ${cost_limit:.2f} per month"
    
    return True, None

