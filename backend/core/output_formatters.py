"""
Output Formatters for Communication Nodes

This module provides a Strategy pattern-based system for formatting node outputs
for communication nodes (Email, Slack, etc.). Each formatter handles a specific
node type or output structure, with a generic fallback for unknown formats.

Architecture:
- OutputFormatter: Abstract base class for all formatters
- FormatterRegistry: Manages and selects appropriate formatters
- Specific formatters: Handle node-specific formatting logic

This keeps the engine.py file clean and makes it easy to add new formatters.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple
import json
import re
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class OutputFormatter(ABC):
    """Abstract base class for output formatters"""
    
    @abstractmethod
    def can_format(self, node_type: str, output: Dict[str, Any]) -> bool:
        """
        Check if this formatter can handle this output.
        
        Args:
            node_type: The type of the source node
            output: The output dictionary from the node
            
        Returns:
            True if this formatter can handle the output
        """
        pass
    
    @abstractmethod
    def format(self, output: Dict[str, Any]) -> Tuple[str, List]:
        """
        Format output for communication nodes.
        
        Args:
            output: The output dictionary from the node
            
        Returns:
            Tuple of (formatted_text, attachments_list)
            - formatted_text: HTML or plain text formatted output
            - attachments_list: List of attachment dicts (for email)
        """
        pass
    
    def format_for_display(self, node_type: str, output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format output for consistent frontend display.
        
        Args:
            node_type: The type of the source node
            output: The output dictionary from the node
            
        Returns:
            Standardized display structure with:
            - display_type: "text", "html", "chart", "data", "agent_report"
            - primary_content: Main content to display
            - metadata: Structured metadata
            - actions: Available actions (copy, download, etc.)
            - attachments: Files/images
        """
        # Default implementation - can be overridden by specific formatters
        return {
            "display_type": "data",
            "primary_content": output,
            "metadata": {
                "node_type": node_type,
                "output_keys": list(output.keys()) if isinstance(output, dict) else [],
                "content_length": len(str(output))
            },
            "actions": ["copy", "download_json"],
            "attachments": []
        }


class BlogPostFormatter(OutputFormatter):
    """Formatter for blog_generator node output"""
    
    def can_format(self, node_type: str, output: Dict[str, Any]) -> bool:
        return node_type == "blog_generator" or "blog_post" in output
    
    def format(self, output: Dict[str, Any]) -> Tuple[str, List]:
        """Format blog post output as HTML"""
        blog_post = output.get("blog_post", {})
        seo_elements = output.get("seo_elements", {})
        metadata = output.get("metadata", {})
        
        parts = []
        parts.append("""<html><head><meta charset="UTF-8"></head><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">""")
        
        # Title
        title = blog_post.get("title", "Blog Post")
        parts.append(f'<h1 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">{title}</h1>')
        
        # Introduction
        if blog_post.get("introduction"):
            parts.append(f'<div style="font-size: 1.1em; color: #555; margin-bottom: 20px;">{blog_post["introduction"]}</div>')
        
        # Main content
        if blog_post.get("content"):
            parts.append(f'<div style="margin: 20px 0;">{blog_post["content"]}</div>')
        
        # Conclusion
        if blog_post.get("conclusion"):
            parts.append(f'<div style="margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #3498db;">{blog_post["conclusion"]}</div>')
        
        # Call to action
        if blog_post.get("call_to_action"):
            parts.append(f'<div style="margin: 20px 0; padding: 15px; background-color: #e8f4f8; border-radius: 5px; text-align: center; font-weight: bold;">{blog_post["call_to_action"]}</div>')
        
        # SEO elements (if available)
        if seo_elements:
            parts.append("<hr style='margin: 30px 0; border: none; border-top: 1px solid #ddd;' />")
            parts.append("<h3 style='color: #2c3e50;'>SEO Information</h3>")
            
            if seo_elements.get("meta_description"):
                parts.append(f"<p><strong>Meta Description:</strong> {seo_elements['meta_description']}</p>")
            
            if seo_elements.get("slug"):
                parts.append(f"<p><strong>URL Slug:</strong> {seo_elements['slug']}</p>")
            
            if seo_elements.get("meta_keywords") and isinstance(seo_elements["meta_keywords"], list):
                keywords = ", ".join(seo_elements["meta_keywords"])
                parts.append(f"<p><strong>Keywords:</strong> {keywords}</p>")
        
        # Metadata
        if metadata:
            parts.append("<hr style='margin: 30px 0; border: none; border-top: 1px solid #ddd;' />")
            parts.append("<h3 style='color: #2c3e50;'>Post Details</h3>")
            
            if metadata.get("word_count"):
                parts.append(f"<p><strong>Word Count:</strong> {metadata['word_count']}</p>")
            
            if metadata.get("model_used"):
                parts.append(f"<p><strong>Generated with:</strong> {metadata['model_used']}</p>")
        
        parts.append("</body></html>")
        
        html_content = "\n".join(parts)
        return html_content, []
    
    def format_for_display(self, node_type: str, output: Dict[str, Any]) -> Dict[str, Any]:
        """Format blog post for display."""
        blog_post = output.get("blog_post", {})
        seo_elements = output.get("seo_elements", {})
        
        return {
            "display_type": "html",
            "primary_content": self.format(output)[0],  # Get formatted HTML
            "metadata": {
                "node_type": node_type,
                "title": blog_post.get("title", "Blog Post"),
                "word_count": output.get("metadata", {}).get("word_count", 0),
                "has_seo": bool(seo_elements),
                "sections": ["introduction", "content", "conclusion", "call_to_action"]
            },
            "actions": ["copy", "download_html", "copy_markdown"],
            "attachments": []
        }


class ChartGeneratorFormatter(OutputFormatter):
    """Formatter for auto_chart_generator node output"""
    
    def can_format(self, node_type: str, output: Dict[str, Any]) -> bool:
        return node_type == "auto_chart_generator" or "charts" in output or "visual_charts" in output
    
    def format(self, output: Dict[str, Any]) -> Tuple[str, List]:
        """Format chart generator output as HTML with embedded images"""
        parts = []
        attachments = []
        
        # Add HTML wrapper with basic styling
        parts.append("""<html><head><meta charset="UTF-8"></head><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">""")
        
        # Add metadata summary
        metadata = output.get("metadata", {})
        if metadata:
            total_charts = metadata.get("total_charts", 0)
            visual_charts = metadata.get("visual_charts_generated", 0)
            data_points = metadata.get("data_points", 0)
            
            parts.append(f"<h2 style='color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;'>Chart Generation Results</h2>")
            parts.append(f"<p><strong>Total Charts Generated:</strong> {total_charts}</p>")
            parts.append(f"<p><strong>Visual Charts:</strong> {visual_charts}</p>")
            parts.append(f"<p><strong>Data Points Analyzed:</strong> {data_points}</p>")
        
        # Add data summary
        data_summary = output.get("data_summary", {})
        if data_summary:
            parts.append("<h3>Data Summary</h3>")
            
            if data_summary.get("data_overview"):
                parts.append(f"<p>{data_summary['data_overview']}</p>")
            
            if data_summary.get("key_insights") and isinstance(data_summary["key_insights"], list):
                parts.append("<h4>Key Insights:</h4>")
                parts.append("<ul>")
                for insight in data_summary["key_insights"]:
                    parts.append(f"<li>{insight}</li>")
                parts.append("</ul>")
            
            if data_summary.get("data_quality"):
                parts.append(f"<p><strong>Data Quality:</strong> {data_summary['data_quality']}</p>")
        
        # Add chart information with attachments
        charts = output.get("charts") or output.get("visual_charts") or []
        if charts and isinstance(charts, list):
            parts.append("<h3>Generated Charts</h3>")
            for idx, chart in enumerate(charts[:5], 1):  # Limit to first 5 charts
                title = chart.get("title", f"Chart {idx}")
                chart_type = chart.get("type", "unknown")
                parts.append(f"<p><strong>{title}</strong> ({chart_type})</p>")
                
                # If chart has base64 image, embed directly in HTML
                # Note: Some email clients (Gmail, Outlook) block base64 images, but many support them
                # We'll embed them inline AND add as attachments as fallback
                if chart.get("image_base64"):
                    # Use base64 data URI directly in img tag
                    image_src = chart["image_base64"]
                    # Ensure it has the data URI prefix
                    if not image_src.startswith("data:image"):
                        # Assume PNG if no prefix
                        image_src = f"data:image/png;base64,{image_src}"
                    
                    # Embed in HTML (works in many email clients)
                    parts.append(f'<p><img src="{image_src}" alt="{title}" style="max-width: 600px; height: auto; border: 1px solid #ddd; margin: 10px 0; display: block;" /></p>')
                    
                    # Also add as attachment as fallback (recipients can view/download)
                    # Extract base64 data for attachment
                    image_data = image_src
                    if image_data.startswith("data:image"):
                        image_data = image_data.split(",", 1)[1]
                    
                    safe_title = re.sub(r'[^a-zA-Z0-9_-]', '_', title)[:50]
                    filename = f"chart_{idx}_{safe_title}.png"
                    
                    attachments.append({
                        "filename": filename,
                        "content": image_data,
                    })
        
        # Add recommendations if available
        recommendations = output.get("chart_recommendations", [])
        if recommendations and isinstance(recommendations, list) and len(recommendations) > 0:
            parts.append("<h3>Recommendations</h3>")
            parts.append("<ul>")
            for rec in recommendations[:3]:  # Limit to first 3
                if isinstance(rec, dict):
                    message = rec.get("message", "")
                    if message:
                        parts.append(f"<li>{message}</li>")
            parts.append("</ul>")
        
        # Add note about images if we have charts
        if charts and len(charts) > 0 and any(chart.get("image_base64") for chart in charts):
            parts.append("<p style='margin-top: 20px; padding: 10px; background-color: #f0f0f0; border-left: 4px solid #3498db; font-size: 12px; color: #666;'>")
            parts.append("<strong>Note:</strong> Chart images are embedded in this email. If images don't display, they are also available as attachments.")
            parts.append("</p>")
        
        # Close HTML wrapper
        parts.append("</body></html>")
        
        html_content = "\n".join(parts)
        return html_content, attachments
    
    def format_for_display(self, node_type: str, output: Dict[str, Any]) -> Dict[str, Any]:
        """Format chart generator for display."""
        charts = output.get("charts") or output.get("visual_charts") or []
        metadata = output.get("metadata", {})
        
        # Extract chart images for attachments
        chart_attachments = []
        for idx, chart in enumerate(charts[:5]):  # Limit to 5 charts
            if chart.get("image_base64"):
                chart_attachments.append({
                    "type": "image",
                    "name": f"chart_{idx + 1}_{chart.get('title', 'unnamed').replace(' ', '_')}.png",
                    "data": chart["image_base64"],
                    "mime_type": "image/png"
                })
        
        return {
            "display_type": "chart",
            "primary_content": {
                "charts": charts,
                "summary": output.get("data_summary", {}),
                "metadata": metadata
            },
            "metadata": {
                "node_type": node_type,
                "total_charts": len(charts),
                "visual_charts": metadata.get("visual_charts_generated", 0),
                "data_points": metadata.get("data_points", 0),
                "chart_types": list(set([c.get("type", "unknown") for c in charts]))
            },
            "actions": ["copy", "download_images", "download_html"],
            "attachments": chart_attachments
        }


class ProposalFormatter(OutputFormatter):
    """Formatter for proposal_generator node output"""
    
    def can_format(self, node_type: str, output: Dict[str, Any]) -> bool:
        return node_type == "proposal_generator" or "proposal_content" in output or "proposal_summary" in output
    
    def format(self, output: Dict[str, Any]) -> Tuple[str, List]:
        """Format proposal output as HTML"""
        parts = []
        parts.append("""<html><head><meta charset="UTF-8"></head><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">""")
        
        # Proposal summary (executive summary)
        if output.get("proposal_summary"):
            parts.append(f'<h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">Executive Summary</h2>')
            parts.append(f'<div style="margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #3498db;">{output["proposal_summary"]}</div>')
        
        # Proposal content
        proposal_content = output.get("proposal_content", {})
        if proposal_content:
            parts.append("<h2 style='color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;'>Proposal Details</h2>")
            
            if isinstance(proposal_content, dict):
                for key, value in proposal_content.items():
                    if isinstance(value, str):
                        parts.append(f"<h3>{key.replace('_', ' ').title()}</h3>")
                        parts.append(f"<p>{value}</p>")
                    elif isinstance(value, list):
                        parts.append(f"<h3>{key.replace('_', ' ').title()}</h3>")
                        parts.append("<ul>")
                        for item in value:
                            parts.append(f"<li>{item}</li>")
                        parts.append("</ul>")
            else:
                parts.append(f"<div>{proposal_content}</div>")
        
        # Pricing section
        pricing = output.get("pricing_section")
        if pricing:
            parts.append("<h2 style='color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;'>Pricing</h2>")
            if isinstance(pricing, dict):
                for key, value in pricing.items():
                    parts.append(f"<p><strong>{key.replace('_', ' ').title()}:</strong> {value}</p>")
            else:
                parts.append(f"<div>{pricing}</div>")
        
        # Implementation timeline
        timeline = output.get("implementation_timeline")
        if timeline and isinstance(timeline, list):
            parts.append("<h2 style='color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;'>Implementation Timeline</h2>")
            parts.append("<ul>")
            for phase in timeline:
                if isinstance(phase, dict):
                    phase_name = phase.get("phase", phase.get("name", "Phase"))
                    phase_desc = phase.get("description", phase.get("desc", ""))
                    parts.append(f"<li><strong>{phase_name}:</strong> {phase_desc}</li>")
                else:
                    parts.append(f"<li>{phase}</li>")
            parts.append("</ul>")
        
        # Next steps
        if output.get("next_steps"):
            parts.append("<h2 style='color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;'>Next Steps</h2>")
            next_steps = output.get("next_steps")
            if isinstance(next_steps, list):
                parts.append("<ul>")
                for step in next_steps:
                    parts.append(f"<li>{step}</li>")
                parts.append("</ul>")
            else:
                parts.append(f"<p>{next_steps}</p>")
        
        parts.append("</body></html>")
        
        html_content = "\n".join(parts)
        return html_content, []


class BrandFormatter(OutputFormatter):
    """Formatter for brand_generator node output"""
    
    def can_format(self, node_type: str, output: Dict[str, Any]) -> bool:
        return node_type == "brand_generator" or "brand_assets" in output
    
    def format(self, output: Dict[str, Any]) -> Tuple[str, List]:
        """Format brand generator output as HTML"""
        parts = []
        parts.append("""<html><head><meta charset="UTF-8"></head><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">""")
        
        parts.append('<h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">Brand Assets</h2>')
        
        # Brand assets
        brand_assets = output.get("brand_assets", {})
        if brand_assets:
            if isinstance(brand_assets, dict):
                for key, value in brand_assets.items():
                    parts.append(f"<h3>{key.replace('_', ' ').title()}</h3>")
                    if isinstance(value, (list, dict)):
                        parts.append(f"<pre>{json.dumps(value, indent=2)}</pre>")
                    else:
                        parts.append(f"<p>{value}</p>")
            else:
                parts.append(f"<div>{brand_assets}</div>")
        
        # Style guide
        if output.get("style_guide"):
            parts.append("<h2 style='color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;'>Style Guide</h2>")
            style_guide = output.get("style_guide")
            if isinstance(style_guide, str):
                parts.append(f"<div>{style_guide}</div>")
            else:
                parts.append(f"<pre>{json.dumps(style_guide, indent=2)}</pre>")
        
        # Recommendations
        recommendations = output.get("recommendations")
        if recommendations:
            parts.append("<h2 style='color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;'>Recommendations</h2>")
            if isinstance(recommendations, list):
                parts.append("<ul>")
                for rec in recommendations:
                    parts.append(f"<li>{rec}</li>")
                parts.append("</ul>")
            else:
                parts.append(f"<p>{recommendations}</p>")
        
        parts.append("</body></html>")
        
        html_content = "\n".join(parts)
        return html_content, []


class CrewAIAgentFormatter(OutputFormatter):
    """Formatter for CrewAI agent node output"""
    
    def can_format(self, node_type: str, output: Dict[str, Any]) -> bool:
        return node_type == "crewai_agent" or "agent_outputs" in output or "agents" in output
    
    def format(self, output: Dict[str, Any]) -> Tuple[str, List]:
        """Format CrewAI agent output as structured HTML."""
        parts = []
        parts.append("""<html><head><meta charset="UTF-8"></head><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">""")
        
        # Main execution summary
        if output.get("output"):
            parts.append('<h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">CrewAI Execution Report</h2>')
            parts.append(f'<div style="margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #3498db;">{output["output"]}</div>')
        
        # Individual agent outputs
        agent_outputs = output.get("agent_outputs", {})
        if agent_outputs:
            parts.append('<h3 style="color: #2c3e50;">Agent Outputs</h3>')
            for agent_role, outputs in agent_outputs.items():
                parts.append(f'<h4 style="color: #3498db;">🤖 {agent_role}</h4>')
                if isinstance(outputs, list):
                    for i, task_output in enumerate(outputs):
                        if isinstance(task_output, dict) and task_output.get("output"):
                            task_name = task_output.get("task", f"Task {i+1}")
                            parts.append(f'<h5 style="color: #555;">{task_name}</h5>')
                            parts.append(f'<p style="margin-left: 20px;">{task_output["output"]}</p>')
        
        parts.append("</body></html>")
        return "\n".join(parts), []
    
    def format_for_display(self, node_type: str, output: Dict[str, Any]) -> Dict[str, Any]:
        """Format CrewAI agent for display."""
        agent_outputs = output.get("agent_outputs", {})
        agents = output.get("agents", [])
        
        # Count total tasks
        total_tasks = 0
        for outputs in agent_outputs.values():
            if isinstance(outputs, list):
                total_tasks += len(outputs)
        
        return {
            "display_type": "agent_report",
            "primary_content": {
                "summary": output.get("output", ""),
                "agent_outputs": agent_outputs,
                "agents": agents
            },
            "metadata": {
                "node_type": node_type,
                "agent_count": len(agents),
                "total_tasks": total_tasks,
                "execution_summary": output.get("output", "")[:200] if output.get("output") else ""
            },
            "actions": ["copy", "download_report", "copy_individual"],
            "attachments": []
        }


class StorageNodeFormatter(OutputFormatter):
    """Formatter for storage nodes (Airtable, Google Sheets, Data Loader) that output structured data"""
    
    def can_format(self, node_type: str, output: Dict[str, Any]) -> bool:
        # Check if this is a storage node type
        if node_type in ["airtable", "google_sheets", "data_loader", "google_drive", "s3", "database", "vector_store"]:
            return True
        # Check if output has structured data format (data + schema + metadata)
        if isinstance(output, dict):
            has_data = "data" in output and isinstance(output.get("data"), list)
            has_schema = "schema" in output
            has_metadata = "metadata" in output
            if has_data and (has_schema or has_metadata):
                return True
        return False
    
    def format(self, output: Dict[str, Any]) -> Tuple[str, List]:
        """Format storage node output as HTML table"""
        data = output.get("data", [])
        schema = output.get("schema", {})
        metadata = output.get("metadata", {})
        
        parts = []
        parts.append("""<html><head><meta charset="UTF-8"></head><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">""")
        
        # Metadata summary
        if metadata:
            parts.append("<h2 style='color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;'>Data Summary</h2>")
            if metadata.get("record_count"):
                parts.append(f"<p><strong>Records:</strong> {metadata['record_count']}</p>")
            if metadata.get("source"):
                parts.append(f"<p><strong>Source:</strong> {metadata['source']}</p>")
        
        # Schema info
        if schema:
            parts.append("<h3>Schema</h3>")
            if schema.get("columns"):
                parts.append(f"<p><strong>Columns:</strong> {', '.join(schema['columns'])}</p>")
            if schema.get("row_count"):
                parts.append(f"<p><strong>Rows:</strong> {schema['row_count']}</p>")
        
        # Data preview (first 10 rows)
        if data and isinstance(data, list) and len(data) > 0:
            parts.append("<h3>Data Preview</h3>")
            parts.append("<table style='width: 100%; border-collapse: collapse; margin-top: 10px;'>")
            
            # Header row
            if len(data) > 0:
                headers = list(data[0].keys())
                parts.append("<tr style='background-color: #f8f9fa;'>")
                for header in headers:
                    parts.append(f"<th style='padding: 8px; border: 1px solid #ddd; text-align: left;'>{header}</th>")
                parts.append("</tr>")
                
                # Data rows (limit to 10)
                for row in data[:10]:
                    parts.append("<tr>")
                    for header in headers:
                        value = row.get(header, "")
                        display_value = str(value)[:100] if value else ""
                        parts.append(f"<td style='padding: 8px; border: 1px solid #ddd;'>{display_value}</td>")
                    parts.append("</tr>")
            
            parts.append("</table>")
            if len(data) > 10:
                parts.append(f"<p style='color: #666; font-size: 12px; margin-top: 10px;'>... and {len(data) - 10} more rows</p>")
        
        parts.append("</body></html>")
        html_content = "\n".join(parts)
        return html_content, []
    
    def format_for_display(self, node_type: str, output: Dict[str, Any]) -> Dict[str, Any]:
        """Format storage node for display as structured data table"""
        data = output.get("data", [])
        schema = output.get("schema", {})
        metadata = output.get("metadata", {})
        
        # Ensure data is a list of dictionaries
        if not isinstance(data, list):
            data = []
        if data and not isinstance(data[0], dict):
            data = []
        
        return {
            "display_type": "data",
            "primary_content": {
                "data": data,
                "schema": schema,
                "metadata": metadata
            },
            "metadata": {
                "node_type": node_type,
                "record_count": len(data) if isinstance(data, list) else 0,
                "source": metadata.get("source", "unknown"),
                "has_schema": bool(schema),
                "has_data": bool(data and len(data) > 0)
            },
            "actions": ["copy", "download_json"],
            "attachments": []
        }


class GenericFormatter(OutputFormatter):
    """Fallback formatter for unknown output structures"""
    
    def can_format(self, node_type: str, output: Dict[str, Any]) -> bool:
        return True  # Always can format (fallback)
    
    def format(self, output: Dict[str, Any]) -> Tuple[str, List]:
        """Format any output by extracting text-like fields"""
        parts = []
        
        # Try to extract text-like fields
        text_fields = ["content", "text", "summary", "message", "description", "output", "result"]
        text_parts = []
        
        for field in text_fields:
            if field in output:
                value = output[field]
                if isinstance(value, str) and value.strip():
                    text_parts.append(f"<h3>{field.replace('_', ' ').title()}</h3>")
                    text_parts.append(f"<p>{value}</p>")
                elif isinstance(value, (dict, list)) and value:
                    text_parts.append(f"<h3>{field.replace('_', ' ').title()}</h3>")
                    text_parts.append(f"<pre>{json.dumps(value, indent=2)}</pre>")
        
        if text_parts:
            parts.append("""<html><head><meta charset="UTF-8"></head><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">""")
            parts.extend(text_parts)
            parts.append("</body></html>")
            html_content = "\n".join(parts)
            return html_content, []
        
        # Last resort: format entire output as JSON
        parts.append("""<html><head><meta charset="UTF-8"></head><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">""")
        parts.append("<h2>Output</h2>")
        parts.append(f"<pre style='background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto;'>{json.dumps(output, indent=2)}</pre>")
        parts.append("</body></html>")
        
        html_content = "\n".join(parts)
        return html_content, []


class FormatterRegistry:
    """Registry that manages and selects appropriate formatters"""
    
    def __init__(self):
        """Initialize registry with all available formatters"""
        self.formatters: List[OutputFormatter] = [
            BlogPostFormatter(),
            ChartGeneratorFormatter(),
            ProposalFormatter(),
            BrandFormatter(),
            CrewAIAgentFormatter(),
            StorageNodeFormatter(),  # Before GenericFormatter to catch storage nodes
            GenericFormatter(),  # Always last (fallback)
        ]
        logger.debug(f"Initialized FormatterRegistry with {len(self.formatters)} formatters")
    
    def format_output(self, node_type: str, output: Dict[str, Any]) -> Tuple[str, List]:
        """
        Find and use appropriate formatter for the given output.
        
        Args:
            node_type: The type of the source node
            output: The output dictionary from the node
            
        Returns:
            Tuple of (formatted_text, attachments_list)
        """
        if not output:
            return "", []
        
        # Try each formatter in order
        for formatter in self.formatters:
            if formatter.can_format(node_type, output):
                try:
                    formatted_text, attachments = formatter.format(output)
                    logger.debug(f"Formatted output from {node_type} using {formatter.__class__.__name__}")
                    return formatted_text, attachments
                except Exception as e:
                    logger.warning(f"Formatter {formatter.__class__.__name__} failed: {e}, trying next formatter")
                    continue
        
        # Should never reach here (GenericFormatter always matches)
        logger.warning(f"No formatter matched for {node_type}, using JSON fallback")
        import json
        return json.dumps(output, indent=2), []
    
    def format_for_display(self, node_type: str, output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find and use appropriate formatter for consistent frontend display.
        
        Args:
            node_type: The type of the source node
            output: The output dictionary from the node
            
        Returns:
            Standardized display structure
        """
        if not output:
            return {
                "display_type": "empty",
                "primary_content": None,
                "metadata": {"node_type": node_type},
                "actions": [],
                "attachments": []
            }
        
        # Try each formatter in order
        for formatter in self.formatters:
            if formatter.can_format(node_type, output):
                try:
                    display_data = formatter.format_for_display(node_type, output)
                    logger.debug(f"Formatted display for {node_type} using {formatter.__class__.__name__}")
                    return display_data
                except Exception as e:
                    logger.warning(f"Display formatter {formatter.__class__.__name__} failed: {e}, trying next formatter")
                    continue
        
        # Fallback if all formatters fail
        logger.warning(f"No display formatter matched for {node_type}, using generic fallback")
        return {
            "display_type": "data",
            "primary_content": output,
            "metadata": {
                "node_type": node_type,
                "error": "No suitable formatter found"
            },
            "actions": ["copy", "download_json"],
            "attachments": []
        }


# Global registry instance
_formatter_registry: FormatterRegistry = None


def get_formatter_registry() -> FormatterRegistry:
    """Get or create the global formatter registry instance"""
    global _formatter_registry
    if _formatter_registry is None:
        _formatter_registry = FormatterRegistry()
    return _formatter_registry

