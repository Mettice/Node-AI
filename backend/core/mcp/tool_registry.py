"""
MCP Tool Registry - Unified registry for all agent tools.

This registry combines:
1. MCP tools from external servers (Slack, Gmail, Airtable, etc.)
2. Internal NodeAI tools (blog_generator, lead_scorer, etc.)

Agents see a unified interface regardless of where the tool comes from.
"""

from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ToolSource(Enum):
    """Where a tool comes from."""
    MCP = "mcp"           # External MCP server
    INTERNAL = "internal"  # NodeAI built-in node


@dataclass
class MCPTool:
    """
    Unified tool definition that works with CrewAI.

    Can wrap either an MCP tool or an internal NodeAI node.
    """
    name: str
    description: str
    input_schema: Dict[str, Any]
    source: ToolSource
    server_name: Optional[str] = None  # For MCP tools
    node_type: Optional[str] = None    # For internal tools
    category: str = "general"

    def to_crewai_tool(self) -> "CrewAIMCPTool":
        """Convert to a CrewAI-compatible tool."""
        return CrewAIMCPTool(mcp_tool=self)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "source": self.source.value,
            "server_name": self.server_name,
            "node_type": self.node_type,
            "category": self.category,
        }


class BaseTool(ABC):
    """Base class for tools that agents can use."""

    name: str = ""
    description: str = ""

    @abstractmethod
    async def run(self, **kwargs) -> Any:
        """Execute the tool."""
        pass


class CrewAIMCPTool:
    """
    CrewAI-compatible wrapper for MCP tools.

    This allows MCP tools to be used directly with CrewAI agents.
    """

    def __init__(self, mcp_tool: MCPTool):
        self.mcp_tool = mcp_tool
        self.name = mcp_tool.name
        self.description = mcp_tool.description

    async def _run(self, **kwargs) -> str:
        """Execute the tool (async version)."""
        from backend.core.mcp.client import get_mcp_client

        if self.mcp_tool.source == ToolSource.MCP:
            # Call MCP server
            client = get_mcp_client()
            result = await client.call_tool(
                f"{self.mcp_tool.server_name}.{self.mcp_tool.name}",
                kwargs,
            )
            return str(result)

        elif self.mcp_tool.source == ToolSource.INTERNAL:
            # Call internal NodeAI node
            result = await self._execute_internal_node(kwargs)
            return str(result)

        return "Unknown tool source"

    async def _execute_internal_node(self, inputs: Dict[str, Any]) -> Any:
        """Execute an internal NodeAI node as a tool."""
        from backend.core.node_registry import NodeRegistry

        try:
            node_class = NodeRegistry.get(self.mcp_tool.node_type)
            node_instance = node_class()

            # Execute the node
            result = await node_instance.execute(
                inputs=inputs,
                config=inputs.get("_config", {}),
            )

            return result

        except Exception as e:
            logger.error(f"Error executing internal node {self.mcp_tool.node_type}: {e}")
            return {"error": str(e)}


class MCPToolRegistry:
    """
    Central registry for all tools available to agents.

    Provides a unified interface for:
    - Discovering available tools
    - Getting tool schemas
    - Executing tools (MCP or internal)
    """

    def __init__(self):
        self._tools: Dict[str, MCPTool] = {}
        self._internal_tools_registered = False

    def register_mcp_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        server_name: str,
        category: str = "integration",
    ) -> None:
        """Register an MCP tool from an external server."""
        tool = MCPTool(
            name=name,
            description=description,
            input_schema=input_schema,
            source=ToolSource.MCP,
            server_name=server_name,
            category=category,
        )
        full_name = f"{server_name}.{name}"
        self._tools[full_name] = tool
        logger.debug(f"Registered MCP tool: {full_name}")

    def register_internal_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        node_type: str,
        category: str = "ai",
    ) -> None:
        """Register an internal NodeAI node as a tool."""
        tool = MCPTool(
            name=name,
            description=description,
            input_schema=input_schema,
            source=ToolSource.INTERNAL,
            node_type=node_type,
            category=category,
        )
        self._tools[name] = tool
        logger.debug(f"Registered internal tool: {name}")

    def register_internal_nodes_as_tools(self) -> None:
        """
        Register all AI-native NodeAI nodes as tools.

        These are nodes that do actual AI work (not just integrations).
        """
        if self._internal_tools_registered:
            return

        # AI Content Generation Tools
        ai_tools = [
            {
                "name": "generate_blog_post",
                "description": "Generate a complete blog post on a given topic with SEO optimization",
                "node_type": "blog_generator",
                "category": "content",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "The topic to write about"},
                        "tone": {"type": "string", "description": "Writing tone (professional, casual, etc.)"},
                        "length": {"type": "string", "description": "Target length (short, medium, long)"},
                    },
                    "required": ["topic"],
                },
            },
            {
                "name": "generate_proposal",
                "description": "Generate a business proposal document",
                "node_type": "proposal_generator",
                "category": "content",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "client_name": {"type": "string", "description": "Client name"},
                        "project_description": {"type": "string", "description": "Project description"},
                        "budget_range": {"type": "string", "description": "Budget range"},
                    },
                    "required": ["project_description"],
                },
            },
            {
                "name": "generate_brand_content",
                "description": "Generate brand-consistent content",
                "node_type": "brand_generator",
                "category": "content",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "brand_info": {"type": "string", "description": "Brand information and guidelines"},
                        "content_type": {"type": "string", "description": "Type of content to generate"},
                    },
                    "required": ["brand_info"],
                },
            },
            # AI Analysis Tools
            {
                "name": "score_lead",
                "description": "Score a sales lead based on provided information",
                "node_type": "lead_scorer",
                "category": "sales",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "lead_data": {"type": "string", "description": "Lead information to analyze"},
                    },
                    "required": ["lead_data"],
                },
            },
            {
                "name": "summarize_meeting",
                "description": "Generate a summary of a meeting transcript",
                "node_type": "meeting_summarizer",
                "category": "productivity",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "transcript": {"type": "string", "description": "Meeting transcript"},
                    },
                    "required": ["transcript"],
                },
            },
            {
                "name": "analyze_data",
                "description": "Perform intelligent analysis on data",
                "node_type": "smart_data_analyzer",
                "category": "intelligence",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "string", "description": "Data to analyze (JSON or text)"},
                        "analysis_type": {"type": "string", "description": "Type of analysis to perform"},
                    },
                    "required": ["data"],
                },
            },
            {
                "name": "moderate_content",
                "description": "Check content for policy violations",
                "node_type": "content_moderator",
                "category": "safety",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Content to moderate"},
                    },
                    "required": ["content"],
                },
            },
            {
                "name": "generate_chart",
                "description": "Generate a chart/visualization from data",
                "node_type": "auto_chart_generator",
                "category": "intelligence",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "string", "description": "Data to visualize"},
                        "chart_type": {"type": "string", "description": "Type of chart"},
                    },
                    "required": ["data"],
                },
            },
            # RAG Tools
            {
                "name": "search_knowledge_base",
                "description": "Search a knowledge base using semantic search",
                "node_type": "vector_search",
                "category": "knowledge",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "index_id": {"type": "string", "description": "Knowledge base ID"},
                        "top_k": {"type": "integer", "description": "Number of results"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "chat_with_context",
                "description": "Chat with LLM using retrieved context",
                "node_type": "chat",
                "category": "llm",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "User query"},
                        "context": {"type": "string", "description": "Context to use"},
                    },
                    "required": ["query"],
                },
            },
        ]

        for tool_def in ai_tools:
            self.register_internal_tool(
                name=tool_def["name"],
                description=tool_def["description"],
                input_schema=tool_def["input_schema"],
                node_type=tool_def["node_type"],
                category=tool_def["category"],
            )

        self._internal_tools_registered = True
        logger.info(f"Registered {len(ai_tools)} internal NodeAI tools")

    def get_tool(self, name: str) -> Optional[MCPTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_tools_by_category(self, category: str) -> List[MCPTool]:
        """Get all tools in a category."""
        return [t for t in self._tools.values() if t.category == category]

    def get_tools_by_source(self, source: ToolSource) -> List[MCPTool]:
        """Get all tools from a specific source."""
        return [t for t in self._tools.values() if t.source == source]

    def get_all_tools(self) -> List[MCPTool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_crewai_tools(self, tool_names: Optional[List[str]] = None) -> List[CrewAIMCPTool]:
        """
        Get CrewAI-compatible tools.

        Args:
            tool_names: Specific tools to get (None = all)

        Returns:
            List of CrewAI-compatible tools
        """
        if tool_names:
            tools = [self._tools[n] for n in tool_names if n in self._tools]
        else:
            tools = list(self._tools.values())

        return [t.to_crewai_tool() for t in tools]

    def to_dict(self) -> Dict[str, Any]:
        """Convert registry to dictionary for API responses."""
        return {
            "tools": [t.to_dict() for t in self._tools.values()],
            "categories": list(set(t.category for t in self._tools.values())),
            "sources": {
                "mcp": len(self.get_tools_by_source(ToolSource.MCP)),
                "internal": len(self.get_tools_by_source(ToolSource.INTERNAL)),
            },
        }


# Singleton instance
_tool_registry: Optional[MCPToolRegistry] = None


def get_tool_registry() -> MCPToolRegistry:
    """Get the global tool registry instance."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = MCPToolRegistry()
        _tool_registry.register_internal_nodes_as_tools()
    return _tool_registry
