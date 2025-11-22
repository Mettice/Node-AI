# Frontend Phase 2: Canvas & Nodes

**Duration:** 2-3 days  
**Status:** 📋 Not Started  
**Prerequisites:** [Frontend Phase 1: Setup & Foundation](./FRONTEND_PHASE_1_SETUP.md)

---

## 🎯 Goals

- Set up React Flow canvas
- Create custom node components
- Implement node palette with drag-and-drop
- Enable node connections (edges)
- Basic canvas interactions (zoom, pan, select)

---

## 📋 Tasks

### 1. React Flow Setup

#### 1.1 Canvas Component (`src/components/Canvas/WorkflowCanvas.tsx`)

- [ ] Set up React Flow provider
  - Import `ReactFlow` and required components
  - Configure default viewport
  - Set up node types and edge types

- [ ] Configure React Flow settings
  - Enable node dragging
  - Enable edge creation
  - Set connection mode
  - Configure snap to grid (optional)

- [ ] Handle canvas events
  - `onNodesChange` - Update nodes in store
  - `onEdgesChange` - Update edges in store
  - `onConnect` - Validate and create new edge
  - `onNodeClick` - Select node
  - `onPaneClick` - Deselect node

- [ ] Connect to workflow store
  - Read nodes/edges from store
  - Update store on changes
  - Sync selected node

#### 1.2 Canvas Controls (`src/components/Canvas/CanvasControls.tsx`)

- [ ] Zoom controls
  - Zoom in button
  - Zoom out button
  - Reset zoom button
  - Fit to view button

- [ ] View controls
  - Grid toggle
  - Minimap toggle (optional)
  - Clear canvas button

- [ ] Position controls
  - Center view
  - Reset viewport

---

### 2. Custom Node Component

#### 2.1 Base Node Component (`src/components/Canvas/CustomNode.tsx`)

- [ ] Node structure
  - Header (icon + name + status)
  - Body (config preview)
  - Connection handles (input/output)

- [ ] Visual styling
  - Category-based colors
  - Border styles
  - Shadow effects
  - Hover states

- [ ] Status indicators
  - Idle (default)
  - Running (animated spinner)
  - Success (checkmark)
  - Error (X icon)
  - Selected (highlighted border)

- [ ] Connection handles
  - Input handles (left side)
  - Output handles (right side)
  - Handle styling
  - Handle validation

- [ ] Node data display
  - Show key config values
  - Provider name (for generic nodes)
  - Model name (if applicable)

#### 2.2 Node Types Mapping

- [ ] Create node type definitions
  - Map node types to components
  - Define default node data
  - Set node dimensions

- [ ] Node category colors
  - Input: Purple (`#8b5cf6`)
  - Processing: Orange (`#f59e0b`)
  - Embedding: Cyan (`#06b6d4`)
  - Storage: Green (`#10b981`)
  - Retrieval: Blue (`#3b82f6`)
  - LLM: Pink (`#ec4899`)

#### 2.3 Node Icons (`src/components/Canvas/NodeIcon.tsx`)

- [ ] Icon component
  - Use Lucide React icons
  - Category-based icons
  - Size variants

- [ ] Icon mapping
  - `text_input` → FileText
  - `chunk` → Scissors
  - `embed` → Brain
  - `vector_store` → Database
  - `vector_search` → Search
  - `chat` → MessageSquare

---

### 3. Custom Edge Component

#### 3.1 Edge Component (`src/components/Canvas/CustomEdge.tsx`)

- [ ] Edge styling
  - Bezier curves
  - Arrow markers
  - Color based on status
  - Width based on status

- [ ] Edge states
  - Default (gray)
  - Active (blue, animated)
  - Success (green)
  - Error (red, dashed)

- [ ] Edge animations
  - Pulsing flow effect (when active)
  - Smooth transitions

#### 3.2 Edge Validation

- [ ] Connection validation
  - Check node types compatibility
  - Prevent circular connections
  - Prevent duplicate connections
  - Show validation errors

---

### 4. Node Palette

#### 4.1 Node Palette Component (`src/components/Sidebar/NodePalette.tsx`)

- [ ] Fetch nodes from API
  - Use React Query to fetch `/api/v1/nodes`
  - Group nodes by category
  - Handle loading/error states

- [ ] Category sections
  - Collapsible categories
  - Remember expanded state (localStorage)
  - Smooth expand/collapse animations

- [ ] Search/filter
  - Search input
  - Filter nodes by name/description
  - Highlight matching nodes

- [ ] Drag and drop
  - Make nodes draggable
  - Handle drop on canvas
  - Generate unique node IDs
  - Position nodes on drop

#### 4.2 Node Category Component (`src/components/Sidebar/NodeCategory.tsx`)

- [ ] Category header
  - Category name
  - Category icon
  - Expand/collapse button
  - Node count

- [ ] Category body
  - List of nodes in category
  - Node cards

#### 4.3 Node Card Component (`src/components/Sidebar/NodeCard.tsx`)

- [ ] Node card design
  - Node icon
  - Node name
  - Node description (tooltip)
  - Drag handle indicator

- [ ] Drag functionality
  - Make card draggable
  - Visual feedback on drag
  - Cursor change

- [ ] Hover effects
  - Show description
  - Highlight card
  - Show drag indicator

---

### 5. Canvas Interactions

#### 5.1 Node Selection

- [ ] Single node selection
  - Click node to select
  - Update selected node in store
  - Highlight selected node
  - Show in properties panel

- [ ] Deselection
  - Click canvas background
  - Press Escape key
  - Clear selected node

#### 5.2 Node Dragging

- [ ] Enable node dragging
  - Drag nodes on canvas
  - Update position in store
  - Maintain connections

- [ ] Snap to grid (optional)
  - Grid overlay
  - Snap nodes to grid
  - Toggle grid

#### 5.3 Edge Creation

- [ ] Create edges
  - Click output handle
  - Drag to input handle
  - Validate connection
  - Create edge on valid connection

- [ ] Edge deletion
  - Click edge to select
  - Press Delete key
  - Or: Delete button in edge context menu

#### 5.4 Node Deletion

- [ ] Delete nodes
  - Select node
  - Press Delete key
  - Or: Delete button in context menu
  - Remove connected edges

---

### 6. Canvas State Management

#### 6.1 Update Workflow Store

- [ ] Add canvas actions
  - `addNode(node)` - Add node to canvas
  - `removeNode(nodeId)` - Remove node
  - `updateNode(nodeId, data)` - Update node data
  - `updateNodePosition(nodeId, position)` - Update position
  - `addEdge(edge)` - Add edge
  - `removeEdge(edgeId)` - Remove edge
  - `selectNode(nodeId)` - Select node
  - `deselectNode()` - Deselect node

- [ ] Handle React Flow callbacks
  - `onNodesChange` → Update store
  - `onEdgesChange` → Update store
  - `onConnect` → Validate and add edge
  - `onNodeClick` → Select node

---

### 7. Visual Enhancements

#### 7.1 Canvas Background

- [ ] Grid background
  - Optional grid overlay
  - Toggle grid visibility
  - Grid styling

- [ ] Canvas styling
  - Background color
  - Border radius
  - Shadow effects

#### 7.2 Minimap (Optional)

- [ ] React Flow minimap
  - Show canvas overview
  - Navigate by clicking
  - Toggle visibility

#### 7.3 Node Animations

- [ ] Status animations
  - Pulsing border (running)
  - Success checkmark animation
  - Error shake animation

- [ ] Hover effects
  - Scale on hover
  - Shadow on hover
  - Tooltip on hover

---

## ✅ Deliverables Checklist

- [ ] React Flow canvas functional
- [ ] Custom nodes render correctly
- [ ] Nodes can be dragged on canvas
- [ ] Nodes can be connected with edges
- [ ] Node palette displays all nodes
- [ ] Can drag nodes from palette to canvas
- [ ] Node selection works
- [ ] Edge creation/deletion works
- [ ] Canvas zoom/pan works
- [ ] Node deletion works
- [ ] Visual feedback for all interactions

---

## 🧪 Testing Checklist

- [ ] Can add node to canvas
- [ ] Can move node on canvas
- [ ] Can connect two nodes
- [ ] Can disconnect nodes
- [ ] Can delete node
- [ ] Can delete edge
- [ ] Node selection works
- [ ] Canvas zoom works
- [ ] Canvas pan works
- [ ] Node palette shows all nodes
- [ ] Can drag node from palette
- [ ] Invalid connections are prevented

---

## 📝 Notes

- Start with basic node rendering
- Add interactions incrementally
- Test each feature as you build
- Keep node components simple initially
- Add visual polish later

---

## 🔗 Related Files

- `frontend/src/components/Canvas/WorkflowCanvas.tsx` - Main canvas
- `frontend/src/components/Canvas/CustomNode.tsx` - Node component
- `frontend/src/components/Canvas/CustomEdge.tsx` - Edge component
- `frontend/src/components/Canvas/CanvasControls.tsx` - Canvas controls
- `frontend/src/components/Sidebar/NodePalette.tsx` - Node palette
- `frontend/src/store/workflowStore.ts` - Workflow state

---

## ➡️ Next Phase

Once Phase 2 is complete, proceed to [Frontend Phase 3: Properties & Configuration](./FRONTEND_PHASE_3_PROPERTIES.md)

