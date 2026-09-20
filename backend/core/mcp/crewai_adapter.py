"""
CrewAI Adapter - Bridge between MCP tools and CrewAI agents.

This module provides tools that CrewAI agents can use, backed by either:
1. MCP servers (external integrations)
2. Internal NodeAI nodes (AI capabilities)

The adapter handles:
- Converting MCP tool definitions to CrewAI-compatible tools
- Async/sync bridging for tool execution
- Error handling and logging
- Passing LLM config to internal AI tools
"""

import asyncio
import threading
from typing import Any, Dict, List, Optional, Type
from functools import wraps

from backend.core.mcp.client import get_mcp_client
from backend.core.mcp.tool_registry import (
    MCPTool,
    ToolSource,
    get_tool_registry,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Thread-local storage for LLM config
# This allows the agent to set its LLM config before tool execution
_llm_config_local = threading.local()


def set_current_llm_config(config: Dict[str, Any]) -> None:
    """Set the LLM config for internal tools to use."""
    _llm_config_local.config = config


def get_current_llm_config() -> Dict[str, Any]:
    """Get the current LLM config for internal tools."""
    return getattr(_llm_config_local, 'config', {})


# Try to import CrewAI's tool base class
try:
    from crewai.tools import BaseTool as CrewAIBaseTool
    from pydantic import BaseModel, Field
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    CrewAIBaseTool = object
    BaseModel = object
    Field = lambda **kwargs: None


def create_crewai_tool_class(mcp_tool: MCPTool) -> Type:
    """
    Dynamically create a CrewAI-compatible tool class from an MCPTool.

    Args:
        mcp_tool: The MCP tool definition

    Returns:
        A CrewAI tool class that can be instantiated
    """
    if not CREWAI_AVAILABLE:
        raise RuntimeError("CrewAI is not installed")

    # Create input schema model from MCP input_schema
    schema_props = mcp_tool.input_schema.get("properties", {})
    required = mcp_tool.input_schema.get("required", [])

    # Build field definitions for Pydantic model
    field_definitions = {}
    for prop_name, prop_def in schema_props.items():
        field_type = str  # Default to string
        if prop_def.get("type") == "integer":
            field_type = int
        elif prop_def.get("type") == "boolean":
            field_type = bool
        elif prop_def.get("type") == "number":
            field_type = float
        elif prop_def.get("type") == "array":
            field_type = list
        elif prop_def.get("type") == "object":
            field_type = dict

        description = prop_def.get("description", f"The {prop_name} parameter")

        if prop_name in required:
            field_definitions[prop_name] = (field_type, Field(description=description))
        else:
            field_definitions[prop_name] = (
                Optional[field_type],
                Field(default=None, description=description)
            )

    # Create the input model dynamically
    if field_definitions:
        # Create Pydantic model with fields
        input_model = type(
            f"{mcp_tool.name.title().replace('_', '')}Input",
            (BaseModel,),
            {"__annotations__": {k: v[0] for k, v in field_definitions.items()},
             **{k: v[1] for k, v in field_definitions.items()}}
        )
    else:
        # Empty input model
        input_model = type(
            f"{mcp_tool.name.title().replace('_', '')}Input",
            (BaseModel,),
            {}
        )

    # Create the tool class
    class DynamicMCPTool(CrewAIBaseTool):
        name: str = mcp_tool.name
        description: str = mcp_tool.description
        args_schema: Type[BaseModel] = input_model

        # Store MCP tool reference
        _mcp_tool: MCPTool = mcp_tool

        def _run(self, **kwargs) -> str:
            """Synchronous execution wrapper."""
            try:
                # Try to get existing event loop
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If loop is running, we're in an async context
                        # Create a new event loop in a new thread
                        import concurrent.futures
                        import threading
                        
                        def run_in_new_loop():
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                return new_loop.run_until_complete(self._async_run(**kwargs))
                            finally:
                                new_loop.close()
                        
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(run_in_new_loop)
                            return future.result(timeout=60)
                    else:
                        # Loop exists but not running, use it
                        return loop.run_until_complete(self._async_run(**kwargs))
                except RuntimeError:
                    # No event loop exists (e.g., called from thread pool)
                    # Create a new event loop and run in it
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(self._async_run(**kwargs))
                    finally:
                        new_loop.close()
            except Exception as e:
                logger.error(f"Error executing tool {self.name}: {e}", exc_info=True)
                return f"Error: {str(e)}"

        async def _async_run(self, **kwargs) -> str:
            """Async execution of the tool."""
            mcp_tool = self._mcp_tool

            if mcp_tool.source == ToolSource.MCP:
                # Call MCP server
                try:
                    client = get_mcp_client()
                    
                    # Check if server is actually connected in the MCP client (source of truth)
                    # The client maintains the actual connection state
                    if mcp_tool.server_name not in client._processes:
                        # Server not connected in client - check manager for API key info
                        from backend.core.mcp.server_manager import get_server_manager
                        manager = get_server_manager()
                        connection = manager.get_connection(mcp_tool.server_name)
                        
                        if connection and connection.env.get("AIRTABLE_API_KEY", "").strip() == "":
                            return f"Error: Airtable API key is not configured. Please set AIRTABLE_API_KEY in the MCP server settings."
                        
                        return f"Error: MCP server '{mcp_tool.server_name}' is not connected. Please connect it via /api/v1/mcp/servers/{mcp_tool.server_name}/connect"
                    
                    # Check if process is still alive
                    process = client._processes.get(mcp_tool.server_name)
                    if process and process.poll() is not None:
                        return f"Error: MCP server '{mcp_tool.server_name}' process has exited. Please reconnect it."
                    
                    # Check for missing API keys (common issue) - get from manager
                    from backend.core.mcp.server_manager import get_server_manager
                    manager = get_server_manager()
                    connection = manager.get_connection(mcp_tool.server_name)
                    if connection and mcp_tool.server_name == "airtable" and connection.env.get("AIRTABLE_API_KEY", "").strip() == "":
                        return f"Error: Airtable API key is not configured. Please set AIRTABLE_API_KEY in the MCP server settings."
                    
                    result = await client.call_tool(
                        f"{mcp_tool.server_name}.{mcp_tool.name}",
                        kwargs,
                    )

                    # Log the raw result for debugging
                    logger.debug(f"MCP tool {mcp_tool.name} raw result: {result}")

                    # Format result
                    if isinstance(result, dict):
                        if "error" in result:
                            error_msg = result.get("error", "Unknown error")
                            logger.error(f"MCP tool {mcp_tool.name} returned error: {error_msg}")
                            return f"Error calling {mcp_tool.name}: {error_msg}"
                        if "content" in result:
                            # MCP returns content as array of content blocks
                            content = result["content"]
                            if isinstance(content, list):
                                texts = [
                                    c.get("text", str(c))
                                    for c in content
                                    if isinstance(c, dict)
                                ]
                                formatted_result = "\n".join(texts) if texts else str(result)
                                logger.debug(f"MCP tool {mcp_tool.name} formatted result: {formatted_result[:200]}")
                                return formatted_result
                        # If result is empty or unexpected format, log it
                        if not result or result == {}:
                            logger.warning(f"MCP tool {mcp_tool.name} returned empty result")
                            return f"Error: {mcp_tool.name} returned empty result. Check MCP server logs."
                        formatted_result = str(result)
                        logger.debug(f"MCP tool {mcp_tool.name} result: {formatted_result[:200]}")
                        return formatted_result
                    
                    # Non-dict result
                    formatted_result = str(result)
                    logger.debug(f"MCP tool {mcp_tool.name} non-dict result: {formatted_result[:200]}")
                    return formatted_result
                except Exception as e:
                    logger.error(f"Error executing MCP tool {mcp_tool.name}: {e}", exc_info=True)
                    return f"Error: Failed to execute {mcp_tool.name}. {str(e)}"

            elif mcp_tool.source == ToolSource.INTERNAL:
                # Call internal NodeAI node
                result = await self._execute_internal_node(kwargs)
                return str(result)

            return "Unknown tool source"

        async def _execute_internal_node(self, inputs: Dict[str, Any]) -> Any:
            """Execute an internal NodeAI node with the agent's LLM config."""
            from backend.core.node_registry import NodeRegistry

            try:
                node_type = self._mcp_tool.node_type
                node_class = NodeRegistry.get(node_type)
                node_instance = node_class()

                # Extract config from inputs if present, or start fresh
                config = inputs.pop("_config", {})

                # ===========================================
                # INHERIT LLM CONFIG FROM AGENT
                # ===========================================
                # Get the current LLM config set by the agent
                llm_config = get_current_llm_config()
                if llm_config:
                    # Map agent's LLM config to node config format
                    provider = llm_config.get("provider", "openai")
                    config["provider"] = provider

                    if provider == "openai":
                        config["openai_model"] = llm_config.get("model", "gpt-4o-mini")
                        if llm_config.get("api_key"):
                            config["openai_api_key"] = llm_config["api_key"]
                    elif provider == "anthropic":
                        config["anthropic_model"] = llm_config.get("model", "claude-sonnet-4-20250514")
                        if llm_config.get("api_key"):
                            config["anthropic_api_key"] = llm_config["api_key"]
                    elif provider in ("gemini", "google"):
                        config["gemini_model"] = llm_config.get("model", "gemini-2.0-flash")
                        if llm_config.get("api_key"):
                            config["gemini_api_key"] = llm_config["api_key"]

                    if llm_config.get("temperature"):
                        config["temperature"] = llm_config["temperature"]

                    logger.debug(f"Internal tool '{node_type}' using LLM config: provider={provider}")

                # Execute the node
                result = await node_instance.execute(
                    inputs=inputs,
                    config=config,
                )

                # Extract the main output
                if isinstance(result, dict):
                    # Try common output fields
                    for field in ["output", "text", "content", "result", "summary"]:
                        if field in result:
                            return result[field]
                    return result

                return result

            except Exception as e:
                logger.error(f"Error executing internal node {self._mcp_tool.node_type}: {e}")
                return f"Error: {str(e)}"

    # Set class name for debugging
    DynamicMCPTool.__name__ = f"MCP_{mcp_tool.name}"
    DynamicMCPTool.__qualname__ = f"MCP_{mcp_tool.name}"

    return DynamicMCPTool


def get_crewai_tools(
    tool_names: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
    sources: Optional[List[ToolSource]] = None,
) -> List[Any]:
    """
    Get CrewAI-compatible tools.

    Args:
        tool_names: Specific tool names to include
        categories: Categories to include
        sources: Sources to include (MCP, INTERNAL)

    Returns:
        List of instantiated CrewAI tools
    """
    if not CREWAI_AVAILABLE:
        logger.warning("CrewAI not available, returning empty tool list")
        return []

    registry = get_tool_registry()
    all_tools = registry.get_all_tools()

    # Filter by criteria
    filtered = all_tools

    if tool_names:
        # Match by both short name and full name (server.tool_name)
        filtered = []
        for t in all_tools:
            short_name = t.name
            full_name = f"{t.server_name}.{t.name}" if t.server_name else t.name
            if short_name in tool_names or full_name in tool_names:
                filtered.append(t)
        
        if len(filtered) < len(tool_names):
            # Try to auto-connect MCP servers that might have these tools
            found_names = {t.name for t in filtered}
            missing = set(tool_names) - found_names
            
            # Try to connect MCP servers that might provide these tools
            try:
                from backend.core.mcp.server_manager import get_server_manager
                manager = get_server_manager()
                
                # Check if any configured but disconnected servers might have these tools
                for server_name, conn in manager.get_connections().items():
                    if conn.enabled and not conn.connected:
                        # Try connecting to see if it provides the missing tools
                        try:
                            import asyncio
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                # If loop is running, create a task
                                asyncio.create_task(manager.connect_server(server_name))
                            else:
                                # If loop not running, run it
                                asyncio.run(manager.connect_server(server_name))
                            
                            # Refresh tools after connection
                            registry = get_tool_registry()
                            all_tools = registry.get_all_tools()
                            
                            # Re-filter with newly connected tools
                            for t in all_tools:
                                if t not in filtered:
                                    short_name = t.name
                                    full_name = f"{t.server_name}.{t.name}" if t.server_name else t.name
                                    if short_name in missing or full_name in missing:
                                        filtered.append(t)
                                        found_names.add(t.name)
                            
                            missing = set(tool_names) - found_names
                            if not missing:
                                logger.info(f"Auto-connected MCP server '{server_name}' and found requested tools")
                                break
                        except Exception as e:
                            logger.debug(f"Failed to auto-connect {server_name}: {e}")
                            continue
            except Exception as e:
                logger.debug(f"Failed to auto-connect MCP servers: {e}")
            
            if missing:
                available_tools = [f"{t.server_name}.{t.name}" if t.server_name else t.name for t in all_tools]
                
                # Check if MCP servers are disconnected
                try:
                    from backend.core.mcp.server_manager import get_server_manager
                    manager = get_server_manager()
                    disconnected = [
                        name for name, conn in manager.get_connections().items()
                        if conn.enabled and not conn.connected
                    ]
                    if disconnected:
                        logger.warning(
                            f"Requested tools not found: {missing}. "
                            f"MCP servers are disconnected: {disconnected}. "
                            f"Connect them via /api/v1/mcp/servers/{{server_name}}/connect or use /api/v1/mcp/connect-all"
                        )
                    else:
                        logger.warning(
                            f"Some requested tools not found: {missing}. "
                            f"Available tools: {available_tools[:10]}..."  # Show first 10
                        )
                except Exception:
                    logger.warning(
                        f"Some requested tools not found: {missing}. "
                        f"Available tools: {available_tools[:10]}..."  # Show first 10
                    )

    if categories:
        filtered = [t for t in filtered if t.category in categories]

    if sources:
        filtered = [t for t in filtered if t.source in sources]

    # Create CrewAI tool instances
    crewai_tools = []
    for mcp_tool in filtered:
        try:
            tool_class = create_crewai_tool_class(mcp_tool)
            crewai_tools.append(tool_class())
        except Exception as e:
            logger.error(f"Failed to create CrewAI tool for {mcp_tool.name}: {e}")

    logger.info(f"Created {len(crewai_tools)} CrewAI tools from {len(filtered)} filtered tools")
    if tool_names and len(crewai_tools) == 0:
        available = [f"{t.server_name}.{t.name}" if t.server_name else t.name for t in all_tools]
        logger.error(f"No tools found matching {tool_names}. Available: {available}")
    
    return crewai_tools


def get_all_available_tools_for_crewai() -> List[Any]:
    """
    Get all available tools for CrewAI agents.

    This is the main function to call when setting up agent tools.
    Returns both MCP tools (external) and internal NodeAI tools.
    """
    return get_crewai_tools()


def get_internal_ai_tools() -> List[Any]:
    """Get only internal NodeAI AI tools."""
    return get_crewai_tools(sources=[ToolSource.INTERNAL])


def get_mcp_integration_tools() -> List[Any]:
    """Get only MCP integration tools."""
    return get_crewai_tools(sources=[ToolSource.MCP])
