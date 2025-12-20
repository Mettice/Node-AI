"""
Enhanced Slack Node for NodeAI.

This node provides a dedicated interface for Slack operations with OAuth support.
Supports sending messages, creating channels, posting to channels, etc.
"""

import json
from typing import Any, Dict, List, Optional

import httpx

from backend.nodes.base import BaseNode
from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.core.oauth import OAuthManager
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SlackNode(BaseNode):
    """
    Enhanced Slack Node.
    
    Provides a dedicated interface for Slack operations with OAuth support.
    """

    node_type = "slack"
    name = "Slack"
    description = "Send messages, create channels, and interact with Slack using OAuth"
    category = "communication"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute Slack operation.
        
        Supports: send_message, create_channel, post_to_channel, upload_file
        """
        node_id = config.get("_node_id", "slack")
        operation = config.get("slack_operation", "send_message")
        
        # Get OAuth token
        token_id = config.get("slack_token_id")
        if not token_id:
            raise ValueError("Slack OAuth token ID is required. Please connect your Slack account first.")
        
        token_data = OAuthManager.get_token(token_id)
        if not token_data:
            raise ValueError("Slack OAuth token not found. Please reconnect your Slack account.")
        
        # Check if token is valid
        if not OAuthManager.is_token_valid(token_data):
            raise ValueError("Slack OAuth token has expired. Please reconnect your Slack account.")
        
        access_token = token_data["access_token"]
        
        await self.stream_progress(node_id, 0.1, f"Executing Slack {operation}...")
        
        # Route to appropriate operation
        if operation == "send_message":
            return await self._send_message(access_token, inputs, config, node_id)
        elif operation == "create_channel":
            return await self._create_channel(access_token, inputs, config, node_id)
        elif operation == "post_to_channel":
            return await self._post_to_channel(access_token, inputs, config, node_id)
        elif operation == "upload_file":
            return await self._upload_file(access_token, inputs, config, node_id)
        else:
            raise ValueError(f"Unsupported Slack operation: {operation}")

    async def _send_message(
        self,
        access_token: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Send a direct message to a user or channel."""
        channel = (
            config.get("slack_channel") or 
            inputs.get("slack_channel") or
            inputs.get("channel") or
            inputs.get("channel_id")
        )
        message = (
            config.get("slack_message") or 
            inputs.get("slack_message") or
            inputs.get("message") or 
            inputs.get("text") or
            inputs.get("output") or
            inputs.get("content") or
            inputs.get("body")
        )
        
        if not channel:
            raise ValueError("Slack channel or user ID is required")
        if not message:
            raise ValueError("Message text is required")
        
        await self.stream_progress(node_id, 0.3, f"Sending message to {channel}...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "channel": channel,
                    "text": message,
                    "blocks": config.get("slack_blocks"),  # Optional rich formatting
                },
            )
            
            data = response.json()
            
            if not data.get("ok"):
                error = data.get("error", "Unknown error")
                raise ValueError(f"Slack API error: {error}")
            
            await self.stream_progress(node_id, 1.0, "Message sent successfully!")
            
            return {
                "output": {
                    "status": "success",
                    "operation": "send_message",
                    "channel": channel,
                    "ts": data.get("ts"),  # Message timestamp
                    "message": data.get("message", {}),
                },
                "message_ts": data.get("ts"),
                "channel": channel,
                "status": "sent",
            }

    async def _create_channel(
        self,
        access_token: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Create a new Slack channel."""
        channel_name = config.get("slack_channel_name") or inputs.get("channel_name")
        is_private = config.get("slack_is_private", False)
        
        if not channel_name:
            raise ValueError("Channel name is required")
        
        await self.stream_progress(node_id, 0.3, f"Creating channel '{channel_name}'...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://slack.com/api/conversations.create",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "name": channel_name,
                    "is_private": is_private,
                },
            )
            
            data = response.json()
            
            if not data.get("ok"):
                error = data.get("error", "Unknown error")
                raise ValueError(f"Slack API error: {error}")
            
            channel = data.get("channel", {})
            
            await self.stream_progress(node_id, 1.0, f"Channel '{channel_name}' created!")
            
            return {
                "output": {
                    "status": "success",
                    "operation": "create_channel",
                    "channel_id": channel.get("id"),
                    "channel_name": channel.get("name"),
                },
                "channel_id": channel.get("id"),
                "channel_name": channel.get("name"),
                "status": "created",
            }

    async def _post_to_channel(
        self,
        access_token: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Post a message to a channel (alias for send_message with channel)."""
        # This is essentially the same as send_message, but we keep it for clarity
        return await self._send_message(access_token, inputs, config, node_id)

    async def _upload_file(
        self,
        access_token: str,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
    ) -> Dict[str, Any]:
        """Upload a file to Slack."""
        channel = config.get("slack_channel") or inputs.get("channel")
        file_content = config.get("slack_file_content") or inputs.get("file_content") or inputs.get("file_data")
        filename = config.get("slack_filename") or inputs.get("filename") or "file.txt"
        title = config.get("slack_file_title")
        initial_comment = config.get("slack_initial_comment")
        
        if not channel:
            raise ValueError("Slack channel is required")
        if not file_content:
            raise ValueError("File content is required")
        
        await self.stream_progress(node_id, 0.3, f"Uploading file to {channel}...")
        
        # Handle file content - can be string or base64
        if isinstance(file_content, str):
            # Try to decode if it looks like base64
            try:
                import base64
                file_bytes = base64.b64decode(file_content)
            except:
                file_bytes = file_content.encode('utf-8')
        else:
            file_bytes = file_content
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Slack file upload requires multipart form data
            files = {
                "file": (filename, file_bytes),
            }
            data = {
                "channels": channel,
            }
            if title:
                data["title"] = title
            if initial_comment:
                data["initial_comment"] = initial_comment
            
            response = await client.post(
                "https://slack.com/api/files.upload",
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
                files=files,
                data=data,
            )
            
            result = response.json()
            
            if not result.get("ok"):
                error = result.get("error", "Unknown error")
                raise ValueError(f"Slack API error: {error}")
            
            file_data = result.get("file", {})
            
            await self.stream_progress(node_id, 1.0, "File uploaded successfully!")
            
            return {
                "output": {
                    "status": "success",
                    "operation": "upload_file",
                    "file_id": file_data.get("id"),
                    "file_name": file_data.get("name"),
                    "file_url": file_data.get("url_private"),
                },
                "file_id": file_data.get("id"),
                "file_url": file_data.get("url_private"),
                "status": "uploaded",
            }

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for Slack node configuration."""
        return {
            "type": "object",
            "properties": {
                "slack_operation": {
                    "type": "string",
                    "enum": ["send_message", "create_channel", "post_to_channel", "upload_file"],
                    "default": "send_message",
                    "title": "Operation",
                    "description": "Slack operation to perform",
                },
                "slack_token_id": {
                    "type": "string",
                    "title": "OAuth Token ID",
                    "description": "OAuth token ID from connected Slack account",
                },
                "slack_channel": {
                    "type": "string",
                    "title": "Channel/User ID",
                    "description": "Slack channel ID (e.g., C1234567890) or user ID (e.g., U1234567890) - required for send_message and upload_file",
                },
                "slack_message": {
                    "type": "string",
                    "title": "Message",
                    "description": "Message text to send (can also come from previous node)",
                },
                "slack_channel_name": {
                    "type": "string",
                    "title": "Channel Name",
                    "description": "Name for new channel (required for create_channel)",
                },
                "slack_is_private": {
                    "type": "boolean",
                    "default": False,
                    "title": "Private Channel",
                    "description": "Create as private channel (for create_channel)",
                },
                "slack_filename": {
                    "type": "string",
                    "title": "Filename",
                    "description": "Filename for upload (required for upload_file)",
                },
                "slack_file_content": {
                    "type": "string",
                    "title": "File Content",
                    "description": "File content (base64 or text) - required for upload_file",
                },
                "slack_file_title": {
                    "type": "string",
                    "title": "File Title",
                    "description": "Optional title for uploaded file",
                },
                "slack_initial_comment": {
                    "type": "string",
                    "title": "Initial Comment",
                    "description": "Optional comment to post with file",
                },
            },
            "required": ["slack_operation", "slack_token_id"],
        }


# Register the node
NodeRegistry.register(
    SlackNode.node_type,
    SlackNode,
    SlackNode().get_metadata(),
)

