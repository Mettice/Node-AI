"""
Webhook Input Node for NodeAI.

This node receives data from webhook HTTP requests and passes it to the workflow.
When a webhook is triggered, the workflow starts from this node.
"""

from typing import Any, Dict

from backend.core.node_registry import NodeRegistry
from backend.nodes.base import BaseNode


class WebhookInputNode(BaseNode):
    """
    Webhook Input Node.
    
    Receives data from webhook HTTP requests.
    When a webhook is triggered, the workflow starts execution from this node.
    """

    node_type = "webhook_input"
    name = "Webhook Input"
    description = "Receive data from HTTP webhook requests. Triggers workflow execution when called."
    category = "input"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the webhook input node.
        
        Returns the webhook payload data.
        This is typically called when a webhook is triggered externally.
        """
        node_id = config.get("_node_id", "webhook_input")
        
        await self.stream_progress(node_id, 0.1, "Receiving webhook data...")
        
        # Get webhook payload from config (injected by webhook trigger)
        payload = config.get("payload", {})
        webhook_id = config.get("webhook_id")
        
        # Extract common fields
        text = payload.get("query") or payload.get("text") or payload.get("message") or ""
        
        # If no text field, convert entire payload to string
        if not text and payload:
            import json
            text = json.dumps(payload)
        
        await self.stream_progress(node_id, 0.5, f"Webhook data received: {len(str(payload))} bytes")
        
        result = {
            "text": text,
            "payload": payload,  # Full payload for advanced use cases
            "metadata": {
                "source": "webhook",
                "webhook_id": webhook_id,
                "payload_keys": list(payload.keys()) if isinstance(payload, dict) else [],
            },
        }
        
        await self.stream_progress(node_id, 1.0, "Webhook input ready")
        
        return result

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for webhook input configuration."""
        return {
            "type": "object",
            "properties": {
                "webhook_id": {
                    "type": "string",
                    "title": "Webhook ID",
                    "description": "Unique identifier for this webhook (auto-generated)",
                    "readOnly": True,
                },
                "webhook_url": {
                    "type": "string",
                    "title": "Webhook URL",
                    "description": "URL to trigger this workflow (auto-generated)",
                    "readOnly": True,
                },
                "name": {
                    "type": "string",
                    "title": "Webhook Name",
                    "description": "Optional name for this webhook",
                },
            },
            "required": [],
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return schema for node outputs."""
        return {
            "text": {
                "type": "string",
                "description": "Extracted text from webhook payload",
            },
            "payload": {
                "type": "object",
                "description": "Full webhook payload",
            },
            "metadata": {
                "type": "object",
                "description": "Webhook metadata",
            },
        }


# Register the node
NodeRegistry.register(
    "webhook_input",
    WebhookInputNode,
    WebhookInputNode().get_metadata(),
)

