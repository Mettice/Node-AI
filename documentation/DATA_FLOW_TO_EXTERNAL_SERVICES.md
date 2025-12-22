# Data Flow to External Services (CSV, Airtable, etc.)

## How Data Flows in Nodeflow

### 1. **Automatic Data Passing via Edges**

When you connect nodes with edges, data automatically flows from source to target:

```
[Chat Node] → [CSV Export Node]
```

**What happens:**
1. Chat node executes and outputs: `{ "output": "Hello world", "tokens_used": 50 }`
2. Engine collects this output into `available_data`
3. CSV Export node receives it in the `inputs` parameter:
   ```python
   inputs = {
       "output": "Hello world",
       "tokens_used": 50,
       "text": "Hello world",  # Auto-mapped from output
   }
   ```

### 2. **How Nodes Receive Data**

Every node's `execute()` method receives:
- `inputs: Dict[str, Any]` - All data from connected source nodes
- `config: Dict[str, Any]` - Node configuration (from UI)

**Example from S3 node:**
```python
async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]):
    # Get data from previous nodes OR config
    file_data = inputs.get("file_data") or inputs.get("data") or inputs.get("content")
    file_key = config.get("s3_key") or inputs.get("file_key")
```

### 3. **Intelligent Routing (When Enabled)**

With intelligent routing ON (default), the AI automatically maps:
- `output` → `data` (for CSV)
- `output` → `records` (for Airtable)
- `text` → `content`
- Structured data → appropriate fields

## Example: CSV Export Node

Here's how to create a CSV export node:

```python
# backend/nodes/storage/csv_export.py

from typing import Any, Dict, List
import csv
import io
from backend.nodes.base import BaseNode
from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CSVExportNode(BaseNode):
    """Export data to CSV file."""
    
    node_type = "csv_export"
    name = "CSV Export"
    description = "Export data to CSV file format"
    category = "storage"
    
    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Export data to CSV.
        
        Accepts data from previous nodes:
        - data: List of dicts (records)
        - output: Can be list of dicts or string
        - records: List of records
        """
        node_id = config.get("_node_id", "csv_export")
        
        # Get data from inputs (from previous nodes) or config
        data = (
            inputs.get("data") or 
            inputs.get("records") or 
            inputs.get("output") or
            config.get("data") or
            []
        )
        
        # Get filename from config or inputs
        filename = config.get("filename") or inputs.get("filename") or "export.csv"
        
        # Handle different input formats
        if isinstance(data, str):
            # If it's a string, try to parse as JSON
            try:
                import json
                data = json.loads(data)
            except:
                # If not JSON, treat as single record
                data = [{"value": data}]
        elif isinstance(data, dict):
            # Single record - convert to list
            data = [data]
        elif not isinstance(data, list):
            # Convert to list
            data = [{"value": str(data)}]
        
        if not data:
            raise ValueError("No data provided to export. Connect a data source node.")
        
        await self.stream_progress(node_id, 0.3, f"Converting {len(data)} records to CSV...")
        
        # Get headers from config or infer from first record
        headers = config.get("headers")
        if not headers and data:
            if isinstance(data[0], dict):
                headers = list(data[0].keys())
            else:
                headers = ["value"]
        
        # Convert to CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        
        for record in data:
            if isinstance(record, dict):
                writer.writerow(record)
            else:
                writer.writerow({"value": str(record)})
        
        csv_content = output.getvalue()
        
        await self.stream_progress(node_id, 0.8, f"CSV generated: {len(csv_content)} bytes")
        
        # Save to file if file_path provided
        file_path = config.get("file_path")
        if file_path:
            import os
            os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(csv_content)
            await self.stream_progress(node_id, 1.0, f"Saved to {file_path}")
        else:
            await self.stream_progress(node_id, 1.0, "CSV content generated")
        
        return {
            "csv_content": csv_content,
            "filename": filename,
            "file_path": file_path,
            "records_count": len(data),
            "headers": headers,
        }
    
    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for CSV export node."""
        return {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "title": "Filename",
                    "description": "Output CSV filename (can also come from previous node)",
                    "default": "export.csv",
                },
                "file_path": {
                    "type": "string",
                    "title": "File Path",
                    "description": "Optional: Save to file path (e.g., '/tmp/export.csv')",
                },
                "headers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "title": "Headers",
                    "description": "Optional: CSV column headers (auto-detected from data if not provided)",
                },
                "data": {
                    "type": "array",
                    "title": "Data",
                    "description": "Optional: Data to export (usually comes from previous node)",
                },
            },
        }


# Register the node
NodeRegistry.register(CSVExportNode.node_type, CSVExportNode, CSVExportNode().get_metadata())
```

## Example: Airtable Node

Here's how to create an Airtable integration node:

```python
# backend/nodes/storage/airtable.py

from typing import Any, Dict, List
import httpx
from backend.nodes.base import BaseNode
from backend.core.models import NodeMetadata
from backend.core.node_registry import NodeRegistry
from backend.core.secret_resolver import resolve_api_key
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class AirtableNode(BaseNode):
    """Store data in Airtable."""
    
    node_type = "airtable"
    name = "Airtable"
    description = "Store records in Airtable base"
    category = "storage"
    
    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Store data in Airtable.
        
        Accepts data from previous nodes:
        - records: List of dicts (records to insert)
        - data: List of dicts
        - output: Can be list of dicts
        """
        node_id = config.get("_node_id", "airtable")
        
        # Get Airtable config
        api_key = config.get("airtable_api_key") or resolve_api_key(config, "airtable_api_key")
        base_id = config.get("airtable_base_id") or inputs.get("base_id")
        table_name = config.get("airtable_table") or inputs.get("table_name")
        operation = config.get("airtable_operation", "create")  # create, update, upsert
        
        if not api_key:
            raise ValueError("Airtable API key is required")
        if not base_id:
            raise ValueError("Airtable Base ID is required")
        if not table_name:
            raise ValueError("Airtable Table name is required")
        
        # Get data from inputs (from previous nodes) or config
        records = (
            inputs.get("records") or 
            inputs.get("data") or 
            inputs.get("output") or
            config.get("records") or
            []
        )
        
        # Handle different input formats
        if isinstance(records, str):
            try:
                import json
                records = json.loads(records)
            except:
                records = [{"value": records}]
        elif isinstance(records, dict):
            records = [records]
        elif not isinstance(records, list):
            records = [{"value": str(records)}]
        
        if not records:
            raise ValueError("No records provided. Connect a data source node.")
        
        await self.stream_progress(node_id, 0.2, f"Preparing {len(records)} records for Airtable...")
        
        # Format records for Airtable API
        airtable_records = []
        for record in records:
            if isinstance(record, dict):
                # Airtable expects {"fields": {...}}
                airtable_records.append({
                    "fields": record
                })
            else:
                airtable_records.append({
                    "fields": {"value": str(record)}
                })
        
        # Execute operation
        if operation == "create":
            return await self._create_records(
                api_key, base_id, table_name, airtable_records, node_id
            )
        elif operation == "update":
            return await self._update_records(
                api_key, base_id, table_name, airtable_records, node_id
            )
        else:
            raise ValueError(f"Unsupported operation: {operation}")
    
    async def _create_records(
        self,
        api_key: str,
        base_id: str,
        table_name: str,
        records: List[Dict[str, Any]],
        node_id: str,
    ) -> Dict[str, Any]:
        """Create records in Airtable."""
        url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        # Airtable allows max 10 records per request
        batch_size = 10
        created_count = 0
        errors = []
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            await self.stream_progress(
                node_id, 
                0.3 + (i / len(records)) * 0.6,
                f"Creating records {i+1}-{min(i+batch_size, len(records))}..."
            )
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json={"records": batch},
                )
                
                if response.status_code == 200:
                    created_count += len(batch)
                else:
                    error_data = response.json()
                    errors.append(error_data)
                    logger.error(f"Airtable error: {error_data}")
        
        await self.stream_progress(node_id, 1.0, f"Created {created_count} records")
        
        return {
            "created_count": created_count,
            "total_records": len(records),
            "errors": errors if errors else None,
            "base_id": base_id,
            "table_name": table_name,
        }
    
    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for Airtable node."""
        return {
            "type": "object",
            "properties": {
                "airtable_api_key": {
                    "type": "string",
                    "title": "API Key",
                    "description": "Airtable API key",
                },
                "airtable_base_id": {
                    "type": "string",
                    "title": "Base ID",
                    "description": "Airtable Base ID (can also come from previous node)",
                },
                "airtable_table": {
                    "type": "string",
                    "title": "Table Name",
                    "description": "Airtable table name (can also come from previous node)",
                },
                "airtable_operation": {
                    "type": "string",
                    "enum": ["create", "update", "upsert"],
                    "default": "create",
                    "title": "Operation",
                    "description": "Operation to perform",
                },
                "records": {
                    "type": "array",
                    "title": "Records",
                    "description": "Optional: Records to store (usually comes from previous node)",
                },
            },
            "required": ["airtable_api_key", "airtable_base_id", "airtable_table"],
        }


# Register the node
NodeRegistry.register(AirtableNode.node_type, AirtableNode, AirtableNode().get_metadata())
```

## How to Use in Workflows

### Example 1: Chat → CSV

```
[Chat Node] → [CSV Export Node]
```

**With Intelligent Routing ON (default):**
- Chat `output` → CSV `data` ✅ Automatic
- No manual configuration needed!

**Without Intelligent Routing:**
- You'd need to manually set CSV node's `data` field to `{{output}}`

### Example 2: CrewAI → Airtable

```
[CrewAI Agent] → [Airtable Node]
```

**With Intelligent Routing ON:**
- CrewAI `agent_outputs` → Airtable `records` ✅ Automatic
- AI understands that agent outputs should become Airtable records

**Configuration needed:**
- Airtable API key (in node config)
- Base ID (can come from previous node or config)
- Table name (can come from previous node or config)

### Example 3: Data Loader → CSV

```
[Data Loader] → [CSV Export Node]
```

**Data flow:**
1. Data Loader outputs: `{ "data": [{"name": "John", "age": 30}, ...] }`
2. CSV Export receives: `inputs = { "data": [...], "records": [...] }`
3. CSV Export automatically uses the `data` field

## Key Points

1. **Data flows automatically** via edges - no manual mapping needed
2. **Intelligent routing** (default ON) maps fields semantically
3. **Nodes check multiple sources** - `inputs.get("data") or config.get("data")`
4. **Flexible input formats** - handles strings, dicts, lists automatically
5. **Configuration overrides** - Config values take precedence over inputs

## Adding New External Services

To add a new service (e.g., Notion, Google Sheets):

1. **Create the node file** in `backend/nodes/storage/`
2. **Inherit from BaseNode**
3. **Get data from `inputs`** (from previous nodes)
4. **Support multiple input formats** (string, dict, list)
5. **Register the node** with NodeRegistry
6. **Add to frontend** node types in `WorkflowCanvas.tsx`

The intelligent routing system will automatically understand how to map data to your new node! 🚀

