"""
Proposal Generator Node - Client info → custom proposals
"""

import json
from typing import Any, Dict, List
from backend.nodes.base import BaseNode
from backend.nodes.intelligence.llm_mixin import LLMConfigMixin
from backend.core.exceptions import NodeValidationError
from backend.core.node_registry import NodeRegistry


class ProposalGeneratorNode(BaseNode, LLMConfigMixin):
    node_type = "proposal_generator"
    name = "Proposal Generator"
    description = "Generates custom proposals from client information"
    category = "sales"

    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        # Accept multiple input formats - can be dict or JSON string
        client_info_raw = (
            inputs.get("client_info") or 
            inputs.get("data") or 
            inputs.get("text") or 
            inputs.get("content") or
            inputs.get("output") or
            {}
        )
        
        # Parse if it's a string (JSON)
        if isinstance(client_info_raw, str):
            try:
                client_info = json.loads(client_info_raw)
            except json.JSONDecodeError:
                # If not JSON, create basic client info from text
                client_info = {"company_name": client_info_raw, "description": client_info_raw}
        elif isinstance(client_info_raw, dict):
            client_info = client_info_raw
        else:
            client_info = {}
        
        proposal_type = config.get("proposal_type", "standard")
        include_pricing = config.get("include_pricing", True)
        
        if not client_info:
            raise NodeValidationError("Client information is required. Connect a text_input node with JSON data or provide client_info in config.")

        proposal_content = self._generate_proposal_content(client_info, proposal_type)
        pricing_section = self._generate_pricing(client_info) if include_pricing else None
        timeline = self._generate_implementation_timeline(client_info)

        return {
            "proposal_content": proposal_content,
            "pricing_section": pricing_section,
            "implementation_timeline": timeline,
            "proposal_summary": self._generate_executive_summary(client_info),
            "next_steps": self._outline_next_steps(client_info)
        }

    def _generate_proposal_content(self, client_info: Dict, proposal_type: str) -> Dict[str, Any]:
        """Generate main proposal content"""
        
        company_name = client_info.get("company_name", "Your Company")
        industry = client_info.get("industry", "Technology")
        pain_points = client_info.get("pain_points", ["Manual processes", "Data silos"])
        
        return {
            "title": f"Custom Solution Proposal for {company_name}",
            "executive_summary": f"This proposal outlines a tailored solution to address {company_name}'s specific needs in {industry}.",
            "problem_statement": f"Based on our discussions, {company_name} faces challenges with: " + ", ".join(pain_points),
            "proposed_solution": {
                "overview": "Our AI-powered platform will streamline your operations and eliminate manual bottlenecks",
                "key_features": [
                    "Automated workflow processing",
                    "Real-time analytics dashboard", 
                    "Integration with existing systems",
                    "24/7 support and monitoring"
                ],
                "benefits": [
                    "50% reduction in manual processing time",
                    "Improved data accuracy and consistency",
                    "Enhanced operational visibility", 
                    "Scalable solution for future growth"
                ]
            },
            "implementation_approach": "Phased rollout starting with pilot program",
            "success_metrics": [
                "Process automation rate",
                "Time savings achieved",
                "User adoption rate",
                "ROI measurement"
            ]
        }

    def _generate_pricing(self, client_info: Dict) -> Dict[str, Any]:
        """Generate pricing structure"""
        
        company_size = client_info.get("company_size", "medium")
        
        # Pricing based on company size
        pricing_tiers = {
            "small": {"setup": 5000, "monthly": 2500},
            "medium": {"setup": 10000, "monthly": 5000}, 
            "large": {"setup": 20000, "monthly": 10000},
            "enterprise": {"setup": 50000, "monthly": 25000}
        }
        
        pricing = pricing_tiers.get(company_size, pricing_tiers["medium"])
        
        return {
            "pricing_model": "Setup fee + Monthly subscription",
            "setup_fee": pricing["setup"],
            "monthly_subscription": pricing["monthly"],
            "annual_discount": "15% discount for annual payment",
            "total_year_one": pricing["setup"] + (pricing["monthly"] * 12 * 0.85),  # With annual discount
            "payment_terms": "Net 30 days",
            "included_services": [
                "Implementation and setup",
                "Training and onboarding",
                "24/7 technical support",
                "Regular system updates"
            ]
        }

    def _generate_implementation_timeline(self, client_info: Dict) -> List[Dict[str, str]]:
        """Generate implementation timeline"""
        
        return [
            {
                "phase": "Discovery & Planning",
                "duration": "2 weeks", 
                "activities": "Requirements gathering, system analysis, project planning",
                "deliverables": "Technical specifications, project plan"
            },
            {
                "phase": "Development & Setup",
                "duration": "4-6 weeks",
                "activities": "System configuration, custom development, testing",
                "deliverables": "Configured platform, test environment"
            },
            {
                "phase": "Testing & Training",
                "duration": "2 weeks",
                "activities": "User acceptance testing, team training, documentation",
                "deliverables": "Trained users, system documentation"
            },
            {
                "phase": "Go-Live & Support",
                "duration": "1 week",
                "activities": "Production deployment, monitoring, ongoing support",
                "deliverables": "Live system, support documentation"
            }
        ]

    def _generate_executive_summary(self, client_info: Dict) -> str:
        """Generate executive summary"""
        
        company_name = client_info.get("company_name", "Your Company")
        expected_roi = client_info.get("expected_roi", "200%")
        
        return f"""
Executive Summary:

{company_name} has an opportunity to transform their operations through intelligent automation. 
Our proposed solution addresses your key challenges while delivering measurable business value.

Key Benefits:
• Significant operational efficiency improvements
• Reduced manual processing and errors
• Enhanced data visibility and insights
• Scalable platform for future growth

Investment: Starting at $10,000 setup + $5,000/month
Expected ROI: {expected_roi} within 12 months
Implementation: 8-10 week timeline

We're committed to your success and look forward to partnering with {company_name} on this transformative journey.
        """.strip()

    def _outline_next_steps(self, client_info: Dict) -> List[Dict[str, str]]:
        """Outline next steps in the sales process"""
        
        return [
            {
                "step": "Proposal Review",
                "timeline": "1 week", 
                "description": "Review proposal with internal stakeholders",
                "owner": "Client"
            },
            {
                "step": "Technical Deep Dive",
                "timeline": "Week 2",
                "description": "Detailed technical discussion with engineering teams",
                "owner": "Both parties"
            },
            {
                "step": "Contract Negotiation",
                "timeline": "Week 3",
                "description": "Finalize terms, pricing, and implementation details",
                "owner": "Both parties"
            },
            {
                "step": "Project Kickoff",
                "timeline": "Week 4",
                "description": "Sign contracts and begin implementation planning",
                "owner": "Vendor"
            }
        ]

    def get_schema(self) -> Dict[str, Any]:
        # Get LLM configuration from mixin
        llm_schema = self._get_llm_schema_section()
        
        return {
            "type": "object",
            "properties": {
                **llm_schema,  # Include LLM configuration
                "proposal_type": {
                    "type": "string",
                    "title": "Proposal Type",
                    "description": "Type of proposal to generate",
                    "enum": ["standard", "enterprise", "custom"],
                    "default": "standard"
                },
                "include_pricing": {
                    "type": "boolean",
                    "title": "Include Pricing Section",
                    "description": "Whether to include pricing details in the proposal",
                    "default": True
                }
            }
        }

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "client_info": {
                "type": "object",
                "title": "Client Information",
                "description": "Comprehensive client information for proposal generation",
                "properties": {
                    "company_name": {"type": "string"},
                    "industry": {"type": "string"},
                    "company_size": {"type": "string", "enum": ["small", "medium", "large", "enterprise"]},
                    "pain_points": {"type": "array", "items": {"type": "string"}},
                    "budget_range": {"type": "string"},
                    "decision_makers": {"type": "array", "items": {"type": "string"}}
                },
                "required": True
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "proposal_content": {"type": "object", "description": "Complete proposal content"},
            "pricing_section": {"type": "object", "description": "Pricing structure and terms"},
            "implementation_timeline": {"type": "array", "description": "Project implementation phases"},
            "proposal_summary": {"type": "string", "description": "Executive summary"}
        }

    def estimate_cost(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> float:
        proposal_type = config.get("proposal_type", "standard")
        type_costs = {"standard": 0.02, "enterprise": 0.05, "custom": 0.10}
        return type_costs.get(proposal_type, 0.02)


# Register the node
NodeRegistry.register(
    "proposal_generator",
    ProposalGeneratorNode,
    ProposalGeneratorNode().get_metadata(),
)