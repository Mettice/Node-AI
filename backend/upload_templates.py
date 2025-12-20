"""
Script to upload workflow templates from test_templates.json to the backend.

This script reads templates from test_templates.json and saves them as workflows
with is_template=True, making them available in the WorkflowLoader.
"""

import json
import sys
import uuid
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.core.models import Workflow, Node, Edge, Position
from backend.api.workflows import _save_workflow


def convert_template_to_workflow(template: dict) -> Workflow:
    """Convert a template dict to a Workflow object."""
    # Generate unique IDs for nodes
    # Templates use node types as identifiers in connections, so we map type -> first node ID of that type
    node_type_to_first_id = {}
    nodes = []
    
    for i, node_data in enumerate(template.get("nodes", [])):
        node_type = node_data["type"]
        
        # Generate unique node ID
        node_id = node_data.get("id") or f"{node_type}_{i+1}"
        
        # Map node type to first occurrence (for connection mapping)
        if node_type not in node_type_to_first_id:
            node_type_to_first_id[node_type] = node_id
        
        # Convert config to data
        node_config = node_data.get("config", {})
        
        # Create Node object
        position = node_data.get("position", {"x": 0, "y": 0})
        node = Node(
            id=node_id,
            type=node_type,
            position=Position(x=position.get("x", 0), y=position.get("y", 0)),
            data=node_config
        )
        nodes.append(node)
    
    # Convert connections to edges
    # Connections use node types as identifiers, map to actual node IDs
    edges = []
    for i, conn in enumerate(template.get("connections", [])):
        from_type = conn.get("from")
        to_type = conn.get("to")
        
        # Find source and target node IDs by type
        source_id = node_type_to_first_id.get(from_type)
        target_id = node_type_to_first_id.get(to_type)
        
        if not source_id or not target_id:
            print(f"Warning: Skipping connection {i+1} - could not find nodes for '{from_type}' -> '{to_type}'")
            continue
        
        edge = Edge(
            id=f"edge_{i+1}",
            source=source_id,
            target=target_id,
            sourceHandle=conn.get("fromHandle"),
            targetHandle=conn.get("toHandle")
        )
        edges.append(edge)
    
    # Create Workflow object
    workflow = Workflow(
        id=str(uuid.uuid4()),
        name=template["name"],
        description=template.get("description"),
        nodes=nodes,
        edges=edges,
        tags=template.get("tags", []),
        is_template=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    return workflow


def main():
    """Main function to upload templates."""
    # Path to templates file
    templates_file = Path(__file__).parent / "test_templates.json"
    
    if not templates_file.exists():
        print(f"Error: Templates file not found at {templates_file}")
        return 1
    
    # Load templates
    with open(templates_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    templates = data.get("templates", [])
    print(f"Found {len(templates)} templates to upload\n")
    
    # Upload each template
    uploaded = 0
    failed = 0
    
    for i, template in enumerate(templates, 1):
        try:
            print(f"[{i}/{len(templates)}] Processing: {template['name']}")
            
            # Convert to workflow
            workflow = convert_template_to_workflow(template)
            
            # Save workflow
            _save_workflow(workflow)
            
            print(f"  ✓ Saved as workflow {workflow.id}")
            uploaded += 1
            
        except Exception as e:
            print(f"  ✗ Failed: {str(e)}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*50}")
    print(f"Upload complete!")
    print(f"  Successfully uploaded: {uploaded}")
    print(f"  Failed: {failed}")
    print(f"{'='*50}")
    
    if uploaded > 0:
        print("\nTemplates are now available in WorkflowLoader!")
        print("Click 'Load Workflow' → Toggle 'Templates Only' to see them.")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

