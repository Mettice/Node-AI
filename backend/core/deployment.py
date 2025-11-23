"""
Deployment versioning and management for workflows.

Handles:
- Deployment version tracking
- Rollback to previous deployments
- Deployment health checks
- Deployment analytics
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class DeploymentStatus(str, Enum):
    """Deployment status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class DeploymentVersion(BaseModel):
    """A version of a deployed workflow."""
    id: str = Field(description="Deployment version ID")
    workflow_id: str = Field(description="Workflow ID")
    version_number: int = Field(description="Version number (1, 2, 3, ...)")
    deployed_at: datetime = Field(description="Deployment timestamp")
    
    # Workflow snapshot at deployment time
    workflow_snapshot: Dict[str, Any] = Field(description="Full workflow JSON at deployment")
    
    # Deployment metadata
    status: DeploymentStatus = Field(default=DeploymentStatus.ACTIVE, description="Deployment status")
    deployed_by: Optional[str] = Field(default=None, description="User who deployed")
    description: Optional[str] = Field(default=None, description="Deployment description/notes")
    
    # Health metrics
    total_queries: int = Field(default=0, description="Total queries handled")
    successful_queries: int = Field(default=0, description="Successful queries")
    failed_queries: int = Field(default=0, description="Failed queries")
    avg_response_time_ms: Optional[float] = Field(default=None, description="Average response time")
    total_cost: float = Field(default=0.0, description="Total cost incurred")
    
    # Rollback info
    rolled_back_at: Optional[datetime] = Field(default=None, description="Rollback timestamp")
    rolled_back_to_version: Optional[int] = Field(default=None, description="Version rolled back to")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "version_number": self.version_number,
            "deployed_at": self.deployed_at.isoformat(),
            "workflow_snapshot": self.workflow_snapshot,
            "status": self.status.value,
            "deployed_by": self.deployed_by,
            "description": self.description,
            "total_queries": self.total_queries,
            "successful_queries": self.successful_queries,
            "failed_queries": self.failed_queries,
            "avg_response_time_ms": self.avg_response_time_ms,
            "total_cost": self.total_cost,
            "rolled_back_at": self.rolled_back_at.isoformat() if self.rolled_back_at else None,
            "rolled_back_to_version": self.rolled_back_to_version,
        }


# In-memory storage for deployment versions
# In production, this should be stored in a database
_deployment_versions: Dict[str, List[DeploymentVersion]] = {}  # workflow_id -> list of versions
_active_deployments: Dict[str, int] = {}  # workflow_id -> active version number


class DeploymentManager:
    """Manages workflow deployments and versions."""
    
    @staticmethod
    def create_deployment_version(
        workflow_id: str,
        workflow_snapshot: Dict[str, Any],
        deployed_by: Optional[str] = None,
        description: Optional[str] = None,
    ) -> DeploymentVersion:
        """Create a new deployment version."""
        # Get current versions for this workflow
        versions = _deployment_versions.get(workflow_id, [])
        
        # Determine next version number
        if versions:
            next_version = max(v.version_number for v in versions) + 1
        else:
            next_version = 1
        
        # Deactivate previous active deployment
        if workflow_id in _active_deployments:
            prev_version_num = _active_deployments[workflow_id]
            for v in versions:
                if v.version_number == prev_version_num and v.status == DeploymentStatus.ACTIVE:
                    v.status = DeploymentStatus.INACTIVE
        
        # Create new deployment version
        deployment = DeploymentVersion(
            id=f"{workflow_id}-v{next_version}",
            workflow_id=workflow_id,
            version_number=next_version,
            deployed_at=datetime.now(),
            workflow_snapshot=workflow_snapshot,
            status=DeploymentStatus.ACTIVE,
            deployed_by=deployed_by,
            description=description,
        )
        
        # Store version
        if workflow_id not in _deployment_versions:
            _deployment_versions[workflow_id] = []
        _deployment_versions[workflow_id].append(deployment)
        _active_deployments[workflow_id] = next_version
        
        logger.info(f"Created deployment version {next_version} for workflow {workflow_id}")
        return deployment
    
    @staticmethod
    def get_active_deployment(workflow_id: str) -> Optional[DeploymentVersion]:
        """Get the currently active deployment for a workflow."""
        if workflow_id not in _active_deployments:
            return None
        
        version_num = _active_deployments[workflow_id]
        versions = _deployment_versions.get(workflow_id, [])
        
        return next((v for v in versions if v.version_number == version_num), None)
    
    @staticmethod
    def list_deployment_versions(workflow_id: str) -> List[DeploymentVersion]:
        """List all deployment versions for a workflow."""
        return _deployment_versions.get(workflow_id, [])
    
    @staticmethod
    def get_deployment_version(workflow_id: str, version_number: int) -> Optional[DeploymentVersion]:
        """Get a specific deployment version."""
        versions = _deployment_versions.get(workflow_id, [])
        return next((v for v in versions if v.version_number == version_number), None)
    
    @staticmethod
    def rollback_to_version(workflow_id: str, version_number: int) -> Optional[DeploymentVersion]:
        """Rollback to a previous deployment version."""
        target_version = DeploymentManager.get_deployment_version(workflow_id, version_number)
        if not target_version:
            logger.warning(f"Version {version_number} not found for workflow {workflow_id}")
            return None
        
        if target_version.status == DeploymentStatus.FAILED:
            logger.warning(f"Cannot rollback to failed version {version_number}")
            return None
        
        # Deactivate current active deployment
        active = DeploymentManager.get_active_deployment(workflow_id)
        if active:
            active.status = DeploymentStatus.ROLLED_BACK
            active.rolled_back_at = datetime.now()
            active.rolled_back_to_version = version_number
        
        # Activate target version
        target_version.status = DeploymentStatus.ACTIVE
        _active_deployments[workflow_id] = version_number
        
        logger.info(f"Rolled back workflow {workflow_id} to version {version_number}")
        return target_version
    
    @staticmethod
    def record_query_metrics(
        workflow_id: str,
        success: bool,
        response_time_ms: float,
        cost: float = 0.0,
    ):
        """Record query metrics for the active deployment."""
        active = DeploymentManager.get_active_deployment(workflow_id)
        if not active:
            return
        
        active.total_queries += 1
        if success:
            active.successful_queries += 1
        else:
            active.failed_queries += 1
        
        active.total_cost += cost
        
        # Update average response time
        if active.avg_response_time_ms is None:
            active.avg_response_time_ms = response_time_ms
        else:
            # Running average
            active.avg_response_time_ms = (
                (active.avg_response_time_ms * (active.total_queries - 1) + response_time_ms)
                / active.total_queries
            )
    
    @staticmethod
    def get_deployment_health(workflow_id: str) -> Dict[str, Any]:
        """Get health metrics for the active deployment."""
        active = DeploymentManager.get_active_deployment(workflow_id)
        if not active:
            return {
                "status": "not_deployed",
                "healthy": False,
            }
        
        # Calculate health metrics
        success_rate = (
            (active.successful_queries / active.total_queries * 100)
            if active.total_queries > 0
            else 100.0
        )
        
        # Determine health status
        healthy = (
            active.status == DeploymentStatus.ACTIVE
            and success_rate >= 95.0  # 95%+ success rate
            and (active.avg_response_time_ms is None or active.avg_response_time_ms < 5000)  # < 5s avg
        )
        
        return {
            "status": active.status.value,
            "healthy": healthy,
            "version_number": active.version_number,
            "deployed_at": active.deployed_at.isoformat(),
            "total_queries": active.total_queries,
            "successful_queries": active.successful_queries,
            "failed_queries": active.failed_queries,
            "success_rate": round(success_rate, 2),
            "avg_response_time_ms": active.avg_response_time_ms,
            "total_cost": active.total_cost,
        }

