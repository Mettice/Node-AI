"""
A/B Test Analyzer Node - Takes experiment data and provides statistical insights

This node analyzes A/B test results for:
- Statistical significance testing
- Conversion rate analysis
- Confidence intervals
- Sample size recommendations
- Test duration optimization
"""

import math
from typing import Any, Dict, List
from backend.nodes.base import BaseNode
from backend.nodes.intelligence.llm_mixin import LLMConfigMixin
from backend.core.exceptions import NodeExecutionError, NodeValidationError
from backend.core.node_registry import NodeRegistry


class ABTestAnalyzerNode(BaseNode, LLMConfigMixin):
    node_type = "ab_test_analyzer"
    name = "A/B Test Analyzer"
    description = "Provides statistical analysis of A/B test experiment data"
    category = "business"

    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute A/B test analysis"""
        try:
            await self.stream_progress("ab_test_analyzer", 0.2, "Processing test data...")

            # Get inputs - accept multiple field names for flexibility
            test_data_raw = (
                inputs.get("test_data") or 
                inputs.get("data") or 
                inputs.get("text") or 
                inputs.get("content") or 
                inputs.get("output") or
                {}
            )
            
            # Parse if it's a string (JSON)
            if isinstance(test_data_raw, str):
                try:
                    import json
                    test_data = json.loads(test_data_raw)
                except json.JSONDecodeError:
                    test_data = {}
            else:
                test_data = test_data_raw if test_data_raw else {}
            
            confidence_level = config.get("confidence_level", 0.95)
            test_type = config.get("test_type", "conversion")

            if not test_data:
                raise NodeValidationError("A/B test data is required. Connect a text_input, file_loader, or data_loader node.")

            await self.stream_progress("ab_test_analyzer", 0.6, "Computing statistical significance...")

            # Extract variant data
            control = test_data.get("control", {})
            treatment = test_data.get("treatment", {})

            # Perform statistical analysis
            statistical_analysis = self._perform_statistical_test(control, treatment, confidence_level)
            
            # Calculate effect sizes and practical significance
            effect_analysis = self._analyze_effect_size(control, treatment)

            await self.stream_progress("ab_test_analyzer", 0.9, "Generating recommendations...")

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
                    recommendations = await self._generate_llm_recommendations(
                        statistical_analysis, effect_analysis, test_type, test_data, llm_config
                    )
                except Exception as e:
                    await self.stream_log("ab_test_analyzer", f"LLM recommendations failed, using pattern matching: {e}", "warning")
                    recommendations = self._generate_test_recommendations(statistical_analysis, effect_analysis)
            else:
                recommendations = self._generate_test_recommendations(statistical_analysis, effect_analysis)

            result = {
                "statistical_analysis": statistical_analysis,
                "effect_analysis": effect_analysis, 
                "recommendations": recommendations,
                "summary": {
                    "is_significant": statistical_analysis.get("is_significant", False),
                    "winner": statistical_analysis.get("winner", "inconclusive"),
                    "confidence": confidence_level * 100
                }
            }

            await self.stream_progress("ab_test_analyzer", 1.0, "A/B test analysis complete!")
            return result

        except Exception as e:
            raise NodeExecutionError(f"A/B test analysis failed: {str(e)}")

    def _perform_statistical_test(self, control: Dict, treatment: Dict, confidence: float) -> Dict[str, Any]:
        """Perform statistical significance testing"""
        
        control_conversions = control.get("conversions", 0)
        control_visitors = control.get("visitors", 1)
        treatment_conversions = treatment.get("conversions", 0) 
        treatment_visitors = treatment.get("visitors", 1)

        # Calculate conversion rates
        control_rate = control_conversions / control_visitors
        treatment_rate = treatment_conversions / treatment_visitors

        # Calculate pooled probability and standard error
        pooled_prob = (control_conversions + treatment_conversions) / (control_visitors + treatment_visitors)
        se = math.sqrt(pooled_prob * (1 - pooled_prob) * (1/control_visitors + 1/treatment_visitors))
        
        # Calculate z-score
        if se > 0:
            z_score = (treatment_rate - control_rate) / se
        else:
            z_score = 0

        # Calculate p-value (simplified)
        p_value = 2 * (1 - self._normal_cdf(abs(z_score)))
        
        # Determine significance
        alpha = 1 - confidence
        is_significant = p_value < alpha
        
        # Determine winner
        if is_significant:
            winner = "treatment" if treatment_rate > control_rate else "control"
        else:
            winner = "inconclusive"

        return {
            "control_rate": control_rate,
            "treatment_rate": treatment_rate,
            "lift": ((treatment_rate - control_rate) / control_rate * 100) if control_rate > 0 else 0,
            "z_score": z_score,
            "p_value": p_value,
            "is_significant": is_significant,
            "winner": winner,
            "confidence_interval": self._calculate_confidence_interval(treatment_rate, treatment_visitors, confidence)
        }

    def _analyze_effect_size(self, control: Dict, treatment: Dict) -> Dict[str, Any]:
        """Analyze practical significance and effect sizes"""
        
        control_rate = control.get("conversions", 0) / control.get("visitors", 1)
        treatment_rate = treatment.get("conversions", 0) / treatment.get("visitors", 1)
        
        # Calculate absolute and relative lift
        absolute_lift = treatment_rate - control_rate
        relative_lift = (absolute_lift / control_rate * 100) if control_rate > 0 else 0
        
        # Assess practical significance
        practical_threshold = 0.02  # 2% minimum meaningful difference
        is_practically_significant = abs(absolute_lift) >= practical_threshold
        
        return {
            "absolute_lift": absolute_lift,
            "relative_lift": relative_lift,
            "is_practically_significant": is_practically_significant,
            "effect_size_interpretation": self._interpret_effect_size(abs(relative_lift))
        }

    def _normal_cdf(self, z: float) -> float:
        """Approximate normal cumulative distribution function"""
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))

    def _calculate_confidence_interval(self, rate: float, n: int, confidence: float) -> List[float]:
        """Calculate confidence interval for conversion rate"""
        z = 1.96  # 95% confidence z-score
        margin = z * math.sqrt(rate * (1 - rate) / n)
        return [max(0, rate - margin), min(1, rate + margin)]

    def _interpret_effect_size(self, lift_percent: float) -> str:
        """Interpret the practical significance of effect size"""
        if lift_percent < 5:
            return "small"
        elif lift_percent < 15:
            return "medium"
        else:
            return "large"

    def _generate_test_recommendations(self, stats: Dict, effects: Dict) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on analysis"""
        
        recommendations = []
        
        if stats["is_significant"] and effects["is_practically_significant"]:
            recommendations.append({
                "type": "action",
                "priority": "high",
                "message": f"Implement {stats['winner']} variant - statistically and practically significant",
                "reason": f"Shows {effects['relative_lift']:.1f}% improvement with high confidence"
            })
        elif stats["is_significant"] and not effects["is_practically_significant"]:
            recommendations.append({
                "type": "caution", 
                "priority": "medium",
                "message": "Statistically significant but small effect size",
                "reason": "Consider cost-benefit analysis before implementation"
            })
        elif not stats["is_significant"]:
            recommendations.append({
                "type": "continue",
                "priority": "medium", 
                "message": "Continue test or increase sample size",
                "reason": f"p-value of {stats['p_value']:.3f} indicates insufficient evidence"
            })
        
        return recommendations

    async def _generate_llm_recommendations(
        self,
        stats: Dict[str, Any],
        effects: Dict[str, Any],
        test_type: str,
        test_data: Dict[str, Any],
        llm_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate intelligent recommendations using LLM"""
        
        control = test_data.get("control", {})
        treatment = test_data.get("treatment", {})
        
        analysis_summary = f"""
A/B Test Analysis Results:

Test Type: {test_type}
Confidence Level: 95%

Control Group:
- Visitors: {control.get('visitors', 0)}
- Conversions: {control.get('conversions', 0)}
- Conversion Rate: {stats.get('control_rate', 0):.2%}

Treatment Group:
- Visitors: {treatment.get('visitors', 0)}
- Conversions: {treatment.get('conversions', 0)}
- Conversion Rate: {stats.get('treatment_rate', 0):.2%}

Statistical Results:
- Lift: {stats.get('lift', 0):.1f}%
- P-value: {stats.get('p_value', 0):.4f}
- Statistically Significant: {stats.get('is_significant', False)}
- Winner: {stats.get('winner', 'inconclusive')}

Effect Analysis:
- Relative Lift: {effects.get('relative_lift', 0):.1f}%
- Practically Significant: {effects.get('is_practically_significant', False)}
- Effect Size: {effects.get('effect_size_interpretation', 'unknown')}
"""
        
        prompt = f"""Analyze this A/B test results and provide actionable recommendations.

{analysis_summary}

Provide 5-7 recommendations in JSON format as an array of objects, each with:
- "type": "action" | "caution" | "continue" | "insight"
- "priority": "high" | "medium" | "low"
- "message": Brief recommendation message
- "reason": Explanation of why this recommendation matters
- "next_steps": Specific next steps to take

Consider:
1. Whether to implement the winning variant
2. Whether to continue testing
3. Sample size adequacy
4. Practical vs statistical significance
5. Business context and implications
6. Risk assessment

Make recommendations specific, actionable, and consider both statistical and business perspectives."""
        
        try:
            import json
            import re
            llm_response = await self._call_llm(prompt, llm_config, max_tokens=1000)
            
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                recommendations = json.loads(json_match.group())
                return recommendations[:7]
            else:
                return self._generate_test_recommendations(stats, effects)
        except Exception:
            return self._generate_test_recommendations(stats, effects)

    def get_schema(self) -> Dict[str, Any]:
        """Return configuration schema"""
        # Get LLM config schema from mixin
        llm_schema = self._get_llm_schema_section()
        
        return {
            "type": "object",
            "properties": {
                **llm_schema,  # Include LLM provider configuration
                "confidence_level": {
                    "type": "number",
                    "title": "Confidence Level",
                    "minimum": 0.8,
                    "maximum": 0.99,
                    "default": 0.95
                },
                "test_type": {
                    "type": "string",
                    "title": "Test Type",
                    "enum": ["conversion", "revenue", "engagement"],
                    "default": "conversion"
                }
            }
        }

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "test_data": {
                "type": "object",
                "title": "A/B Test Data", 
                "description": "Test results with control and treatment data",
                "properties": {
                    "control": {"type": "object", "properties": {"conversions": {"type": "integer"}, "visitors": {"type": "integer"}}},
                    "treatment": {"type": "object", "properties": {"conversions": {"type": "integer"}, "visitors": {"type": "integer"}}}
                },
                "required": True
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "statistical_analysis": {"type": "object", "description": "Statistical test results"},
            "effect_analysis": {"type": "object", "description": "Effect size and practical significance"},
            "recommendations": {"type": "array", "description": "Actionable recommendations"},
            "summary": {"type": "object", "description": "Test summary and conclusions"}
        }

    def estimate_cost(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> float:
        return 0.003  # Fixed cost for statistical analysis


# Register the node
NodeRegistry.register(
    "ab_test_analyzer",
    ABTestAnalyzerNode,
    ABTestAnalyzerNode().get_metadata(),
)