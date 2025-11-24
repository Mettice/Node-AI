"""
Email tool implementation using Resend.
Supports sending emails with optional attachments, CC, BCC, etc.
"""

import asyncio
import httpx
import re
import json
from typing import Dict, Any, Callable, Optional
from backend.core.secret_resolver import resolve_api_key


def get_email_schema() -> Dict[str, Any]:
    """Get schema fields for email tool."""
    return {
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
            "description": "Default sender email address (e.g., noreply@example.com)",
        },
        "email_from_name": {
            "type": "string",
            "title": "From Name",
            "description": "Default sender name (optional)",
        },
        "email_reply_to": {
            "type": "string",
            "title": "Reply-To Email",
            "description": "Default reply-to email address (optional)",
        },
    }


def parse_email_string(input_str: str) -> Dict[str, Any]:
    """
    Parse email input from agent string format.
    Supports formats like:
    - "to: email@example.com, subject: Hello, body: Message"
    - "Send email to email@example.com with subject 'Hello' and body 'Message'"
    """
    email_data = {}
    
    # Try to extract to, subject, body using regex
    to_match = re.search(r'to:\s*([^\s,]+@[^\s,]+)', input_str, re.IGNORECASE)
    if to_match:
        email_data["to"] = to_match.group(1)
    
    subject_match = re.search(r'subject:\s*["\']?([^"\',]+)["\']?', input_str, re.IGNORECASE)
    if subject_match:
        email_data["subject"] = subject_match.group(1).strip()
    
    body_match = re.search(r'body:\s*["\']?([^"\']+)["\']?', input_str, re.IGNORECASE)
    if not body_match:
        # Try alternative format: "with body '...'"
        body_match = re.search(r'body\s+["\']([^"\']+)["\']', input_str, re.IGNORECASE)
    if body_match:
        email_data["body"] = body_match.group(1).strip()
    
    # Extract CC and BCC if present
    cc_match = re.search(r'cc:\s*([^\s,]+@[^\s,]+)', input_str, re.IGNORECASE)
    if cc_match:
        email_data["cc"] = [cc_match.group(1)]
    
    bcc_match = re.search(r'bcc:\s*([^\s,]+@[^\s,]+)', input_str, re.IGNORECASE)
    if bcc_match:
        email_data["bcc"] = [bcc_match.group(1)]
    
    return email_data


async def send_email_resend(
    to: str,
    subject: str,
    body: str,
    from_email: str,
    api_key: str,
    from_name: Optional[str] = None,
    reply_to: Optional[str] = None,
    cc: Optional[list] = None,
    bcc: Optional[list] = None,
    html: Optional[str] = None,
) -> Dict[str, Any]:
    """Send email using Resend API."""
    if not api_key:
        return {
            "success": False,
            "error": {"code": "missing_api_key", "message": "Resend API key is required"}
        }
    
    if not to:
        return {
            "success": False,
            "error": {"code": "missing_recipient", "message": "Recipient email is required"}
        }
    
    if not from_email:
        return {
            "success": False,
            "error": {"code": "missing_sender", "message": "Sender email is required"}
        }
    
    # Prepare payload
    payload = {
        "from": f"{from_name} <{from_email}>" if from_name else from_email,
        "to": [to] if isinstance(to, str) else to,
        "subject": subject,
    }
    
    # Add body (prefer HTML if provided)
    if html:
        payload["html"] = html
    else:
        payload["text"] = body
    
    # Add optional fields
    if reply_to:
        payload["reply_to"] = reply_to
    if cc:
        payload["cc"] = cc if isinstance(cc, list) else [cc]
    if bcc:
        payload["bcc"] = bcc if isinstance(bcc, list) else [bcc]
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "message_id": data.get("id"),
                    "to": to,
                    "subject": subject,
                    "status": "queued",
                    "timestamp": data.get("created_at"),
                    "error": None
                }
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                return {
                    "success": False,
                    "error": {
                        "code": f"http_{response.status_code}",
                        "message": error_data.get("message", f"Email sending failed with status {response.status_code}"),
                        "details": error_data
                    }
                }
    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "exception",
                "message": str(e)
            }
        }


def format_email_output(result: Dict[str, Any]) -> str:
    """Format email result as string for agent."""
    if result.get("success"):
        output = f"Email sent successfully\n"
        output += f"Message ID: {result.get('message_id', 'N/A')}\n"
        output += f"To: {result.get('to', 'N/A')}\n"
        output += f"Subject: {result.get('subject', 'N/A')}\n"
        output += f"Status: {result.get('status', 'N/A')}"
        return output
    else:
        error = result.get("error", {})
        return f"Email failed: {error.get('message', 'Unknown error')}"


def create_email_tool(config: Dict[str, Any]) -> Callable[[str], str]:
    """Create email tool function."""
    async def email_func_async(input_data: str) -> str:
        """Send an email."""
        # Parse input (string from agent or structured from node)
        if isinstance(input_data, str):
            # Parse string input
            email_data = parse_email_string(input_data)
        elif isinstance(input_data, dict):
            # Use structured input directly
            email_data = input_data
        else:
            return "Error: Invalid input format. Expected string or dict."
        
        # Get required fields
        to = email_data.get("to")
        subject = email_data.get("subject", "")
        body = email_data.get("body", "")
        
        # Get config
        provider = config.get("email_provider", "resend")
        user_id = config.get("_user_id")
        api_key = resolve_api_key(config, "resend_api_key", user_id=user_id) or config.get("resend_api_key", "")
        from_email = config.get("email_from", "")
        from_name = config.get("email_from_name")
        reply_to = config.get("email_reply_to")
        
        # Get optional fields from input
        cc = email_data.get("cc")
        bcc = email_data.get("bcc")
        html = email_data.get("html")
        
        if provider == "resend":
            result = await send_email_resend(
                to=to,
                subject=subject,
                body=body,
                from_email=from_email,
                api_key=api_key,
                from_name=from_name,
                reply_to=reply_to,
                cc=cc,
                bcc=bcc,
                html=html,
            )
            
            # Format output for agent (string)
            return format_email_output(result)
        else:
            return f"Error: Unknown email provider: {provider}"
    
    # Wrapper to make async function work with LangChain Tool
    def email_func(input_data: str) -> str:
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(email_func_async(input_data))
        except RuntimeError:
            # If no event loop, create one
            return asyncio.run(email_func_async(input_data))
    
    return email_func

