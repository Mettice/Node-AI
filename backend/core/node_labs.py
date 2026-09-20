"""
Labs nodes: registered and runnable, but kept out of the node palette.

These are mostly thin prompt wrappers (one LLM call with a fixed prompt) that can be
built from the chat node instead. Hiding them keeps the palette focused on the core
RAG, evaluation and cost path without breaking saved workflows or the templates that
use them: they still run, and their settings still open.

Set SHOW_LABS_NODES=true to list them again, or call the node endpoints with
?include_labs=true.
"""

from typing import FrozenSet

LABS_NODE_TYPES: FrozenSet[str] = frozenset({
    # business
    "ab_test_analyzer",
    "cost_optimizer",
    "social_analyzer",
    "stripe_analytics",
    # content
    "blog_generator",
    "brand_generator",
    "podcast_transcriber",
    "social_scheduler",
    # developer
    "bug_triager",
    "docs_writer",
    "performance_monitor",
    # intelligence
    "auto_chart_generator",
    "lead_scorer",
    "meeting_summarizer",
    "smart_data_analyzer",
    # sales
    "call_summarizer",
    "followup_writer",
    "lead_enricher",
    "proposal_generator",
    # second agent framework; CrewAI covers this
    "langchain_agent",
    # app connectors: an MCP server covers these without a bespoke node each
    "airtable",
    "azure_blob",
    "database",
    "email",
    "google_drive",
    "google_sheets",
    "reddit",
    "s3",
    "slack",
    # needs bandit/safety, which are not installed in the deployed image
    "security_scanner",
})


def is_labs_node(node_type: str) -> bool:
    return node_type in LABS_NODE_TYPES


def show_labs_nodes() -> bool:
    """Whether Labs nodes should be listed, from settings."""
    from backend.config import settings

    return bool(getattr(settings, "show_labs_nodes", False))
