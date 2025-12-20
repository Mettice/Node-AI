"""
Sales & CRM Category Nodes - Sales & CRM Automation
"""

from .lead_enricher import LeadEnricherNode
from .call_summarizer import CallSummarizerNode
from .followup_writer import FollowupWriterNode
from .proposal_generator import ProposalGeneratorNode

__all__ = [
    "LeadEnricherNode",
    "CallSummarizerNode",
    "FollowupWriterNode", 
    "ProposalGeneratorNode",
]