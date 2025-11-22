"""
Model Registry API endpoints.

This module provides REST API endpoints for managing fine-tuned models:
- List models
- Get model details
- Update model metadata
- Delete models
- Track usage
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.core.finetune_models import FineTunedModel, ModelVersion, ModelUsage
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Models"])

# In-memory storage for models (will be replaced with database later)
_models: Dict[str, FineTunedModel] = {}
_model_versions: Dict[str, List[ModelVersion]] = {}
_model_usage: Dict[str, List[ModelUsage]] = {}


class CreateModelRequest(BaseModel):
    """Request to create/register a model."""
    job_id: str
    model_id: str
    name: str
    description: Optional[str] = None
    base_model: str
    provider: str
    training_examples: int
    validation_examples: Optional[int] = 0
    epochs: int
    training_file_id: Optional[str] = None
    validation_file_id: Optional[str] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    metadata: Optional[dict] = None


class UpdateModelRequest(BaseModel):
    """Request to update model metadata."""
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[dict] = None


@router.get("/models", response_model=List[FineTunedModel])
async def list_models(
    status: Optional[str] = Query(None, description="Filter by status"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    base_model: Optional[str] = Query(None, description="Filter by base model"),
    sort_by: Optional[str] = Query("created_at", description="Sort field (created_at, name, usage_count)"),
    order: Optional[str] = Query("desc", description="Sort order (asc, desc)"),
) -> List[FineTunedModel]:
    """
    List all fine-tuned models.
    
    Args:
        status: Filter by status (training, ready, failed, deleted)
        provider: Filter by provider (openai, anthropic, custom)
        base_model: Filter by base model (e.g., gpt-3.5-turbo)
        sort_by: Field to sort by
        order: Sort order (asc or desc)
        
    Returns:
        List of fine-tuned models
    """
    models = list(_models.values())
    
    # Apply filters
    if status:
        models = [m for m in models if m.status == status]
    if provider:
        models = [m for m in models if m.provider == provider]
    if base_model:
        models = [m for m in models if m.base_model == base_model]
    
    # Sort
    reverse = order == "desc"
    if sort_by == "created_at":
        models.sort(key=lambda x: x.created_at, reverse=reverse)
    elif sort_by == "name":
        models.sort(key=lambda x: x.name.lower(), reverse=reverse)
    elif sort_by == "usage_count":
        models.sort(key=lambda x: x.usage_count, reverse=reverse)
    else:
        models.sort(key=lambda x: x.created_at, reverse=True)  # Default: newest first
    
    return models


@router.get("/models/{model_id}", response_model=FineTunedModel)
async def get_model(model_id: str) -> FineTunedModel:
    """
    Get details of a specific model.
    
    Args:
        model_id: Model ID
        
    Returns:
        Model details
        
    Raises:
        HTTPException: If model not found
    """
    if model_id not in _models:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
    
    return _models[model_id]


@router.post("/models", response_model=FineTunedModel)
async def create_model(request: CreateModelRequest) -> FineTunedModel:
    """
    Register a new fine-tuned model.
    
    This is typically called automatically when a fine-tuning job completes,
    but can also be called manually.
    
    Args:
        request: Model creation request
        
    Returns:
        Created model
    """
    model_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    model = FineTunedModel(
        id=model_id,
        job_id=request.job_id,
        model_id=request.model_id,
        name=request.name,
        description=request.description,
        base_model=request.base_model,
        provider=request.provider,
        status="ready",  # Assume ready when explicitly created
        training_examples=request.training_examples,
        validation_examples=request.validation_examples or 0,
        epochs=request.epochs,
        training_file_id=request.training_file_id,
        validation_file_id=request.validation_file_id,
        estimated_cost=request.estimated_cost,
        actual_cost=request.actual_cost,
        usage_count=0,
        created_at=now,
        updated_at=now,
        metadata=request.metadata or {},
    )
    
    _models[model_id] = model
    logger.info(f"Registered fine-tuned model: {model_id} ({model.name})")
    
    return model


@router.patch("/models/{model_id}", response_model=FineTunedModel)
async def update_model(
    model_id: str,
    request: UpdateModelRequest,
) -> FineTunedModel:
    """
    Update model metadata.
    
    Args:
        model_id: Model ID
        request: Update request
        
    Returns:
        Updated model
        
    Raises:
        HTTPException: If model not found
    """
    if model_id not in _models:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
    
    model = _models[model_id]
    
    # Update fields
    if request.name is not None:
        model.name = request.name
    if request.description is not None:
        model.description = request.description
    if request.metadata is not None:
        model.metadata = {**model.metadata, **request.metadata}
    
    model.updated_at = datetime.now().isoformat()
    
    logger.info(f"Updated model: {model_id}")
    
    return model


@router.delete("/models/{model_id}")
async def delete_model(
    model_id: str,
    delete_from_provider: bool = Query(False, description="Also delete from provider (OpenAI, etc.)"),
) -> Dict[str, str]:
    """
    Delete a model.
    
    Args:
        model_id: Model ID
        delete_from_provider: Whether to also delete from provider
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If model not found
    """
    if model_id not in _models:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
    
    model = _models[model_id]
    
    # Delete from provider if requested
    if delete_from_provider and model.provider == "openai":
        try:
            import os
            from openai import OpenAI
            
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                client = OpenAI(api_key=api_key)
                # Note: OpenAI doesn't have a delete endpoint for fine-tuned models
                # They can only be deleted through the dashboard
                logger.warning(f"Cannot delete model from OpenAI via API: {model.model_id}")
        except Exception as e:
            logger.warning(f"Failed to delete model from provider: {e}")
    
    # Soft delete (mark as deleted)
    model.status = "deleted"
    model.updated_at = datetime.now().isoformat()
    
    # Or hard delete (remove from registry)
    # del _models[model_id]
    
    logger.info(f"Deleted model: {model_id}")
    
    return {"message": "Model deleted successfully", "model_id": model_id}


@router.post("/models/{model_id}/usage")
async def record_model_usage(
    model_id: str,
    node_type: Optional[str] = None,
    execution_id: Optional[str] = None,
    tokens_used: Optional[int] = None,
    cost: Optional[float] = None,
) -> Dict[str, str]:
    """
    Record model usage.
    
    Called when a model is used in a workflow execution.
    
    Args:
        model_id: Model ID
        node_type: Type of node that used the model
        execution_id: Execution ID
        tokens_used: Number of tokens used
        cost: Cost of this usage
        
    Returns:
        Success message
    """
    if model_id not in _models:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
    
    model = _models[model_id]
    
    # Create usage entry
    usage = ModelUsage(
        id=str(uuid.uuid4()),
        model_id=model_id,
        used_at=datetime.now().isoformat(),
        node_type=node_type,
        execution_id=execution_id,
        tokens_used=tokens_used,
        cost=cost,
    )
    
    # Store usage
    if model_id not in _model_usage:
        _model_usage[model_id] = []
    _model_usage[model_id].append(usage)
    
    # Update model usage stats
    model.usage_count += 1
    model.last_used_at = datetime.now().isoformat()
    model.updated_at = datetime.now().isoformat()
    
    logger.info(f"Recorded usage for model: {model_id} (total: {model.usage_count})")
    
    return {"message": "Usage recorded", "model_id": model_id}


@router.get("/models/{model_id}/usage", response_model=List[ModelUsage])
async def get_model_usage(
    model_id: str,
    limit: int = Query(50, description="Maximum number of usage entries to return"),
) -> List[ModelUsage]:
    """
    Get usage history for a model.
    
    Args:
        model_id: Model ID
        limit: Maximum number of entries to return
        
    Returns:
        List of usage entries
    """
    if model_id not in _models:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
    
    usage_list = _model_usage.get(model_id, [])
    
    # Sort by used_at (newest first) and limit
    usage_list.sort(key=lambda x: x.used_at, reverse=True)
    return usage_list[:limit]


@router.get("/models/{model_id}/versions", response_model=List[ModelVersion])
async def get_model_versions(model_id: str) -> List[ModelVersion]:
    """
    Get version history for a model.
    
    Args:
        model_id: Model ID
        
    Returns:
        List of model versions
    """
    if model_id not in _models:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
    
    return _model_versions.get(model_id, [])


@router.get("/models/available/{provider}", response_model=List[FineTunedModel])
async def get_available_models(
    provider: str,
    status: Optional[str] = Query("ready", description="Filter by status"),
) -> List[FineTunedModel]:
    """
    Get available fine-tuned models for a provider.
    
    Used by Chat/Embed nodes to populate model selector dropdown.
    
    Args:
        provider: Provider name (openai, anthropic, etc.)
        status: Filter by status (default: ready)
        
    Returns:
        List of available models
    """
    models = list(_models.values())
    
    # Filter by provider and status
    filtered = [m for m in models if m.provider == provider]
    if status:
        filtered = [m for m in filtered if m.status == status]
    
    # Sort by name
    filtered.sort(key=lambda x: x.name)
    
    return filtered


@router.get("/models/base/{provider}")
async def get_base_models(
    provider: str,
    model_type: Optional[str] = Query("llm", description="Model type: llm, embedding, or reranking"),
) -> Dict[str, Any]:
    """
    Get available base models from the pricing system for a provider.
    
    Used by Prompt Playground and other components to populate model dropdowns.
    
    Args:
        provider: Provider name (openai, anthropic, gemini, etc.)
        model_type: Type of models to return (llm, embedding, reranking)
        
    Returns:
        Dictionary with model list and pricing information
    """
    try:
        from backend.utils.model_pricing import get_available_models, ModelType
        
        # Map model_type string to enum
        type_map = {
            "llm": ModelType.LLM,
            "embedding": ModelType.EMBEDDING,
            "reranking": ModelType.RERANKING,
        }
        
        model_type_enum = type_map.get(model_type.lower(), ModelType.LLM)
        
        # Get models from pricing system
        models = get_available_models(provider=provider, model_type=model_type_enum)
        
        # Format response
        model_list = []
        for model in models:
            # Skip deprecated models and aliases for cleaner UI
            metadata = model.metadata or {}
            if metadata.get("deprecated", False) or metadata.get("is_alias", False):
                continue
            
            model_info = {
                "model_id": model.model_id,
                "description": model.description,
                "max_tokens": model.max_tokens,
                "pricing": {},
            }
            
            # Extract pricing information
            if model_type_enum == ModelType.LLM:
                model_info["pricing"] = {
                    "input_per_1k": metadata.get("input_price_per_1k_tokens", 0.0),
                    "output_per_1k": metadata.get("output_price_per_1k_tokens", 0.0),
                    "cached_input_per_1k": metadata.get("cached_input_price_per_1k_tokens"),
                }
            elif model_type_enum == ModelType.EMBEDDING:
                model_info["pricing"] = {
                    "per_1k_tokens": model.price_per_1k_tokens or 0.0,
                    "batch_per_1k_tokens": metadata.get("batch_price_per_1k_tokens"),
                }
            elif model_type_enum == ModelType.RERANKING:
                model_info["pricing"] = {
                    "per_1k_units": model.price_per_1k_units or 0.0,
                }
            
            model_list.append(model_info)
        
        return {
            "provider": provider,
            "model_type": model_type,
            "models": model_list,
        }
    except Exception as e:
        logger.error(f"Error getting base models: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get base models: {str(e)}"
        )
