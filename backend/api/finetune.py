"""
Fine-tuning job management API endpoints.

This module provides REST API endpoints for managing fine-tuning jobs,
checking status, and retrieving model information.
"""

import os
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Fine-Tuning"])

# In-memory storage for fine-tuning jobs (will be replaced with database later)
_finetune_jobs: Dict[str, Dict] = {}


class FineTuneJobStatus(BaseModel):
    """Fine-tuning job status response."""
    job_id: str
    status: str  # validating_training_file, queued, running, succeeded, failed, cancelled
    progress: Optional[float] = None  # 0.0 to 1.0
    model_id: Optional[str] = None  # Available when status is "succeeded"
    error: Optional[str] = None
    training_file_id: Optional[str] = None
    validation_file_id: Optional[str] = None
    created_at: str
    updated_at: str
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    training_examples: Optional[int] = None
    validation_examples: Optional[int] = None
    epochs: Optional[int] = None
    base_model: Optional[str] = None
    provider: Optional[str] = None


@router.get("/finetune/{job_id}/status", response_model=FineTuneJobStatus)
async def get_finetune_status(job_id: str) -> FineTuneJobStatus:
    """
    Get status of a fine-tuning job.
    
    Args:
        job_id: Fine-tuning job ID
        
    Returns:
        Job status with progress and metadata
        
    Raises:
        HTTPException: If job not found
    """
    # Check if we have cached job info
    if job_id in _finetune_jobs:
        job_info = _finetune_jobs[job_id]
        provider = job_info.get("provider", "openai")
        
        # Check status from provider API
        if provider == "openai":
            status = await _check_openai_job_status(job_id)
            # Update cache
            _finetune_jobs[job_id].update(status)
            job_info = _finetune_jobs[job_id]
        else:
            # Return cached status
            status = job_info
    else:
        # Try to check from OpenAI directly (job might exist but not in cache)
        try:
            status = await _check_openai_job_status(job_id)
            # Cache it
            _finetune_jobs[job_id] = status
            job_info = status
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Fine-tuning job not found: {job_id}. Error: {str(e)}"
            )
    
    return FineTuneJobStatus(**job_info)


@router.get("/finetune/jobs", response_model=List[FineTuneJobStatus])
async def list_finetune_jobs(
    status: Optional[str] = None,
    provider: Optional[str] = None,
) -> List[FineTuneJobStatus]:
    """
    List all fine-tuning jobs.
    
    Args:
        status: Filter by status (optional)
        provider: Filter by provider (optional)
        
    Returns:
        List of job statuses
    """
    jobs = list(_finetune_jobs.values())
    
    # Apply filters
    if status:
        jobs = [j for j in jobs if j.get("status") == status]
    if provider:
        jobs = [j for j in jobs if j.get("provider") == provider]
    
    # Sort by created_at (newest first)
    jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return [FineTuneJobStatus(**job) for job in jobs]


@router.post("/finetune/{job_id}/register")
async def register_finetune_job(job_id: str, job_data: Dict) -> Dict:
    """
    Register a fine-tuning job (called by FineTuneNode after starting job).
    
    This is an internal endpoint used by the FineTuneNode to register
    jobs for status tracking.
    """
    _finetune_jobs[job_id] = {
        **job_data,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    
    logger.info(f"Registered fine-tuning job: {job_id}")
    
    return {"job_id": job_id, "status": "registered"}


async def _check_openai_job_status(job_id: str) -> Dict:
    """Check fine-tuning job status from OpenAI API."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ValueError("OpenAI package not installed")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    
    client = OpenAI(api_key=api_key)
    
    try:
        job = client.fine_tuning.jobs.retrieve(job_id)
        
        # Calculate progress based on status
        progress = None
        if job.status == "validating_training_file":
            progress = 0.1
        elif job.status == "queued":
            progress = 0.2
        elif job.status == "running":
            # Estimate progress (OpenAI doesn't provide exact progress)
            # Use a rough estimate based on time elapsed
            if hasattr(job, "created_at") and job.created_at:
                # OpenAI returns timestamp as integer
                created_timestamp = job.created_at
                if isinstance(created_timestamp, int):
                    created = datetime.fromtimestamp(created_timestamp)
                else:
                    # Try parsing as ISO string
                    created = datetime.fromisoformat(str(created_timestamp).replace('Z', '+00:00'))
                elapsed = (datetime.now() - created.replace(tzinfo=None)).total_seconds()
                # Assume average training time is 1 hour
                estimated_duration = 3600
                progress = min(0.2 + (elapsed / estimated_duration) * 0.7, 0.9)
            else:
                progress = 0.5  # Default estimate
        elif job.status == "succeeded":
            progress = 1.0
        elif job.status == "failed":
            progress = None
        elif job.status == "cancelled":
            progress = None
        
        # Get model ID if succeeded
        model_id = None
        if job.status == "succeeded" and hasattr(job, "fine_tuned_model") and job.fine_tuned_model:
            model_id = job.fine_tuned_model
            
        # Get error if failed
        error = None
        if job.status == "failed" and hasattr(job, "error"):
            error_obj = job.error
            if error_obj:
                error = getattr(error_obj, "message", str(error_obj))
        
        # Get file IDs
        training_file_id = getattr(job, "training_file", None)
        validation_file_id = getattr(job, "validation_file", None)
        
        result = {
            "job_id": job_id,
            "status": job.status,
            "progress": progress,
            "model_id": model_id,
            "error": error,
            "training_file_id": training_file_id,
            "validation_file_id": validation_file_id,
            "updated_at": datetime.now().isoformat(),
            "provider": "openai",
        }
        
        # Auto-register model in registry when training completes
        if model_id and job.status == "succeeded":
            try:
                # Get job data from cache for registration
                if job_id in _finetune_jobs:
                    job_data = _finetune_jobs[job_id]
                    await _auto_register_model(job_id, model_id, job_data)
            except Exception as e:
                logger.warning(f"Failed to auto-register model: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error checking OpenAI job status: {e}")
        raise ValueError(f"Failed to check job status: {str(e)}")


async def _auto_register_model(job_id: str, model_id: str, job_data: Dict) -> None:
    """Auto-register a completed fine-tuned model in the registry."""
    try:
        import httpx
        import os
        
        # Get job details from cache (use job_info if provided, otherwise fetch from cache)
        if job_id not in _finetune_jobs and not job_info:
            return  # Can't register without job details
        
        job_data = job_info if job_info else _finetune_jobs[job_id]
        
        # Create model name from base model and timestamp
        base_model = job_data.get("base_model", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d")
        model_name = f"{base_model} Fine-Tuned ({timestamp})"
        
        # Register model
        api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
        url = f"{api_base}/api/v1/models"
        
        create_request = {
            "job_id": job_id,
            "model_id": model_id,
            "name": model_name,
            "description": f"Fine-tuned {base_model} model",
            "base_model": base_model,
            "provider": job_data.get("provider", "openai"),
            "training_examples": job_data.get("training_examples", 0),
            "validation_examples": job_data.get("validation_examples", 0),
            "epochs": job_data.get("epochs", 3),
            "training_file_id": job_data.get("training_file_id"),
            "validation_file_id": job_data.get("validation_file_id"),
            "estimated_cost": job_data.get("estimated_cost"),
            "actual_cost": job_data.get("actual_cost"),
            "metadata": job_data.get("metadata", {}),
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(url, json=create_request, timeout=5.0)
        
        logger.info(f"Auto-registered model: {model_id}")
        
    except Exception as e:
        # Non-critical, just log
        logger.debug(f"Could not auto-register model (this is OK): {e}")

