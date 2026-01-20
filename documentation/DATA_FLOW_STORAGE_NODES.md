# Data Flow: Storage Nodes (Airtable, Google Sheets)

## How Storage Nodes Pass Data to Other Nodes

### 1. **Airtable Read Operation Output**

When Airtable reads data, it returns:
```python
{
    "data": [
        {"id": "rec123", "Name": "John", "Email": "john@example.com", ...},
        {"id": "rec456", "Name": "Jane", "Email": "jane@example.com", ...},
        ...
    ],
    "schema": {
        "base_id": "...",
        "table_name": "Leads",
        "field_names": ["Name", "Email", ...],
        "record_count": 29
    },
    "metadata": {
        "source": "airtable",
        "base_id": "...",
        "table_name": "Leads",
        "view": "",
        "record_count": 29
    }
}
```

### 2. **Data Flow to Downstream Nodes**

The `DataCollector` in `backend/core/engine/data_collector.py` passes **all output fields** to downstream nodes. There's no specific handling for storage nodes, so:

- **All fields are passed through**: `data`, `schema`, `metadata` all become available in `inputs`
- **Downstream nodes access data via**: `inputs.get("data")` or `inputs.get("output")` or `inputs.get("results")`

**Example: Airtable → Chat Node**
```python
# Airtable outputs
{
    "data": [...],
    "schema": {...},
    "metadata": {...}
}

# Chat node receives in inputs:
inputs = {
    "data": [...],           # ✅ Available
    "schema": {...},         # ✅ Available
    "metadata": {...},       # ✅ Available
    # Also available by node ID:
    "airtable_node_id_data": [...],
    "airtable_node_id_schema": {...},
    ...
}
```

### 3. **How Nodes Consume Storage Data**

Most nodes look for data in common fields:
- `inputs.get("data")` - Primary data field (list of dicts)
- `inputs.get("output")` - Alternative field name
- `inputs.get("results")` - Another alternative
- `inputs.get("records")` - For record-based operations

**Example: Airtable → Google Sheets Write**
```python
# In Google Sheets write operation:
data = (
    inputs.get("data") or      # ✅ Gets Airtable data
    inputs.get("results") or
    inputs.get("records") or
    []
)
# data is now the list of dictionaries from Airtable
```

### 4. **Current Limitations**

1. **No field selection**: All fields from Airtable are passed (can't select specific columns)
2. **No post-fetch filtering**: All records are passed (filtering must be done at Airtable level)
3. **No data transformation**: Data flows as-is (no automatic conversion)

### 5. **Display in Execution Panel**

**Summary Tab (`ExecutionSummary.tsx`)**:
- Shows node results as JSON preview
- Does NOT use `UnifiedNodeOutput` component
- Currently shows raw output structure

**Outputs Tab (`ExecutionOutputs.tsx`)**:
- Uses `UnifiedNodeOutput` when `_display_metadata` exists
- Should display structured data as interactive table
- Falls back to JSON if no metadata

**Expected Behavior**:
- Storage nodes should have `_display_metadata` with `display_type: "data"`
- Frontend should detect `primary_content.data` as array and render `StructuredDataTable`
- Table should be interactive (sort, search, paginate, export)

### 6. **Data Flow Diagram**

```
Airtable Read
    ↓
Output: {"data": [...], "schema": {...}, "metadata": {...}}
    ↓
DataCollector.smart_merge_sources()
    ↓
Available in inputs: {"data": [...], "schema": {...}, "metadata": {...}}
    ↓
Downstream Node (e.g., Chat, Google Sheets Write, Slack)
    ↓
Node accesses: inputs.get("data") → List of dictionaries
```

### 7. **Writing to Storage Nodes**

**Airtable Write expects**:
```python
inputs.get("data")  # List of dictionaries
# OR
inputs.get("output")
# OR
inputs.get("records")
```

**Example Workflow**:
```
Data Loader → Process → Airtable Write
     ↓            ↓              ↓
  [records]   [processed]    Writes to Airtable
```

The write operation:
- Takes list of dictionaries from inputs
- Converts to Airtable record format
- Writes in batches (max 10 per request)
