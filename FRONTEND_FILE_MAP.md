# Frontend File Map - Canvas & Design System

## Priority 1: Core Canvas & Node Styling

### CSS/Styling Files
- **`frontend/src/index.css`** - Main stylesheet with:
  - Dark glassmorphic theme
  - Canvas background & animated grid (`.canvas-dark`)
  - Glassmorphism utilities (`.glass`, `.glass-light`, `.glass-strong`, `.node-glass`)
  - Category glow effects (`.glow-input`, `.glow-processing`, etc.)
  - Node animations (`.node-active`, `.node-running`, `.node-completed`, etc.)
  
- **`frontend/src/styles/mobile-canvas.css`** - Mobile-specific canvas optimizations:
  - Touch-optimized React Flow controls
  - Mobile node interactions
  - Mobile connection mode styles
  - Mobile gestures

- **`frontend/tailwind.config.js`** - Tailwind configuration:
  - Dark theme colors
  - Glass effect colors
  - Node category colors
  - Custom spacing, border radius, transitions

- **`frontend/src/styles/theme.ts`** - Theme tokens & design system:
  - Color palette (canvas, categories, text)
  - Glassmorphism effects
  - Shadows & glows
  - Animation speeds
  - Utility functions (`getCategoryColor`, `getCategoryGlow`)

### Node Components
- **`frontend/src/components/Canvas/CustomNode.tsx`** - Main node component:
  - Node rendering logic
  - Node styling (glassmorphic style)
  - Status badges & animations
  - Icon mapping for different node types
  - Execution status handling
  - Cost & duration display
  
- **`frontend/src/components/Canvas/NodeEditModal.tsx`** - Node editing modal
- **`frontend/src/components/Canvas/NodeConfigDisplay.tsx`** - Node configuration display
- **`frontend/src/components/Canvas/NodePreviewModal.tsx`** - Node preview modal
- **`frontend/src/components/Canvas/ExecutionStatusIcon.tsx`** - Execution status icon component

### Canvas/React Flow Setup
- **`frontend/src/components/Canvas/WorkflowCanvas.tsx`** - Main React Flow canvas:
  - React Flow configuration
  - Node & edge type definitions (`NODE_TYPES`, `EDGE_TYPES`)
  - Canvas event handlers (drag, drop, connect, etc.)
  - Mobile toolbar integration
  - Panel positioning (top-left, top-right, bottom-center, bottom-right)
  - Grid background (handled via CSS, not React Flow Background component)

- **`frontend/src/components/Canvas/CustomEdge.tsx`** - Custom edge/connection component:
  - Edge styling (premium/schematic look)
  - Execution status-based edge colors
  - Animated flowing particles
  - Bezier path rendering

### Node Type Definitions & Constants
- **`frontend/src/constants/index.ts`** - Application constants:
  - `NODE_CATEGORY_COLORS` - Color mapping for node categories
  - `NODE_CATEGORY_ICONS` - Icon mapping for node categories

---

## Priority 2: Layout & Panels

### Layout Components
- **`frontend/src/components/Layout/MainLayout.tsx`** - Main app layout:
  - Sidebar toggle button
  - Left sidebar (UtilitySidebar)
  - Canvas area (WorkflowCanvas)
  - Right sidebar (ExecutionLogsSidebar)
  - Chat interface overlay
  - Utility modals

### Sidebar Components
- **`frontend/src/components/Sidebar/UtilitySidebar.tsx`** - Left sidebar with utilities
- **`frontend/src/components/Sidebar/ExecutionLogsSidebar.tsx`** - Right sidebar for execution logs
- **`frontend/src/components/Sidebar/NodePalette.tsx`** - Node palette (for adding nodes)
- **`frontend/src/components/Sidebar/NodeCategory.tsx`** - Node category grouping
- **`frontend/src/components/Sidebar/NodeCard.tsx`** - Individual node card in palette
- **`frontend/src/components/Sidebar/UtilityModal.tsx`** - Utility modal overlay

### Panel Components
- **`frontend/src/components/Execution/ExecutionPanel.tsx`** - Execution results panel
- **`frontend/src/components/Properties/PropertiesPanel.tsx`** - Properties/configuration panel
- **`frontend/src/components/Settings/SettingsPanel.tsx`** - Settings panel
- **`frontend/src/components/RAGEvaluation/RAGEvaluationPanel.tsx`** - RAG evaluation panel
- **`frontend/src/components/RAGOptimization/RAGOptimizationPanel.tsx`** - RAG optimization panel

### Header Components
- **`frontend/src/components/Header/WorkflowHeader.tsx`** - Workflow header/toolbar

---

## Priority 3: Design System

### Shared UI Components
- **`frontend/src/components/common/Button.tsx`** - Button component
- **`frontend/src/components/common/Card.tsx`** - Card component
- **`frontend/src/components/common/Input.tsx`** - Input component
- **`frontend/src/components/common/Select.tsx`** - Select component
- **`frontend/src/components/common/SelectWithIcons.tsx`** - Select with icons
- **`frontend/src/components/common/Textarea.tsx`** - Textarea component
- **`frontend/src/components/common/Spinner.tsx`** - Loading spinner
- **`frontend/src/components/common/ProviderIcon.tsx`** - Provider icon component
- **`frontend/src/components/common/ErrorBoundary.tsx`** - Error boundary
- **`frontend/src/components/common/ErrorDisplay.tsx`** - Error display component
- **`frontend/src/components/common/ErrorToast.tsx`** - Error toast component

### Color Constants & Theme Variables
- **`frontend/src/constants/index.ts`** - Contains `NODE_CATEGORY_COLORS`
- **`frontend/src/styles/theme.ts`** - Complete theme configuration:
  - Canvas colors
  - Category colors (input, processing, embedding, storage, retrieval, llm)
  - Text colors
  - Glassmorphism effects
  - Shadows & glows

### Typography Settings
- Defined in **`frontend/src/index.css`**:
  - Font family: `Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
  - Base text color: `#f8fafc`
  - Text hierarchy defined in `theme.ts` (primary, secondary, tertiary, muted)

---

## Additional Canvas-Related Files

### Mobile Canvas Components
- **`frontend/src/components/Canvas/MobileToolbar.tsx`** - Mobile toolbar
- **`frontend/src/components/Canvas/MobileNodeEditor.tsx`** - Mobile node editor
- **`frontend/src/components/Canvas/MobileConnectionMode.tsx`** - Mobile connection mode
- **`frontend/src/components/Canvas/NodePalettePopup.tsx`** - Mobile node palette popup
- **`frontend/src/components/Canvas/AddNodeButton.tsx`** - Floating add node button

### Execution-Related Components (Canvas Integration)
- **`frontend/src/components/Execution/ExecutionControls.tsx`** - Run/Stop/Clear buttons (shown in canvas)
- **`frontend/src/components/Execution/ExecutionStatusBar.tsx`** - Execution status bar (fixed at bottom)

---

## Key Styling Patterns

### Glassmorphism Classes
- `.glass` - Standard glass effect
- `.glass-light` - Lighter glass effect
- `.glass-strong` - Stronger glass effect
- `.node-glass` - Node-specific glass style

### Canvas Classes
- `.canvas-dark` - Dark canvas with animated grid background

### Node Animation Classes
- `.node-active` - Currently active node
- `.node-running` - Running node animation
- `.node-pending` - Pending node animation
- `.node-completed` - Completed node animation
- `.node-failed` - Failed node animation
- `.node-border-pulse` - Border pulse animation

### Category Glow Classes
- `.glow-input` - Input node glow
- `.glow-processing` - Processing node glow
- `.glow-embedding` - Embedding node glow
- `.glow-storage` - Storage node glow
- `.glow-retrieval` - Retrieval node glow
- `.glow-llm` - LLM node glow

---

## File Organization Summary

```
frontend/src/
├── index.css                    # Main stylesheet (canvas, glassmorphism, animations)
├── styles/
│   ├── mobile-canvas.css        # Mobile canvas optimizations
│   └── theme.ts                 # Theme tokens & design system
├── constants/
│   └── index.ts                 # Node category colors & icons
├── components/
│   ├── Canvas/
│   │   ├── WorkflowCanvas.tsx   # Main React Flow canvas
│   │   ├── CustomNode.tsx        # Node component
│   │   ├── CustomEdge.tsx        # Edge component
│   │   └── [other canvas components]
│   ├── Layout/
│   │   └── MainLayout.tsx        # Main app layout
│   ├── Sidebar/
│   │   └── [sidebar components]
│   ├── Execution/
│   │   └── [execution components]
│   └── common/
│       └── [shared UI components]
└── tailwind.config.js            # Tailwind configuration
```

