"""
Brand Asset Generator Node - Company info → logos, color schemes
"""

from typing import Any, Dict
from backend.nodes.base import BaseNode
from backend.nodes.intelligence.llm_mixin import LLMConfigMixin
from backend.core.exceptions import NodeExecutionError, NodeValidationError
from backend.core.node_registry import NodeRegistry


class BrandGeneratorNode(BaseNode, LLMConfigMixin):
    node_type = "brand_generator"
    name = "Brand Asset Generator"
    description = "Generates brand assets like logos and color schemes from company info"
    category = "content"

    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute brand generation with LLM support"""
        try:
            # Get inputs - accept multiple field names
            company_info_raw = (
                inputs.get("company_info") or
                inputs.get("data") or
                inputs.get("text") or
                inputs.get("content") or
                {}
            )
            
            # Parse if it's a string (JSON)
            if isinstance(company_info_raw, str):
                import json
                try:
                    company_info = json.loads(company_info_raw)
                except json.JSONDecodeError:
                    # If not JSON, create basic company info from text
                    company_info = {"name": company_info_raw, "description": company_info_raw}
            elif isinstance(company_info_raw, dict):
                company_info = company_info_raw
            else:
                company_info = {}
            
            brand_style = config.get("brand_style", "modern")
            
            if not company_info:
                raise NodeValidationError("Company information is required. Connect a data source or provide company_info in config.")

            # Try to use LLM if available
            use_llm = False
            llm_config = None
            
            try:
                llm_config = self._resolve_llm_config(config)
                if llm_config.get("api_key"):
                    use_llm = True
            except Exception:
                use_llm = False

            if use_llm and llm_config:
                # Use LLM for better brand generation
                try:
                    brand_assets = await self._generate_llm_brand_assets(company_info, brand_style, llm_config)
                    style_guide = await self._generate_llm_style_guide(company_info, brand_style, brand_assets, llm_config)
                    recommendations = await self._generate_llm_recommendations(company_info, brand_assets, llm_config)
                except Exception as e:
                    # Fallback to pattern-based if LLM fails
                    await self.stream_log("brand_generator", f"LLM generation failed, using pattern matching: {e}", "warning")
                    brand_assets = self._generate_brand_assets(company_info, brand_style)
                    style_guide = f"Generated {brand_style} brand guide"
                    recommendations = ["Use consistent colors", "Maintain brand voice"]
            else:
                # Use pattern-based fallback
                brand_assets = self._generate_brand_assets(company_info, brand_style)
                style_guide = f"Generated {brand_style} brand guide"
                recommendations = ["Use consistent colors", "Maintain brand voice"]

            return {
                "brand_assets": brand_assets,
                "style_guide": style_guide,
                "recommendations": recommendations
            }
        except Exception as e:
            raise NodeExecutionError(f"Brand generation failed: {str(e)}")

    def get_schema(self) -> Dict[str, Any]:
        """Return configuration schema"""
        # Get LLM config schema from mixin
        llm_schema = self._get_llm_schema_section()
        
        return {
            "type": "object",
            "properties": {
                **llm_schema,  # Include LLM provider configuration
                "brand_style": {
                    "type": "string",
                    "title": "Brand Style",
                    "description": "Desired brand aesthetic style",
                    "enum": ["modern", "classic", "playful", "minimal"],
                    "default": "modern"
                }
            }
        }

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "company_info": {
                "type": "object",
                "title": "Company Information",
                "required": True
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "brand_assets": {"type": "object", "description": "Generated brand assets"},
            "style_guide": {"type": "string", "description": "Brand style guidelines"}
        }

    def estimate_cost(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> float:
        return 0.03


# Register the node
NodeRegistry.register(
    "brand_generator",
    BrandGeneratorNode,
    BrandGeneratorNode().get_metadata(),
)
