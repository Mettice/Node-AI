"""Check saved template files to see what data was saved."""
import json
from pathlib import Path

workflows_dir = Path("data/workflows")
template_files = []

for f in workflows_dir.glob("*.json"):
    try:
        data = json.load(open(f))
        if data.get("is_template"):
            template_files.append((f, data))
    except:
        pass

print(f"Found {len(template_files)} template files\n")

if template_files:
    # Show the most recently modified one
    latest_file, latest_data = max(template_files, key=lambda x: x[0].stat().st_mtime)
    print(f"Latest template: {latest_data['name']}")
    print(f"File: {latest_file.name}\n")
    
    if latest_data.get("nodes"):
        print("First node:")
        first_node = latest_data["nodes"][0]
        print(json.dumps(first_node, indent=2))
        print("\n" + "="*50 + "\n")
        
        print("All nodes data:")
        for i, node in enumerate(latest_data["nodes"]):
            print(f"\nNode {i+1}: {node['type']}")
            print(f"  ID: {node['id']}")
            print(f"  Data keys: {list(node.get('data', {}).keys())}")
            if node.get('data'):
                print(f"  Data: {json.dumps(node['data'], indent=4)}")

