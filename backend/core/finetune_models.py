"""
Database models for fine-tuned models registry.

This module defines the data models for storing and managing fine-tuned models.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class FineTunedModel(BaseModel):
    """Fine-tuned model registry entry."""
    
    id: str = Field(description="Unique model ID (UUID)")
    job_id: str = Field(description="Fine-tuning job ID from provider")
    model_id: str = Field(description="Provider model ID (e.g., ft:gpt-3.5-turbo:org:model:id)")
    name: str = Field(description="User-friendly model name")
    description: Optional[str] = Field(default=None, description="Model description")
    base_model: str = Field(description="Base model that was fine-tuned (e.g., gpt-3.5-turbo)")
    provider: str = Field(description="Provider (openai, anthropic, custom)")
    status: str = Field(description="Model status (training, ready, failed, deleted)")
    
    # Training metadata
    training_examples: int = Field(description="Number of training examples")
    validation_examples: Optional[int] = Field(default=0, description="Number of validation examples")
    epochs: int = Field(description="Number of training epochs")
    training_file_id: Optional[str] = Field(default=None, description="Training file ID")
    validation_file_id: Optional[str] = Field(default=None, description="Validation file ID")
    
    # Cost tracking
    estimated_cost: Optional[float] = Field(default=None, description="Estimated training cost")
    actual_cost: Optional[float] = Field(default=None, description="Actual training cost")
    
    # Usage tracking
    usage_count: int = Field(default=0, description="Number of times model has been used")
    last_used_at: Optional[str] = Field(default=None, description="ISO timestamp of last use")
    
    # Timestamps
    created_at: str = Field(description="ISO timestamp when model was created")
    updated_at: str = Field(description="ISO timestamp when model was last updated")
    
    # Additional metadata
    metadata: dict = Field(default_factory=dict, description="Additional metadata (training params, etc.)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "job_id": "ftjob-abc123",
                "model_id": "ft:gpt-3.5-turbo:org:model:id",
                "name": "Legal Document Analyzer",
                "description": "Fine-tuned for legal document analysis",
                "base_model": "gpt-3.5-turbo",
                "provider": "openai",
                "status": "ready",
                "training_examples": 1000,
                "validation_examples": 200,
                "epochs": 3,
                "estimated_cost": 12.50,
                "actual_cost": 11.80,
                "usage_count": 45,
                "last_used_at": "2024-01-15T10:30:00Z",
                "created_at": "2024-01-10T08:00:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        }


class ModelVersion(BaseModel):
    """Model version tracking."""
    
    id: str = Field(description="Version ID")
    model_id: str = Field(description="Parent model ID")
    version: int = Field(description="Version number")
    model_id_provider: str = Field(description="Provider model ID for this version")
    notes: Optional[str] = Field(default=None, description="Version notes/changelog")
    created_at: str = Field(description="ISO timestamp when version was created")


class ModelUsage(BaseModel):
    """Model usage tracking entry."""
    
    id: str = Field(description="Usage entry ID")
    model_id: str = Field(description="Model ID that was used")
    used_at: str = Field(description="ISO timestamp when model was used")
    node_type: Optional[str] = Field(default=None, description="Node type that used the model (embed, chat, etc.)")
    execution_id: Optional[str] = Field(default=None, description="Execution ID where model was used")
    tokens_used: Optional[int] = Field(default=None, description="Tokens used in this execution")
    cost: Optional[float] = Field(default=None, description="Cost of this usage")

