"""
Smart Data Analyzer Node - AI analyzes any data and suggests insights

This node takes structured or unstructured data and uses AI to:
- Identify patterns and trends
- Generate actionable insights
- Suggest recommendations
- Detect anomalies
- Provide summary statistics
"""

import json
import pandas as pd
from typing import Any, Dict, Optional
from backend.nodes.base import BaseNode
from backend.nodes.intelligence.llm_mixin import LLMConfigMixin
from backend.core.exceptions import NodeExecutionError, NodeValidationError
from backend.core.node_registry import NodeRegistry


class SmartDataAnalyzerNode(BaseNode, LLMConfigMixin):
    node_type = "smart_data_analyzer"
    name = "Smart Data Analyzer"
    description = "AI analyzes any data and suggests actionable insights"
    category = "intelligence"

    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute smart data analysis"""
        try:
            await self.stream_progress("smart_data_analyzer", 0.1, "Initializing data analysis...")

            # Get inputs - accept multiple field names for flexibility
            # text_input provides "text", but we also accept "data", "content", "output"
            data_input = (
                inputs.get("data") or 
                inputs.get("text") or 
                inputs.get("content") or 
                inputs.get("output") or
                ""
            )
            analysis_type = config.get("analysis_type", "general")
            include_visualizations = config.get("include_visualizations", True)
            focus_areas = config.get("focus_areas", [])
            provider = config.get("provider", "openai")

            if not data_input:
                raise NodeValidationError("Data input is required. Connect a text_input, file_loader, or data_loader node.")

            # Resolve LLM configuration using mixin
            llm_config = self._resolve_llm_config(config)

            await self.stream_progress("smart_data_analyzer", 0.3, "Processing data format...")

            # Parse different data formats
            analyzed_data = self._parse_data_input(data_input)
            
            await self.stream_progress("smart_data_analyzer", 0.5, "Analyzing data patterns...")

            # Generate AI insights using the resolved LLM config
            insights = await self._generate_ai_insights(
                analyzed_data, analysis_type, focus_areas, llm_config
            )

            await self.stream_progress("smart_data_analyzer", 0.8, "Generating recommendations...")

            # Generate recommendations
            recommendations = await self._generate_recommendations(analyzed_data, insights)

            # Generate visualization suggestions if requested
            visualizations = []
            if include_visualizations:
                visualizations = self._suggest_visualizations(analyzed_data, insights)

            result = {
                "insights": insights,
                "recommendations": recommendations,
                "visualizations": visualizations,
                "data_summary": self._generate_data_summary(analyzed_data),
                "analysis_metadata": {
                    "data_type": type(analyzed_data).__name__,
                    "analysis_type": analysis_type,
                    "focus_areas": focus_areas,
                    "timestamp": pd.Timestamp.now().isoformat()
                }
            }

            await self.stream_progress("smart_data_analyzer", 1.0, "Analysis complete!")
            return result

        except Exception as e:
            raise NodeExecutionError(f"Smart data analysis failed: {str(e)}")

    def _parse_data_input(self, data_input: Any) -> Any:
        """Parse various data input formats"""
        if isinstance(data_input, str):
            # Try to parse as JSON
            try:
                return json.loads(data_input)
            except json.JSONDecodeError:
                # Treat as raw text
                return data_input
        elif isinstance(data_input, (list, dict)):
            return data_input
        else:
            # Try to convert to pandas DataFrame if possible
            try:
                return pd.DataFrame(data_input)
            except:
                return data_input

    async def _generate_ai_insights(self, data: Any, analysis_type: str, focus_areas: list, llm_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered insights from data"""
        try:
            # Prepare data summary for LLM analysis
            data_summary = self._prepare_data_for_llm(data)
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(data_summary, analysis_type, focus_areas)
            
            # Call LLM using mixin method
            llm_response = await self._call_llm(prompt, llm_config, max_tokens=2000)
            
            # Parse LLM response into structured insights
            insights = self._parse_llm_response(llm_response)
            
            # Add statistical analysis as baseline
            statistical_insights = self._generate_statistical_insights(data)
            insights.update(statistical_insights)
            
            return insights
            
        except Exception as e:
            # Fallback to statistical analysis only
            await self.stream_log("smart_data_analyzer", f"LLM analysis failed, using statistical fallback: {e}", "warning")
            return self._generate_statistical_insights(data)

    def _prepare_data_for_llm(self, data: Any) -> str:
        """Prepare data summary for LLM analysis"""
        if isinstance(data, pd.DataFrame):
            summary = {
                "shape": list(data.shape),
                "columns": list(data.columns),
                "dtypes": data.dtypes.to_dict(),
                "head": data.head().to_dict(),
                "describe": data.describe().to_dict() if len(data.select_dtypes(include=['number']).columns) > 0 else {},
                "missing_values": data.isnull().sum().to_dict()
            }
            return json.dumps(summary, indent=2, default=str)[:4000]  # Limit size
        else:
            return str(data)[:4000]  # Limit size for LLM

    def _create_analysis_prompt(self, data_summary: str, analysis_type: str, focus_areas: list) -> str:
        """Create analysis prompt for LLM"""
        focus_text = f", focusing on: {', '.join(focus_areas)}" if focus_areas else ""
        
        return f"""Analyze the following data and provide business insights in JSON format.

Data Summary:
{data_summary}

Analysis Type: {analysis_type}{focus_text}

Please provide insights in the following JSON structure:
{{
    "key_findings": [
        {{"finding": "description", "impact": "high|medium|low", "recommendation": "action"}}
    ],
    "patterns": [
        {{"pattern": "description", "confidence": "high|medium|low"}}
    ],
    "anomalies": [
        {{"anomaly": "description", "severity": "high|medium|low"}}
    ],
    "trends": [
        {{"trend": "description", "direction": "increasing|decreasing|stable"}}
    ],
    "business_recommendations": [
        {{"recommendation": "action", "priority": "high|medium|low", "expected_outcome": "description"}}
    ]
}}

Focus on actionable insights that can drive business decisions."""


    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured insights"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback to basic parsing
                return {
                    "key_findings": [{"finding": "AI analysis completed", "impact": "medium", "recommendation": response[:500]}],
                    "patterns": [],
                    "anomalies": [],
                    "trends": [],
                    "business_recommendations": []
                }
        except Exception as e:
            return {
                "key_findings": [{"finding": "Analysis completed with limited parsing", "impact": "low", "recommendation": response[:500]}],
                "patterns": [],
                "anomalies": [],
                "trends": [],
                "business_recommendations": []
            }

    def _generate_statistical_insights(self, data: Any) -> Dict[str, Any]:
        """Generate basic statistical insights as fallback"""
        insights = {
            "statistical_summary": {
                "data_type": type(data).__name__,
                "analysis_method": "statistical"
            }
        }

        # Basic statistical analysis for DataFrames
        if isinstance(data, pd.DataFrame):
            numerical_cols = data.select_dtypes(include=['number']).columns
            insights["statistical_summary"]["numerical_columns"] = len(numerical_cols)
            insights["statistical_summary"]["total_rows"] = len(data)
            
            if len(numerical_cols) > 0:
                insights["statistical_summary"]["basic_stats"] = data[numerical_cols].describe().to_dict()

            # Missing data analysis
            missing_data = data.isnull().sum()
            if missing_data.any():
                insights["data_quality"] = {
                    "missing_values": missing_data.to_dict(),
                    "completeness_score": ((data.shape[0] * data.shape[1] - missing_data.sum()) / (data.shape[0] * data.shape[1])) * 100
                }

        return insights

    async def _generate_recommendations(self, data: Any, insights: Dict[str, Any]) -> list:
        """Generate actionable recommendations based on insights"""
        recommendations = []

        # Data quality recommendations
        if insights.get("anomalies"):
            for anomaly in insights["anomalies"]:
                # Safely check for type field
                if isinstance(anomaly, dict) and anomaly.get("type") == "missing_data":
                    recommendations.append({
                        "category": "data_quality",
                        "priority": "high",
                        "action": "Address missing data",
                        "description": "Consider data imputation or collection improvements"
                    })

        # Performance recommendations
        if isinstance(data, pd.DataFrame) and len(data) > 1000:
            recommendations.append({
                "category": "performance",
                "priority": "medium", 
                "action": "Consider data sampling",
                "description": "Large dataset detected - consider sampling for faster analysis"
            })

        # Business insights
        key_findings = insights.get("key_findings", [])
        if key_findings:
            recommendations.append({
                "category": "business_insight",
                "priority": "high",
                "action": "Focus on high-variance metrics",
                "description": "Metrics with high standard deviation may need attention"
            })

        return recommendations

    def _suggest_visualizations(self, data: Any, insights: Dict[str, Any]) -> list:
        """Suggest appropriate visualizations for the data"""
        suggestions = []

        if isinstance(data, pd.DataFrame):
            # Suggest charts based on data types
            numerical_cols = data.select_dtypes(include=['number']).columns
            categorical_cols = data.select_dtypes(include=['object', 'category']).columns

            if len(numerical_cols) >= 2:
                suggestions.append({
                    "type": "scatter_plot",
                    "x_axis": numerical_cols[0],
                    "y_axis": numerical_cols[1],
                    "purpose": "Explore correlation between variables"
                })

            if len(numerical_cols) >= 1:
                suggestions.append({
                    "type": "histogram",
                    "column": numerical_cols[0],
                    "purpose": "Show distribution of values"
                })

            if len(categorical_cols) >= 1:
                suggestions.append({
                    "type": "bar_chart",
                    "column": categorical_cols[0],
                    "purpose": "Show category frequencies"
                })

        return suggestions

    def _generate_data_summary(self, data: Any) -> Dict[str, Any]:
        """Generate summary statistics for the data"""
        summary = {
            "data_type": type(data).__name__,
            "size": 0,
            "shape": None,
            "columns": None
        }

        if isinstance(data, pd.DataFrame):
            summary.update({
                "size": len(data),
                "shape": list(data.shape),
                "columns": list(data.columns),
                "dtypes": data.dtypes.to_dict()
            })
        elif isinstance(data, list):
            summary["size"] = len(data)
        elif isinstance(data, dict):
            summary["size"] = len(data.keys())
        elif isinstance(data, str):
            summary["size"] = len(data)

        return summary

    def get_schema(self) -> Dict[str, Any]:
        """Return configuration schema"""
        # Get LLM configuration from mixin
        llm_schema = self._get_llm_schema_section()
        
        return {
            "type": "object",
            "properties": {
                **llm_schema,  # Include LLM configuration
                # Analysis Configuration
                "analysis_type": {
                    "type": "string",
                    "title": "Analysis Type",
                    "description": "Type of analysis to perform",
                    "enum": ["general", "statistical", "business", "technical", "exploratory"],
                    "default": "general"
                },
                "include_visualizations": {
                    "type": "boolean",
                    "title": "Include Visualization Suggestions",
                    "description": "Generate chart and graph suggestions",
                    "default": True
                },
                "focus_areas": {
                    "type": "array",
                    "title": "Focus Areas",
                    "description": "Specific areas to focus analysis on",
                    "items": {
                        "type": "string",
                        "enum": ["trends", "anomalies", "patterns", "correlations", "outliers"]
                    },
                    "default": []
                }
            }
        }

    def get_input_schema(self) -> Dict[str, Any]:
        """Define expected inputs"""
        return {
            "data": {
                "type": "any",
                "title": "Data Input",
                "description": "Data to analyze (CSV, JSON, DataFrame, or text)",
                "required": True
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Define expected outputs"""
        return {
            "insights": {
                "type": "object",
                "description": "AI-generated insights about the data"
            },
            "recommendations": {
                "type": "array",
                "description": "Actionable recommendations based on analysis"
            },
            "visualizations": {
                "type": "array",
                "description": "Suggested visualizations for the data"
            },
            "data_summary": {
                "type": "object",
                "description": "Summary statistics and metadata"
            }
        }

    def estimate_cost(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> float:
        """Estimate cost based on data size and analysis complexity"""
        data_input = inputs.get("data", "")
        
        # Base cost for analysis
        base_cost = 0.01
        
        # Additional cost based on data size
        if isinstance(data_input, str):
            size_cost = len(data_input) / 10000 * 0.001
        elif isinstance(data_input, (list, dict)):
            size_cost = len(str(data_input)) / 10000 * 0.001
        else:
            size_cost = 0.001
            
        return base_cost + size_cost


# Register the node
NodeRegistry.register(
    "smart_data_analyzer",
    SmartDataAnalyzerNode,
    SmartDataAnalyzerNode().get_metadata(),
)