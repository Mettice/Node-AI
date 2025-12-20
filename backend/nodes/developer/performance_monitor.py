"""
Performance Monitor Node - App metrics → optimization recommendations
"""

from typing import Any, Dict, List
from backend.nodes.base import BaseNode
from backend.nodes.intelligence.llm_mixin import LLMConfigMixin
from backend.core.exceptions import NodeValidationError, NodeExecutionError
from backend.core.node_registry import NodeRegistry


class PerformanceMonitorNode(BaseNode, LLMConfigMixin):
    node_type = "performance_monitor"
    name = "Performance Monitor"
    description = "Analyzes app metrics and provides optimization recommendations"
    category = "developer"

    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute performance monitoring with LLM support"""
        try:
            metrics = inputs.get("metrics", {})
            threshold_config = config.get("thresholds", {})
            
            if not metrics:
                raise NodeValidationError("Performance metrics are required")

            analysis = self._analyze_performance(metrics, threshold_config)
            
            # Try to use LLM for better recommendations
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
                    recommendations = await self._generate_llm_optimizations(analysis, metrics, threshold_config, llm_config)
                except Exception as e:
                    await self.stream_log("performance_monitor", f"LLM recommendations failed, using pattern matching: {e}", "warning")
                    recommendations = self._generate_optimizations(analysis)
            else:
                recommendations = self._generate_optimizations(analysis)
            
            alerts = self._check_alerts(analysis, threshold_config)

            return {
                "performance_analysis": analysis,
                "optimization_recommendations": recommendations,
                "alerts": alerts,
                "overall_score": analysis.get("overall_score", 0)
            }
        except NodeValidationError:
            raise
        except Exception as e:
            raise NodeExecutionError(f"Performance monitoring failed: {str(e)}") from e

    def _analyze_performance(self, metrics: Dict, thresholds: Dict) -> Dict[str, Any]:
        """Analyze performance metrics"""
        
        # Default thresholds
        default_thresholds = {
            "response_time_ms": 500,
            "cpu_usage_percent": 80,
            "memory_usage_percent": 85,
            "error_rate_percent": 1
        }
        thresholds = {**default_thresholds, **thresholds}
        
        analysis = {
            "response_time": {
                "value": metrics.get("response_time_ms", 0),
                "status": "good" if metrics.get("response_time_ms", 0) < thresholds["response_time_ms"] else "warning",
                "threshold": thresholds["response_time_ms"]
            },
            "cpu_usage": {
                "value": metrics.get("cpu_usage_percent", 0),
                "status": "good" if metrics.get("cpu_usage_percent", 0) < thresholds["cpu_usage_percent"] else "critical",
                "threshold": thresholds["cpu_usage_percent"]
            },
            "memory_usage": {
                "value": metrics.get("memory_usage_percent", 0),
                "status": "good" if metrics.get("memory_usage_percent", 0) < thresholds["memory_usage_percent"] else "critical",
                "threshold": thresholds["memory_usage_percent"]
            },
            "error_rate": {
                "value": metrics.get("error_rate_percent", 0),
                "status": "good" if metrics.get("error_rate_percent", 0) < thresholds["error_rate_percent"] else "warning",
                "threshold": thresholds["error_rate_percent"]
            }
        }
        
        # Calculate overall score
        good_metrics = len([m for m in analysis.values() if m["status"] == "good"])
        overall_score = (good_metrics / len(analysis)) * 100
        analysis["overall_score"] = overall_score
        
        return analysis

    def _generate_optimizations(self, analysis: Dict) -> List[Dict[str, str]]:
        """Generate optimization recommendations"""
        recommendations = []
        
        if analysis["response_time"]["status"] != "good":
            recommendations.append({
                "category": "response_time",
                "priority": "high",
                "recommendation": "Optimize database queries and implement caching",
                "expected_improvement": "30-50% response time reduction"
            })
        
        if analysis["cpu_usage"]["status"] == "critical":
            recommendations.append({
                "category": "cpu",
                "priority": "critical", 
                "recommendation": "Scale horizontally or optimize CPU-intensive operations",
                "expected_improvement": "Reduce CPU load by 20-40%"
            })
        
        if analysis["memory_usage"]["status"] == "critical":
            recommendations.append({
                "category": "memory",
                "priority": "critical",
                "recommendation": "Implement memory optimization and garbage collection tuning",
                "expected_improvement": "Reduce memory usage by 15-30%"
            })
        
        if analysis["error_rate"]["status"] != "good":
            recommendations.append({
                "category": "errors",
                "priority": "medium",
                "recommendation": "Improve error handling and add monitoring",
                "expected_improvement": "Reduce error rate to <1%"
            })
        
        return recommendations

    async def _generate_llm_optimizations(
        self,
        analysis: Dict[str, Any],
        metrics: Dict[str, Any],
        thresholds: Dict[str, Any],
        llm_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate intelligent optimization recommendations using LLM"""
        
        performance_summary = f"""
Performance Metrics:
- Response Time: {metrics.get('response_time_ms', 0)}ms (Threshold: {thresholds.get('response_time_ms', 500)}ms)
- CPU Usage: {metrics.get('cpu_usage_percent', 0)}% (Threshold: {thresholds.get('cpu_usage_percent', 80)}%)
- Memory Usage: {metrics.get('memory_usage_percent', 0)}% (Threshold: {thresholds.get('memory_usage_percent', 85)}%)
- Error Rate: {metrics.get('error_rate_percent', 0)}% (Threshold: {thresholds.get('error_rate_percent', 1)}%)

Performance Status:
- Overall Score: {analysis.get('overall_score', 0):.1f}/100
- Response Time Status: {analysis.get('response_time', {}).get('status', 'unknown')}
- CPU Status: {analysis.get('cpu_usage', {}).get('status', 'unknown')}
- Memory Status: {analysis.get('memory_usage', {}).get('status', 'unknown')}
- Error Rate Status: {analysis.get('error_rate', {}).get('status', 'unknown')}
"""
        
        prompt = f"""Analyze this application performance data and provide intelligent optimization recommendations.

{performance_summary}

Provide 5-7 actionable recommendations in JSON format as an array of objects, each with:
- "category": "response_time" | "cpu" | "memory" | "errors" | "architecture" | "monitoring"
- "priority": "critical" | "high" | "medium" | "low"
- "recommendation": Specific optimization recommendation
- "expected_improvement": Expected improvement description
- "implementation_effort": "low" | "medium" | "high"
- "technical_details": Brief technical explanation

Focus on:
1. Quick wins with high impact
2. Root cause analysis for performance issues
3. Scalability improvements
4. Monitoring and alerting enhancements
5. Architecture optimizations

Make recommendations specific, actionable, and prioritized by impact."""
        
        try:
            import json
            import re
            llm_response = await self._call_llm(prompt, llm_config, max_tokens=1000)
            
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                recommendations = json.loads(json_match.group())
                return recommendations[:7]
            else:
                return self._generate_optimizations(analysis)
        except Exception:
            return self._generate_optimizations(analysis)

    def _check_alerts(self, analysis: Dict, thresholds: Dict) -> List[Dict[str, str]]:
        """Check for performance alerts"""
        alerts = []
        
        for metric_name, metric_data in analysis.items():
            if metric_name == "overall_score":
                continue
                
            if metric_data.get("status") == "critical":
                alerts.append({
                    "type": "critical",
                    "metric": metric_name,
                    "message": f"{metric_name} is critically high: {metric_data['value']}%",
                    "action": "Immediate attention required"
                })
            elif metric_data.get("status") == "warning":
                alerts.append({
                    "type": "warning",
                    "metric": metric_name,
                    "message": f"{metric_name} exceeds threshold: {metric_data['value']}",
                    "action": "Monitor closely and consider optimization"
                })
        
        return alerts

    def get_schema(self) -> Dict[str, Any]:
        """Return configuration schema"""
        # Get LLM config schema from mixin
        llm_schema = self._get_llm_schema_section()
        
        return {
            "type": "object",
            "properties": {
                **llm_schema,  # Include LLM provider configuration
                "thresholds": {
                    "type": "object",
                    "title": "Performance Thresholds",
                    "properties": {
                        "response_time_ms": {"type": "number", "default": 500},
                        "cpu_usage_percent": {"type": "number", "default": 80},
                        "memory_usage_percent": {"type": "number", "default": 85},
                        "error_rate_percent": {"type": "number", "default": 1}
                    }
                }
            }
        }

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "metrics": {
                "type": "object",
                "title": "Performance Metrics",
                "description": "Application performance metrics",
                "properties": {
                    "response_time_ms": {"type": "number"},
                    "cpu_usage_percent": {"type": "number"},
                    "memory_usage_percent": {"type": "number"},
                    "error_rate_percent": {"type": "number"}
                },
                "required": True
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "performance_analysis": {"type": "object", "description": "Performance analysis results"},
            "optimization_recommendations": {"type": "array", "description": "Optimization suggestions"},
            "alerts": {"type": "array", "description": "Performance alerts"},
            "overall_score": {"type": "number", "description": "Overall performance score (0-100)"}
        }

    def estimate_cost(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> float:
        return 0.008  # Fixed cost for performance analysis


# Register the node
NodeRegistry.register(
    "performance_monitor",
    PerformanceMonitorNode,
    PerformanceMonitorNode().get_metadata(),
)