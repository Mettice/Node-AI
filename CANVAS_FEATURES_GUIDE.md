# Canvas Features Guide

## 🖱️ How to Select Nodes

### Single Node Selection:
- **Click on a node** to select it
- Click on empty canvas to deselect

### Multi-Node Selection:
There are **two ways** to select multiple nodes:

1. **Ctrl/Cmd + Click** (Recommended):
   - Hold `Ctrl` (Windows/Linux) or `Cmd` (Mac)
   - Click on each node you want to select
   - Each click adds/removes that node from selection

2. **Selection Box** (Drag to select):
   - Hold `Shift` key
   - Click and drag on the canvas to draw a selection box
   - All nodes inside the box will be selected

### Keyboard Shortcuts:
- `Ctrl/Cmd + A` - Select all nodes (if implemented)
- `Delete` - Delete selected nodes
- `Escape` - Deselect all nodes

---

## 🎯 Multi-Selection Toolbar

### How It Works:
1. **Select Multiple Nodes** using one of the methods above
2. **Toolbar Appears**: When 2+ nodes are selected, a floating toolbar appears at the top center of the canvas
3. **Available Actions**:
   - **Align**: Align nodes to left, center, or right edges
   - **Distribute**: Evenly space nodes horizontally
   - **Group**: Create a visual frame around selected nodes
   - **Duplicate**: Clone all selected nodes with offset
   - **Delete**: Remove all selected nodes

### Location:
- Component: `QuickActionsToolbar` in `CanvasInteractions.tsx`
- Rendered in: `WorkflowCanvas.tsx` (line 549-556)
- Condition: Only shows when `selectedNodes.length >= 2`

---

## 📦 Grouping / Frames

### How It Works:

#### Creating a Group:
1. **Select 2+ nodes** using multi-selection
2. **Click the Group button** in the Quick Actions Toolbar
3. **A frame appears** around the selected nodes with:
   - Color-coded border (8 different colors)
   - Editable label (default: "New Group")
   - Collapse/expand button
   - Node count display

#### Editing Group Label:
1. **Click on the group label** in the header
2. **Type new name** (e.g., "RAG Pipeline", "Agent System")
3. **Press Enter** to save, or **Escape** to cancel

#### Collapsing/Expanding:
1. **Click the chevron** (▶/▼) in the group header
2. **Collapsed**: Shows only header with label
3. **Expanded**: Shows full frame with all nodes

#### Deleting a Group:
1. **Hover over group header** to show controls
2. **Click delete button** (trash icon)
3. **Group is removed** (nodes remain on canvas)

### Features:
- ✅ Visual frames with color-coded borders
- ✅ Editable labels (click to rename)
- ✅ Collapsible groups (minimize/expand)
- ✅ 8 distinct colors for different groups
- ✅ Drag group to move all contained nodes (future enhancement)
- ✅ Delete protection (confirmation before removing)

### Location:
- Component: `NodeGroups.tsx`
- Hook: `useCanvasInteractions` in `CanvasInteractions.tsx`
- Functions: `createGroup()`, `updateGroup()`, `deleteGroup()`

---

## 🎨 Auto-Layout Dropdown

### How It Works:
1. **Click the grid icon** in bottom-right panel
2. **Dropdown opens** showing icon-only buttons
3. **Hover over icons** to see tooltips with descriptions
4. **Click an icon** to apply that layout:
   - **→ Horizontal Flow**: Arranges nodes left to right
   - **↓ Vertical Flow**: Arranges nodes top to bottom
   - **○ Radial**: Arranges nodes in a circle
   - **⊞ Hierarchical**: Arranges by dependencies
   - **⌘ Fit View**: Centers and scales to show all nodes

### Features:
- ✅ Icon-only interface (cleaner design)
- ✅ Hover tooltips show full descriptions
- ✅ Smart positioning (opens up/down based on space)
- ✅ Click outside to close
- ✅ Auto-fit view after layout

### Location:
- Component: `AutoLayoutToolbar` in `CanvasInteractions.tsx`
- Rendered in: `WorkflowCanvas.tsx` (line 501-504)

---

## 📝 Sticky Notes

### How It Works:
1. **Double-click canvas** to create a note at that position
2. **Or click the sticky note button** in bottom-right panel
3. **Click note** to edit content
4. **Drag note** to move it
5. **Resize note** using corner handle
6. **Change color** via color picker

### Features:
- ✅ Double-click creation
- ✅ Draggable
- ✅ Resizable
- ✅ 8 color options
- ✅ Rich text support (basic markdown)
- ✅ Auto-save on edit

---

## 🔧 Smart Snapping

### How It Works:
1. **Drag a node** near another node
2. **Alignment guides appear** (blue lines) when within 20px
3. **Node snaps** to aligned position automatically
4. **Grid snapping** to 20px grid for clean positioning

### Features:
- ✅ 20px snap distance
- ✅ Visual alignment guides
- ✅ Grid snapping
- ✅ Multi-node alignment

