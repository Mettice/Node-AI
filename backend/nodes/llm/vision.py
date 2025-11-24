"""
Vision Node for NodeAI.

This node analyzes images using GPT-4 Vision API.
"""

import base64
from pathlib import Path
from typing import Any, Dict, Optional

from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.core.secret_resolver import resolve_api_key
from backend.nodes.base import BaseNode
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class VisionNode(BaseNode):
    """
    Vision Node.
    
    Analyzes images using GPT-4 Vision API.
    Can describe images, extract information, answer questions about images.
    """

    node_type = "vision"
    name = "Vision"
    description = "Analyze images using GPT-4 Vision API. Describe, extract information, or answer questions about images."
    category = "llm"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the vision node.
        
        Analyzes images using GPT-4 Vision API.
        """
        node_id = config.get("_node_id", "vision")
        
        await self.stream_progress(node_id, 0.1, "Preparing vision analysis...")
        
        # Get image - can come from File Upload node as image_path, base64, or data_url
        image_path = inputs.get("image_path")
        base64_image = inputs.get("base64")
        data_url = inputs.get("data_url")
        
        # Get prompt
        prompt = config.get("prompt", "What's in this image? Describe it in detail.")
        
        # Get model
        model = config.get("model", "gpt-4-vision-preview")
        
        # Get max tokens
        max_tokens = config.get("max_tokens", 300)
        
        await self.stream_progress(node_id, 0.3, "Loading image...")
        
        # Prepare image for API
        image_base64 = None
        if base64_image:
            image_base64 = base64_image
        elif data_url:
            # Extract base64 from data URL
            if "," in data_url:
                image_base64 = data_url.split(",", 1)[1]
        elif image_path:
            # Read image and encode to base64
            if isinstance(image_path, str):
                image_path = Path(image_path)
            
            if not image_path.exists():
                raise ValueError(f"Image file not found: {image_path}")
            
            await self.stream_progress(node_id, 0.5, "Encoding image...")
            with open(image_path, "rb") as f:
                image_bytes = f.read()
                image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        else:
            raise ValueError("No image provided. Connect an Image file from File Upload node or provide base64/data_url.")
        
        await self.stream_progress(node_id, 0.7, f"Analyzing image with {model}...")
        
        # Call OpenAI Vision API
        try:
            from openai import AsyncOpenAI
            import os
            
            user_id = config.get("_user_id")
            api_key = resolve_api_key(config, "openai_api_key", user_id=user_id) or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found. Please configure it in the node settings or set OPENAI_API_KEY environment variable")
            
            client = AsyncOpenAI(api_key=api_key)
            
            # Determine image format from data
            image_format = "png"  # Default
            if image_path:
                ext = image_path.suffix.lower()
                if ext in [".jpg", ".jpeg"]:
                    image_format = "jpeg"
                elif ext == ".png":
                    image_format = "png"
                elif ext == ".gif":
                    image_format = "gif"
                elif ext == ".webp":
                    image_format = "webp"
            
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{image_format};base64,{image_base64}",
                                },
                            },
                        ],
                    }
                ],
                max_tokens=max_tokens,
            )
            
            description = response.choices[0].message.content or ""
            
            # Calculate cost
            # GPT-4 Vision pricing: $0.01 per image + $0.03 per 1K tokens
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            cost = (0.01 + (input_tokens / 1000) * 0.03 + (output_tokens / 1000) * 0.06)
            
            await self.stream_progress(node_id, 0.9, "Analysis complete")
            
            result = {
                "text": description,
                "description": description,  # Alias for consistency
                "metadata": {
                    "source": "vision",
                    "model": model,
                    "prompt": prompt,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                    "cost": cost,
                },
            }
            
            await self.stream_progress(node_id, 1.0, f"Vision analysis complete: {len(description)} characters")
            
            return result
            
        except ImportError:
            raise ImportError("OpenAI SDK is required. Install with: pip install openai")
        except Exception as e:
            logger.error(f"Vision API call failed: {e}")
            raise ValueError(f"Vision analysis failed: {str(e)}")

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for vision configuration."""
        return {
            "type": "object",
            "properties": {
                "model": {
                    "type": "string",
                    "title": "Model",
                    "description": "Vision model to use",
                    "enum": ["gpt-4-vision-preview", "gpt-4o", "gpt-4o-mini"],
                    "default": "gpt-4-vision-preview",
                },
                "prompt": {
                    "type": "string",
                    "title": "Prompt",
                    "description": "What to ask about the image",
                    "default": "What's in this image? Describe it in detail.",
                },
                "max_tokens": {
                    "type": "integer",
                    "title": "Max Tokens",
                    "description": "Maximum tokens in response",
                    "default": 300,
                    "minimum": 1,
                    "maximum": 4096,
                },
            },
            "required": [],
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for node outputs."""
        return {
            "text": {
                "type": "string",
                "description": "Image description/analysis",
            },
            "description": {
                "type": "string",
                "description": "Image description (alias for text)",
            },
            "metadata": {
                "type": "object",
                "description": "Vision API metadata (tokens, cost, etc.)",
            },
        }


# Register the node
NodeRegistry.register(
    VisionNode.node_type,
    VisionNode,
    VisionNode().get_metadata(),
)

