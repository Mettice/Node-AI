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
        
        if not channel:
            raise ValueError("Slack channel or user ID is required")
        
        # Check for structured data first
        structured_data = (
            inputs.get("data") or
            inputs.get("results") or
            inputs.get("records") or
            None
        )
        
        # Check if structured data is present and valid
        is_structured = (
            structured_data and
            isinstance(structured_data, list) and
            len(structured_data) > 0 and
            isinstance(structured_data[0], dict)
        )
        
        # Get format preference
        format_type = config.get("slack_data_format", "table") if is_structured else None
        
        # Format message based on data type
        if is_structured and format_type:
            message = self._format_structured_data(structured_data, format_type, config)
        else:
            # Fallback to regular message
            message = (
                config.get("slack_message") or 
                inputs.get("slack_message") or
                inputs.get("message") or 
                inputs.get("text") or
                inputs.get("output") or
                inputs.get("content") or
                inputs.get("body") or
                ""
            )
        
        if not message:
            raise ValueError("Message text is required")
        
        # Handle individual messages for structured data
        if is_structured and format_type == "individual":
            return await self._send_individual_messages(
                access_token, channel, structured_data, node_id
            )
        
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
    
    def _format_structured_data(
        self,
        data: List[Dict[str, Any]],
        format_type: str,
        config: Dict[str, Any],
    ) -> str:
        """
        Format structured data for Slack.
        
        Args:
            data: List of dictionaries
            format_type: Format type (table, list, summary)
            config: Node configuration
            
        Returns:
            Formatted string
        """
        if format_type == "table":
            return self._format_as_table(data, config)
        elif format_type == "list":
            return self._format_as_list(data, config)
        elif format_type == "summary":
            return self._format_as_summary(data, config)
        else:
            # Default to table
            return self._format_as_table(data, config)
    
    def _format_as_table(
        self,
        data: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> str:
        """Format data as a table."""
        if not data:
            return "No data available."
        
        # Get all columns
        all_keys = set()
        for record in data:
            all_keys.update(record.keys())
        columns = sorted(all_keys)
        
        # Limit rows for display
        max_rows = config.get("slack_max_rows", 50)
        display_data = data[:max_rows]
        
        # Build table
        lines = []
        lines.append("```")
        
        # Header row
        header = " | ".join(str(col) for col in columns)
        lines.append(header)
        lines.append("-" * len(header))
        
        # Data rows
        for record in display_data:
            row = " | ".join(str(record.get(col, "")) for col in columns)
            lines.append(row)
        
        lines.append("```")
        
        if len(data) > max_rows:
            lines.append(f"\n_... ({len(data) - max_rows} more rows)_")
        
        return "\n".join(lines)
    
    def _format_as_list(
        self,
        data: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> str:
        """Format data as a list."""
        if not data:
            return "No data available."
        
        max_items = config.get("slack_max_rows", 20)
        display_data = data[:max_items]
        
        lines = []
        for i, record in enumerate(display_data, 1):
            record_str = ", ".join(f"{k}: {v}" for k, v in record.items())
            lines.append(f"{i}. {record_str}")
        
        if len(data) > max_items:
            lines.append(f"\n_... ({len(data) - max_items} more items)_")
        
        return "\n".join(lines)
    
    def _format_as_summary(
        self,
        data: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> str:
        """Format data as a summary."""
        if not data:
            return "No data available."
        
        lines = []
        lines.append(f"*Data Summary*")
        lines.append(f"Total records: {len(data)}")
        
        # Get column info
        if data:
            all_keys = set()
            for record in data:
                all_keys.update(record.keys())
            lines.append(f"Columns: {', '.join(sorted(all_keys))}")
        
        # Sample first few records
        sample_size = min(3, len(data))
        if sample_size > 0:
            lines.append(f"\n*Sample ({sample_size} records):*")
            for i, record in enumerate(data[:sample_size], 1):
                record_str = ", ".join(f"{k}: {v}" for k, v in list(record.items())[:5])
                lines.append(f"{i}. {record_str}")
        
        return "\n".join(lines)
    
    async def _send_individual_messages(
        self,
        access_token: str,
        channel: str,
        data: List[Dict[str, Any]],
        node_id: str,
    ) -> Dict[str, Any]:
        """Send each row as a separate message."""
        total = len(data)
        sent = 0
        
        for i, record in enumerate(data, 1):
            record_str = ", ".join(f"{k}: {v}" for k, v in record.items())
            message = f"Record {i}/{total}: {record_str}"
            
            await self.stream_progress(
                node_id, 
                0.3 + (i / total) * 0.6,
                f"Sending message {i}/{total}..."
            )
            
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
                    },
                )
                
                data_resp = response.json()
                if data_resp.get("ok"):
                    sent += 1
        
        await self.stream_progress(node_id, 1.0, f"Sent {sent} messages successfully!")
        
        return {
            "output": {
                "status": "success",
                "operation": "send_message",
                "channel": channel,
                "messages_sent": sent,
                "total_records": total,
            },
            "messages_sent": sent,
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
                "slack_data_format": {
                    "type": "string",
                    "enum": ["table", "list", "summary", "individual"],
                    "default": "table",
                    "title": "Data Format",
                    "description": "Format for structured data (when data from previous node is detected): table, list, summary, or individual messages",
                },
                "slack_max_rows": {
                    "type": "integer",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 100,
                    "title": "Max Rows",
                    "description": "Maximum number of rows to display in formatted message (for table/list formats)",
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

