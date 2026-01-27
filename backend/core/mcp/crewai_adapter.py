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
                # Run async code in event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If already in async context, create a new task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            self._async_run(**kwargs)
                        )
                        return future.result(timeout=60)
                else:
                    return loop.run_until_complete(self._async_run(**kwargs))
            except Exception as e:
                logger.error(f"Error executing tool {self.name}: {e}")
                return f"Error: {str(e)}"

        async def _async_run(self, **kwargs) -> str:
            """Async execution of the tool."""
            mcp_tool = self._mcp_tool

            if mcp_tool.source == ToolSource.MCP:
                # Call MCP server
                client = get_mcp_client()
                result = await client.call_tool(
                    f"{mcp_tool.server_name}.{mcp_tool.name}",
                    kwargs,
                )

                # Format result
                if isinstance(result, dict):
                    if "error" in result:
                        return f"Error: {result['error']}"
                    if "content" in result:
                        # MCP returns content as array of content blocks
                        content = result["content"]
                        if isinstance(content, list):
                            texts = [
                                c.get("text", str(c))
                                for c in content
                                if isinstance(c, dict)
                            ]
                            return "\n".join(texts) if texts else str(result)
                    return str(result)
                return str(result)

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
        filtered = [t for t in filtered if t.name in tool_names]

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

    logger.info(f"Created {len(crewai_tools)} CrewAI tools")
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
