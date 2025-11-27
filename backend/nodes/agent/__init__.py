"""
Agent nodes for NodeAI.
"""

# Import LangChain agent (may fail if LangChain not available, but that's OK)
# We import it first but catch any errors so it doesn't block CrewAI
LANGCHAIN_AVAILABLE = False
LangChainAgentNode = None  # type: ignore
try:
    from backend.nodes.agent.langchain_agent import LangChainAgentNode  # noqa: F401
    LANGCHAIN_AVAILABLE = True
except (ImportError, Exception) as e:
    # LangChain not available - that's OK, node just won't be registered
    # Don't log here - let the langchain_agent module handle its own logging
    pass

# CrewAI node (optional - may fail if crewai not installed)
# Import directly from the module file to avoid going through this __init__.py
# which might have issues with LangChain import
CREWAI_AVAILABLE = False
try:
    # Import the module directly to trigger registration (registration happens at module level)
    import backend.nodes.agent.crewai_agent  # noqa: F401
    from backend.nodes.agent.crewai_agent import CrewAINode  # noqa: F401
    CREWAI_AVAILABLE = True
except (ImportError, Exception) as e:
    # CrewAI not available - that's OK
    # The crewai_agent module will log its own errors
    pass

# Set __all__ based on what's available
if LANGCHAIN_AVAILABLE and CREWAI_AVAILABLE:
    __all__ = ["LangChainAgentNode", "CrewAINode"]
elif LANGCHAIN_AVAILABLE:
    __all__ = ["LangChainAgentNode"]
elif CREWAI_AVAILABLE:
    __all__ = ["CrewAINode"]
else:
    __all__ = []

