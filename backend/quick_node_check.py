"""
Quick one-liner alternative for checking node counts.
Can be used as: python -c "exec(open('quick_node_check.py').read())"
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

# Get and count nodes
nodes = NodeRegistry.list_all_metadata()
intelligence_nodes = [n for n in nodes if n.category == 'intelligence']
business_nodes = [n for n in nodes if n.category == 'business']
content_nodes = [n for n in nodes if n.category == 'content']
developer_nodes = [n for n in nodes if n.category == 'developer']
sales_nodes = [n for n in nodes if n.category == 'sales']

print(f'Intelligence nodes: {len(intelligence_nodes)}')
print(f'Business nodes: {len(business_nodes)}')
print(f'Content nodes: {len(content_nodes)}')
print(f'Developer nodes: {len(developer_nodes)}')
print(f'Sales nodes: {len(sales_nodes)}')
print(f'Total new AI nodes: {len(intelligence_nodes) + len(business_nodes) + len(content_nodes) + len(developer_nodes) + len(sales_nodes)}')

