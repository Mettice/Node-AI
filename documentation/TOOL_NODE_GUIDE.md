# Tool Node Implementation Guide

## ✅ Currently Implemented Tools

The backend already has **6 tool types** fully implemented:

1. **Calculator** (`calculator`)
   - Mathematical expression evaluation
   - Config: `calculator_allowed_operations` (all, basic, advanced)

2. **Web Search** (`web_search`)
   - Search the web for information
   - Providers: DuckDuckGo, SerpAPI, Brave Search
   - Config: `web_search_provider`, `web_search_api_key`

3. **Code Execution** (`code_execution`)
   - Execute Python or JavaScript code in sandboxed environment
   - Config: `code_execution_language` (python, javascript), `code_execution_timeout`

4. **Database Query** (`database_query`)
   - Execute SQL queries on databases
   - Database types: SQLite, PostgreSQL, MySQL
   - Config: `database_type`, `database_connection_string`

5. **API Call** (`api_call`)
   - Make HTTP requests to external APIs
   - Config: `api_call_url`, `api_call_method` (GET, POST, PUT, DELETE), `api_call_headers`

6. **Custom** (`custom`)
   - Placeholder for custom tool implementations
   - Config: None (fully custom)

---

## 🔧 How to Add a New Tool

### Step 1: Update Backend Schema

Edit `backend/nodes/tools/tool_node.py`:

1. **Add to enum** in `get_schema()`:
```python
"tool_type": {
    "type": "string",
    "enum": ["calculator", "web_search", "code_execution", "database_query", "api_call", "custom", "your_new_tool"],  # Add here
    "default": "calculator",
    ...
}
```

2. **Add config fields** in `get_schema()`:
```python
# Your new tool config
"your_new_tool_api_key": {
    "type": "string",
    "title": "API Key",
    "description": "API key for your service",
},
"your_new_tool_endpoint": {
    "type": "string",
    "title": "Endpoint",
    "description": "API endpoint URL",
},
```

3. **Implement tool function** in `create_langchain_tool()`:
```python
elif tool_type == "your_new_tool":
    def your_tool_func(param: str) -> str:
        """Description of what your tool does."""
        api_key = config.get("your_new_tool_api_key", "")
        endpoint = config.get("your_new_tool_endpoint", "")
        
        try:
            # Your implementation here
            # Make API calls, process data, etc.
            result = your_implementation(param, api_key, endpoint)
            return result
        except Exception as e:
            return f"Error: {str(e)}"
    
    return Tool(
        name=tool_name,
        func=your_tool_func,
        description=tool_description,
    )
```

### Step 2: Update Frontend

1. **Add to ToolTypeSelector** (`frontend/src/components/Properties/ToolTypeSelector.tsx`):
```typescript
const TOOL_TYPE_OPTIONS = [
  // ... existing options
  { value: 'your_new_tool', label: 'Your New Tool', icon: 'your_icon' },
];
```

2. **Add icon** to `ProviderIcon.tsx`:
```typescript
const TOOL_TYPE_ICONS: Record<string, { icon: React.ComponentType<{ className?: string }>, color: string }> = {
  // ... existing icons
  your_icon: { icon: YourIconComponent, color: '#YOUR_COLOR' },
};
```

3. **Update tool type prefixes** in `SchemaForm.tsx`:
```typescript
const toolTypePrefixes: Record<string, string[]> = {
  // ... existing
  your_new_tool: ['your_new_tool_'],
};
```

4. **Update defaults** in `handleToolTypeChange`:
```typescript
const toolDefaults: Record<string, { name: string; description: string }> = {
  // ... existing
  your_new_tool: { name: 'your_new_tool', description: 'Description of your tool' },
};
```

---

## 📋 Example: Adding Serper Tool

### Backend Changes:

```python
# In get_schema(), add to enum:
"enum": ["calculator", "web_search", "code_execution", "database_query", "api_call", "custom", "serper"],

# Add config fields:
"serper_api_key": {
    "type": "string",
    "title": "Serper API Key",
    "description": "API key from serper.dev",
},

# In create_langchain_tool(), add implementation:
elif tool_type == "serper":
    async def serper_search_async(query: str) -> str:
        """Search the web using Serper API."""
        api_key = config.get("serper_api_key", "")
        if not api_key:
            return "Error: Serper API key required"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                    json={"q": query}
                )
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("organic", [])[:5]
                    formatted = "\n".join([
                        f"{i+1}. {r.get('title', 'No title')}\n   {r.get('snippet', 'No description')}\n   {r.get('link', 'No URL')}"
                        for i, r in enumerate(results)
                    ])
                    return formatted
                return f"Error: Search failed with status {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def serper_search(query: str) -> str:
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(serper_search_async(query))
        except RuntimeError:
            return asyncio.run(serper_search_async(query))
    
    return Tool(
        name=tool_name,
        func=serper_search,
        description=tool_description,
    )
```

### Frontend Changes:

```typescript
// In ToolTypeSelector.tsx
{ value: 'serper', label: 'Serper', icon: 'serper' },

// In ProviderIcon.tsx (already has serper in FALLBACK_ICONS)
// No changes needed if using existing icon

// In SchemaForm.tsx
const toolTypePrefixes: Record<string, string[]> = {
  // ... existing
  serper: ['serper_'],
};

const toolDefaults: Record<string, { name: string; description: string }> = {
  // ... existing
  serper: { name: 'serper', description: 'Serper API tool for Google search' },
};
```

---

## 🎯 Best Practices

1. **Naming Convention**: Use snake_case for tool types and config fields
   - Tool type: `web_search`, `api_call`
   - Config fields: `web_search_provider`, `api_call_url`

2. **Error Handling**: Always return error messages as strings
   ```python
   try:
       result = your_operation()
       return result
   except Exception as e:
       return f"Error: {str(e)}"
   ```

3. **Async Support**: If your tool needs async operations, use the wrapper pattern:
   ```python
   async def async_func(param: str) -> str:
       # Async implementation
       pass
   
   def sync_func(param: str) -> str:
       try:
           loop = asyncio.get_event_loop()
           return loop.run_until_complete(async_func(param))
       except RuntimeError:
           return asyncio.run(async_func(param))
   ```

4. **Config Validation**: Add validation in the tool function:
   ```python
   api_key = config.get("your_tool_api_key", "")
   if not api_key:
       return "Error: API key is required"
   ```

5. **Documentation**: Update this guide when adding new tools!

---

## 🔍 Testing New Tools

1. Add tool node to canvas
2. Select your new tool type
3. Configure required fields
4. Connect to an Agent node
5. Execute workflow and verify tool works

---

## 📝 Current Tool Status

| Tool | Status | Config Fields | Notes |
|------|--------|---------------|-------|
| Calculator | ✅ Complete | `calculator_allowed_operations` | Safe math evaluation |
| Web Search | ✅ Complete | `web_search_provider`, `web_search_api_key` | Supports 3 providers |
| Code Execution | ✅ Complete | `code_execution_language`, `code_execution_timeout` | Sandboxed Python/JS |
| Database Query | ✅ Complete | `database_type`, `database_connection_string` | SQLite, PostgreSQL, MySQL |
| API Call | ✅ Complete | `api_call_url`, `api_call_method`, `api_call_headers` | Generic HTTP client |
| Custom | ✅ Placeholder | None | For custom implementations |

---

## 🚀 Planned Tools (Not Yet Implemented)

Based on `INTEGRATIONS_PRIORITY.md`:

- **Serper** - Google Search API (high priority)
- **Resend** - Email sending (high priority)
- **S3** - AWS S3 file operations (high priority)
- **Slack** - Team notifications (medium priority)
- **Reddit** - Content aggregation (medium priority)
- **Salesforce** - CRM operations (medium priority)

See `INTEGRATIONS_PRIORITY.md` for full list and priorities.

