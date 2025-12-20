"""
Comprehensive verification script for new AI nodes.
Checks all nodes in business, content, intelligence, developer, and sales categories.
"""

import sys
from pathlib import Path

# Setup path
_backend_dir = Path(__file__).parent
_project_root = _backend_dir.parent
if _backend_dir.name == "backend" and str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Import nodes to register them
from backend.nodes import *  # noqa: F401, F403
from backend.core.node_registry import NodeRegistry

def verify_new_nodes():
    """Verify all new AI nodes in target categories."""
    
    # Get all metadata
    nodes = NodeRegistry.list_all_metadata()
    
    # Target categories
    target_categories = ['intelligence', 'business', 'content', 'developer', 'sales']
    
    # Expected nodes by category
    expected_nodes = {
        'intelligence': [
            'smart_data_analyzer',
            'auto_chart_generator',
            'content_moderator',
            'meeting_summarizer',
            'lead_scorer'
        ],
        'business': [
            'stripe_analytics',
            'cost_optimizer',
            'social_analyzer',
            'ab_test_analyzer'
        ],
        'content': [
            'blog_generator',
            'brand_generator',
            'social_scheduler',
            'podcast_transcriber'
        ],
        'developer': [
            'bug_triager',
            'docs_writer',
            'security_scanner',
            'performance_monitor'
        ],
        'sales': [
            'lead_enricher',
            'call_summarizer',
            'followup_writer',
            'proposal_generator'
        ]
    }
    
    print("=" * 80)
    print("NEW AI NODES VERIFICATION REPORT")
    print("=" * 80)
    print()
    
    # Collect nodes by category
    nodes_by_category = {cat: [] for cat in target_categories}
    for node in nodes:
        if node.category in target_categories:
            nodes_by_category[node.category].append(node)
    
    # Verify each category
    all_good = True
    total_found = 0
    total_expected = sum(len(nodes) for nodes in expected_nodes.values())
    
    for category in target_categories:
        print(f"\n{'=' * 80}")
        print(f"📦 {category.upper()} CATEGORY")
        print(f"{'=' * 80}")
        
        found_nodes = nodes_by_category[category]
        expected = expected_nodes[category]
        
        print(f"\nExpected: {len(expected)} nodes")
        print(f"Found: {len(found_nodes)} nodes")
        print()
        
        # Check each expected node
        for node_type in expected:
            found = any(n.type == node_type for n in found_nodes)
            status = "✅" if found else "❌ MISSING"
            print(f"  {status} {node_type}")
            
            if found:
                node = next(n for n in found_nodes if n.type == node_type)
                total_found += 1
                
                # Check node details
                issues = []
                
                # Check inputs
                if not node.inputs or len(node.inputs) == 0:
                    issues.append("⚠️  No inputs defined")
                
                # Check outputs
                if not node.outputs or len(node.outputs) == 0:
                    issues.append("⚠️  No outputs defined")
                
                # Check description
                if not node.description or len(node.description) < 10:
                    issues.append("⚠️  Description too short")
                
                if issues:
                    for issue in issues:
                        print(f"      {issue}")
                    all_good = False
                else:
                    print(f"      ✅ Schema: {len(node.inputs)} inputs, {len(node.outputs)} outputs")
        
        # Check for unexpected nodes
        found_types = [n.type for n in found_nodes]
        unexpected = [t for t in found_types if t not in expected]
        if unexpected:
            print(f"\n  ⚠️  Unexpected nodes found: {', '.join(unexpected)}")
    
    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total Expected: {total_expected} nodes")
    print(f"Total Found: {total_found} nodes")
    print(f"Missing: {total_expected - total_found} nodes")
    print()
    
    if total_found == total_expected and all_good:
        print("✅ ALL NODES VERIFIED AND READY!")
    elif total_found == total_expected:
        print("⚠️  All nodes found but some have issues (see above)")
    else:
        print("❌ SOME NODES ARE MISSING!")
    
    # Detailed node information
    print(f"\n{'=' * 80}")
    print("DETAILED NODE INFORMATION")
    print(f"{'=' * 80}")
    
    for category in target_categories:
        found_nodes = nodes_by_category[category]
        if found_nodes:
            print(f"\n📦 {category.upper()} ({len(found_nodes)} nodes):")
            for node in sorted(found_nodes, key=lambda n: n.type):
                print(f"\n  • {node.type}")
                print(f"    Name: {node.name}")
                print(f"    Description: {node.description[:80]}..." if len(node.description) > 80 else f"    Description: {node.description}")
                print(f"    Inputs: {len(node.inputs)} fields")
                print(f"    Outputs: {len(node.outputs)} fields")
                
                # Check if node uses LLM
                if hasattr(node, 'config_schema'):
                    config_str = str(node.config_schema) if hasattr(node, 'config_schema') else ""
                    if 'provider' in config_str or 'llm' in config_str.lower() or 'api_key' in config_str:
                        print(f"    ✅ Uses LLM/API")
    
    print(f"\n{'=' * 80}")
    print("VERIFICATION COMPLETE")
    print(f"{'=' * 80}")

if __name__ == "__main__":
    verify_new_nodes()

