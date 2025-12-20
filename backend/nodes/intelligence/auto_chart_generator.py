"""
Auto Chart Generator Node - Creates visualizations from any dataset

This node automatically generates appropriate charts and visualizations
based on data type, structure, and content analysis.
"""

import json
import pandas as pd
import base64
import io
from datetime import datetime
from typing import Any, Dict, Optional
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
from backend.nodes.base import BaseNode
from backend.nodes.intelligence.llm_mixin import LLMConfigMixin
from backend.core.exceptions import NodeExecutionError, NodeValidationError
from backend.core.node_registry import NodeRegistry


class AutoChartGeneratorNode(BaseNode, LLMConfigMixin):
    node_type = "auto_chart_generator"
    name = "Auto Chart Generator"
    description = "Automatically creates appropriate visualizations from any dataset"
    category = "intelligence"

    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute automatic chart generation"""
        try:
            await self.stream_progress("auto_chart_generator", 0.1, "Analyzing data for visualization...")

            # Get inputs - accept multiple field names for flexibility
            # text_input provides "text", but we also accept "data", "content", "output"
            data_input = (
                inputs.get("data") or 
                inputs.get("text") or 
                inputs.get("content") or 
                inputs.get("output") or
                ""
            )
            chart_types = config.get("chart_types", ["auto"])
            max_charts = config.get("max_charts", 5)
            include_interactive = config.get("include_interactive", True)
            theme = config.get("theme", "default")

            if not data_input:
                raise NodeValidationError("Data input is required. Connect a text_input, file_loader, or data_loader node.")

            await self.stream_progress("auto_chart_generator", 0.3, "Processing data format...")

            # Parse and analyze data
            processed_data = self._parse_data_for_visualization(data_input)
            
            await self.stream_progress("auto_chart_generator", 0.5, "Determining optimal chart types...")

            # Determine best chart types
            suggested_charts = self._analyze_data_for_charts(processed_data, chart_types)
            
            await self.stream_progress("auto_chart_generator", 0.7, "Generating visualizations...")

            # Generate chart configurations
            chart_configs = self._generate_chart_configs(
                processed_data, suggested_charts[:max_charts], theme
            )

            await self.stream_progress("auto_chart_generator", 0.9, "Creating chart data...")

            # Generate chart data and metadata
            charts = []
            for config_item in chart_configs:
                chart_data = self._create_chart_data(processed_data, config_item)
                charts.append(chart_data)

            # Try to use LLM for better summaries and recommendations
            use_llm = False
            llm_config = None
            
            try:
                llm_config = self._resolve_llm_config(config)
                # Check if we have a valid API key
                if llm_config and llm_config.get("api_key") and llm_config.get("provider"):
                    use_llm = True
                    await self.stream_log("auto_chart_generator", f"Using LLM: {llm_config['provider']}:{llm_config['model']}", "info")
                else:
                    await self.stream_log("auto_chart_generator", "No LLM configuration available, using pattern matching", "info")
            except Exception as llm_error:
                await self.stream_log("auto_chart_generator", f"LLM config failed: {llm_error}, using pattern matching", "warning")
                use_llm = False

            if use_llm and llm_config:
                try:
                    data_summary = await self._generate_llm_data_summary(processed_data, llm_config)
                    chart_recommendations = await self._generate_llm_chart_recommendations(processed_data, charts, llm_config)
                except Exception as e:
                    await self.stream_log("auto_chart_generator", f"LLM generation failed, using pattern matching: {e}", "warning")
                    data_summary = self._generate_data_summary(processed_data)
                    chart_recommendations = self._generate_chart_recommendations(processed_data)
            else:
                data_summary = self._generate_data_summary(processed_data)
                chart_recommendations = self._generate_chart_recommendations(processed_data)

            # Create result with detailed logging
            await self.stream_log("auto_chart_generator", f"Generated {len(charts)} charts successfully", "info")
            
            # Count successful visual charts
            visual_charts_count = sum(1 for chart in charts if chart.get("plotly_json") is not None)
            
            result = {
                "charts": charts,
                "data_summary": data_summary,
                "chart_recommendations": chart_recommendations,
                "visual_charts": [chart for chart in charts if chart.get("plotly_json")],
                "metadata": {
                    "total_charts": len(charts),
                    "visual_charts_generated": visual_charts_count,
                    "data_points": len(processed_data) if isinstance(processed_data, pd.DataFrame) else 1,
                    "theme": theme,
                    "generation_timestamp": datetime.now().isoformat(),
                    "used_llm": use_llm,
                    "llm_provider": llm_config.get("provider") if llm_config else None,
                    "chart_types_generated": list(set(chart["type"] for chart in charts))
                }
            }

            await self.stream_progress("auto_chart_generator", 1.0, "Chart generation complete!")
            await self.stream_log("auto_chart_generator", f"Returning result with {len(charts)} charts", "info")
            return result

        except Exception as e:
            await self.stream_log("auto_chart_generator", f"Chart generation error: {str(e)}", "error")
            raise NodeExecutionError(f"Chart generation failed: {str(e)}")

    def _parse_data_for_visualization(self, data_input: Any) -> pd.DataFrame:
        """Parse input data into a DataFrame for visualization"""
        if isinstance(data_input, str):
            try:
                # Try JSON first
                json_data = json.loads(data_input)
                if isinstance(json_data, list):
                    return pd.DataFrame(json_data)
                elif isinstance(json_data, dict):
                    # Convert dict to DataFrame
                    if all(isinstance(v, (list, tuple)) for v in json_data.values()):
                        return pd.DataFrame(json_data)
                    else:
                        return pd.DataFrame([json_data])
            except json.JSONDecodeError:
                # Try CSV parsing
                try:
                    return pd.read_csv(io.StringIO(data_input))
                except:
                    # Create a simple DataFrame from text
                    lines = data_input.strip().split('\n')
                    return pd.DataFrame({'text': lines, 'line_number': range(1, len(lines) + 1)})
        
        elif isinstance(data_input, dict):
            if all(isinstance(v, (list, tuple)) for v in data_input.values()):
                return pd.DataFrame(data_input)
            else:
                return pd.DataFrame([data_input])
        
        elif isinstance(data_input, list):
            return pd.DataFrame(data_input)
        
        elif isinstance(data_input, pd.DataFrame):
            return data_input
        
        else:
            # Create simple DataFrame from any other input
            return pd.DataFrame({'value': [data_input], 'index': [0]})

    def _analyze_data_for_charts(self, df: pd.DataFrame, requested_types: list) -> list:
        """Analyze DataFrame to suggest appropriate chart types"""
        if "auto" in requested_types:
            suggested_charts = []
            
            # Get column types
            numerical_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
            
            # Suggest charts based on data structure
            if len(numerical_cols) >= 2:
                suggested_charts.append("scatter")
                if len(numerical_cols) >= 3:
                    suggested_charts.append("bubble")
            
            if len(numerical_cols) >= 1:
                suggested_charts.append("histogram")
                suggested_charts.append("box")
                
                if len(categorical_cols) >= 1:
                    suggested_charts.append("bar")
                    suggested_charts.append("violin")
            
            if len(categorical_cols) >= 1:
                suggested_charts.append("pie")
                suggested_charts.append("donut")
            
            if len(datetime_cols) >= 1 and len(numerical_cols) >= 1:
                suggested_charts.append("line")
                suggested_charts.append("area")
            
            # Add heatmap for correlation analysis
            if len(numerical_cols) >= 3:
                suggested_charts.append("heatmap")
            
            return suggested_charts[:5]  # Limit to 5 suggestions
        
        else:
            return requested_types

    def _generate_chart_configs(self, df: pd.DataFrame, chart_types: list, theme: str) -> list:
        """Generate chart configurations for each chart type"""
        configs = []
        
        numerical_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        for chart_type in chart_types:
            config = {
                "type": chart_type,
                "theme": theme,
                "title": f"{chart_type.title()} Chart",
                "data": {},
                "options": {}
            }
            
            if chart_type == "scatter" and len(numerical_cols) >= 2:
                config.update({
                    "x_column": numerical_cols[0],
                    "y_column": numerical_cols[1],
                    "title": f"{numerical_cols[1]} vs {numerical_cols[0]}"
                })
            
            elif chart_type == "bar" and len(categorical_cols) >= 1:
                config.update({
                    "x_column": categorical_cols[0],
                    "y_column": numerical_cols[0] if numerical_cols else "count",
                    "title": f"{numerical_cols[0] if numerical_cols else 'Count'} by {categorical_cols[0]}"
                })
            
            elif chart_type == "line" and len(datetime_cols) >= 1 and len(numerical_cols) >= 1:
                config.update({
                    "x_column": datetime_cols[0],
                    "y_column": numerical_cols[0],
                    "title": f"{numerical_cols[0]} Over Time"
                })
            
            elif chart_type == "histogram" and len(numerical_cols) >= 1:
                config.update({
                    "column": numerical_cols[0],
                    "bins": 20,
                    "title": f"Distribution of {numerical_cols[0]}"
                })
            
            elif chart_type == "pie" and len(categorical_cols) >= 1:
                config.update({
                    "category_column": categorical_cols[0],
                    "value_column": numerical_cols[0] if numerical_cols else "count",
                    "title": f"Distribution of {categorical_cols[0]}"
                })
            
            elif chart_type == "heatmap" and len(numerical_cols) >= 2:
                config.update({
                    "columns": numerical_cols[:5],  # Limit to 5 columns
                    "title": "Correlation Heatmap"
                })
            
            configs.append(config)
        
        return configs

    def _create_chart_data(self, df: pd.DataFrame, config: dict) -> dict:
        """Create chart data structure and visual chart from DataFrame and config"""
        chart_type = config["type"]
        chart_id = f"chart_{chart_type}_{datetime.now().strftime('%H%M%S')}"
        chart_data = {
            "id": chart_id,
            "type": chart_type,
            "title": config["title"],
            "data": {},
            "config": config,
            "plotly_json": None,  # Will contain the plotly chart
            "chart_html": None,   # Will contain HTML representation
            "metadata": {
                "rows": len(df),
                "columns": len(df.columns)
            }
        }
        
        try:
            if chart_type == "scatter":
                x_col, y_col = config["x_column"], config["y_column"]
                chart_data["data"] = {
                    "x": [float(x) if pd.notna(x) else None for x in df[x_col].tolist()],
                    "y": [float(y) if pd.notna(y) else None for y in df[y_col].tolist()],
                    "labels": {"x": x_col, "y": y_col}
                }
            
            elif chart_type == "bar":
                x_col = config["x_column"]
                y_col = config.get("y_column", "count")
                
                if y_col == "count":
                    # Count frequency
                    value_counts = df[x_col].value_counts()
                    chart_data["data"] = {
                        "x": [str(x) for x in value_counts.index.tolist()],
                        "y": [int(y) for y in value_counts.values.tolist()],
                        "labels": {"x": x_col, "y": "Count"}
                    }
                else:
                    # Group by categorical and sum numerical
                    grouped = df.groupby(x_col)[y_col].sum()
                    chart_data["data"] = {
                        "x": [str(x) for x in grouped.index.tolist()],
                        "y": [float(y) if pd.notna(y) else 0 for y in grouped.values.tolist()],
                        "labels": {"x": x_col, "y": y_col}
                    }
            
            elif chart_type == "line":
                x_col, y_col = config["x_column"], config["y_column"]
                sorted_df = df.sort_values(x_col)
                chart_data["data"] = {
                    "x": [str(x) if not isinstance(x, (int, float)) else x for x in sorted_df[x_col].tolist()],
                    "y": [float(y) if pd.notna(y) else None for y in sorted_df[y_col].tolist()],
                    "labels": {"x": x_col, "y": y_col}
                }
            
            elif chart_type == "histogram":
                col = config["column"]
                bins = config.get("bins", 20)
                chart_data["data"] = {
                    "values": [float(x) if pd.notna(x) else None for x in df[col].tolist()],
                    "bins": bins,
                    "labels": {"x": col, "y": "Frequency"}
                }
            
            elif chart_type == "pie":
                cat_col = config["category_column"]
                val_col = config.get("value_column", "count")
                
                if val_col == "count":
                    value_counts = df[cat_col].value_counts()
                    chart_data["data"] = {
                        "labels": [str(x) for x in value_counts.index.tolist()],
                        "values": [int(x) for x in value_counts.values.tolist()]
                    }
                else:
                    grouped = df.groupby(cat_col)[val_col].sum()
                    chart_data["data"] = {
                        "labels": [str(x) for x in grouped.index.tolist()],
                        "values": [float(x) if pd.notna(x) else 0 for x in grouped.values.tolist()]
                    }
            
            elif chart_type == "heatmap":
                columns = config["columns"]
                correlation_matrix = df[columns].corr()
                chart_data["data"] = {
                    "matrix": [[float(x) if pd.notna(x) else None for x in row] for row in correlation_matrix.values.tolist()],
                    "labels": [str(x) for x in correlation_matrix.index.tolist()],
                    "columns": [str(x) for x in correlation_matrix.columns.tolist()]
                }
        
        except Exception as e:
            chart_data["error"] = f"Failed to generate {chart_type} chart: {str(e)}"
        
        # Generate Plotly visualization
        try:
            plotly_fig = self._create_plotly_chart(df, chart_type, config)
            if plotly_fig:
                chart_data["plotly_json"] = plotly_fig.to_json()
                chart_data["chart_html"] = plotly_fig.to_html(include_plotlyjs='cdn', div_id=chart_id)
                
                # Generate base64 image for direct display (if kaleido is available)
                try:
                    img_bytes = plotly_fig.to_image(format="png", width=800, height=600)
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                    chart_data["image_base64"] = f"data:image/png;base64,{img_base64}"
                except Exception as img_error:
                    # Fallback: Just provide the HTML version
                    chart_data["image_error"] = f"Image generation failed: {str(img_error)}"
        except Exception as e:
            chart_data["chart_error"] = f"Failed to create visual chart: {str(e)}"
        
        return chart_data

    def _create_plotly_chart(self, df: pd.DataFrame, chart_type: str, config: dict):
        """Create a Plotly chart based on the chart type and configuration"""
        try:
            if chart_type == "scatter":
                x_col, y_col = config["x_column"], config["y_column"]
                fig = px.scatter(df, x=x_col, y=y_col, title=config["title"])
                
            elif chart_type == "bar":
                x_col = config["x_column"]
                y_col = config.get("y_column", "count")
                
                if y_col == "count":
                    # Count frequency
                    value_counts = df[x_col].value_counts().reset_index()
                    value_counts.columns = [x_col, "count"]
                    fig = px.bar(value_counts, x=x_col, y="count", title=config["title"])
                else:
                    # Group by categorical and sum numerical
                    grouped = df.groupby(x_col)[y_col].sum().reset_index()
                    fig = px.bar(grouped, x=x_col, y=y_col, title=config["title"])
            
            elif chart_type == "line":
                x_col, y_col = config["x_column"], config["y_column"]
                sorted_df = df.sort_values(x_col)
                fig = px.line(sorted_df, x=x_col, y=y_col, title=config["title"])
            
            elif chart_type == "histogram":
                col = config["column"]
                bins = config.get("bins", 20)
                fig = px.histogram(df, x=col, nbins=bins, title=config["title"])
            
            elif chart_type == "pie":
                cat_col = config["category_column"]
                val_col = config.get("value_column", "count")
                
                if val_col == "count":
                    value_counts = df[cat_col].value_counts().reset_index()
                    value_counts.columns = [cat_col, "count"]
                    fig = px.pie(value_counts, values="count", names=cat_col, title=config["title"])
                else:
                    grouped = df.groupby(cat_col)[val_col].sum().reset_index()
                    fig = px.pie(grouped, values=val_col, names=cat_col, title=config["title"])
            
            elif chart_type == "heatmap":
                columns = config["columns"]
                correlation_matrix = df[columns].corr()
                fig = px.imshow(correlation_matrix, 
                               title=config["title"],
                               labels=dict(x="Features", y="Features", color="Correlation"),
                               x=correlation_matrix.columns,
                               y=correlation_matrix.columns)
            
            elif chart_type == "box":
                numerical_cols = df.select_dtypes(include=['number']).columns.tolist()
                if numerical_cols:
                    col = numerical_cols[0]
                    fig = px.box(df, y=col, title=f"Box Plot - {col}")
                else:
                    return None
            
            else:
                return None
                
            # Apply theme
            theme = config.get("theme", "default")
            if theme == "dark":
                fig.update_layout(template="plotly_dark")
            elif theme == "professional":
                fig.update_layout(template="plotly_white")
            
            return fig
            
        except Exception as e:
            # Return None if chart generation fails
            return None

    def _generate_data_summary(self, df: pd.DataFrame) -> dict:
        """Generate summary of the data for context"""
        return {
            "shape": list(df.shape),
            "columns": list(df.columns),
            "dtypes": {str(k): str(v) for k, v in df.dtypes.to_dict().items()},  # Convert dtypes to strings
            "missing_values": {str(k): int(v) for k, v in df.isnull().sum().to_dict().items()},  # Convert to basic types
            "numerical_columns": df.select_dtypes(include=['number']).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=['object', 'category']).columns.tolist(),
            "datetime_columns": df.select_dtypes(include=['datetime64']).columns.tolist()
        }

    def _generate_chart_recommendations(self, df: pd.DataFrame) -> list:
        """Generate recommendations for chart improvements"""
        recommendations = []
        
        numerical_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Data size recommendations
        if len(df) > 1000:
            recommendations.append({
                "type": "performance",
                "message": "Large dataset detected. Consider sampling for better performance.",
                "action": "Sample data or use aggregation"
            })
        
        # Missing data warnings
        missing_data = df.isnull().sum()
        high_missing = missing_data[missing_data > len(df) * 0.1]
        if not high_missing.empty:
            recommendations.append({
                "type": "data_quality",
                "message": f"Columns with significant missing data: {list(high_missing.index)}",
                "action": "Consider data cleaning or imputation"
            })
        
        # Chart-specific recommendations
        if len(categorical_cols) > 0:
            unique_counts = df[categorical_cols].nunique()
            high_cardinality = unique_counts[unique_counts > 20]
            if not high_cardinality.empty:
                recommendations.append({
                    "type": "visualization",
                    "message": f"High cardinality categorical columns: {list(high_cardinality.index)}",
                    "action": "Consider grouping or filtering for clearer charts"
                })
        
        return recommendations

    async def _generate_llm_data_summary(self, df: pd.DataFrame, llm_config: Dict[str, Any]) -> dict:
        """Generate intelligent data summary using LLM"""
        
        # Prepare data summary for LLM
        data_info = {
            "shape": list(df.shape),
            "columns": list(df.columns),
            "dtypes": {str(k): str(v) for k, v in df.dtypes.to_dict().items()},
            "sample_data": df.head(5).to_dict('records') if len(df) > 0 else [],
            "numerical_summary": {str(k): {str(k2): float(v2) if pd.notna(v2) else None for k2, v2 in v.items()} for k, v in df.describe().to_dict().items()} if len(df.select_dtypes(include=['number']).columns) > 0 else {}
        }
        
        prompt = f"""Analyze this dataset and provide a comprehensive summary.

Dataset Information:
- Shape: {data_info['shape']} (rows, columns)
- Columns: {', '.join(data_info['columns'])}
- Data Types: {data_info['dtypes']}
- Sample Data: {str(data_info['sample_data'][:3])}

Return a JSON object with:
- "data_overview": Brief description of what the data represents
- "key_insights": Array of 3-5 key insights about the data
- "data_quality": Assessment of data quality (missing values, outliers, etc.)
- "recommended_analysis": Array of recommended analysis approaches
- "potential_issues": Array of any data quality issues or concerns

Make it insightful and actionable."""
        
        try:
            import re
            llm_response = await self._call_llm(prompt, llm_config, max_tokens=800)
            
            # Try to parse JSON
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                llm_summary = json.loads(json_match.group())
                # Merge with technical summary
                base_summary = self._generate_data_summary(df)
                base_summary.update(llm_summary)
                return base_summary
            else:
                return self._generate_data_summary(df)
        except Exception:
            return self._generate_data_summary(df)

    async def _generate_llm_chart_recommendations(self, df: pd.DataFrame, charts: list, llm_config: Dict[str, Any]) -> list:
        """Generate intelligent chart recommendations using LLM"""
        
        chart_summary = "\n".join([
            f"- {chart.get('type', 'unknown')}: {chart.get('title', 'Untitled')}"
            for chart in charts[:5]
        ])
        
        data_info = f"""
Data Shape: {df.shape}
Columns: {', '.join(df.columns.tolist()[:10])}
Numerical Columns: {len(df.select_dtypes(include=['number']).columns)}
Categorical Columns: {len(df.select_dtypes(include=['object', 'category']).columns)}
"""
        
        prompt = f"""Based on this dataset and generated charts, provide recommendations for improving visualizations.

Dataset:
{data_info}

Generated Charts:
{chart_summary}

Provide 5-7 recommendations in JSON format as an array of objects, each with:
- "type": "visualization" | "data_quality" | "performance" | "design"
- "message": Brief recommendation message
- "action": Specific actionable suggestion
- "priority": "high" | "medium" | "low"

Focus on:
1. Chart type improvements
2. Data presentation enhancements
3. Visual design suggestions
4. Performance optimizations
5. Missing visualizations that would be valuable"""
        
        try:
            import re
            llm_response = await self._call_llm(prompt, llm_config, max_tokens=600)
            
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                recommendations = json.loads(json_match.group())
                return recommendations[:7]
            else:
                return self._generate_chart_recommendations(df)
        except Exception:
            return self._generate_chart_recommendations(df)

    def get_schema(self) -> Dict[str, Any]:
        """Return configuration schema"""
        # Get LLM config schema from mixin
        llm_schema = self._get_llm_schema_section()
        
        return {
            "type": "object",
            "properties": {
                **llm_schema,  # Include LLM provider configuration
                "chart_types": {
                    "type": "array",
                    "title": "Chart Types",
                    "description": "Select chart types to generate (use 'auto' to let the system choose)",
                    "items": {
                        "type": "string",
                        "enum": ["auto", "scatter", "line", "bar", "histogram", "pie", "box", "heatmap", "area", "donut", "violin", "bubble"]
                    },
                    "default": ["auto"],
                    "uniqueItems": True,
                    "minItems": 1,
                    "maxItems": 5
                },
                "max_charts": {
                    "type": "integer",
                    "title": "Maximum Charts",
                    "description": "Maximum number of charts to generate",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5
                },
                "theme": {
                    "type": "string",
                    "title": "Chart Theme",
                    "description": "Visual theme for the charts",
                    "enum": ["default", "dark", "light", "professional", "colorful"],
                    "default": "default"
                },
                "include_interactive": {
                    "type": "boolean",
                    "title": "Include Interactive Elements",
                    "description": "Add interactive features to charts",
                    "default": True
                }
            }
        }

    def get_input_schema(self) -> Dict[str, Any]:
        """Define expected inputs"""
        return {
            "data": {
                "type": "any",
                "title": "Data Input",
                "description": "Data to visualize (CSV, JSON, DataFrame, or structured text)",
                "required": True
            }
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Define expected outputs"""
        return {
            "charts": {
                "type": "array",
                "description": "Generated chart configurations, data, and Plotly visualizations"
            },
            "visual_charts": {
                "type": "array",
                "description": "Charts with successfully generated Plotly visualizations"
            },
            "data_summary": {
                "type": "object",
                "description": "AI-powered summary of input data characteristics and insights"
            },
            "chart_recommendations": {
                "type": "array",
                "description": "AI-generated recommendations for chart improvements"
            },
            "metadata": {
                "type": "object",
                "description": "Generation metadata, statistics, and chart information"
            }
        }

    def estimate_cost(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> float:
        """Estimate cost based on data size and number of charts"""
        data_input = inputs.get("data", "")
        max_charts = config.get("max_charts", 5)
        
        # Base cost per chart
        base_cost = 0.005 * max_charts
        
        # Additional cost based on data complexity
        if isinstance(data_input, str):
            complexity_cost = len(data_input) / 5000 * 0.001
        else:
            complexity_cost = 0.001
            
        return base_cost + complexity_cost


# Register the node
NodeRegistry.register(
    "auto_chart_generator",
    AutoChartGeneratorNode,
    AutoChartGeneratorNode().get_metadata(),
)