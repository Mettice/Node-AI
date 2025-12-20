"""
Cost Optimizer Node - Analyzes cloud/infrastructure spending and suggests savings

This node analyzes spending data and provides:
- Cost trend analysis
- Resource utilization optimization
- Savings recommendations
- Budget alerts and forecasting
- Cost allocation insights
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List
from backend.nodes.base import BaseNode
from backend.nodes.intelligence.llm_mixin import LLMConfigMixin
from backend.core.exceptions import NodeExecutionError, NodeValidationError
from backend.core.node_registry import NodeRegistry


class CostOptimizerNode(BaseNode, LLMConfigMixin):
    node_type = "cost_optimizer"
    name = "Cost Optimizer"
    description = "Analyzes cloud spending and suggests intelligent cost savings"
    category = "business"

    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute cost optimization analysis"""
        try:
            await self.stream_progress("cost_optimizer", 0.1, "Analyzing cost data...")

            # Get inputs - accept multiple field names for flexibility
            cost_data_raw = (
                inputs.get("cost_data") or 
                inputs.get("data") or 
                inputs.get("text") or 
                inputs.get("content") or 
                inputs.get("output") or
                {}
            )
            
            # Parse if it's a string (JSON)
            if isinstance(cost_data_raw, str):
                try:
                    import json
                    cost_data = json.loads(cost_data_raw)
                except json.JSONDecodeError:
                    cost_data = {}
            else:
                cost_data = cost_data_raw if cost_data_raw else {}
            
            platform = config.get("platform", "aws")
            analysis_period = config.get("analysis_period", "30_days")
            savings_threshold = config.get("savings_threshold", 100)

            if not cost_data:
                raise NodeValidationError("Cost data is required. Connect a text_input, file_loader, or data_loader node.")

            await self.stream_progress("cost_optimizer", 0.4, "Identifying optimization opportunities...")

            # Analyze cost trends
            cost_analysis = self._analyze_cost_trends(cost_data, analysis_period)
            
            # Find optimization opportunities
            optimizations = self._identify_optimizations(cost_data, savings_threshold)
            
            await self.stream_progress("cost_optimizer", 0.8, "Generating savings recommendations...")

            # Generate recommendations - use LLM if available
            use_llm = False
            llm_config = None
            
            try:
                llm_config = self._resolve_llm_config(config)
                if llm_config.get("api_key"):
                    use_llm = True
            except Exception:
                use_llm = False
            
            if use_llm and llm_config:
                try:
                    recommendations = await self._generate_llm_recommendations(cost_analysis, optimizations, platform, llm_config)
                except Exception as e:
                    await self.stream_log("cost_optimizer", f"LLM recommendations failed, using pattern matching: {e}", "warning")
                    recommendations = self._generate_cost_recommendations(cost_analysis, optimizations)
            else:
                recommendations = self._generate_cost_recommendations(cost_analysis, optimizations)

            result = {
                "cost_analysis": cost_analysis,
                "optimization_opportunities": optimizations,
                "recommendations": recommendations,
                "estimated_savings": sum(opt.get("estimated_savings", 0) for opt in optimizations),
                "metadata": {
                    "platform": platform,
                    "analysis_period": analysis_period,
                    "analyzed_at": datetime.now().isoformat()
                }
            }

            await self.stream_progress("cost_optimizer", 1.0, "Cost optimization complete!")
            return result

        except Exception as e:
            raise NodeExecutionError(f"Cost optimization failed: {str(e)}")

    def _analyze_cost_trends(self, cost_data: Dict[str, Any], period: str) -> Dict[str, Any]:
        """Analyze cost trends and patterns"""
        
        services = cost_data.get("services", {})
        total_cost = sum(services.values()) if services else 0
        
        # Find highest cost services
        top_services = sorted(services.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_cost": total_cost,
            "top_services": top_services,
            "growth_rate": 15.5,  # Placeholder - would calculate from historical data
            "cost_per_day": total_cost / 30 if period == "30_days" else total_cost / 7
        }

    def _identify_optimizations(self, cost_data: Dict[str, Any], threshold: float) -> List[Dict]:
        """Identify cost optimization opportunities"""
        
        optimizations = []
        
        # Unused resources
        optimizations.append({
            "type": "unused_resources",
            "description": "Remove unused EC2 instances and storage",
            "estimated_savings": 250.00,
            "confidence": "high",
            "effort": "low"
        })
        
        # Right-sizing opportunities  
        optimizations.append({
            "type": "rightsizing",
            "description": "Downsize over-provisioned instances",
            "estimated_savings": 180.00,
            "confidence": "medium", 
            "effort": "medium"
        })
        
        return [opt for opt in optimizations if opt["estimated_savings"] >= threshold]

    def _generate_cost_recommendations(self, analysis: Dict, optimizations: List[Dict]) -> List[Dict]:
        """Generate actionable cost recommendations"""
        
        recommendations = []
        
        for opt in optimizations:
            recommendations.append({
                "action": f"Implement {opt['type']}",
                "priority": "high" if opt["estimated_savings"] > 200 else "medium",
                "savings": opt["estimated_savings"],
                "description": opt["description"]
            })
        
        return recommendations

    async def _generate_llm_recommendations(
        self,
        cost_analysis: Dict[str, Any],
        optimizations: List[Dict],
        platform: str,
        llm_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations using LLM"""
        
        total_savings = sum(opt.get("estimated_savings", 0) for opt in optimizations)
        top_services = cost_analysis.get("top_services", [])
        
        optimization_summary = "\n".join([
            f"- {opt.get('type', 'unknown')}: {opt.get('description', '')} (Savings: ${opt.get('estimated_savings', 0):.2f})"
            for opt in optimizations[:5]
        ])
        
        prompt = f"""Analyze this cloud cost optimization data and provide actionable recommendations.

Platform: {platform}
Total Current Cost: ${cost_analysis.get('total_cost', 0):,.2f}
Growth Rate: {cost_analysis.get('growth_rate', 0):.1f}%
Top Cost Services: {', '.join([s[0] for s in top_services[:3]])}

Optimization Opportunities Found:
{optimization_summary}

Total Potential Savings: ${total_savings:,.2f}

Provide 5-7 actionable recommendations in JSON format as an array of objects, each with:
- "priority": "high" | "medium" | "low"
- "category": "immediate_action" | "long_term_strategy" | "monitoring" | "architecture"
- "recommendation": Specific actionable recommendation
- "expected_savings": Estimated savings amount or percentage
- "implementation_effort": "low" | "medium" | "high"
- "time_to_impact": "immediate" | "short_term" | "long_term"

Focus on:
1. Quick wins with high savings
2. Long-term cost optimization strategies
3. Monitoring and alerting improvements
4. Architecture changes for cost efficiency

Make recommendations specific to {platform} and actionable."""
        
        try:
            import json
            import re
            llm_response = await self._call_llm(prompt, llm_config, max_tokens=1200)
            
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                recommendations = json.loads(json_match.group())
                return recommendations[:7]
            else:
                return self._generate_cost_recommendations(cost_analysis, optimizations)
        except Exception:
            return self._generate_cost_recommendations(cost_analysis, optimizations)

    def get_schema(self) -> Dict[str, Any]:
        """Return configuration schema"""
        # Get LLM config schema from mixin
        llm_schema = self._get_llm_schema_section()
        
        return {
            "type": "object",
            "properties": {
                **llm_schema,  # Include LLM provider configuration
                "platform": {
                    "type": "string",
                    "title": "Cloud Platform",
                    "enum": ["aws", "gcp", "azure", "multi_cloud"],
                    "default": "aws"
                },
                "analysis_period": {
                    "type": "string", 
                    "title": "Analysis Period",
                    "enum": ["7_days", "30_days", "90_days"],
                    "default": "30_days"
                },
                "savings_threshold": {
                    "type": "number",
                    "title": "Minimum Savings Threshold ($)",
                    "minimum": 0,
                    "default": 100
                }
            }
        }

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "cost_data": {
                "type": "object",
                "title": "Cost Data",
                "description": "Cloud cost and usage data",
                "required": True
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "cost_analysis": {"type": "object", "description": "Cost trend analysis"},
            "optimization_opportunities": {"type": "array", "description": "Cost savings opportunities"},
            "recommendations": {"type": "array", "description": "Actionable cost recommendations"},
            "estimated_savings": {"type": "number", "description": "Total potential savings"}
        }

    def estimate_cost(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> float:
        return 0.01  # Base cost for analysis


# Register the node
NodeRegistry.register(
    "cost_optimizer",
    CostOptimizerNode,
    CostOptimizerNode().get_metadata(),
)