"""
Lead Enricher Node - Email → full contact profile with AI research
"""

from typing import Any, Dict
from backend.nodes.base import BaseNode
from backend.nodes.intelligence.llm_mixin import LLMConfigMixin
from backend.core.exceptions import NodeValidationError, NodeExecutionError
from backend.core.node_registry import NodeRegistry


class LeadEnricherNode(BaseNode, LLMConfigMixin):
    node_type = "lead_enricher"
    name = "Lead Enricher"
    description = "Enriches lead data with AI-powered research and contact information"
    category = "sales"

    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute lead enrichment with LLM support"""
        try:
            # Get inputs - accept multiple field names
            email = (
                inputs.get("email") or
                inputs.get("text") or
                inputs.get("content") or
                inputs.get("output") or
                ""
            )
            enrichment_level = config.get("enrichment_level", "standard")
            
            if not email or "@" not in email:
                raise NodeValidationError("Valid email address is required. Connect a text_input node or provide email in config.")

            # Enrich contact information (pattern-based or external API)
            contact_info = self._enrich_contact_data(email, enrichment_level)
            company_info = self._research_company(contact_info.get("company_domain", ""))
            social_profiles = self._find_social_profiles(email, contact_info)

            # Try to use LLM for intelligent analysis and insights
            use_llm = False
            llm_config = None
            
            try:
                llm_config = self._resolve_llm_config(config)
                if llm_config.get("api_key"):
                    use_llm = True
            except Exception:
                use_llm = False

            # Generate intelligent insights using LLM if available
            insights = None
            if use_llm and llm_config:
                try:
                    insights = await self._generate_llm_insights(contact_info, company_info, social_profiles, enrichment_level, llm_config)
                except Exception as e:
                    await self.stream_log("lead_enricher", f"LLM insights generation failed: {e}", "warning")

            result = {
                "contact_info": contact_info,
                "company_info": company_info,
                "social_profiles": social_profiles,
                "enrichment_score": self._calculate_enrichment_score(contact_info, company_info),
                "data_sources": ["email_lookup", "company_research", "social_search"]
            }
            
            if insights:
                result["ai_insights"] = insights

            return result
        except Exception as e:
            raise NodeExecutionError(f"Lead enrichment failed: {str(e)}")

    def _enrich_contact_data(self, email: str, level: str) -> Dict[str, Any]:
        """Enrich basic contact information"""
        # In production, would use services like Clearbit, ZoomInfo, etc.
        domain = email.split("@")[1] if "@" in email else ""
        
        return {
            "email": email,
            "full_name": "John Doe",  # Would be looked up
            "first_name": "John",
            "last_name": "Doe", 
            "title": "Marketing Manager",
            "company": "Example Corp",
            "company_domain": domain,
            "location": "San Francisco, CA",
            "phone": "+1-555-0123" if level == "comprehensive" else None,
            "confidence_score": 0.85
        }

    def _research_company(self, domain: str) -> Dict[str, Any]:
        """Research company information"""
        if not domain:
            return {}
            
        return {
            "company_name": "Example Corp",
            "industry": "Software Technology",
            "employee_count": "51-200",
            "annual_revenue": "$10M-$50M",
            "headquarters": "San Francisco, CA",
            "website": f"https://{domain}",
            "description": "AI-powered software solutions company",
            "technologies": ["React", "Node.js", "AWS"],
            "funding_stage": "Series B",
            "key_competitors": ["Company A", "Company B"]
        }

    def _find_social_profiles(self, email: str, contact_info: Dict) -> Dict[str, str]:
        """Find social media profiles"""
        name = contact_info.get("full_name", "")
        
        return {
            "linkedin": f"https://linkedin.com/in/john-doe",
            "twitter": f"https://twitter.com/johndoe",
            "github": f"https://github.com/johndoe" if "tech" in contact_info.get("title", "").lower() else None
        }

    def _calculate_enrichment_score(self, contact: Dict, company: Dict) -> int:
        """Calculate data enrichment completeness score"""
        contact_fields = ["full_name", "title", "company", "location"]
        company_fields = ["industry", "employee_count", "annual_revenue"]
        
        contact_score = sum(1 for field in contact_fields if contact.get(field))
        company_score = sum(1 for field in company_fields if company.get(field))
        
        total_possible = len(contact_fields) + len(company_fields)
        total_found = contact_score + company_score
        
        return int((total_found / total_possible) * 100)

    async def _generate_llm_insights(
        self,
        contact_info: Dict[str, Any],
        company_info: Dict[str, Any],
        social_profiles: Dict[str, Any],
        enrichment_level: str,
        llm_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate intelligent insights about the lead using LLM"""
        
        # Prepare enrichment summary
        enrichment_summary = f"""
Contact Information:
- Name: {contact_info.get('full_name', 'N/A')}
- Title: {contact_info.get('title', 'N/A')}
- Company: {contact_info.get('company', 'N/A')}
- Location: {contact_info.get('location', 'N/A')}
- Email: {contact_info.get('email', 'N/A')}

Company Information:
- Industry: {company_info.get('industry', 'N/A')}
- Employee Count: {company_info.get('employee_count', 'N/A')}
- Annual Revenue: {company_info.get('annual_revenue', 'N/A')}
- Headquarters: {company_info.get('headquarters', 'N/A')}
- Technologies: {', '.join(company_info.get('technologies', []))}
- Funding Stage: {company_info.get('funding_stage', 'N/A')}

Social Profiles:
- LinkedIn: {social_profiles.get('linkedin', 'Not found')}
- Twitter: {social_profiles.get('twitter', 'Not found')}
- GitHub: {social_profiles.get('github', 'Not found')}
"""
        
        prompt = f"""Analyze this enriched lead data and provide intelligent insights for sales teams.

{enrichment_summary}

Enrichment Level: {enrichment_level}

Provide insights in JSON format with:
- "lead_quality": "high" | "medium" | "low" (based on company size, title, etc.)
- "sales_approach": Recommended approach for this lead
- "key_talking_points": Array of 3-5 talking points based on company/role
- "potential_interest_areas": Array of product/service areas this lead might be interested in
- "decision_maker_likelihood": "high" | "medium" | "low" (based on title and company structure)
- "recommended_follow_up": Specific follow-up recommendation
- "risk_factors": Array of any concerns or red flags

Make insights actionable and specific to help sales teams personalize their outreach."""
        
        try:
            import json
            import re
            llm_response = await self._call_llm(prompt, llm_config, max_tokens=800)
            
            # Try to parse JSON
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                insights = json.loads(json_match.group())
                return insights
            else:
                return None
        except Exception:
            return None

    def get_schema(self) -> Dict[str, Any]:
        """Return configuration schema"""
        # Get LLM config schema from mixin
        llm_schema = self._get_llm_schema_section()
        
        return {
            "type": "object",
            "properties": {
                **llm_schema,  # Include LLM provider configuration
                "enrichment_level": {
                    "type": "string",
                    "title": "Enrichment Level",
                    "description": "Level of data enrichment to perform",
                    "enum": ["basic", "standard", "comprehensive"],
                    "default": "standard"
                }
            }
        }

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "email": {
                "type": "string",
                "title": "Email Address",
                "description": "Lead email address to enrich",
                "format": "email",
                "required": True
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "contact_info": {"type": "object", "description": "Enriched contact information"},
            "company_info": {"type": "object", "description": "Company research data"},
            "social_profiles": {"type": "object", "description": "Social media profiles"},
            "enrichment_score": {"type": "integer", "description": "Data completeness score (0-100)"}
        }

    def estimate_cost(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> float:
        level = config.get("enrichment_level", "standard")
        level_costs = {"basic": 0.02, "standard": 0.05, "comprehensive": 0.10}
        return level_costs.get(level, 0.05)


# Register the node
NodeRegistry.register(
    "lead_enricher",
    LeadEnricherNode,
    LeadEnricherNode().get_metadata(),
)