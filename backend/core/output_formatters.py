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


class MeetingSummaryFormatter(OutputFormatter):
    """Formatter for meeting_summarizer node output"""
    
    def can_format(self, node_type: str, output: Dict[str, Any]) -> bool:
        return node_type == "meeting_summarizer" or "meeting_summary" in output
    
    def format(self, output: Dict[str, Any]) -> Tuple[str, List]:
        """Format meeting summary output as HTML"""
        meeting_summary = output.get("meeting_summary", {})
        follow_ups = output.get("follow_up_recommendations", [])
        metadata = output.get("metadata", {})
        
        parts = []
        parts.append("""<html><head><meta charset="UTF-8"></head><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #e2e8f0; background-color: transparent; max-width: 900px; margin: 0 auto; padding: 20px;">""")
        
        # Title
        title = meeting_summary.get("title", metadata.get("meeting_title", "Meeting Summary"))
        parts.append(f"<h1 style='color: #60a5fa; border-bottom: 3px solid #3b82f6; padding-bottom: 10px;'>{title}</h1>")
        
        # Metadata
        if metadata:
            parts.append("<div style='background-color: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 5px; margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.1);'>")
            if metadata.get("meeting_date"):
                parts.append(f"<p><strong>Date:</strong> {metadata['meeting_date']}</p>")
            if metadata.get("attendee_count"):
                parts.append(f"<p><strong>Attendees:</strong> {metadata['attendee_count']}</p>")
            if metadata.get("duration_estimate"):
                parts.append(f"<p><strong>Duration:</strong> {metadata['duration_estimate']}</p>")
            parts.append("</div>")
        
        # Executive Summary
        exec_summary = meeting_summary.get("executive_summary", "")
        if exec_summary:
            parts.append("<h2 style='color: #60a5fa; margin-top: 30px;'>Executive Summary</h2>")
            # Convert markdown-style headers to HTML if present
            exec_summary_html = exec_summary.replace("### ", "<h3 style='color: #93c5fd;'>").replace("\n", "</h3>\n<p>").replace("## ", "<h2 style='color: #60a5fa;'>")
            parts.append(f"<div style='background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-left: 4px solid #3b82f6; margin-bottom: 20px; border-radius: 5px;'>{exec_summary_html}</div>")
        
        # Main Topics
        main_topics = meeting_summary.get("main_topics", [])
        if main_topics:
            parts.append("<h2 style='color: #60a5fa; margin-top: 30px;'>Main Topics Discussed</h2>")
            parts.append("<ul style='list-style-type: none; padding: 0;'>")
            for topic in main_topics[:10]:  # Limit to 10 topics
                topic_name = topic.get("topic", "Unknown Topic")
                topic_content = topic.get("content", "")[:300]  # Truncate long content
                parts.append(f"<li style='background-color: rgba(255, 255, 255, 0.05); padding: 15px; margin-bottom: 10px; border-radius: 5px; border: 1px solid rgba(255, 255, 255, 0.1);'>")
                parts.append(f"<strong style='color: #3b82f6;'>{topic_name}</strong>")
                if topic_content:
                    parts.append(f"<p style='margin-top: 8px; color: #cbd5e1;'>{topic_content}{'...' if len(topic.get('content', '')) > 300 else ''}</p>")
                parts.append("</li>")
            parts.append("</ul>")
        
        # Action Items
        action_items = meeting_summary.get("action_items", [])
        if action_items:
            parts.append("<h2 style='color: #60a5fa; margin-top: 30px;'>Action Items</h2>")
            parts.append("<ul style='list-style-type: none; padding: 0;'>")
            for item in action_items[:20]:  # Limit to 20 items
                desc = item.get("description", "No description")
                owner = item.get("owner", "Unassigned")
                deadline = item.get("deadline", "No deadline")
                priority = item.get("priority", "medium")
                priority_color = {"high": "#ef4444", "medium": "#f59e0b", "low": "#94a3b8"}.get(priority, "#94a3b8")
                parts.append(f"<li style='background-color: rgba(255, 255, 255, 0.05); padding: 15px; margin-bottom: 10px; border-left: 4px solid {priority_color}; border-radius: 5px; border: 1px solid rgba(255, 255, 255, 0.1);'>")
                parts.append(f"<p style='margin: 0; color: #e2e8f0;'><strong>{desc}</strong></p>")
                parts.append(f"<p style='margin: 5px 0 0 0; color: #94a3b8; font-size: 0.9em;'>Owner: {owner} | Deadline: {deadline} | Priority: <span style='color: {priority_color};'>{priority}</span></p>")
                parts.append("</li>")
            parts.append("</ul>")
        
        # Decisions
        decisions = meeting_summary.get("decisions", [])
        if decisions:
            parts.append("<h2 style='color: #60a5fa; margin-top: 30px;'>Decisions Made</h2>")
            parts.append("<ul style='list-style-type: none; padding: 0;'>")
            for decision in decisions[:10]:  # Limit to 10 decisions
                desc = decision.get("description", "No description")
                parts.append(f"<li style='background-color: rgba(34, 197, 94, 0.1); padding: 15px; margin-bottom: 10px; border-left: 4px solid #22c55e; border-radius: 5px; border: 1px solid rgba(255, 255, 255, 0.1);'>")
                parts.append(f"<p style='margin: 0; color: #e2e8f0;'>{desc}</p>")
                parts.append("</li>")
            parts.append("</ul>")
        
        # Follow-up Recommendations
        if follow_ups:
            parts.append("<h2 style='color: #60a5fa; margin-top: 30px;'>Follow-up Recommendations</h2>")
            parts.append("<ul style='list-style-type: none; padding: 0;'>")
            for rec in follow_ups[:10]:  # Limit to 10 recommendations
                rec_type = rec.get("type", "general")
                recommendation = rec.get("recommendation", "No recommendation")
                priority = rec.get("priority", "medium")
                priority_color = {"high": "#ef4444", "medium": "#f59e0b", "low": "#94a3b8"}.get(priority, "#94a3b8")
                parts.append(f"<li style='background-color: rgba(251, 191, 36, 0.1); padding: 15px; margin-bottom: 10px; border-left: 4px solid {priority_color}; border-radius: 5px; border: 1px solid rgba(255, 255, 255, 0.1);'>")
                parts.append(f"<p style='margin: 0; color: #e2e8f0;'><strong>{rec_type.replace('_', ' ').title()}:</strong> {recommendation}</p>")
                parts.append("</li>")
            parts.append("</ul>")
        
        parts.append("</body></html>")
        html_content = "\n".join(parts)
        return html_content, []
    
    def format_for_display(self, node_type: str, output: Dict[str, Any]) -> Dict[str, Any]:
        """Format meeting summary for frontend display"""
        meeting_summary = output.get("meeting_summary", {})
        metadata = output.get("metadata", {})
        
        # Extract key information for preview
        exec_summary = meeting_summary.get("executive_summary", "")
        title = meeting_summary.get("title", metadata.get("meeting_title", "Meeting Summary"))
        action_items_count = len(meeting_summary.get("action_items", []))
        decisions_count = len(meeting_summary.get("decisions", []))
        topics_count = len(meeting_summary.get("main_topics", []))
        
        # Get HTML content from format method
        html_content, _ = self.format(output)
        
        return {
            "display_type": "html",  # Use HTML for rich formatting
            "primary_content": html_content,  # Return HTML string directly
            "metadata": {
                "node_type": node_type,
                "meeting_title": title,
                "meeting_date": metadata.get("meeting_date"),
                "attendee_count": metadata.get("attendee_count", 0),
                "duration_estimate": meeting_summary.get("duration_estimate"),
                "action_items_count": action_items_count,
                "decisions_count": decisions_count,
                "topics_count": topics_count,
                "executive_summary_preview": exec_summary[:500] + "..." if len(exec_summary) > 500 else exec_summary,
            },
            "actions": ["copy", "download_html", "download_json"],
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


class FineTuneFormatter(OutputFormatter):
    """Formatter for finetune node output - shows job status and progress"""
    
    def can_format(self, node_type: str, output: Dict[str, Any]) -> bool:
        return node_type == "finetune" or "job_id" in output and "status" in output
    
    def format(self, output: Dict[str, Any]) -> Tuple[str, List]:
        """Format fine-tuning job output as text summary"""
        job_id = output.get("job_id", "Unknown")
        status = output.get("status", "unknown")
        provider = output.get("provider", "unknown")
        base_model = output.get("base_model", "unknown")
        estimated_cost = output.get("estimated_cost", 0)
        training_examples = output.get("training_examples", 0)
        validation_examples = output.get("validation_examples", 0)
        epochs = output.get("epochs", 0)
        
        # Status descriptions
        status_descriptions = {
            "validating_files": "Validating training files...",
            "validating_training_file": "Validating training files...",
            "queued": "Queued for training...",
            "running": "Training in progress...",
            "succeeded": "Training completed successfully!",
            "failed": "Training failed",
            "cancelled": "Training cancelled"
        }
        
        status_desc = status_descriptions.get(status, f"Status: {status}")
        
        parts = [
            f"Fine-Tuning Job: {job_id}",
            f"Status: {status_desc}",
            f"Provider: {provider}",
            f"Base Model: {base_model}",
            f"Training Examples: {training_examples}",
            f"Validation Examples: {validation_examples}",
            f"Epochs: {epochs}",
            f"Estimated Cost: ${estimated_cost:.2f}",
        ]
        
        if status in ["succeeded", "failed", "cancelled"]:
            model_id = output.get("model_id")
            if model_id:
                parts.append(f"Fine-Tuned Model: {model_id}")
            error = output.get("error")
            if error:
                parts.append(f"Error: {error}")
        else:
            parts.append("\n⚠️ Training is still running on OpenAI's servers.")
            parts.append("This can take several hours. Check status using the job_id.")
        
        return "\n".join(parts), []
    
    def format_for_display(self, node_type: str, output: Dict[str, Any]) -> Dict[str, Any]:
        """Format fine-tuning job for frontend display with status indicator"""
        job_id = output.get("job_id", "Unknown")
        status = output.get("status", "unknown")
        provider = output.get("provider", "openai")
        base_model = output.get("base_model", "unknown")
        estimated_cost = output.get("estimated_cost", 0)
        training_examples = output.get("training_examples", 0)
        validation_examples = output.get("validation_examples", 0)
        epochs = output.get("epochs", 0)
        model_id = output.get("model_id")
        error = output.get("error")
        
        # Determine if job is still running
        is_running = status in ["validating_files", "validating_training_file", "queued", "running"]
        is_complete = status == "succeeded"
        is_failed = status in ["failed", "cancelled"]
        
        # Build HTML content with status indicator and inline styles for dark theme
        html_parts = [
            '<style>',
            '.finetune-status { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #e2e8f0; }',
            '.status-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(255,255,255,0.1); }',
            '.status-header h3 { margin: 0; font-size: 1.25rem; color: #f1f5f9; }',
            '.status-header code { background: rgba(139, 92, 246, 0.2); padding: 0.25rem 0.5rem; border-radius: 0.25rem; color: #c084fc; font-size: 0.9rem; }',
            '.status-badge { padding: 0.5rem 1rem; border-radius: 0.5rem; font-weight: 600; font-size: 0.875rem; }',
            '.status-badge.running { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }',
            '.status-badge.success { background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }',
            '.status-badge.failed { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }',
            '.job-details { margin-top: 1rem; }',
            '.job-details p { margin: 0.75rem 0; color: #cbd5e1; }',
            '.job-details strong { color: #f1f5f9; }',
            '.status-warning { background: rgba(251, 191, 36, 0.1); border: 1px solid rgba(251, 191, 36, 0.3); border-radius: 0.5rem; padding: 1rem; margin: 1rem 0; color: #fbbf24; }',
            '.error-message { background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 0.5rem; padding: 1rem; margin: 1rem 0; color: #f87171; }',
            '</style>',
            '<div class="finetune-status">',
            f'<div class="status-header">',
            f'<h3>Fine-Tuning Job: <code>{job_id}</code></h3>',
        ]
        
        # Status badge
        if is_running:
            html_parts.append('<span class="status-badge running">🔄 Training in Progress</span>')
        elif is_complete:
            html_parts.append('<span class="status-badge success">✅ Training Complete</span>')
        elif is_failed:
            html_parts.append('<span class="status-badge failed">❌ Training Failed</span>')
        else:
            html_parts.append(f'<span class="status-badge">{status}</span>')
        
        html_parts.append('</div>')
        
        # Job details
        html_parts.append('<div class="job-details">')
        html_parts.append(f'<p><strong>Provider:</strong> {provider}</p>')
        html_parts.append(f'<p><strong>Base Model:</strong> {base_model}</p>')
        html_parts.append(f'<p><strong>Training Examples:</strong> {training_examples}</p>')
        if validation_examples > 0:
            html_parts.append(f'<p><strong>Validation Examples:</strong> {validation_examples}</p>')
        html_parts.append(f'<p><strong>Epochs:</strong> {epochs}</p>')
        html_parts.append(f'<p><strong>Estimated Cost:</strong> ${estimated_cost:.2f}</p>')
        
        if is_running:
            html_parts.append('<div class="status-warning">')
            html_parts.append('⚠️ <strong>Training is still running on OpenAI\'s servers.</strong><br>')
            html_parts.append('This can take several hours. The job will continue processing even after this workflow completes.')
            html_parts.append('</div>')
        
        if model_id:
            html_parts.append(f'<p><strong>Fine-Tuned Model ID:</strong> <code style="background: rgba(139, 92, 246, 0.2); padding: 0.25rem 0.5rem; border-radius: 0.25rem; color: #c084fc;">{model_id}</code></p>')
            if is_complete:
                html_parts.append('<div class="register-model-section" style="margin-top: 1rem; padding: 1rem; background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 0.5rem;">')
                html_parts.append('<p style="margin: 0 0 0.5rem 0; color: #cbd5e1; font-size: 0.875rem;">To use this model in your workflows, register it in the Model Registry:</p>')
                html_parts.append(f'<button onclick="registerModel(\'{job_id}\')" class="register-model-btn" style="padding: 0.5rem 1rem; background: rgba(139, 92, 246, 0.3); border: 1px solid rgba(139, 92, 246, 0.5); border-radius: 0.375rem; color: #c084fc; cursor: pointer; font-weight: 600; font-size: 0.875rem; transition: all 0.2s;">📝 Register Model</button>')
                html_parts.append('</div>')
        
        if error:
            html_parts.append(f'<div class="error-message"><strong>Error:</strong> {error}</div>')
        
        html_parts.append('</div>')
        html_parts.append('</div>')
        
        # Add JavaScript for register button (will be executed in frontend)
        if model_id and is_complete:
            html_parts.append('<script>')
            html_parts.append('function registerModel(jobId) {')
            html_parts.append('  if (window.registerFinetunedModel) {')
            html_parts.append('    window.registerFinetunedModel(jobId);')
            html_parts.append('  } else {')
            html_parts.append('    console.error("registerFinetunedModel function not available");')
            html_parts.append('  }')
            html_parts.append('}')
            html_parts.append('</script>')
        
        html_content = "\n".join(html_parts)
        
        return {
            "display_type": "html",
            "primary_content": html_content,
            "metadata": {
                "node_type": node_type,
                "job_id": job_id,
                "status": status,
                "is_running": is_running,
                "is_complete": is_complete,
                "is_failed": is_failed,
                "provider": provider,
                "base_model": base_model,
                "estimated_cost": estimated_cost,
                "training_examples": training_examples,
                "validation_examples": validation_examples,
                "epochs": epochs,
                "model_id": model_id,
            },
            "actions": ["copy", "download_json", "check_status", "register_model"] if (model_id and is_complete) else ["copy", "download_json", "check_status"],
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
            FineTuneFormatter(),
            BlogPostFormatter(),
            ChartGeneratorFormatter(),
            ProposalFormatter(),
            BrandFormatter(),
            CrewAIAgentFormatter(),
            MeetingSummaryFormatter(),  # Format meeting summaries nicely
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

