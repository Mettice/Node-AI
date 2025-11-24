"""
Tool Node for NodeAI.

This node defines and registers tools that can be used by Agent nodes.
Tools can be: calculator, web_search, code_execution, database_query, etc.
"""

from typing import Any, Dict, List, Optional
import json
import subprocess
import sys
import io
import contextlib
import math
import re
import httpx
import asyncio
from urllib.parse import urljoin

from backend.nodes.base import BaseNode
from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.core.secret_resolver import resolve_api_key
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Import modular tool implementations
try:
    from backend.nodes.tools.tools import (
        get_calculator_schema,
        create_calculator_tool,
        get_web_search_schema,
        create_web_search_tool,
        get_web_scraping_schema,
        create_web_scraping_tool,
        get_rss_feed_schema,
        create_rss_feed_tool,
        get_s3_storage_schema,
        create_s3_storage_tool,
        get_email_schema,
        create_email_tool,
        get_code_execution_schema,
        create_code_execution_tool,
        get_database_query_schema,
        create_database_query_tool,
        get_api_call_schema,
        create_api_call_tool,
        get_custom_schema,
        create_custom_tool,
    )
    MODULAR_TOOLS_AVAILABLE = True
except ImportError:
    MODULAR_TOOLS_AVAILABLE = False
    logger.warning("Modular tool implementations not available, using inline implementations")

# Global tool registry - stores tool definitions
_tool_registry: Dict[str, Dict[str, Any]] = {}


class ToolNode(BaseNode):
    """
    Tool Node for defining tools that agents can use.
    
    Tools are registered and can be connected to Agent nodes.
    """

    node_type = "tool"
    name = "Tool"
    description = "Define a tool that agents can use (calculator, web search, code execution, etc.)"
    category = "tool"

    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the tool node.
        
        This registers the tool definition so it can be used by agents.
        """
        node_id = config.get("_node_id", "tool")
        tool_type = config.get("tool_type", "calculator")
        tool_name = config.get("tool_name", tool_type)
        tool_description = config.get("tool_description", f"{tool_type} tool")
        
        await self.stream_progress(node_id, 0.1, f"Registering {tool_type} tool: {tool_name}...")
        
        # Create tool definition
        tool_def = {
            "type": tool_type,
            "name": tool_name,
            "description": tool_description,
            "config": config,
        }
        
        await self.stream_progress(node_id, 0.5, "Creating tool definition...")
        
        # Register tool
        tool_id = config.get("tool_id") or f"{tool_type}_{id(self)}"
        _tool_registry[tool_id] = tool_def
        
        logger.info(f"Registered tool: {tool_name} (type: {tool_type}, id: {tool_id})")
        
        await self.stream_progress(node_id, 0.8, f"Tool registered successfully (ID: {tool_id})")
        
        # Return tool output with unique key to avoid overwrites when multiple tools connect to same node
        # Use tool_id as key so agent can discover all tools
        result = {
            f"tool_{tool_id}": {
                "tool_id": tool_id,
                "tool_name": tool_name,
                "tool_type": tool_type,
                "tool_description": tool_description,
                "registered": True,
            },
            # Also include at root level for backward compatibility
            "tool_id": tool_id,
            "tool_name": tool_name,
            "tool_type": tool_type,
            "tool_description": tool_description,
            "registered": True,
        }
        
        await self.stream_progress(node_id, 1.0, f"Tool '{tool_name}' ready for use")
        
        return result

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool configuration."""
        properties = {
            "tool_type": {
                "type": "string",
                "enum": ["calculator", "web_search", "web_scraping", "rss_feed", "s3_storage", "code_execution", "database_query", "api_call", "email", "custom"],
                "default": "calculator",
                "title": "Tool Type",
                "description": "Type of tool to create",
            },
            "tool_name": {
                "type": "string",
                "default": "calculator",
                "title": "Tool Name",
                "description": "Unique name for this tool",
            },
            "tool_description": {
                "type": "string",
                "default": "Calculator tool for mathematical expressions",
                "title": "Tool Description",
                "description": "Description of what this tool does (for agent to understand)",
            },
            "tool_id": {
                "type": "string",
                "title": "Tool ID",
                "description": "Optional unique identifier (auto-generated if not provided)",
            },
        }
        
        # Add tool-specific schemas from modules
        if MODULAR_TOOLS_AVAILABLE:
            if get_calculator_schema:
                properties.update(get_calculator_schema())
            if get_web_search_schema:
                properties.update(get_web_search_schema())
            if get_web_scraping_schema:
                properties.update(get_web_scraping_schema())
            if get_rss_feed_schema:
                properties.update(get_rss_feed_schema())
            if get_s3_storage_schema:
                properties.update(get_s3_storage_schema())
            if get_email_schema:
                properties.update(get_email_schema())
            if get_code_execution_schema:
                properties.update(get_code_execution_schema())
            if get_database_query_schema:
                properties.update(get_database_query_schema())
            if get_api_call_schema:
                properties.update(get_api_call_schema())
            if get_custom_schema:
                properties.update(get_custom_schema())
        
        return {
            "type": "object",
            "properties": properties,
            "required": ["tool_type"],
        }

    @staticmethod
    def get_tool_definition(tool_id: str) -> Optional[Dict[str, Any]]:
        """Get a tool definition by ID."""
        return _tool_registry.get(tool_id)
    
    @staticmethod
    def list_all_tools() -> List[Dict[str, Any]]:
        """List all registered tools."""
        return list(_tool_registry.values())
    
    @staticmethod
    def create_langchain_tool(tool_def: Dict[str, Any]):
        """Convert tool definition to LangChain Tool object."""
        try:
            from langchain.tools import Tool
            
            tool_type = tool_def.get("type")
            tool_name = tool_def.get("name", tool_type)
            tool_description = tool_def.get("description", "")
            config = tool_def.get("config", {})
            
            # Use modular implementations if available
            if tool_type == "calculator" and MODULAR_TOOLS_AVAILABLE and create_calculator_tool:
                calculator_func = create_calculator_tool(config)
                return Tool(
                    name=tool_name,
                    func=calculator_func,
                    description=tool_description,
                )
            
            elif tool_type == "web_search" and MODULAR_TOOLS_AVAILABLE and create_web_search_tool:
                search_func = create_web_search_tool(config)
                return Tool(
                    name=tool_name,
                    func=search_func,
                    description=tool_description,
                )
            
            elif tool_type == "web_scraping" and MODULAR_TOOLS_AVAILABLE and create_web_scraping_tool:
                scraping_func = create_web_scraping_tool(config)
                return Tool(
                    name=tool_name,
                    func=scraping_func,
                    description=tool_description or "Scrape and extract clean text content from web pages. Input: URL string",
                )
            
            elif tool_type == "rss_feed" and MODULAR_TOOLS_AVAILABLE and create_rss_feed_tool:
                rss_feed_func = create_rss_feed_tool(config)
                return Tool(
                    name=tool_name,
                    func=rss_feed_func,
                    description=tool_description or "Fetch and parse RSS/Atom feeds. Input: Feed URL string",
                )
            
            elif tool_type == "s3_storage" and MODULAR_TOOLS_AVAILABLE and create_s3_storage_tool:
                s3_storage_func = create_s3_storage_tool(config)
                action = config.get("s3_action", "list")
                action_descriptions = {
                    "list": "List objects in S3 bucket. Input: optional prefix (e.g., 'folder/')",
                    "download": "Download object from S3. Input: object key (e.g., 'path/to/file.txt')",
                    "upload": "Upload content to S3. Input: JSON string with 'key' and 'content'",
                    "delete": "Delete object from S3. Input: object key (e.g., 'path/to/file.txt')",
                    "get_url": "Get presigned URL for object. Input: object key (e.g., 'path/to/file.txt')",
                }
                return Tool(
                    name=tool_name,
                    func=s3_storage_func,
                    description=tool_description or f"S3 storage operations. {action_descriptions.get(action, 'S3 storage tool')}",
                )
            
            elif tool_type == "email" and MODULAR_TOOLS_AVAILABLE and create_email_tool:
                email_func = create_email_tool(config)
                return Tool(
                    name=tool_name,
                    func=email_func,
                    description=tool_description or "Send an email. Input format: 'to: email@example.com, subject: Subject, body: Message body'",
                )
            
            elif tool_type == "code_execution" and MODULAR_TOOLS_AVAILABLE and create_code_execution_tool:
                code_exec_func = create_code_execution_tool(config)
                return Tool(
                    name=tool_name,
                    func=code_exec_func,
                    description=tool_description,
                )
            
            elif tool_type == "database_query" and MODULAR_TOOLS_AVAILABLE and create_database_query_tool:
                db_query_func = create_database_query_tool(config)
                return Tool(
                    name=tool_name,
                    func=db_query_func,
                    description=tool_description,
                )
            
            elif tool_type == "api_call" and MODULAR_TOOLS_AVAILABLE and create_api_call_tool:
                api_call_func = create_api_call_tool(config)
                return Tool(
                    name=tool_name,
                    func=api_call_func,
                    description=tool_description,
                )
            
            elif tool_type == "custom" and MODULAR_TOOLS_AVAILABLE and create_custom_tool:
                custom_func = create_custom_tool(config)
                return Tool(
                    name=tool_name,
                    func=custom_func,
                    description=tool_description,
                )
            
            # Fallback to inline implementations for tools not yet modularized
            elif tool_type == "calculator":
                # Inline calculator implementation (fallback)
                def calculator_func(expression: str) -> str:
                    """Evaluate a mathematical expression safely."""
                    try:
                        expression = expression.strip()
                        allowed_ops = config.get("calculator_allowed_operations", "all")
                        if allowed_ops == "basic":
                            allowed_chars = set("0123456789+-*/()., ")
                        else:
                            allowed_chars = set("0123456789+-*/()., ^sqrtlogsinco")
                        if not all(c in allowed_chars for c in expression):
                            return "Error: Invalid characters in expression"
                        expression = expression.replace("^", "**")
                        expression = re.sub(r'sqrt\(([^)]+)\)', r'math.sqrt(\1)', expression)
                        expression = re.sub(r'log\(([^)]+)\)', r'math.log(\1)', expression)
                        expression = re.sub(r'sin\(([^)]+)\)', r'math.sin(\1)', expression)
                        expression = re.sub(r'cos\(([^)]+)\)', r'math.cos(\1)', expression)
                        safe_dict = {"__builtins__": {}, "math": math}
                        result = eval(expression, safe_dict)
                        if isinstance(result, float):
                            if result.is_integer():
                                return str(int(result))
                            return f"{result:.6f}".rstrip('0').rstrip('.')
                        return str(result)
                    except Exception as e:
                        return f"Error: {str(e)}"
                return Tool(name=tool_name, func=calculator_func, description=tool_description)
            
            elif tool_type == "web_search":
                async def search_func_async(query: str) -> str:
                    """Search the web for information."""
                    provider = config.get("web_search_provider", "duckduckgo")
                    user_id = config.get("_user_id")
                    api_key = resolve_api_key(config, "web_search_api_key", user_id=user_id) or config.get("web_search_api_key", "")
                    serper_api_key = resolve_api_key(config, "serper_api_key", user_id=user_id) or config.get("serper_api_key", "") or api_key
                    perplexity_api_key = resolve_api_key(config, "perplexity_api_key", user_id=user_id) or config.get("perplexity_api_key", "") or api_key
                    
                    try:
                        if provider == "duckduckgo":
                            # Use DuckDuckGo (no API key needed)
                            try:
                                from duckduckgo_search import DDGS
                                with DDGS() as ddgs:
                                    results = list(ddgs.text(query, max_results=5))
                                    if results:
                                        formatted = "\n".join([
                                            f"{i+1}. {r.get('title', 'No title')}\n   {r.get('body', 'No description')}\n   {r.get('href', 'No URL')}"
                                            for i, r in enumerate(results)
                                        ])
                                        return formatted
                                    return f"No results found for: {query}"
                            except ImportError:
                                return f"Error: duckduckgo-search package not installed. Install with: pip install duckduckgo-search"
                        
                        elif provider == "serpapi":
                            if not api_key:
                                return "Error: API key required for SerpAPI"
                            async with httpx.AsyncClient() as client:
                                response = await client.get(
                                    "https://serpapi.com/search",
                                    params={"q": query, "api_key": api_key}
                                )
                                if response.status_code == 200:
                                    data = response.json()
                                    results = data.get("organic_results", [])[:5]
                                    formatted = "\n".join([
                                        f"{i+1}. {r.get('title', 'No title')}\n   {r.get('snippet', 'No description')}\n   {r.get('link', 'No URL')}"
                                        for i, r in enumerate(results)
                                    ])
                                    return formatted
                                return f"Error: Search failed with status {response.status_code}"
                        
                        elif provider == "brave":
                            if not api_key:
                                return "Error: API key required for Brave Search"
                            async with httpx.AsyncClient() as client:
                                response = await client.get(
                                    "https://api.search.brave.com/res/v1/web/search",
                                    params={"q": query},
                                    headers={"X-Subscription-Token": api_key}
                                )
                                if response.status_code == 200:
                                    data = response.json()
                                    results = data.get("web", {}).get("results", [])[:5]
                                    formatted = "\n".join([
                                        f"{i+1}. {r.get('title', 'No title')}\n   {r.get('description', 'No description')}\n   {r.get('url', 'No URL')}"
                                        for i, r in enumerate(results)
                                    ])
                                    return formatted
                                return f"Error: Search failed with status {response.status_code}"
                        
                        elif provider == "serper":
                            if not serper_api_key:
                                return "Error: API key required for Serper"
                            async with httpx.AsyncClient() as client:
                                response = await client.post(
                                    "https://google.serper.dev/search",
                                    json={"q": query, "num": 10},
                                    headers={
                                        "X-API-KEY": serper_api_key,
                                        "Content-Type": "application/json"
                                    }
                                )
                                if response.status_code == 200:
                                    data = response.json()
                                    results = data.get("organic", [])[:10]
                                    if results:
                                        formatted = "\n".join([
                                            f"{i+1}. {r.get('title', 'No title')}\n   {r.get('snippet', 'No description')}\n   {r.get('link', 'No URL')}"
                                            for i, r in enumerate(results)
                                        ])
                                        return formatted
                                    return f"No results found for: {query}"
                                return f"Error: Search failed with status {response.status_code}: {response.text[:200]}"
                        
                        elif provider == "perplexity":
                            if not perplexity_api_key:
                                return "Error: API key required for Perplexity"
                            async with httpx.AsyncClient() as client:
                                response = await client.post(
                                    "https://api.perplexity.ai/chat/completions",
                                    json={
                                        "model": "sonar",
                                        "messages": [
                                            {
                                                "role": "system",
                                                "content": "You are a helpful assistant that provides accurate, up-to-date information from the web."
                                            },
                                            {
                                                "role": "user",
                                                "content": query
                                            }
                                        ],
                                        "temperature": 0.2,
                                        "max_tokens": 1000
                                    },
                                    headers={
                                        "Authorization": f"Bearer {perplexity_api_key}",
                                        "Content-Type": "application/json"
                                    },
                                    timeout=30.0
                                )
                                if response.status_code == 200:
                                    data = response.json()
                                    answer = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                                    citations = data.get("citations", [])
                                    
                                    if answer:
                                        result = f"Answer: {answer}\n\n"
                                        if citations:
                                            result += "Sources:\n"
                                            result += "\n".join([f"- {cite}" for cite in citations[:5]])
                                        return result
                                    return "No answer generated"
                                return f"Error: Search failed with status {response.status_code}: {response.text[:200]}"
                        
                        return f"Error: Unknown search provider: {provider}"
                    except Exception as e:
                        return f"Error: {str(e)}"
                
                # Wrapper to make async function work with LangChain Tool
                def search_func(query: str) -> str:
                    try:
                        loop = asyncio.get_event_loop()
                        return loop.run_until_complete(search_func_async(query))
                    except RuntimeError:
                        # If no event loop, create one
                        return asyncio.run(search_func_async(query))
                
                return Tool(
                    name=tool_name,
                    func=search_func,
                    description=tool_description,
                )
            
        
        except ImportError:
            logger.warning("LangChain not available for tool conversion")
            return None


# Register the node
NodeRegistry.register(
    ToolNode.node_type,
    ToolNode,
    ToolNode().get_metadata(),
)

