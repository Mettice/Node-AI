# Frontend Design & Architecture

**Project:** NodeAI (NodeFlow)  
**Status:** 📋 Planning  
**Last Updated:** 2025-11-09

---

## 🎨 Visual Design Overview

### Layout Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│  NodeAI - Visual GenAI Workflow Builder                    [⚙️] [👤]   │
├──────────┬──────────────────────────────────────────────┬──────────────┤
│          │                                               │              │
│  Node    │                                               │  Properties  │
│  Palette │            Canvas (React Flow)                │  Panel       │
│          │                                               │              │
│  ┌────┐  │  ┌────────┐      ┌────────┐      ┌────────┐│  ┌────────┐ │
│  │ 📝 │  │  │ Text   │──────▶│ Chunk  │──────▶│ Embed  ││  │ Node   │ │
│  │Text│  │  │ Input  │      │        │      │        ││  │ Config │ │
│  └────┘  │  └────────┘      └────────┘      └────────┘│  └────────┘ │
│          │                                               │              │
│  ┌────┐  │  ┌────────┐      ┌────────┐      ┌────────┐│  Provider:  │
│  │ ✂️  │  │  │Vector │      │Vector  │      │ Chat   ││  [OpenAI ▼]│
│  │Chunk│  │  │ Store │      │Search  │      │        ││              │
│  └────┘  │  └────────┘      └────────┘      └────────┘│  Model:     │
│          │                                               │  [gpt-3.5 ▼]│
│  ┌────┐  │                                               │              │
│  │ 🧠 │  │                                               │  [Test Node]│
│  │Embed│  │                                               │              │
│  └────┘  │                                               │              │
│          │                                               │              │
│  ┌────┐  │                                               │              │
│  │ 💾 │  │                                               │              │
│  │Store│  │                                               │              │
│  └────┘  │                                               │              │
│          │                                               │              │
│  ┌────┐  │                                               │              │
│  │ 🔍 │  │                                               │              │
│  │Search│ │                                               │              │
│  └────┘  │                                               │              │
│          │                                               │              │
│  ┌────┐  │                                               │              │
│  │ 🤖 │  │                                               │              │
│  │ Chat │ │                                               │              │
│  └────┘  │                                               │              │
│          │                                               │              │
│  [Search]│                                               │              │
│          │                                               │              │
└──────────┴──────────────────────────────────────────────┴──────────────┘
│  Execution Panel (Bottom)                                                  │
│  [▶ Run] [⏹ Stop] [🔄 Clear]  Status: Ready  Cost: $0.00  Duration: 0s  │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ Execution Logs                                                     │ │
│  │ ✅ Node 1 (text_input) - completed (5ms)                          │ │
│  │ ✅ Node 2 (chunk) - completed (12ms)                               │ │
│  │ ⏳ Node 3 (embed) - running...                                     │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🎨 Color Scheme & Visual Identity

### Color Palette

```css
/* Primary Colors */
--primary: #3b82f6;        /* Blue - Primary actions */
--primary-dark: #2563eb;   /* Darker blue for hover */
--primary-light: #60a5fa; /* Lighter blue for accents */

/* Status Colors */
--success: #10b981;        /* Green - Success states */
--warning: #f59e0b;        /* Orange - Warnings */
--error: #ef4444;          /* Red - Errors */
--info: #3b82f6;           /* Blue - Info */

/* Background Colors */
--bg-primary: #ffffff;     /* White - Main background */
--bg-secondary: #f9fafb;   /* Light gray - Secondary areas */
--bg-tertiary: #f3f4f6;    /* Medium gray - Panels */
--bg-dark: #1f2937;        /* Dark - Sidebar */

/* Text Colors */
--text-primary: #111827;   /* Dark gray - Main text */
--text-secondary: #6b7280;  /* Medium gray - Secondary text */
--text-tertiary: #9ca3af;   /* Light gray - Tertiary text */
--text-inverse: #ffffff;    /* White - Text on dark */

/* Border Colors */
--border-light: #e5e7eb;   /* Light borders */
--border-medium: #d1d5db;  /* Medium borders */
--border-dark: #9ca3af;    /* Dark borders */

/* Node Category Colors */
--node-input: #8b5cf6;     /* Purple - Input nodes */
--node-processing: #f59e0b; /* Orange - Processing nodes */
--node-embedding: #06b6d4;  /* Cyan - Embedding nodes */
--node-storage: #10b981;    /* Green - Storage nodes */
--node-retrieval: #3b82f6;  /* Blue - Retrieval nodes */
--node-llm: #ec4899;        /* Pink - LLM nodes */
```

### Typography

- **Font Family:** Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
- **Headings:** 600-700 weight
- **Body:** 400 weight
- **Code:** 'Fira Code', 'Consolas', monospace

---

## 📦 Node Visual Design

### Node Structure

Each node on the canvas has:

```
┌─────────────────────────────────────┐
│  [Icon] Node Name          [Status] │  ← Header (category color)
├─────────────────────────────────────┤
│  Input Handles (left)               │
│                                     │
│  [Config Preview]                   │  ← Body (shows key config)
│  Provider: OpenAI                    │
│  Model: text-embedding-3-small      │
│                                     │
│  Output Handles (right)             │
└─────────────────────────────────────┘
```

### Node States

1. **Idle** (default)
   - Gray border
   - No animation
   - Opacity: 100%

2. **Running** (executing)
   - Blue border with pulse animation
   - Spinner icon
   - Opacity: 100%

3. **Success** (completed)
   - Green border
   - Checkmark icon
   - Opacity: 100%

4. **Error** (failed)
   - Red border
   - X icon
   - Opacity: 100%

5. **Selected** (user selected)
   - Blue border (thicker)
   - Blue shadow
   - Slightly elevated

### Node Icons by Category

- **Input:** 📝 (Text Input)
- **Processing:** ✂️ (Chunk)
- **Embedding:** 🧠 (Embed)
- **Storage:** 💾 (Vector Store)
- **Retrieval:** 🔍 (Vector Search)
- **LLM:** 🤖 (Chat)

### Connection Handles

- **Input Handle** (left side): Circle, accepts incoming connections
- **Output Handle** (right side): Circle, creates outgoing connections
- **Color:** Matches node category
- **Size:** 8px diameter
- **Hover:** Scale to 12px, show tooltip

---

## 🔗 Edge (Connection) Design

### Edge Styles

1. **Default** (not connected to execution)
   - Color: `#9ca3af` (gray)
   - Width: 2px
   - Style: Bezier curve

2. **Active** (data flowing)
   - Color: `#3b82f6` (blue)
   - Width: 3px
   - Animation: Pulsing flow effect
   - Arrow: Blue, animated

3. **Success** (data passed successfully)
   - Color: `#10b981` (green)
   - Width: 2px
   - Arrow: Green

4. **Error** (data flow failed)
   - Color: `#ef4444` (red)
   - Width: 2px
   - Arrow: Red, dashed

### Edge Labels (Optional)

- Show on hover
- Display data type or size
- Format: `{type} ({size})`

---

## 📱 Component Breakdown

### 1. Node Palette (Left Sidebar)

**Purpose:** Display all available nodes, organized by category

**Features:**
- Collapsible categories
- Search/filter nodes
- Drag nodes to canvas
- Show node descriptions on hover

**Categories:**
1. **Input** (Purple)
   - Text Input
   
2. **Processing** (Orange)
   - Chunk
   
3. **Embedding** (Cyan)
   - Embed (with provider dropdown)
   
4. **Storage** (Green)
   - Vector Store (with provider dropdown)
   
5. **Retrieval** (Blue)
   - Vector Search (with provider dropdown)
   
6. **LLM** (Pink)
   - Chat (with provider dropdown)

### 2. Canvas (Center)

**Purpose:** Visual workflow builder using React Flow

**Features:**
- Drag and drop nodes
- Connect nodes with edges
- Zoom/pan controls
- Grid background (optional)
- Minimap (optional)
- Node selection
- Multi-select (future)

### 3. Properties Panel (Right Sidebar)

**Purpose:** Configure selected node

**Features:**
- Dynamic form based on node schema
- Provider selection (for generic nodes)
- Provider-specific config fields
- Real-time validation
- Test node button
- Output preview

**Layout:**
```
┌─────────────────────────┐
│ Node: Embed             │
├─────────────────────────┤
│ Provider: [OpenAI ▼]    │
│                         │
│ Model: [text-embedding-3-small ▼]
│                         │
│ [Test Node]             │
│                         │
│ Output Preview:         │
│ ┌─────────────────────┐ │
│ │ embeddings: [...]  │ │
│ │ count: 4           │ │
│ └─────────────────────┘ │
└─────────────────────────┘
```

### 4. Execution Panel (Bottom)

**Purpose:** Control and monitor workflow execution

**Features:**
- Run/Stop/Clear buttons
- Real-time status updates
- Cost tracker
- Duration display
- Execution logs
- Node-by-node progress

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│ [▶ Run] [⏹ Stop] [🔄 Clear]                            │
│ Status: Ready | Cost: $0.00 | Duration: 0s             │
├─────────────────────────────────────────────────────────┤
│ Execution Logs                                          │
│ ✅ Node 1 (text_input) - completed (5ms)               │
│ ✅ Node 2 (chunk) - completed (12ms)                      │
│ ⏳ Node 3 (embed) - running...                          │
│ ❌ Node 4 (vector_store) - error: Connection failed     │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Visualization

### During Execution

1. **Node Highlighting**
   - Currently executing node: Blue border, pulsing
   - Completed nodes: Green border
   - Failed nodes: Red border
   - Pending nodes: Gray border

2. **Edge Animation**
   - Active edges: Blue, pulsing flow animation
   - Completed edges: Green, static
   - Failed edges: Red, dashed

3. **Progress Indicators**
   - Per-node: Small progress bar in node header
   - Overall: Progress bar in execution panel

---

## 📐 Responsive Design

### Breakpoints

- **Desktop:** ≥ 1024px (Full layout)
- **Tablet:** 768px - 1023px (Collapsible sidebars)
- **Mobile:** < 768px (Stacked layout, simplified)

### Mobile Adaptations

- Sidebars become drawers
- Canvas becomes full-width
- Properties panel becomes modal
- Execution panel becomes collapsible

---

## 🎯 User Experience Flow

### Building a Workflow

1. **Add Nodes**
   - Drag from palette → Drop on canvas
   - Or: Click node in palette → Click on canvas

2. **Connect Nodes**
   - Click output handle → Drag to input handle
   - Visual feedback on valid/invalid connections

3. **Configure Nodes**
   - Click node to select
   - Properties panel appears
   - Configure in form
   - Test node (optional)

4. **Execute Workflow**
   - Click "Run" button
   - Watch real-time execution
   - View results in logs
   - Check cost and duration

5. **Iterate**
   - Modify node configs
   - Add/remove nodes
   - Re-run workflow

---

## 🛠️ Technical Stack

### Core Libraries

- **React 18+** - UI framework
- **TypeScript** - Type safety
- **React Flow** - Canvas/graph visualization
- **Zustand** - State management
- **TanStack Query** - API/data fetching
- **Tailwind CSS** - Styling
- **Vite** - Build tool

### Additional Libraries

- **React Hook Form** - Form management
- **Zod** - Schema validation
- **Lucide React** - Icons
- **React Hot Toast** - Notifications
- **Monaco Editor** (optional) - Code editing

---

## 📋 Design Principles

1. **Clarity First**
   - Clear visual hierarchy
   - Obvious actions
   - Minimal cognitive load

2. **Feedback Always**
   - Loading states
   - Success/error messages
   - Progress indicators

3. **Consistency**
   - Same patterns throughout
   - Predictable interactions
   - Familiar UI patterns

4. **Performance**
   - Smooth animations (60fps)
   - Fast interactions
   - Optimized rendering

5. **Accessibility**
   - Keyboard navigation
   - Screen reader support
   - High contrast mode
   - Focus indicators

---

## 🎨 Design Tokens

### Spacing

```css
--spacing-xs: 0.25rem;   /* 4px */
--spacing-sm: 0.5rem;    /* 8px */
--spacing-md: 1rem;      /* 16px */
--spacing-lg: 1.5rem;    /* 24px */
--spacing-xl: 2rem;      /* 32px */
--spacing-2xl: 3rem;     /* 48px */
```

### Border Radius

```css
--radius-sm: 0.25rem;    /* 4px */
--radius-md: 0.5rem;     /* 8px */
--radius-lg: 0.75rem;    /* 12px */
--radius-xl: 1rem;       /* 16px */
--radius-full: 9999px;   /* Full circle */
```

### Shadows

```css
--shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
--shadow-md: 0 4px 6px rgba(0,0,0,0.1);
--shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
--shadow-xl: 0 20px 25px rgba(0,0,0,0.15);
```

### Transitions

```css
--transition-fast: 150ms ease;
--transition-base: 200ms ease;
--transition-slow: 300ms ease;
```

---

## 🔗 Related Documents

- [Frontend Phase 1: Setup & Foundation](./FRONTEND_PHASE_1_SETUP.md)
- [Frontend Phase 2: Canvas & Nodes](./FRONTEND_PHASE_2_CANVAS.md)
- [Frontend Phase 3: Properties & Configuration](./FRONTEND_PHASE_3_PROPERTIES.md)
- [Frontend Phase 4: Execution & Real-time](./FRONTEND_PHASE_4_EXECUTION.md)
- [Frontend Phase 5: Polish & Optimization](./FRONTEND_PHASE_5_POLISH.md)

---

## 📝 Notes

- Design is iterative - we'll refine as we build
- Keep it simple for MVP
- Focus on core functionality first
- Polish comes later

