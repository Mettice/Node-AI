"""
Enhanced Email Node for NodeAI.

This node provides a dedicated interface for sending emails with better UX
than the generic tool node. Supports HTML/text emails, attachments, and templates.
"""

import base64
import json
from typing import Any, Dict, List, Optional
from pathlib import Path

import httpx

from backend.nodes.base import BaseNode
from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class EmailNode(BaseNode):
    """
    Enhanced Email Node.
    
    Provides a dedicated interface for sending emails with better UX
    than the generic tool node.
    """

    node_type = "email"
    name = "Email"
    description = "Send emails with HTML/text support, attachments, and templates"
    category = "communication"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute email sending operation.
        
        Supports: Resend (and can be extended to SendGrid, etc.)
        """
        node_id = config.get("_node_id", "email")
        provider = config.get("email_provider", "resend")
        
        # Get email data from inputs or config
        # Check multiple possible sources for each field (intelligent routing + fallback)
        to_email = (
            config.get("email_to") or 
            inputs.get("email_to") or 
            inputs.get("to") or
            inputs.get("recipient") or
            inputs.get("email")
        )
        subject = (
            config.get("email_subject") or 
            inputs.get("email_subject") or 
            inputs.get("subject") or
            inputs.get("title")
        )
        body = (
            config.get("email_body") or 
            inputs.get("email_body") or 
            inputs.get("body") or 
            inputs.get("content") or
            inputs.get("text") or
            inputs.get("output") or
            inputs.get("message")
        )
        
        # Check if email type should be HTML (from intelligent routing or if body contains HTML)
        email_type_override = inputs.get("_email_type")
        if email_type_override == "html" or (body and ("<h" in body or "<p>" in body or "<img" in body or "<ul>" in body)):
            # Auto-detect HTML content and set email type
            if config.get("email_type") != "html":
                config = config.copy()
                config["email_type"] = "html"
        
        # Get attachments from inputs (e.g., from chart generator) or config
        email_attachments = inputs.get("_email_attachments") or config.get("email_attachments") or inputs.get("attachments") or []
        
        if not to_email:
            raise ValueError("Recipient email address (to) is required")
        if not subject:
            raise ValueError("Email subject is required")
        if not body:
            raise ValueError("Email body is required")
        
        await self.stream_progress(node_id, 0.1, f"Preparing email to {to_email}...")
        
        # Route to appropriate provider
        if provider == "resend":
            return await self._send_resend_email(inputs, config, node_id, to_email, subject, body, email_attachments)
        else:
            raise ValueError(f"Unsupported email provider: {provider}")

    async def _send_resend_email(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        node_id: str,
        to_email: str,
        subject: str,
        body: str,
        email_attachments: list = None,
    ) -> Dict[str, Any]:
        """Send email using Resend API."""
        api_key = config.get("resend_api_key")
        from_email = config.get("email_from")
        from_name = config.get("email_from_name")
        reply_to = config.get("email_reply_to")
        # Get email type from config (may have been auto-set to HTML by intelligent routing)
        email_type = config.get("email_type", "text")  # "text" or "html"
        
        if not api_key:
            raise ValueError("Resend API key is required")
        if not from_email:
            raise ValueError("From email address is required")
        
        # Get CC and BCC from config or inputs
        cc = config.get("email_cc") or inputs.get("cc")
        bcc = config.get("email_bcc") or inputs.get("bcc")
        
        # Handle CC/BCC as strings or lists
        if cc and isinstance(cc, str):
            cc = [email.strip() for email in cc.split(",")]
        if bcc and isinstance(bcc, str):
            bcc = [email.strip() for email in bcc.split(",")]
        
        # Get attachments from parameter (from intelligent routing) or config or inputs
        attachments = email_attachments if email_attachments else (config.get("email_attachments") or inputs.get("attachments") or [])
        
        await self.stream_progress(node_id, 0.3, "Sending email via Resend...")
        
        # Prepare email payload
        payload: Dict[str, Any] = {
            "from": f"{from_name} <{from_email}>" if from_name else from_email,
            "to": [to_email] if isinstance(to_email, str) else to_email,
            "subject": subject,
        }
        
        if email_type == "html":
            payload["html"] = body
        else:
            payload["text"] = body
        
        if reply_to:
            payload["reply_to"] = reply_to
        
        if cc:
            payload["cc"] = cc if isinstance(cc, list) else [cc]
        
        if bcc:
            payload["bcc"] = bcc if isinstance(bcc, list) else [bcc]
        
        # Handle attachments (including inline images with CID)
        if attachments:
            processed_attachments = []
            for attachment in attachments:
                if isinstance(attachment, dict):
                    # Resend API format: { "filename": "...", "content": "base64...", "cid": "..." } for inline
                    # For inline images, we need to use a different approach
                    # Resend doesn't support CID directly, so we'll embed base64 in HTML instead
                    processed_attachments.append({
                        "filename": attachment.get("filename", "attachment"),
                        "content": attachment.get("content", ""),
                    })
                elif isinstance(attachment, str):
                    # Try to parse as file path or base64
                    # For now, assume it's a file path or needs to be handled differently
                    # In a real implementation, you'd handle file uploads
                    logger.warning(f"String attachment format not fully supported: {attachment}")
                else:
                    logger.warning(f"Unsupported attachment format: {type(attachment)}")
            
            if processed_attachments:
                payload["attachments"] = processed_attachments
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                )
                
                await self.stream_progress(node_id, 0.8, "Email sent, waiting for response...")
                
                if response.status_code == 200:
                    result = response.json()
                    message_id = result.get("id")
                    
                    await self.stream_progress(node_id, 1.0, f"Email sent successfully! (ID: {message_id})")
                    
                    return {
                        "output": {
                            "status": "success",
                            "provider": "resend",
                            "message_id": message_id,
                            "to": to_email,
                            "subject": subject,
                        },
                        "message_id": message_id,
                        "status": "sent",
                        "to": to_email,
                        "subject": subject,
                    }
                else:
                    error_data = response.json() if response.content else {}
                    error_message = error_data.get("message", f"HTTP {response.status_code}")
                    
                    await self.stream_progress(node_id, 1.0, f"Email failed: {error_message}")
                    
                    raise ValueError(f"Failed to send email: {error_message}")
                    
        except httpx.TimeoutException:
            raise ValueError("Email sending timed out. Please try again.")
        except httpx.RequestError as e:
            raise ValueError(f"Network error while sending email: {str(e)}")
        except Exception as e:
            logger.error(f"Email sending failed: {e}", exc_info=True)
            raise ValueError(f"Failed to send email: {str(e)}")

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for Email node configuration."""
        return {
            "type": "object",
            "properties": {
                "email_provider": {
                    "type": "string",
                    "enum": ["resend"],
                    "default": "resend",
                    "title": "Email Provider",
                    "description": "Email service provider",
                },
                "resend_api_key": {
                    "type": "string",
                    "title": "Resend API Key",
                    "description": "API key for Resend email service",
                },
                "email_from": {
                    "type": "string",
                    "title": "From Email",
                    "description": "Sender email address (e.g., noreply@example.com)",
                },
                "email_from_name": {
                    "type": "string",
                    "title": "From Name",
                    "description": "Sender name (optional, e.g., 'NodAI Team')",
                },
                "email_reply_to": {
                    "type": "string",
                    "title": "Reply-To Email",
                    "description": "Reply-to email address (optional)",
                },
                "email_to": {
                    "type": "string",
                    "title": "To Email",
                    "description": "Recipient email address (can also come from previous node)",
                },
                "email_cc": {
                    "type": "string",
                    "title": "CC",
                    "description": "CC recipients (comma-separated, optional)",
                },
                "email_bcc": {
                    "type": "string",
                    "title": "BCC",
                    "description": "BCC recipients (comma-separated, optional)",
                },
                "email_subject": {
                    "type": "string",
                    "title": "Subject",
                    "description": "Email subject (can also come from previous node)",
                },
                "email_type": {
                    "type": "string",
                    "enum": ["text", "html"],
                    "default": "text",
                    "title": "Email Type",
                    "description": "Email format (plain text or HTML)",
                },
                "email_body": {
                    "type": "string",
                    "title": "Body",
                    "description": "Email body content (can also come from previous node)",
                },
                "email_attachments": {
                    "type": "array",
                    "title": "Attachments",
                    "description": "Email attachments (optional)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string"},
                            "content": {"type": "string", "description": "Base64 encoded content"},
                            "path": {"type": "string", "description": "File path (if available)"},
                        },
                    },
                },
            },
            "required": ["email_provider", "resend_api_key", "email_from"],
        }


# Register the node
NodeRegistry.register(
    EmailNode.node_type,
    EmailNode,
    EmailNode().get_metadata(),
)

