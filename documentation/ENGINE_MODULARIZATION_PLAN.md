# Engine Modularization Plan

## 📊 Current Structure Analysis

**File**: `backend/core/engine.py` (1675 lines)

**Methods Breakdown**:
1. **Main Orchestration** (~300 lines): `execute()`
2. **Workflow Validation & Graph** (~170 lines): `_validate_workflow()`, `_build_execution_order()`, `_has_circular_dependency()`, `_find_cycle()`, `_get_node_by_id()`
3. **Data Collection & Merging** (~540 lines): `_collect_source_data()`, `_smart_merge_sources()`, `_collect_all_source_data()`, `_collect_node_inputs()`
4. **Node Execution** (~210 lines): `_execute_node()`
5. **Tracing & Observability** (~320 lines): `_add_to_query_trace()`, `_map_node_type_to_span_type()`, `_sanitize_inputs_for_trace()`, `_create_safe_output_copy()`, `_complete_observability_span()`
6. **Cost Tracking** (~150 lines): `_record_execution_costs()`

---

## 🎯 Proposed Modular Structure

```
backend/core/engine/
├── __init__.py              # Exports WorkflowEngine and engine instance
├── engine.py                # Main orchestration (small, ~200 lines)
├── workflow_validator.py    # Validation & graph analysis (~200 lines)
├── data_collector.py        # Data collection & merging (~600 lines)
├── node_executor.py         # Node execution (~250 lines)
├── tracing.py               # Tracing & observability (~350 lines)
└── cost_tracker.py          # Cost tracking (~180 lines)
```

---

## 📋 Module Responsibilities

### 1. `engine/engine.py` (Main Orchestration)
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

---

### 2. `engine/workflow_validator.py`
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

**Dependencies**:
- `backend.core.models` (Workflow, Node, Edge)
- `backend.core.exceptions` (CircularDependencyError, WorkflowValidationError)
- `backend.core.node_registry` (NodeRegistry)

---

### 3. `engine/data_collector.py`
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

**Dependencies**:
- `backend.core.models` (Workflow, Node)
- `backend.core.intelligent_router` (route_data_intelligently)
- `backend.core.output_formatters` (get_formatter_registry)
- `backend.core.node_registry` (NodeRegistry)

---

### 4. `engine/node_executor.py`
**Responsibilities**:
- Execute individual nodes
- Handle node execution errors
- Extract costs and tokens
- Add display metadata

**Methods**:
- `execute_node()` - Execute a single node
- `_create_safe_output_copy()` - Utility for safe copying

**Dependencies**:
- `backend.core.models` (Node, NodeResult, Execution, NodeStatus)
- `backend.core.node_registry` (NodeRegistry)
- `backend.core.output_formatters` (get_formatter_registry)
- `backend.core.observability` (get_observability_manager)

---

### 5. `engine/tracing.py`
**Responsibilities**:
- Query tracing for RAG workflows
- Observability span management
- Input/output sanitization

**Methods**:
- `add_to_query_trace()` - Add to query trace
- `map_node_type_to_span_type()` - Map node types
- `sanitize_inputs_for_trace()` - Sanitize inputs
- `complete_observability_span()` - Complete spans

**Dependencies**:
- `backend.core.query_tracer` (QueryTracer, TraceStepType)
- `backend.core.observability` (get_observability_manager, SpanType)
- `backend.core.models` (Node, NodeResult)

---

### 6. `engine/cost_tracker.py`
**Responsibilities**:
- Record execution costs
- Persist costs to database
- Extract cost metadata

**Methods**:
- `record_execution_costs()` - Record costs for execution

**Dependencies**:
- `backend.api.cost_intelligence` (_cost_history)
- `backend.core.cost_storage` (record_cost)
- `backend.core.models` (NodeResult)

---

## 🔧 Implementation Strategy

### Phase 1: Create Module Structure
1. Create `backend/core/engine/` directory
2. Create `__init__.py` with exports
3. Create empty module files

### Phase 2: Extract Modules (One at a Time)
1. Extract `workflow_validator.py` first (least dependencies)
2. Extract `cost_tracker.py` (isolated)
3. Extract `tracing.py` (isolated)
4. Extract `node_executor.py` (depends on tracing)
5. Extract `data_collector.py` (most complex)
6. Refactor `engine.py` to use modules

### Phase 3: Update Imports
1. Update `backend/core/engine/__init__.py` to export `WorkflowEngine` and `engine`
2. Update all imports from `backend.core.engine` to `backend.core.engine.engine` (or keep backward compatibility)

### Phase 4: Testing
1. Test that all existing functionality works
2. Verify no breaking changes
3. Test with real workflows

---

## ✅ Benefits

1. **Maintainability**: Each module has a single responsibility
2. **Readability**: Smaller files are easier to understand
3. **Testability**: Modules can be tested independently
4. **Reusability**: Modules can be reused in other contexts
5. **Scalability**: Easy to add new features without bloating files

---

## ⚠️ Important Notes

1. **Backward Compatibility**: Keep `backend/core/engine.py` as a compatibility shim that imports from `engine/engine.py`
2. **No Breaking Changes**: All existing imports should continue to work
3. **Gradual Migration**: Extract modules one at a time, test after each
4. **Shared State**: Some methods need access to `self._user_id`, `self._use_intelligent_routing` - pass as parameters

---

## 🚀 Next Steps

1. Create module structure
2. Start with `workflow_validator.py` (easiest, least dependencies)
3. Test after each extraction
4. Continue with other modules
5. Finally refactor main `engine.py`

