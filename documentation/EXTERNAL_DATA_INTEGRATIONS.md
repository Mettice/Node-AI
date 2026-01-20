# External Data Integrations: Google Sheets, CSV, Airtable & Slack

## 📊 Overview

This document explains how to integrate external data sources (Google Sheets, CSV files, Airtable) and communication tools (Slack) into NodeAI workflows, focusing on how structured data flows through nodes.

---

## 🔄 Data Flow Architecture

### **Core Principle: Structured Data as Lists of Dictionaries**

All structured data in NodeAI flows as **lists of dictionaries** (records/rows):

```python
# Example: CSV/Google Sheets/Airtable data structure
[
    {"name": "John", "age": 30, "email": "john@example.com"},
    {"name": "Jane", "age": 28, "email": "jane@example.com"},
    {"name": "Bob", "age": 35, "email": "bob@example.com"}
]
```

### **How Data Flows Between Nodes**

```
[Input Node] → [Processing Node] → [Output Node]
     ↓              ↓                    ↓
  {data: [...]}  {data: [...]}    {data: [...]}
  {schema: {...}} {schema: {...}}  {schema: {...}}
```

**Key Points:**
- Data flows via **edges** (connections between nodes)
- Each node receives `inputs: Dict[str, Any]` from previous nodes
- Each node outputs `Dict[str, Any]` to next nodes
- Structured data is always in `inputs["data"]` or `inputs["results"]`

---

## 📥 Input Nodes (Data Sources)

### **1. CSV File Input**

**Node:** `data_loader` (already exists)

**How it works:**
```python
# Node outputs:
{
    "data": [
        {"column1": "value1", "column2": "value2"},
        {"column1": "value3", "column2": "value4"}
    ],
    "schema": {
        "columns": ["column1", "column2"],
        "dtypes": {"column1": "object", "column2": "int64"},
        "row_count": 2,
        "column_count": 2
    },
    "metadata": {
        "source": "data_upload",
        "file_path": "uploads/data.csv",
        "file_type": ".csv"
    }
}
```

**Workflow:**
```
[File Upload] → [Data Loader] → [Next Node]
     ↓              ↓
  file_path    {data: [...], schema: {...}}
```

**Usage:**
1. Upload CSV file via File Upload node
2. Connect to Data Loader node
3. Data Loader parses CSV → outputs `data` (list of dicts)
4. Next node receives `inputs["data"]`

---

### **2. Google Sheets Input**

**Node:** `google_sheets` (to be created)

**How it works:**
```python
# Node outputs:
{
    "data": [
        {"Name": "John", "Age": 30, "Email": "john@example.com"},
        {"Name": "Jane", "Age": 28, "Email": "jane@example.com"}
    ],
    "schema": {
        "columns": ["Name", "Age", "Email"],
        "row_count": 2,
        "column_count": 3,
        "spreadsheet_id": "abc123",
        "sheet_name": "Sheet1",
        "range": "A1:C3"
    },
    "metadata": {
        "source": "google_sheets",
        "spreadsheet_id": "abc123",
        "sheet_name": "Sheet1"
    }
}
```

**Configuration:**
```json
{
    "spreadsheet_id": "1abc123...",
    "sheet_name": "Sheet1",
    "range": "A1:C100",  // Optional
    "has_header": true,
    "oauth_token_id": "token_123"  // OAuth token for Google API
}
```

**Workflow:**
```
[Google Sheets] → [Processing Node] → [Output Node]
      ↓                ↓                   ↓
  {data: [...]}   {data: [...]}      {data: [...]}
```

**Implementation Pattern:**
```python
# backend/nodes/input/google_sheets.py
class GoogleSheetsNode(BaseNode):
    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]):
        # 1. Authenticate with Google Sheets API (OAuth)
        # 2. Read spreadsheet data
        # 3. Convert to list of dicts
        # 4. Return structured output
        
        data = [
            {"Name": row[0], "Age": row[1], "Email": row[2]}
            for row in sheet_data
        ]
        
        return {
            "data": data,
            "schema": {...},
            "metadata": {...}
        }
```

---

### **3. Airtable Input**

**Node:** `airtable` (to be created)

**How it works:**
```python
# Node outputs:
{
    "data": [
        {
            "id": "rec123",
            "fields": {
                "Name": "John",
                "Age": 30,
                "Email": "john@example.com"
            }
        },
        {
            "id": "rec456",
            "fields": {
                "Name": "Jane",
                "Age": 28,
                "Email": "jane@example.com"
            }
        }
    ],
    "schema": {
        "base_id": "app123",
        "table_name": "Users",
        "field_names": ["Name", "Age", "Email"],
        "record_count": 2
    },
    "metadata": {
        "source": "airtable",
        "base_id": "app123",
        "table_name": "Users"
    }
}
```

**Configuration:**
```json
{
    "base_id": "app123abc",
    "table_name": "Users",
    "view": "Grid View",  // Optional
    "filter_by_formula": "{Status} = 'Active'",  // Optional
    "max_records": 100,  // Optional
    "api_key": "key123..."  // Airtable API key
}
```

**Workflow:**
```
[Airtable] → [Processing Node] → [Output Node]
    ↓              ↓                   ↓
{data: [...]}  {data: [...]}      {data: [...]}
```

**Implementation Pattern:**
```python
# backend/nodes/input/airtable.py
class AirtableNode(BaseNode):
    async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]):
        # 1. Authenticate with Airtable API
        # 2. Fetch records from base/table
        # 3. Convert to list of dicts (flatten fields)
        # 4. Return structured output
        
        records = airtable.get_all()
        data = [
            {
                "id": record["id"],
                **record["fields"]  # Flatten fields
            }
            for record in records
        ]
        
        return {
            "data": data,
            "schema": {...},
            "metadata": {...}
        }
```

---

## 🔄 Processing Nodes (Transform Data)

### **How Processing Nodes Receive Structured Data**

All processing nodes receive data via `inputs["data"]`:

```python
# Example: Smart Data Analyzer processing CSV data
async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]):
    # Get structured data from previous node
    data = inputs.get("data") or inputs.get("results") or []
    
    if not data:
        raise ValueError("No data provided. Connect a data source node.")
    
    # Process data (e.g., analyze, filter, transform)
    # ...
    
    # Return processed data (same structure)
    return {
        "data": processed_data,  # Still list of dicts
        "schema": {...},
        "analysis": {...}
    }
```

### **Common Processing Patterns**

#### **1. Filter Data**
```python
# Filter rows based on condition
filtered_data = [
    row for row in data
    if row.get("age", 0) > 25
]
```

#### **2. Transform Data**
```python
# Add computed columns
transformed_data = [
    {**row, "age_group": "adult" if row["age"] >= 18 else "minor"}
    for row in data
]
```

#### **3. Aggregate Data**
```python
# Group and aggregate
from collections import defaultdict
groups = defaultdict(list)
for row in data:
    groups[row["category"]].append(row["value"])

aggregated = [
    {"category": k, "total": sum(v), "count": len(v)}
    for k, v in groups.items()
]
```

---

## 📤 Output Nodes (Data Destinations)

### **1. Google Sheets Output**

**Node:** `google_sheets` (write mode)

**How it works:**
```python
# Node receives:
inputs = {
    "data": [
        {"Name": "John", "Age": 30, "Email": "john@example.com"},
        {"Name": "Jane", "Age": 28, "Email": "jane@example.com"}
    ]
}

# Node writes to Google Sheets:
# - Converts list of dicts to rows
# - Writes to specified spreadsheet/range
# - Returns confirmation
```

**Configuration:**
```json
{
    "operation": "write",  // or "append", "update"
    "spreadsheet_id": "1abc123...",
    "sheet_name": "Sheet1",
    "range": "A1:C100",
    "clear_existing": false,  // Clear before writing
    "oauth_token_id": "token_123"
}
```

**Workflow:**
```
[Processing Node] → [Google Sheets Write]
         ↓                    ↓
    {data: [...]}      Writes to spreadsheet
```

**Implementation Pattern:**
```python
# backend/nodes/storage/google_sheets.py (write mode)
async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]):
    # Get data from previous node
    data = inputs.get("data") or inputs.get("results") or []
    
    if not data:
        raise ValueError("No data to write. Connect a data source node.")
    
    # Convert list of dicts to rows
    if isinstance(data, list) and len(data) > 0:
        # Get column names from first row
        columns = list(data[0].keys())
        rows = [columns]  # Header row
        rows.extend([list(row.values()) for row in data])
    else:
        raise ValueError("Data must be a non-empty list of dictionaries")
    
    # Write to Google Sheets
    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range,
        valueInputOption="RAW",
        body={"values": rows}
    ).execute()
    
    return {
        "success": True,
        "rows_written": len(data),
        "spreadsheet_id": spreadsheet_id,
        "range": range
    }
```

---

### **2. Airtable Output**

**Node:** `airtable` (write mode)

**How it works:**
```python
# Node receives:
inputs = {
    "data": [
        {"Name": "John", "Age": 30, "Email": "john@example.com"},
        {"Name": "Jane", "Age": 28, "Email": "jane@example.com"}
    ]
}

# Node writes to Airtable:
# - Converts list of dicts to Airtable records
# - Creates/updates records in base/table
# - Returns confirmation
```

**Configuration:**
```json
{
    "operation": "create",  // or "update", "upsert"
    "base_id": "app123abc",
    "table_name": "Users",
    "api_key": "key123..."
}
```

**Workflow:**
```
[Processing Node] → [Airtable Write]
         ↓                    ↓
    {data: [...]}      Creates/updates records
```

**Implementation Pattern:**
```python
# backend/nodes/storage/airtable.py (write mode)
async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]):
    # Get data from previous node
    data = inputs.get("data") or inputs.get("results") or []
    
    if not data:
        raise ValueError("No data to write. Connect a data source node.")
    
    # Convert list of dicts to Airtable records
    records = [
        {"fields": row}  # Airtable expects {"fields": {...}}
        for row in data
    ]
    
    # Batch create/update records
    airtable.batch_create(records)  # or batch_update
    
    return {
        "success": True,
        "records_created": len(data),
        "base_id": base_id,
        "table_name": table_name
    }
```

---

### **3. Slack Output**

**Node:** `slack` (already exists, enhanced for structured data)

**How it works:**
```python
# Node receives structured data
inputs = {
    "data": [
        {"Name": "John", "Status": "Active"},
        {"Name": "Jane", "Status": "Pending"}
    ]
}

# Node formats data and sends to Slack
# Options:
# 1. Send as formatted table
# 2. Send as list
# 3. Send each row as separate message
# 4. Send summary
```

**Configuration:**
```json
{
    "slack_operation": "send_message",
    "slack_channel": "#general",
    "format": "table",  // or "list", "summary", "individual"
    "include_header": true,
    "slack_token_id": "token_123"
}
```

**Workflow:**
```
[Processing Node] → [Slack]
         ↓              ↓
    {data: [...]}  Formats & sends message
```

**Implementation Pattern:**
```python
# Enhanced Slack node for structured data
async def _send_structured_message(
    self, access_token: str, inputs: Dict[str, Any], config: Dict[str, Any], node_id: str
):
    # Get data from previous node
    data = inputs.get("data") or inputs.get("results") or []
    format_type = config.get("format", "table")
    
    if not data:
        # Fallback to text message
        message = inputs.get("message") or inputs.get("text") or inputs.get("output")
        return await self._send_message(access_token, inputs, config, node_id)
    
    # Format structured data
    if format_type == "table":
        message = self._format_as_table(data)
    elif format_type == "list":
        message = self._format_as_list(data)
    elif format_type == "summary":
        message = self._format_as_summary(data)
    elif format_type == "individual":
        # Send each row as separate message
        for row in data:
            await self._send_single_message(access_token, row, config, node_id)
        return {"success": True, "messages_sent": len(data)}
    
    # Send formatted message
    return await self._send_message(access_token, {"message": message}, config, node_id)
```

---

## 🔗 Complete Workflow Examples

### **Example 1: CSV → Process → Google Sheets**

```
[CSV File] → [Data Loader] → [Smart Data Analyzer] → [Google Sheets Write]
     ↓            ↓                    ↓                        ↓
  file.csv   {data: [...]}      {data: [...],        Writes to spreadsheet
            {schema: {...}}      analysis: {...}}
```

**Data Flow:**
1. **CSV File** uploaded
2. **Data Loader** parses CSV → outputs `{data: [...], schema: {...}}`
3. **Smart Data Analyzer** receives `inputs["data"]` → analyzes → outputs `{data: [...], analysis: {...}}`
4. **Google Sheets Write** receives `inputs["data"]` → writes to spreadsheet

---

### **Example 2: Airtable → Filter → Slack**

```
[Airtable Read] → [Data Filter] → [Slack]
       ↓               ↓              ↓
  {data: [...]}   {data: [...]}  Formats & sends
```

**Data Flow:**
1. **Airtable Read** fetches records → outputs `{data: [...], schema: {...}}`
2. **Data Filter** receives `inputs["data"]` → filters rows → outputs `{data: [...]}`
3. **Slack** receives `inputs["data"]` → formats as table → sends message

---

### **Example 3: Google Sheets → AI Analysis → Airtable**

```
[Google Sheets] → [Chat/LLM] → [Airtable Write]
       ↓              ↓              ↓
  {data: [...]}  {output: "...",  Creates records
                  analysis: {...}}
```

**Data Flow:**
1. **Google Sheets** reads data → outputs `{data: [...], schema: {...}}`
2. **Chat/LLM** receives `inputs["data"]` → converts to text → analyzes → outputs `{output: "...", analysis: {...}}`
3. **Airtable Write** receives `inputs["data"]` (from step 1) or `inputs["analysis"]` → creates records

---

## 🎯 Key Design Patterns

### **1. Universal Data Structure**

All structured data nodes use the same output format:

```python
{
    "data": [  # List of dictionaries (rows/records)
        {"column1": "value1", "column2": "value2"},
        {"column1": "value3", "column2": "value4"}
    ],
    "schema": {  # Metadata about data structure
        "columns": ["column1", "column2"],
        "row_count": 2,
        "column_count": 2
    },
    "metadata": {  # Source information
        "source": "google_sheets",
        "spreadsheet_id": "abc123"
    }
}
```

### **2. Flexible Input Handling**

Nodes should accept data from multiple sources:

```python
# ✅ GOOD - Flexible input handling
data = (
    inputs.get("data") or
    inputs.get("results") or
    inputs.get("records") or
    []
)

# ❌ BAD - Only accepts one field name
data = inputs.get("data", [])
```

### **3. Schema Preservation**

Always preserve and pass through schema information:

```python
# Input node outputs schema
output = {
    "data": [...],
    "schema": {"columns": [...], "row_count": 10}
}

# Processing node preserves schema
output = {
    "data": processed_data,
    "schema": inputs.get("schema", {}),  # Preserve original schema
    "transformations": [...]  # Add transformation metadata
}
```

### **4. Error Handling**

Handle missing or invalid data gracefully:

```python
data = inputs.get("data") or []

if not data:
    raise ValueError("No data provided. Connect a data source node.")

if not isinstance(data, list):
    raise ValueError(f"Data must be a list, got {type(data).__name__}")

if len(data) > 0 and not isinstance(data[0], dict):
    raise ValueError("Data must be a list of dictionaries")
```

---

## 🔐 Authentication

### **Google Sheets: OAuth 2.0**

```python
# Use existing OAuthManager
from backend.core.oauth import OAuthManager

token_id = config.get("oauth_token_id")
token_data = OAuthManager.get_token(token_id)
access_token = token_data["access_token"]

# Use Google Sheets API
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

credentials = Credentials(token=access_token)
service = build('sheets', 'v4', credentials=credentials)
```

### **Airtable: API Key**

```python
# Store API key in config (encrypted)
api_key = config.get("api_key")
headers = {"Authorization": f"Bearer {api_key}"}

# Use Airtable API
import httpx
response = httpx.get(
    f"https://api.airtable.com/v0/{base_id}/{table_name}",
    headers=headers
)
```

### **Slack: OAuth 2.0**

```python
# Use existing OAuthManager (already implemented)
from backend.core.oauth import OAuthManager

token_id = config.get("slack_token_id")
token_data = OAuthManager.get_token(token_id)
access_token = token_data["access_token"]
```

---

## 📋 Implementation Checklist

### **Google Sheets Node**
- [ ] Create `backend/nodes/input/google_sheets.py` (read)
- [ ] Create `backend/nodes/storage/google_sheets.py` (write)
- [ ] Implement OAuth authentication
- [ ] Handle spreadsheet reading (range, sheet selection)
- [ ] Handle spreadsheet writing (append, update, clear)
- [ ] Convert to/from list of dicts format
- [ ] Add to node registry
- [ ] Create frontend UI components

### **Airtable Node**
- [ ] Create `backend/nodes/input/airtable.py` (read)
- [ ] Create `backend/nodes/storage/airtable.py` (write)
- [ ] Implement API key authentication
- [ ] Handle record fetching (filtering, views)
- [ ] Handle record creation/updates
- [ ] Convert to/from list of dicts format
- [ ] Add to node registry
- [ ] Create frontend UI components

### **Enhanced Slack Node**
- [ ] Add structured data formatting methods
- [ ] Support table/list/summary formats
- [ ] Handle batch messaging (individual messages)
- [ ] Update frontend UI for format selection

---

## 📺 Display in Execution Panel

### **Where Data is Displayed**

Structured data from Google Sheets, CSV, Airtable, and Slack **will be displayed in the Execution Panel** during and after workflow execution.

**Location:**
- **Execution Panel** (slides up from bottom during execution)
- **Tab: "Outputs"** → Shows all node outputs
- **Each node** with structured data gets its own result card

### **Current Display Behavior**

**Currently**, structured data (lists of dictionaries) is displayed as **raw JSON**:

```json
{
  "data": [
    {"Name": "John", "Age": 30, "Email": "john@example.com"},
    {"Name": "Jane", "Age": 28, "Email": "jane@example.com"}
  ],
  "schema": {...}
}
```

**Component:** `UnifiedNodeOutput` → `display_type: 'data'` → Shows as formatted JSON

### **Recommended Enhancement: Table View**

To improve UX, we should enhance the display to show structured data as **interactive tables**:

**Proposed Enhancement:**
1. **Detect structured data** (list of dicts with consistent keys)
2. **Render as table** with columns and rows
3. **Add features:**
   - Sortable columns
   - Searchable/filterable rows
   - Pagination for large datasets
   - Export to CSV/Excel
   - Row count display

**Implementation:**
- Update `UnifiedNodeOutput.tsx` to detect `data` field with list of dicts
- Create `StructuredDataTable` component
- Add `display_type: 'table'` to output formatters

**Example Display:**
```
┌─────────────────────────────────────────────┐
│ 📊 Structured Data (3 rows)                │
├─────────────────────────────────────────────┤
│ Name  │ Age │ Email              │          │
├───────┼─────┼────────────────────┤          │
│ John  │ 30  │ john@example.com   │          │
│ Jane  │ 28  │ jane@example.com  │          │
│ Bob   │ 35  │ bob@example.com   │          │
└─────────────────────────────────────────────┘
[Export CSV] [Export Excel] [View JSON]
```

### **Display Flow**

```
[Node Executes] → [Output: {data: [...], schema: {...}}]
                           ↓
              [Execution Panel Opens]
                           ↓
              [Outputs Tab Selected]
                           ↓
        [Node Result Card Appears]
                           ↓
    [User Expands Card] → [Data Displayed]
                           ↓
    Current: JSON View | Enhanced: Table View
```

### **Where Data Appears**

1. **During Execution:**
   - Execution Panel slides up from bottom
   - Real-time updates as nodes complete
   - Each node's output appears in result cards

2. **After Execution:**
   - All outputs remain visible in Execution Panel
   - Can expand/collapse each node's result
   - Can copy/export data

3. **In Workflow Canvas:**
   - Nodes show execution status (idle/running/completed)
   - Click node → See output in Execution Panel
   - Data flows visually via edges

### **Example: CSV → Google Sheets Workflow**

```
Execution Panel Display:
┌─────────────────────────────────────────────┐
│ 📥 Data Loader                              │
│ ✓ Completed • 0.5s • $0.00                 │
│ ─────────────────────────────────────────── │
│ 📊 Structured Data (100 rows)              │
│ [Name] [Age] [Email]                        │
│ John   30    john@example.com              │
│ Jane   28    jane@example.com              │
│ ... (98 more rows)                          │
│ [Export CSV] [View JSON]                    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 📤 Google Sheets Write                      │
│ ✓ Completed • 1.2s • $0.00                 │
│ ─────────────────────────────────────────── │
│ ✅ Successfully wrote 100 rows              │
│ Spreadsheet: abc123                         │
│ Sheet: Sheet1                               │
│ Range: A1:C100                              │
└─────────────────────────────────────────────┘
```

---

## 🎓 Summary

**Key Takeaways:**

1. **Structured data = List of dictionaries** - All CSV/Sheets/Airtable data flows as `[{...}, {...}]`

2. **Data flows via edges** - Connect nodes with edges, data automatically passes through `inputs` parameter

3. **Universal format** - All data nodes output `{data: [...], schema: {...}, metadata: {...}}`

4. **Flexible inputs** - Nodes should accept `data`, `results`, `records` for maximum compatibility

5. **Schema preservation** - Always pass through schema information for downstream nodes

6. **OAuth for user data** - Google Sheets and Slack use OAuth, Airtable uses API keys

This architecture ensures seamless data flow between external sources, processing nodes, and output destinations!


