"""
Agent nodes for NodeAI.
"""

from backend.nodes.agent.langchain_agent import LangChainAgentNode

# CrewAI node (optional - may fail if crewai not installed)
# Note: The node registers itself when imported, so we just need to import it
try:
    from backend.nodes.agent import crewai_agent  # noqa: F401
    # Import the class for __all__
    from backend.nodes.agent.crewai_agent import CrewAINode  # noqa: F401
    __all__ = ["LangChainAgentNode", "CrewAINode"]
except (ImportError, Exception) as e:
    # Silently fail if CrewAI not available
    __all__ = ["LangChainAgentNode"]

