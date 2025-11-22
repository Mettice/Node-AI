# Phase 2: Frontend Canvas

**Duration:** Week 4-5  
**Status:** 🔄 Not Started  
**Prerequisites:** [Phase 1: Core Engine & First Nodes](./PHASE_1_CORE_ENGINE.md)

---

## 🎯 Goals

- Visual canvas with drag-and-drop
- Node configuration panel
- Real-time execution display
- Basic workflow building

---

## 📋 Tasks

### Frontend: Canvas Setup

#### 1. React Flow Integration

- [ ] Set up React Flow with custom node types
  - Install `reactflow` package
  - Configure React Flow provider
  - Set up custom node types registry

- [ ] Configure node styles and positioning
  - Define node dimensions
  - Set up default node styles
  - Configure node positioning logic

- [ ] Handle node dragging
  - Enable node dragging
  - Snap to grid (optional)
  - Prevent dragging outside canvas

- [ ] Handle edge connections
  - Enable edge creation
  - Validate connections (type checking)
  - Prevent invalid connections
  - Handle edge deletion

- [ ] Zoom/pan controls
  - Zoom in/out buttons
  - Pan with mouse drag
  - Fit to view functionality
  - Mini-map (optional)

#### 2. Custom Node Component (`frontend/src/components/Canvas/CustomNode.tsx`)

- [ ] Visual representation of each node type
  - Different icons for each category
  - Node type label
  - Node ID display (optional)

- [ ] Status indicators
  - Idle state (default)
  - Running state (animated)
  - Success state (green checkmark)
  - Error state (red X)

- [ ] Node icons and labels
  - Category-based icons
  - Node type name
  - Status badge

- [ ] Connection handles
  - Input handles (left side)
  - Output handles (right side)
  - Handle styling
  - Handle validation

#### 3. Custom Edge Component (`frontend/src/components/Canvas/CustomEdge.tsx`)

- [ ] Visual connections between nodes
  - Bezier curves
  - Arrow markers
  - Edge labels (optional)

- [ ] Animated flow during execution
  - Animate data flow
  - Show execution progress
  - Highlight active edges

- [ ] Status colors
  - Default (gray)
  - Active (blue)
  - Success (green)
  - Error (red)

#### 4. Canvas Controls (`frontend/src/components/Canvas/CanvasControls.tsx`)

- [ ] Zoom in/out buttons
- [ ] Fit to view button
- [ ] Clear canvas button
- [ ] Grid toggle
- [ ] Minimap toggle (optional)

---

### Frontend: Node Palette

#### 1. Node Palette Component (`frontend/src/components/Sidebar/NodePalette.tsx`)

- [ ] Collapsible categories
  - Expand/collapse each category
  - Remember state (localStorage)
  - Smooth animations

- [ ] Search/filter nodes
  - Search input
  - Filter by category
  - Highlight matching nodes

- [ ] Drag nodes to canvas
  - Make nodes draggable
  - Create new node on drop
  - Generate unique node IDs

#### 2. Node Categories

- [ ] Input nodes category
  - Text Input
  - Upload File (placeholder for Phase 3)

- [ ] Processing nodes category
  - Text Splitter

- [ ] Embedding nodes category
  - OpenAI Embed

- [ ] Storage nodes category
  - FAISS Store

- [ ] Retrieval nodes category
  - Vector Search

- [ ] LLM nodes category
  - OpenAI Chat

- [ ] Output nodes category
  - Text Output (simple display)

#### 3. Node Card (`frontend/src/components/Sidebar/NodeCard.tsx`)

- [ ] Node icon
  - Category-based icon
  - Consistent sizing

- [ ] Node name
  - Display name
  - Tooltip with description

- [ ] Node description
  - Short description
  - Expandable (optional)

- [ ] Drag handle
  - Visual drag indicator
  - Cursor change on hover

---

### Frontend: Properties Panel

#### 1. Properties Panel (`frontend/src/components/Properties/PropertiesPanel.tsx`)

- [ ] Show when node selected
  - Display panel on node selection
  - Hide when no node selected
  - Show "Select a node" message

- [ ] Dynamic form based on node schema
  - Fetch schema from API
  - Generate form fields
  - Support all field types

- [ ] Form validation
  - Real-time validation
  - Show error messages
  - Prevent invalid submissions

- [ ] Save configuration
  - Update node data on change
  - Auto-save (debounced)
  - Show save confirmation

#### 2. Schema Form (`frontend/src/components/Properties/SchemaForm.tsx`)

- [ ] Generate form from node schema
  - Parse JSON schema
  - Create appropriate input components

- [ ] Support different field types:
  - `string` - Text input
  - `number` - Number input
  - `integer` - Integer input
  - `boolean` - Checkbox
  - `array` - List input
  - `object` - Nested form
  - `enum` - Select dropdown

- [ ] Real-time validation
  - Validate on input change
  - Show validation errors
  - Highlight invalid fields

#### 3. Node Testing (`frontend/src/components/Properties/NodeTestPanel.tsx`)

- [ ] "Test Node" button
  - Visible in properties panel
  - Disabled if node not configured

- [ ] Sample input generator
  - Generate sample inputs based on node type
  - Allow manual input override

- [ ] Test execution
  - Call test endpoint
  - Show loading state
  - Display results

- [ ] Results display
  - Show output preview
  - Show execution time
  - Show cost (if applicable)
  - Expandable JSON viewer

---

### Frontend: Execution Panel

#### 1. Execution Controls (`frontend/src/components/Execution/ExecutionControls.tsx`)

- [ ] Run workflow button
  - Validate workflow before execution
  - Show loading state
  - Disable during execution

- [ ] Stop execution button
  - Cancel running execution
  - Show confirmation dialog

- [ ] Clear results button
  - Clear execution results
  - Reset node states

#### 2. Execution Status (`frontend/src/components/Execution/ExecutionStatus.tsx`)

- [ ] Real-time node status updates
  - Update node status on canvas
  - Show progress indicators
  - Display error messages

- [ ] Progress indicators
  - Overall progress bar
  - Per-node progress
  - Execution timeline

- [ ] Error messages
  - Display node errors
  - Show error details
  - Link to error node

#### 3. Cost Tracker (`frontend/src/components/Execution/CostTracker.tsx`)

- [ ] Real-time cost display
  - Update cost during execution
  - Show total cost
  - Show cost breakdown

- [ ] Cost breakdown by node
  - List each node's cost
  - Show cost percentage
  - Highlight expensive nodes

- [ ] Cost history
  - Track costs over time
  - Show cost trends (optional)

#### 4. Execution Logs (`frontend/src/components/Execution/ExecutionLogs.tsx`)

- [ ] Execution timeline
  - Chronological list of steps
  - Show node execution order
  - Display timestamps

- [ ] Node execution order
  - Visual timeline
  - Show dependencies
  - Highlight parallel execution

- [ ] Duration per node
  - Show execution time
  - Compare with previous runs
  - Identify slow nodes

- [ ] Output previews
  - Expandable output views
  - JSON viewer for structured data
  - Text preview for text data

---

### Frontend: State Management

#### 1. Workflow Store (`frontend/src/store/workflowStore.ts`)

- [ ] Current workflow state
  - Nodes array
  - Edges array
  - Workflow metadata

- [ ] Selected node
  - Track selected node ID
  - Update on selection change

- [ ] Execution state
  - Execution status
  - Execution results
  - Execution trace

- [ ] Actions:
  - `addNode(node)`
  - `removeNode(nodeId)`
  - `updateNode(nodeId, data)`
  - `addEdge(edge)`
  - `removeEdge(edgeId)`
  - `selectNode(nodeId)`
  - `startExecution()`
  - `updateExecutionStatus(status)`

#### 2. API Integration (`frontend/src/services/`)

- [ ] Workflow API client (`workflows.ts`)
  - `executeWorkflow(workflow)`
  - `getExecutionStatus(executionId)`
  - `getExecutionTrace(executionId)`

- [ ] Execution API client (`execution.ts`)
  - `startExecution(workflowId)`
  - `stopExecution(executionId)`
  - `getExecutionResults(executionId)`

- [ ] Node schema API client (`nodes.ts`)
  - `listNodes()`
  - `getNodeSchema(nodeType)`

- [ ] SSE for real-time updates
  - Connect to SSE endpoint
  - Handle connection errors
  - Reconnect on disconnect

---

### Frontend: Real-time Updates

#### 1. Server-Sent Events (SSE)

- [ ] Connect to execution endpoint
  - Create SSE connection
  - Handle connection lifecycle
  - Error handling and reconnection

- [ ] Receive node status updates
  - Parse SSE messages
  - Update node status in store
  - Trigger UI updates

- [ ] Update UI in real-time
  - Update node visual state
  - Update execution panel
  - Update cost tracker

#### 2. Execution Visualization

- [ ] Highlight active nodes
  - Visual indicator on running nodes
  - Animate active state
  - Show progress (if available)

- [ ] Show data flow
  - Animate data through edges
  - Show data size (optional)
  - Highlight data paths

- [ ] Display intermediate results
  - Show node outputs on hover
  - Expandable result previews
  - Copy to clipboard

---

## ✅ Deliverables Checklist

- [ ] Visual canvas functional
- [ ] Can drag nodes from palette
- [ ] Can connect nodes with edges
- [ ] Can configure nodes
- [ ] Can execute workflow
- [ ] Real-time execution feedback
- [ ] Cost tracking visible
- [ ] Execution logs working
- [ ] Node testing functional
- [ ] Error handling in place

---

## 🎨 UI Components Structure

```
frontend/src/components/
├── Canvas/
│   ├── WorkflowCanvas.tsx      # Main canvas component
│   ├── CustomNode.tsx          # Custom node rendering
│   ├── CustomEdge.tsx          # Custom edge rendering
│   └── CanvasControls.tsx      # Canvas controls
├── Sidebar/
│   ├── NodePalette.tsx         # Node palette container
│   ├── NodeCategory.tsx        # Category section
│   └── NodeCard.tsx            # Individual node card
├── Properties/
│   ├── PropertiesPanel.tsx     # Properties panel container
│   ├── SchemaForm.tsx          # Dynamic form generator
│   ├── FormField.tsx           # Individual form field
│   └── NodeTestPanel.tsx       # Node testing panel
└── Execution/
    ├── ExecutionPanel.tsx      # Execution panel container
    ├── ExecutionControls.tsx   # Run/stop controls
    ├── ExecutionStatus.tsx     # Status display
    ├── CostTracker.tsx         # Cost tracking
    └── ExecutionLogs.tsx       # Execution logs
```

---

## 🧪 Testing Checklist

- [ ] Can add node to canvas
- [ ] Can remove node from canvas
- [ ] Can connect two nodes
- [ ] Can disconnect nodes
- [ ] Can configure node properties
- [ ] Can execute simple workflow
- [ ] See real-time execution updates
- [ ] See cost tracking updates
- [ ] See execution logs
- [ ] Can test individual nodes
- [ ] Error messages display correctly

---

## 📝 Notes

- Use React Flow's built-in features where possible
- Keep components small and focused
- Use TypeScript for type safety
- Handle loading and error states
- Optimize for performance (memoization)
- Make UI responsive

---

## 🔗 Related Files

- `frontend/src/components/Canvas/WorkflowCanvas.tsx` - Main canvas
- `frontend/src/store/workflowStore.ts` - State management
- `frontend/src/services/api.ts` - API client
- `frontend/src/types/workflow.ts` - TypeScript types

---

## ➡️ Next Phase

Once Phase 2 is complete, proceed to [Phase 3: Complete RAG Pipeline](./PHASE_3_COMPLETE_RAG.md)

