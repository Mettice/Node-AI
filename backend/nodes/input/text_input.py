"""
Text Input Node for NodeAI.

This node allows users to manually enter text for processing.
It's useful for testing and quick demos.
"""

from typing import Any, Dict

from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.nodes.base import BaseNode


class TextInputNode(BaseNode):
    """
    Text Input Node.
    
    Allows manual text entry for workflow processing.
    """

    node_type = "text_input"
    name = "Text Input"
    description = "Manually enter text for processing. Useful for testing and quick demos."
    category = "input"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the text input node.
        
        Simply returns the text from configuration.
        """
        node_id = config.get("_node_id", "text_input")
        
        await self.stream_progress(node_id, 0.1, "Reading text input...")
        
        text = config.get("text", "")
        
        if not text:
            raise ValueError("Text input cannot be empty")
        
        await self.stream_progress(node_id, 0.5, f"Text loaded: {len(text)} characters")
        
        result = {
            "text": text,
            "metadata": {
                "source": "manual_input",
                "length": len(text),
            },
        }
        
        await self.stream_progress(node_id, 1.0, "Text input ready")
        
        return result

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for text input configuration."""
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "title": "Text",
                    "description": "Enter the text you want to process",
                    "default": "",
                },
            },
            "required": ["text"],
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for node outputs."""
        return {
            "text": {
                "type": "string",
                "description": "The input text",
            },
            "metadata": {
                "type": "object",
                "description": "Text metadata",
            },
        }


# Register the node
NodeRegistry.register(
    "text_input",
    TextInputNode,
    TextInputNode().get_metadata(),
)

