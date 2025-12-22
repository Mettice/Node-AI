Proposal: Standardized "Smart" Output Visualization
The Problem
Currently, different nodes output raw JSON, strings, or ad-hoc structures. The frontend tries to render them genericially, leading to inconsistent UI (sometimes a chart, sometimes a raw dictionary).

The Solution Strategy
1. Backend: Leverage the Existing 
OutputFormatter
Good news! You already have a powerful 
backend/core/output_formatters.py
 system. It defines "Display Formatters" for:

BlogPostFormatter
 -> Renders HTML
ChartGeneratorFormatter
 -> Renders Charts + Images
CrewAIAgentFormatter
 -> Renders Agent Reports
The Fix: Ensure every node execution runs through 
get_formatter_registry().format_for_display(...)
 before returning results to the frontend.

Action: Modify NodeExecutor.execute_node to always inject a _display_metadata key into the result.
Data Structure:
{
  "output": {...},
  "_display_metadata": {
    "display_type": "html | chart | markdown | table | json",
    "primary_content": "...",
    "attachments": []
  }
}
2. Frontend: "Universal Result Viewer" Component
Instead of specific "Output Nodes" (which add clutter), create a Smart Component in the execution panel.

Logic:

const ResultViewer = ({ result }) => {
  const meta = result._display_metadata;
  
  if (meta.display_type === 'chart') return <ChartRenderer data={meta.primary_content} />;
  if (meta.display_type === 'html') return <HtmlPreview content={meta.primary_content} />;
  if (meta.display_type === 'markdown') return <MarkdownViewer content={meta.primary_content} />;
  
  return <JsonViewer data={result} />; // Fallback
}
3. User's Idea: The "Dashboard Node"
Your idea for an "Output Node" is excellent for Final Reports. We should add a generic DashboardNode that:

Accepts any input.
Has a configuration dropdown: Display As: [Auto | Table | Kanban | Metric Card].
When connected, it forces the _display_metadata.display_type to the user's selection.
It can be "Pinned" to a Dashboard view for end-users.
Implementation Plan
Backend: Verify 
NodeExecutor
 uses 
FormatterRegistry
. (It seems to be there but maybe not fully wired for all nodes).
Frontend: Update the 'Execution Result' panel to look for _display_metadata before dumping raw JSON.