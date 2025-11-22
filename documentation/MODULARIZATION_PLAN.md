# Code Modularization Plan

## Overview
Both `tool_node.py` (656 lines) and `SchemaForm.tsx` (793 lines) are getting too large. We need to modularize them before adding more integrations.

## Backend: Tool Node Modularization

### Structure
```
backend/nodes/tools/
├── tool_node.py (main orchestrator, ~200 lines)
└── tools/
    ├── __init__.py
    ├── calculator.py
    ├── web_search.py
    ├── code_execution.py
    ├── database_query.py
    ├── api_call.py
    └── email.py (new)
```

### Each tool module exports:
- `get_<tool>_schema()` → Returns schema fields dict
- `create_<tool>_tool(config)` → Returns tool function

### tool_node.py will:
- Import all tool modules
- Aggregate schemas in `get_schema()`
- Route to appropriate tool creator in `create_langchain_tool()`

## Frontend: SchemaForm Modularization

### Structure
```
frontend/src/components/Properties/
├── SchemaForm.tsx (main orchestrator, ~200 lines)
└── SchemaForm/
    ├── FieldRenderers.tsx (handles field rendering logic)
    ├── FieldHandlers.tsx (special field handling)
    ├── ToolFieldHandlers.tsx (tool-specific fields)
    └── ProviderFieldHandlers.tsx (provider-specific fields)
```

### SchemaForm.tsx will:
- Import field handlers
- Orchestrate field rendering
- Handle form state management

## Implementation Steps

1. ✅ Create tools/ folder structure
2. ✅ Create calculator.py
3. ✅ Create web_search.py
4. ⏳ Create code_execution.py
5. ⏳ Create database_query.py
6. ⏳ Create api_call.py
7. ⏳ Refactor tool_node.py to use modules
8. ⏳ Create SchemaForm/ folder
9. ⏳ Split SchemaForm.tsx
10. ⏳ Implement email.py
11. ⏳ Test all integrations

