"""
Script to verify and count nodes by category.
Usage:
    python verify_nodes.py              # Show summary
    python verify_nodes.py --detailed   # Show detailed info with inputs/outputs
    python verify_nodes.py --node <type> # Show details for specific node
"""
import sys
import argparse
from pathlib import Path

# Add parent directory to path to allow imports when running from backend/
# This must be done BEFORE any backend imports
_backend_dir = Path(__file__).parent
_project_root = _backend_dir.parent

# If we're in the backend directory, add project root to path
if _backend_dir.name == "backend" and str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Import all nodes to trigger registration
try:
    from backend.nodes import *  # noqa: F401, F403
except Exception as e:
    print(f"Warning: Some nodes failed to import: {e}")

from backend.core.node_registry import NodeRegistry

def print_detailed_node_info(node_metadata):
    """Print detailed information about a node including inputs/outputs."""
    print(f"\n{'='*80}")
    print(f"📦 {node_metadata.name} ({node_metadata.type})")
    print(f"{'='*80}")
    print(f"Category: {node_metadata.category}")
    print(f"Description: {node_metadata.description}")
    
    # Get actual node instance to extract inputs/outputs from schema methods
    try:
        node_class = NodeRegistry.get(node_metadata.type)
        node_instance = node_class()
        input_schema = node_instance.get_input_schema()
        output_schema = node_instance.get_output_schema()
    except Exception as e:
        input_schema = {}
        output_schema = {}
        print(f"\n⚠️  Warning: Could not load node instance: {e}")
    
    # Inputs from schema
    if input_schema:
        print(f"\n📥 INPUTS ({len(input_schema)}):")
        for inp_name, inp_info in input_schema.items():
            inp_type = inp_info.get('type', 'any')
            inp_desc = inp_info.get('description', inp_info.get('title', 'No description'))
            is_required = inp_info.get('required', False)
            req = "✓ Required" if is_required else "○ Optional"
            print(f"  • {inp_name} ({inp_type}) - {req}")
            if inp_desc and inp_desc != 'No description':
                # Wrap long descriptions
                desc_lines = [inp_desc[i:i+70] for i in range(0, len(inp_desc), 70)]
                for line in desc_lines:
                    print(f"    {line}")
    else:
        # Fallback to metadata inputs if available
        if node_metadata.inputs:
            print(f"\n📥 INPUTS ({len(node_metadata.inputs)}):")
            for inp in node_metadata.inputs:
                req = "✓ Required" if inp.required else "○ Optional"
                print(f"  • {inp.name} ({inp.type}) - {req}")
                if inp.description:
                    print(f"    {inp.description}")
        else:
            print(f"\n📥 INPUTS: None")
    
    # Outputs from schema
    if output_schema:
        print(f"\n📤 OUTPUTS ({len(output_schema)}):")
        for out_name, out_info in output_schema.items():
            out_type = out_info.get('type', 'any')
            out_desc = out_info.get('description', 'No description')
            print(f"  • {out_name} ({out_type})")
            if out_desc and out_desc != 'No description':
                # Wrap long descriptions
                desc_lines = [out_desc[i:i+70] for i in range(0, len(out_desc), 70)]
                for line in desc_lines:
                    print(f"    {line}")
    else:
        # Fallback to metadata outputs if available
        if node_metadata.outputs:
            print(f"\n📤 OUTPUTS ({len(node_metadata.outputs)}):")
            for out in node_metadata.outputs:
                print(f"  • {out.name} ({out.type})")
                if out.description:
                    print(f"    {out.description}")
        else:
            print(f"\n📤 OUTPUTS: Not specified")
    
    # Config schema
    if node_metadata.config_schema:
        props = node_metadata.config_schema.get('properties', {})
        required = node_metadata.config_schema.get('required', [])
        if props:
            print(f"\n⚙️  CONFIGURATION ({len(props)} options):")
            for prop_name, prop_info in sorted(props.items()):
                req = "✓ Required" if prop_name in required else "○ Optional"
                prop_type = prop_info.get('type', 'any')
                prop_desc = prop_info.get('description', prop_info.get('title', 'No description'))
                print(f"  • {prop_name} ({prop_type}) - {req}")
                if prop_desc and prop_desc != 'No description':
                    # Wrap long descriptions
                    desc_lines = [prop_desc[i:i+70] for i in range(0, len(prop_desc), 70)]
                    for line in desc_lines:
                        print(f"    {line}")
                # Show enum values if available
                if 'enum' in prop_info:
                    enum_vals = ', '.join([str(v) for v in prop_info['enum'][:5]])
                    if len(prop_info['enum']) > 5:
                        enum_vals += f", ... (+{len(prop_info['enum']) - 5} more)"
                    print(f"    Options: {enum_vals}")
                # Show default if available
                if 'default' in prop_info:
                    default_val = prop_info['default']
                    if isinstance(default_val, (list, dict)):
                        default_val = str(default_val)[:50]
                    print(f"    Default: {default_val}")

def verify_nodes(detailed=False, node_type=None):
    """Verify and count nodes by category."""
    # Get all metadata
    nodes = NodeRegistry.list_all_metadata()
    
    # Count by category
    intelligence_nodes = [n for n in nodes if n.category == 'intelligence']
    business_nodes = [n for n in nodes if n.category == 'business']
    content_nodes = [n for n in nodes if n.category == 'content']
    developer_nodes = [n for n in nodes if n.category == 'developer']
    sales_nodes = [n for n in nodes if n.category == 'sales']
    
    # Print results
    print(f"Intelligence nodes: {len(intelligence_nodes)}")
    print(f"Business nodes: {len(business_nodes)}")
    print(f"Content nodes: {len(content_nodes)}")
    print(f"Developer nodes: {len(developer_nodes)}")
    print(f"Sales nodes: {len(sales_nodes)}")
    
    total_new_ai_nodes = len(intelligence_nodes) + len(business_nodes) + len(content_nodes) + len(developer_nodes) + len(sales_nodes)
    print(f"Total new AI nodes: {total_new_ai_nodes}")
    print(f"Total all nodes: {len(nodes)}")
    
    # Additional verification
    print("\n=== Verification Details ===")
    all_categories = {}
    for node in nodes:
        category = node.category
        if category not in all_categories:
            all_categories[category] = []
        all_categories[category].append(node.type)
    
    print("\nAll categories found:")
    for category, node_types in sorted(all_categories.items()):
        print(f"  {category}: {len(node_types)} nodes")
        if category in ['intelligence', 'business', 'content', 'developer', 'sales']:
            print(f"    Examples: {', '.join(node_types[:5])}")
    
    # Verify specific categories
    print("\n=== Category Verification ===")
    target_categories = ['intelligence', 'business', 'content', 'developer', 'sales']
    for cat in target_categories:
        count = len([n for n in nodes if n.category == cat])
        status = "✓" if count > 0 else "✗"
        print(f"{status} {cat}: {count} nodes")
    
    # List all nodes by category
    print("\n" + "="*80)
    print("=== ALL AVAILABLE NODES ===")
    print("="*80)
    
    for category in sorted(all_categories.keys()):
        category_nodes = [n for n in nodes if n.category == category]
        print(f"\n📁 {category.upper()} ({len(category_nodes)} nodes)")
        print("-" * 80)
        for node in sorted(category_nodes, key=lambda x: x.name):
            # Get input/output counts for better display
            try:
                node_class = NodeRegistry.get(node.type)
                node_instance = node_class()
                input_count = len(node_instance.get_input_schema())
                output_count = len(node_instance.get_output_schema())
                io_info = f" [{input_count} in, {output_count} out]"
            except:
                io_info = ""
            
            print(f"  • {node.name} ({node.type}){io_info}")
            if node.description:
                desc = node.description
                if len(desc) > 75:
                    desc = desc[:72] + "..."
                print(f"    {desc}")
    
    print("\n" + "="*80)
    print(f"TOTAL: {len(nodes)} nodes across {len(all_categories)} categories")
    print("="*80)
    
    # Show detailed information if requested
    if node_type:
        found_node = next((n for n in nodes if n.type == node_type), None)
        if found_node:
            print_detailed_node_info(found_node)
        else:
            print(f"\n❌ Node type '{node_type}' not found!")
            print(f"Available node types: {', '.join(sorted([n.type for n in nodes]))}")
    elif detailed:
        print("\n" + "="*80)
        print("=== DETAILED NODE INFORMATION ===")
        print("="*80)
        for category in sorted(all_categories.keys()):
            category_nodes = [n for n in nodes if n.category == category]
            for node in sorted(category_nodes, key=lambda x: x.name):
                print_detailed_node_info(node)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Verify and list nodes')
    parser.add_argument('--detailed', action='store_true', 
                       help='Show detailed information including inputs/outputs')
    parser.add_argument('--node', type=str, 
                       help='Show detailed information for a specific node type')
    args = parser.parse_args()
    
    verify_nodes(detailed=args.detailed, node_type=args.node)

