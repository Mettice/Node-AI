# RAG Chat Issue Analysis & Engine Modularization Plan

## 🔍 Issue 1: Chatbot Answer Doesn't Match Sources

### Problem Description
After running a RAG pipeline, the chatbot provides answers that don't match the retrieved sources, even though it cites the correct sources.

### Root Cause Analysis

#### Data Flow in RAG Pipeline
1. **Vector Search Node** outputs:
   ```python
   {
       "results": [
           {
               "text": "...",  # Retrieved chunk text
               "score": 0.532,
               "distance": 0.468,
               "index": 123,
               "metadata": {...}
           },
           ...
       ],
       "query": "user question",
       "provider": "faiss",
       "top_k": 5,
       "results_count": 3
   }
   ```

2. **Engine Data Collection** (lines 1195-1223 in `engine.py`):
   - When intelligent routing is ON, it reconstructs `results` and `query` from prefixed keys
   - When intelligent routing is OFF, it uses `_smart_merge_sources` which may not properly handle `results`

3. **Chat Node Template Rendering** (lines 83-127 in `chat.py`):
   ```python
   # Default template: "{context}\n\nQuestion: {query}\n\nAnswer:"
   # The _render_template method:
   # - Looks for {context} variable
   # - If not found, tries to get from results (line 102-111)
   # - Formats results as: "[1] text1\n\n[2] text2\n\n..."
   ```

#### Potential Issues

**Issue A: Context Not Properly Formatted**
- The chat node's `_render_template` method formats results as numbered list
- But it only extracts `text` field, ignoring `score` and `metadata`
- If `results` is empty or malformed, `context` will be empty

**Issue B: Query Mismatch**
- The query might come from config instead of inputs
- If query in config doesn't match the actual user question, the LLM gets confused

**Issue C: Template Not Using Context Effectively**
- Default template: `"{context}\n\nQuestion: {query}\n\nAnswer:"`
- The LLM might not be instructed to ONLY use the context
- No explicit instruction like "Answer based ONLY on the provided context"

**Issue D: Results Not Passed Correctly**
- In `engine.py` lines 1196-1223, there's special handling for chat nodes
- But this only works when intelligent routing is ON
- When intelligent routing is OFF, `_smart_merge_sources` might not handle `results` correctly

### Recommended Fixes

1. **Improve Context Formatting** (in `chat.py`):
   ```python
   # In _render_template, when formatting results:
   formatted_context = "\n\n".join([
       f"Source {i+1} (Score: {item.get('score', 0):.3f}):\n{item.get('text', '')}" 
       for i, item in enumerate(results)
   ])
   ```

2. **Add Explicit Instructions** (default template):
   ```python
   default_template = """Use the following context to answer the question. If the answer cannot be found in the context, say "I don't know."

Context:
{context}

Question: {query}

Answer based ONLY on the context above:"""
   ```

3. **Ensure Results Are Passed** (in `engine.py`):
   - Check that `results` from vector_search is properly passed to chat node
   - Add logging to verify `results` is present in chat node inputs

4. **Verify Query Consistency**:
   - Ensure the query passed to chat node matches the query used in vector_search
   - Log both queries to compare

---

## 📊 Issue 2: Engine.py Modularization

### Current State
- **File**: `backend/core/engine.py` (1848 lines)
- **Single Responsibility Violation**: The file handles:
  1. Workflow orchestration
  2. Validation & graph analysis
  3. Data collection & merging
  4. Node execution
  5. Tracing & observability
  6. Cost tracking

### Proposed Structure

```
backend/core/engine/
├── __init__.py              # Exports WorkflowEngine and engine instance
├── engine.py                # Main orchestration (~200 lines)
├── workflow_validator.py    # Validation & graph analysis (~200 lines)
├── data_collector.py        # Data collection & merging (~600 lines)
├── node_executor.py         # Node execution (~250 lines)
├── tracing.py               # Tracing & observability (~350 lines)
└── cost_tracker.py          # Cost tracking (~180 lines)
```

### Module Breakdown

#### 1. `engine/engine.py` (Main Orchestration)
**Responsibilities**:
- Main `execute()` method
- Orchestrates workflow execution
- Coordinates between modules
- Error handling and execution state management

**Methods**:
- `execute()` - Main entry point
- `__init__()` - Initialize engine

**Dependencies**:
- Imports from all other modules
- Uses WorkflowValidator, DataCollector, NodeExecutor, Tracing, CostTracker

#### 2. `engine/workflow_validator.py`
**Responsibilities**:
- Workflow structure validation
- Graph analysis (cycles, dependencies)
- Execution order building

**Methods**:
- `validate_workflow()` - Validate workflow structure
- `build_execution_order()` - Topological sort
- `has_circular_dependency()` - Check for cycles
- `find_cycle()` - Find cycle path
- `get_node_by_id()` - Utility to get node

**Lines**: ~200 (from current lines 382-553)

#### 3. `engine/data_collector.py`
**Responsibilities**:
- Collect source data from nodes
- Merge multiple inputs intelligently
- Handle direct vs indirect source priority
- Support intelligent routing

**Methods**:
- `collect_source_data()` - Collect without merging
- `smart_merge_sources()` - Merge with direct source priority
- `collect_all_source_data()` - Collect for intelligent routing
- `collect_node_inputs()` - Main input collection method

**Lines**: ~600 (from current lines 554-1255)

**Key Complexity**:
- Direct vs indirect source handling
- Intelligent routing integration
- Pattern-based field mapping
- Special handling for chat/vector nodes

#### 4. `engine/node_executor.py`
**Responsibilities**:
- Execute individual nodes
- Handle node execution errors
- Extract costs and tokens
- Add display metadata

**Methods**:
- `execute_node()` - Execute a single node
- `_create_safe_output_copy()` - Utility for safe copying

**Lines**: ~250 (from current lines 1257-1471)

#### 5. `engine/tracing.py`
**Responsibilities**:
- Query tracing for RAG workflows
- Observability span management
- Input/output sanitization

**Methods**:
- `add_to_query_trace()` - Add to query trace
- `map_node_type_to_span_type()` - Map node types
- `sanitize_inputs_for_trace()` - Sanitize inputs
- `complete_observability_span()` - Complete spans

**Lines**: ~350 (from current lines 1473-1842)

#### 6. `engine/cost_tracker.py`
**Responsibilities**:
- Record execution costs
- Persist costs to database
- Extract cost metadata

**Methods**:
- `record_execution_costs()` - Record costs for execution

**Lines**: ~180 (from current lines 1571-1722)

### Implementation Strategy

#### Phase 1: Create Module Structure
1. Create `backend/core/engine/` directory (already exists, but empty)
2. Create `__init__.py` with exports
3. Create empty module files

#### Phase 2: Extract Modules (One at a Time)
1. ✅ Extract `workflow_validator.py` first (least dependencies, ~200 lines)
2. ✅ Extract `cost_tracker.py` (isolated, ~180 lines)
3. ✅ Extract `tracing.py` (isolated, ~350 lines)
4. ✅ Extract `node_executor.py` (depends on tracing, ~250 lines)
5. ✅ Extract `data_collector.py` (most complex, ~600 lines)
6. ✅ Refactor `engine.py` to use modules (~200 lines)

#### Phase 3: Update Imports
1. Update `backend/core/engine/__init__.py` to export `WorkflowEngine` and `engine`
2. Keep backward compatibility: `backend/core/engine.py` can import from `engine/engine.py`

#### Phase 4: Testing
1. Test that all existing functionality works
2. Verify no breaking changes
3. Test with real workflows (especially RAG workflows)

### Benefits

1. **Maintainability**: Each module has a single responsibility
2. **Readability**: Smaller files are easier to understand
3. **Testability**: Modules can be tested independently
4. **Reusability**: Modules can be reused in other contexts
5. **Scalability**: Easy to add new features without bloating files

### Important Notes

1. **Backward Compatibility**: Keep `backend/core/engine.py` as a compatibility shim that imports from `engine/engine.py`
2. **No Breaking Changes**: All existing imports should continue to work
3. **Gradual Migration**: Extract modules one at a time, test after each
4. **Shared State**: Some methods need access to `self._user_id`, `self._use_intelligent_routing` - pass as parameters

### Dependencies Map

```
engine.py
├── workflow_validator.py
│   ├── models (Workflow, Node, Edge)
│   ├── exceptions (CircularDependencyError, WorkflowValidationError)
│   └── node_registry (NodeRegistry)
├── data_collector.py
│   ├── models (Workflow, Node)
│   ├── intelligent_router (route_data_intelligently)
│   ├── output_formatters (get_formatter_registry)
│   └── node_registry (NodeRegistry)
├── node_executor.py
│   ├── models (Node, NodeResult, Execution, NodeStatus)
│   ├── node_registry (NodeRegistry)
│   ├── output_formatters (get_formatter_registry)
│   └── observability (get_observability_manager)
├── tracing.py
│   ├── query_tracer (QueryTracer, TraceStepType)
│   ├── observability (get_observability_manager, SpanType)
│   └── models (Node, NodeResult)
└── cost_tracker.py
    ├── cost_intelligence (_cost_history)
    └── cost_storage (record_cost)
```

---

## 🎯 Next Steps

### For RAG Chat Issue:
1. Add logging to verify `results` and `query` are passed correctly to chat node
2. Improve context formatting to include scores
3. Update default template with explicit instructions
4. Test with a simple RAG workflow

### For Engine Modularization:
1. Start with `workflow_validator.py` (easiest, least dependencies)
2. Test after each extraction
3. Continue with other modules
4. Finally refactor main `engine.py`

