"""
Fine-Tune Node for NodeAI.

This node handles fine-tuning of LLM models (OpenAI, Anthropic, etc.).
Supports async job management for long-running training tasks.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.core.secret_resolver import resolve_api_key
from backend.nodes.base import BaseNode
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class FineTuneNode(BaseNode):
    """
    Fine-Tune Node.
    
    Fine-tunes LLM models using training data.
    Supports OpenAI fine-tuning with async job management.
    """

    node_type = "finetune"
    name = "Fine-Tune"
    description = "Fine-tune LLM models with custom training data. Supports OpenAI fine-tuning with async job management."
    category = "training"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the fine-tuning node.
        
        Starts a fine-tuning job and returns job ID for async tracking.
        """
        node_id = config.get("_node_id", "finetune")
        
        await self.stream_progress(node_id, 0.1, "Preparing fine-tuning job...")
        
        # Get configuration
        provider = config.get("provider", "openai")
        base_model = config.get("base_model", "gpt-3.5-turbo")
        validation_split = config.get("validation_split", 0.2)
        epochs = config.get("epochs", 3)
        batch_size = config.get("batch_size", None)  # Auto if None
        learning_rate = config.get("learning_rate", None)  # Auto if None
        
        # Get training data
        training_data = inputs.get("data") or inputs.get("training_data") or []
        training_file_id = config.get("training_file_id", "")
        
        if not training_data and not training_file_id:
            raise ValueError("No training data provided. Either provide data from a previous node or upload a file.")
        
        await self.stream_progress(node_id, 0.2, "Validating training data...")
        
        # Prepare training data
        if training_file_id:
            # Load from uploaded file
            training_data = await self._load_training_file(training_file_id, node_id)
        else:
            # Validate and format data from inputs
            training_data = self._validate_training_data(training_data)
        
        # Convert to JSONL format
        jsonl_data = self._convert_to_jsonl(training_data)
        
        await self.stream_progress(node_id, 0.3, f"Prepared {len(jsonl_data)} training examples")
        
        # Split validation data if needed
        if validation_split > 0:
            validation_data, training_data_split = self._split_validation(
                jsonl_data, validation_split
            )
            await self.stream_progress(node_id, 0.4, f"Split: {len(training_data_split)} train, {len(validation_data)} validation")
        else:
            training_data_split = jsonl_data
            validation_data = None
        
        # Start fine-tuning based on provider
        if provider == "openai":
            result = await self._fine_tune_openai(
                training_data_split,
                validation_data,
                base_model,
                epochs,
                batch_size,
                learning_rate,
                node_id,
            )
        elif provider == "anthropic":
            raise ValueError("Anthropic fine-tuning not yet supported")
        elif provider == "custom":
            raise ValueError("Custom fine-tuning not yet supported")
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        await self.stream_progress(node_id, 1.0, "Fine-tuning job started successfully")
        
        return result
    
    def _validate_training_data(self, data: List[Any]) -> List[Dict[str, Any]]:
        """Validate and normalize training data format."""
        if not isinstance(data, list):
            raise ValueError(f"Training data must be a list, got {type(data)}")
        
        validated = []
        for i, item in enumerate(data):
            if isinstance(item, str):
                # Try to parse as JSON
                try:
                    item = json.loads(item)
                except json.JSONDecodeError:
                    raise ValueError(f"Training example {i} is not valid JSON: {item[:100]}")
            
            if not isinstance(item, dict):
                raise ValueError(f"Training example {i} must be a dict, got {type(item)}")
            
            # OpenAI format: {"messages": [...]} or {"prompt": "...", "completion": "..."}
            if "messages" in item:
                # Chat format
                if not isinstance(item["messages"], list):
                    raise ValueError(f"Training example {i}: 'messages' must be a list")
                validated.append(item)
            elif "prompt" in item and "completion" in item:
                # Completion format
                validated.append(item)
            else:
                raise ValueError(
                    f"Training example {i} must have either 'messages' (chat) or "
                    "'prompt'/'completion' (completion) format"
                )
        
        return validated
    
    def _convert_to_jsonl(self, data: List[Dict[str, Any]]) -> List[str]:
        """Convert training data to JSONL format (list of JSON strings)."""
        return [json.dumps(item) for item in data]
    
    def _split_validation(
        self, data: List[str], validation_split: float
    ) -> tuple[List[str], List[str]]:
        """Split data into training and validation sets."""
        import random
        
        # Shuffle for random split
        shuffled = data.copy()
        random.shuffle(shuffled)
        
        split_idx = int(len(shuffled) * (1 - validation_split))
        training = shuffled[:split_idx]
        validation = shuffled[split_idx:]
        
        return validation, training
    
    async def _load_training_file(self, file_id: str, node_id: str) -> List[Dict[str, Any]]:
        """Load training data from uploaded file."""
        from pathlib import Path
        
        UPLOAD_DIR = Path("uploads")
        
        # Try to find the file
        jsonl_path = UPLOAD_DIR / f"{file_id}.jsonl"
        json_path = UPLOAD_DIR / f"{file_id}.json"
        
        file_path = None
        if jsonl_path.exists():
            file_path = jsonl_path
        elif json_path.exists():
            file_path = json_path
        else:
            raise ValueError(f"Training file with ID {file_id} not found")
        
        await self.stream_progress(node_id, 0.25, f"Loading training file: {file_path.name}")
        
        # Load and parse
        data = []
        with open(file_path, "r", encoding="utf-8") as f:
            if file_path.suffix == ".jsonl":
                # JSONL format: one JSON object per line
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                        data.append(item)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid JSON on line {line_num}: {e}")
            else:
                # JSON format: array of objects
                try:
                    data = json.load(f)
                    if not isinstance(data, list):
                        raise ValueError("JSON file must contain an array of training examples")
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON file: {e}")
        
        return data
    
    async def _fine_tune_openai(
        self,
        training_data: List[str],
        validation_data: Optional[List[str]],
        base_model: str,
        epochs: int,
        batch_size: Optional[int],
        learning_rate: Optional[float],
        node_id: str,
    ) -> Dict[str, Any]:
        """Start OpenAI fine-tuning job."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("OpenAI fine-tuning requires openai package. Install with: pip install openai")
        
        user_id = config.get("_user_id")
        api_key = resolve_api_key(config, "openai_api_key", user_id=user_id) or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found. Please configure it in the node settings or set OPENAI_API_KEY environment variable")
        
        client = OpenAI(api_key=api_key)
        
        await self.stream_progress(node_id, 0.5, "Uploading training data to OpenAI...")
        
        # Save training data to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for line in training_data:
                f.write(line + "\n")
            training_file_path = f.name
        
        try:
            # Upload training file
            with open(training_file_path, "rb") as f:
                training_file = client.files.create(
                    file=f,
                    purpose="fine-tune",
                )
            
            await self.stream_progress(node_id, 0.6, f"Training file uploaded: {training_file.id}")
            
            # Upload validation file if provided
            validation_file_id = None
            if validation_data:
                await self.stream_progress(node_id, 0.65, "Uploading validation data...")
                with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
                    for line in validation_data:
                        f.write(line + "\n")
                    validation_file_path = f.name
                
                with open(validation_file_path, "rb") as f:
                    validation_file = client.files.create(
                        file=f,
                        purpose="fine-tune",
                    )
                validation_file_id = validation_file.id
                os.unlink(validation_file_path)
                await self.stream_progress(node_id, 0.7, f"Validation file uploaded: {validation_file_id}")
            
            # Prepare fine-tuning parameters
            fine_tune_params = {
                "training_file": training_file.id,
                "model": base_model,
                "hyperparameters": {},
            }
            
            if validation_file_id:
                fine_tune_params["validation_file"] = validation_file_id
            
            if epochs:
                fine_tune_params["hyperparameters"]["n_epochs"] = epochs
            
            if batch_size:
                fine_tune_params["hyperparameters"]["batch_size"] = batch_size
            
            if learning_rate:
                fine_tune_params["hyperparameters"]["learning_rate_multiplier"] = learning_rate
            
            await self.stream_progress(node_id, 0.8, "Starting fine-tuning job...")
            
            # Create fine-tuning job
            job = client.fine_tuning.jobs.create(**fine_tune_params)
            
            await self.stream_progress(node_id, 0.9, f"Fine-tuning job created: {job.id}")
            
            # Estimate cost
            cost_estimate = self._estimate_cost(len(training_data), base_model, epochs)
            
            # Clean up temp file
            os.unlink(training_file_path)
            
            result = {
                "job_id": job.id,
                "status": job.status,
                "provider": "openai",
                "base_model": base_model,
                "training_file_id": training_file.id,
                "validation_file_id": validation_file_id,
                "training_examples": len(training_data),
                "validation_examples": len(validation_data) if validation_data else 0,
                "epochs": epochs,
                "estimated_cost": cost_estimate,
                "created_at": datetime.now().isoformat(),
                "metadata": {
                    "job_id": job.id,
                    "status": job.status,
                    "provider": "openai",
                },
            }
            
            # Register job for status tracking (fire and forget)
            try:
                # Register job in background (non-blocking)
                # Use asyncio.create_task to run in background without blocking
                import asyncio
                loop = asyncio.get_event_loop()
                loop.create_task(self._register_job(job.id, result))
            except Exception as e:
                logger.warning(f"Failed to register fine-tuning job: {e}")
            
            return result
            
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(training_file_path):
                os.unlink(training_file_path)
            logger.error(f"OpenAI fine-tuning failed: {e}")
            raise ValueError(f"OpenAI fine-tuning failed: {str(e)}")
    
    async def _register_job(self, job_id: str, job_data: Dict[str, Any]) -> None:
        """Register fine-tuning job for status tracking."""
        try:
            import httpx
            import os
            
            # Get API base URL from environment or use default
            api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
            url = f"{api_base}/api/v1/finetune/{job_id}/register"
            
            async with httpx.AsyncClient() as client:
                await client.post(url, json=job_data, timeout=5.0)
        except Exception as e:
            # Non-critical, just log
            logger.debug(f"Could not register job (this is OK if API not available): {e}")
    
    def _estimate_cost(self, num_examples: int, model: str, epochs: int) -> float:
        """Estimate fine-tuning cost."""
        # OpenAI pricing (approximate, as of 2024)
        # Training: $0.008 per 1K tokens
        # Usage: varies by model
        
        # Rough estimate: assume 500 tokens per example
        tokens_per_example = 500
        total_tokens = num_examples * tokens_per_example * epochs
        
        # Training cost
        training_cost = (total_tokens / 1000) * 0.008
        
        return round(training_cost, 2)
    
    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for fine-tuning configuration."""
        return {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "title": "Provider",
                    "description": "Fine-tuning provider",
                    "enum": ["openai", "anthropic", "custom"],
                    "default": "openai",
                },
                "base_model": {
                    "type": "string",
                    "title": "Base Model",
                    "description": "Base model to fine-tune",
                    "enum": [
                        "gpt-3.5-turbo",
                        "gpt-4",
                        "gpt-4-turbo-preview",
                    ],
                    "default": "gpt-3.5-turbo",
                },
                "training_file_id": {
                    "type": "string",
                    "title": "Training File ID (Optional)",
                    "description": "ID of uploaded JSONL training file (if not using data from previous node)",
                    "default": "",
                },
                "validation_split": {
                    "type": "number",
                    "title": "Validation Split",
                    "description": "Fraction of data to use for validation (0.0 to 1.0)",
                    "default": 0.2,
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
                "epochs": {
                    "type": "integer",
                    "title": "Epochs",
                    "description": "Number of training epochs",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 50,
                },
                "batch_size": {
                    "type": "integer",
                    "title": "Batch Size (Optional)",
                    "description": "Batch size for training (leave empty for auto)",
                    "default": None,
                    "minimum": 1,
                },
                "learning_rate": {
                    "type": "number",
                    "title": "Learning Rate (Optional)",
                    "description": "Learning rate multiplier (leave empty for auto)",
                    "default": None,
                    "minimum": 0.0,
                },
            },
            "required": ["provider", "base_model"],
        }
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Return schema for node inputs."""
        return {
            "data": {
                "type": "array",
                "description": "Training data from previous node (array of examples)",
            },
            "training_data": {
                "type": "array",
                "description": "Alternative input name for training data",
            },
        }
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for node outputs."""
        return {
            "job_id": {
                "type": "string",
                "description": "Fine-tuning job ID for status tracking",
            },
            "status": {
                "type": "string",
                "description": "Current job status (validating_training_file, queued, running, succeeded, failed)",
            },
            "provider": {
                "type": "string",
                "description": "Fine-tuning provider used",
            },
            "base_model": {
                "type": "string",
                "description": "Base model that was fine-tuned",
            },
            "training_file_id": {
                "type": "string",
                "description": "OpenAI file ID for training data",
            },
            "validation_file_id": {
                "type": "string",
                "description": "OpenAI file ID for validation data (if used)",
            },
            "training_examples": {
                "type": "integer",
                "description": "Number of training examples",
            },
            "validation_examples": {
                "type": "integer",
                "description": "Number of validation examples",
            },
            "epochs": {
                "type": "integer",
                "description": "Number of epochs used",
            },
            "estimated_cost": {
                "type": "number",
                "description": "Estimated cost of fine-tuning",
            },
            "created_at": {
                "type": "string",
                "description": "ISO timestamp when job was created",
            },
            "metadata": {
                "type": "object",
                "description": "Additional metadata about the job",
            },
        }


# Register the node
NodeRegistry.register(
    FineTuneNode.node_type,
    FineTuneNode,
    FineTuneNode().get_metadata(),
)

