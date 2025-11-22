"""
API call tool implementation.
"""

import json
import httpx
import asyncio
from typing import Dict, Any, Callable
from urllib.parse import urljoin


def get_api_call_schema() -> Dict[str, Any]:
    """Get schema fields for API call tool."""
    return {
        "api_call_url": {
            "type": "string",
            "title": "API URL",
            "description": "Base URL for API calls",
        },
        "api_call_method": {
            "type": "string",
            "enum": ["GET", "POST", "PUT", "DELETE"],
            "default": "GET",
            "title": "HTTP Method",
            "description": "HTTP method for API calls",
        },
        "api_call_headers": {
            "type": "string",
            "title": "Headers (JSON)",
            "description": "HTTP headers as JSON string",
        },
    }


def create_api_call_tool(config: Dict[str, Any]) -> Callable[[str], str]:
    """Create API call tool function."""
    base_url = config.get("api_call_url", "")
    method = config.get("api_call_method", "GET")
    headers_str = config.get("api_call_headers", "{}")
    
    # Parse headers
    try:
        headers = json.loads(headers_str) if headers_str else {}
    except json.JSONDecodeError:
        headers = {}
    
    async def api_call_func_async(endpoint: str) -> str:
        """Make an API call."""
        if not base_url:
            return "Error: API URL is required"
        
        try:
            # Construct full URL
            full_url = urljoin(base_url.rstrip('/') + '/', endpoint.lstrip('/'))
            
            # Make request
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == "GET":
                    response = await client.get(full_url, headers=headers)
                elif method == "POST":
                    response = await client.post(full_url, headers=headers)
                elif method == "PUT":
                    response = await client.put(full_url, headers=headers)
                elif method == "DELETE":
                    response = await client.delete(full_url, headers=headers)
                else:
                    return f"Error: Unsupported HTTP method: {method}"
                
                # Format response
                try:
                    response_data = response.json()
                    return json.dumps(response_data, indent=2)
                except:
                    return f"Status: {response.status_code}\n\n{response.text[:1000]}"
                    
        except httpx.TimeoutException:
            return "Error: Request timed out"
        except Exception as e:
            return f"Error: {str(e)}"
    
    # Wrapper to make async function work with LangChain Tool
    def api_call_func(endpoint: str) -> str:
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(api_call_func_async(endpoint))
        except RuntimeError:
            return asyncio.run(api_call_func_async(endpoint))
    
    return api_call_func

