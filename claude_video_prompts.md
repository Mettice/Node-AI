# Claude Video Generation Prompts - Copy & Paste Ready

## 🎬 Video 1: Hero Workflow Demo (15 seconds)

Copy this entire prompt to Claude:

```
Create a Remotion TSX composition for NodeAI landing page hero video.

REQUIREMENTS:
- Duration: 15 seconds (450 frames at 30fps)
- Dimensions: 1920x1080
- FPS: 30
- Style: Dark theme (#030712 background), amber/pink/cyan accents
- Brand colors: #f0b429 (amber), #f472b6 (pink), #22d3ee (cyan), #a78bfa (purple)

COMPOSITION DETAILS:
Create a 15-second video showing NodeAI workflow canvas with nodes executing.

SCENE BREAKDOWN:
0-3s: Canvas fades in, 5 nodes appear one by one:
  - File Loader (cyan, left)
  - Chunk (purple, center-left)
  - Embed (pink, center)
  - Vector Store (emerald, center-right)
  - Chat (amber, right)

3-6s: Connection lines animate between nodes (drawing from left to right)
  - Lines have animated particles flowing along them
  - Use gradient colors matching node colors

6-9s: Execution starts - nodes pulse amber when active:
  - File Loader activates (glow effect)
  - Then Chunk activates
  - Then Embed activates
  - Then Vector Store activates
  - Then Chat activates

9-12s: Data packets (small glowing dots) flow along edges:
  - Dots move from node to node
  - Leave a trail effect
  - Match node colors

12-15s: Results appear in Chat node:
  - Text response fades in
  - Cost counter appears: "$0.0003"
  - Token counter: "1,500 tokens"
  - Success checkmark appears

VISUAL STYLE:
- Dark background: #030712
- Nodes: Rounded rectangles (border-radius: 12px)
  - Background: rgba(13, 17, 23, 0.9)
  - Border: 2px gradient (amber to pink)
  - Padding: 16px
  - Glow on active: box-shadow with amber color
- Edges: Smooth bezier curves
  - Stroke: 2px, gradient colors
  - Animated particles: 4px circles
- Typography: Inter font, white text, 14px
- Smooth easing: cubic-bezier(0.16, 1, 0.3, 1)

TECHNICAL:
- Export as HeroWorkflow.tsx
- Use Remotion hooks: useCurrentFrame, interpolate, useVideoConfig
- Animate with spring() for natural motion
- Use <AbsoluteFill> for positioning

OUTPUT FORMAT:
Export a complete TSX file that:
1. Imports from 'remotion'
2. Defines composition with id="HeroWorkflow"
3. Exports default component
4. Can be rendered directly with: npx remotion render HeroWorkflow
```

---

## 🎬 Video 2: RAG Pipeline Flow (12 seconds)

Copy this entire prompt to Claude:

```
Create a Remotion TSX composition for NodeAI RAG pipeline demonstration.

REQUIREMENTS:
- Duration: 12 seconds (360 frames at 30fps)
- Dimensions: 1280x960 (4:3 aspect ratio)
- FPS: 30
- Style: Dark theme (#030712), step-by-step process visualization

COMPOSITION DETAILS:
Show a RAG pipeline executing step by step with visual data flow.

SCENE BREAKDOWN:
0-2s: File upload animation
  - Document icon drops in from top
  - PDF preview appears (simplified rectangle with text lines)
  - Label: "Document.pdf" appears below

2-4s: Document chunking
  - Document splits into 4 chunks (rectangles breaking apart)
  - Chunks float to center
  - Label: "Chunking" appears
  - Each chunk shows "Chunk 1", "Chunk 2", etc.

4-6s: Embedding process
  - Chunks transform into vector embeddings
  - Show geometric shapes (dots in 3D space)
  - Label: "Embedding" appears
  - Vectors glow with pink color

6-8s: Vector store
  - Vectors flow into database icon
  - Database fills up (progress bar)
  - Label: "Vector Store" appears
  - Show "1,234 vectors stored"

8-10s: Search query
  - Search icon appears
  - Query text: "What is NodeAI?"
  - Similar vectors light up (similarity matching)
  - Top 3 results highlighted

10-12s: Chat response
  - Retrieved chunks flow to chat bubble
  - Response text appears: "NodeAI is a visual platform..."
  - Label: "Response" appears
  - Success indicator

VISUAL STYLE:
- Step labels: Top of screen, amber color
- Color coding:
  - File: #22d3ee (cyan)
  - Chunk: #a78bfa (purple)
  - Embed: #f472b6 (pink)
  - Store: #34d399 (emerald)
  - Chat: #f0b429 (amber)
- Arrows: Animated, showing data flow
- Progress indicators: Filling bars
- Smooth transitions between steps

TECHNICAL:
- Export as RAGPipeline.tsx
- Use sequence() for step-by-step animation
- Each step should be clearly separated
- Use <AbsoluteFill> for full-screen layout

OUTPUT FORMAT:
Complete TSX file ready to render with Remotion.
```

---

## 🎬 Video 3: Observability Dashboard (10 seconds)

Copy this entire prompt to Claude:

```
Create a Remotion TSX composition for NodeAI observability dashboard.

REQUIREMENTS:
- Duration: 10 seconds (300 frames at 30fps)
- Dimensions: 1280x960 (4:3 aspect ratio)
- FPS: 30
- Style: Dashboard UI, dark theme, real-time updates

COMPOSITION DETAILS:
Show execution observability panel with live metrics updating.

SCENE BREAKDOWN:
0-2s: Panel slides in from right
  - Dashboard card appears
  - Title: "Execution #abc123" fades in
  - Status badge: "Running" (amber, pulsing)

2-4s: Cost counter animates
  - Label: "Total Cost"
  - Counter: $0.0000 → $0.0012 → $0.0024 → $0.0036
  - Number format: 4 decimal places
  - Amber color, large font (32px)

4-6s: Token usage bars
  - "Input Tokens" bar fills: 0 → 1,500
  - "Output Tokens" bar fills: 0 → 800
  - Bars have gradient (cyan to amber)
  - Numbers update in real-time

6-8s: Execution timeline
  - Horizontal timeline appears
  - Colored bars show node execution:
    - File Loader: 0-1s (cyan)
    - Chunk: 1-2s (purple)
    - Embed: 2-3s (pink)
    - Chat: 3-4s (amber)
  - Current time indicator moves

8-10s: Trace logs scroll
  - Code-like panel appears
  - Logs scroll up showing:
    "Node: file_loader | Status: completed | Cost: $0.0001"
    "Node: chunk | Status: completed | Cost: $0.0000"
    "Node: embed | Status: completed | Cost: $0.0001"
    "Node: chat | Status: running | Cost: $0.0002"
  - Monospace font, green text on dark background

VISUAL STYLE:
- Dashboard cards: Rounded corners, subtle borders
- Metrics: Large numbers, amber accents
- Progress bars: Gradient fills, smooth animation
- Timeline: Horizontal, color-coded
- Logs: Terminal-style, monospace font
- All elements: Smooth fade-in animations

TECHNICAL:
- Export as Observability.tsx
- Use interpolate() for number animations
- Use sequence() for sequential updates
- Realistic timing (numbers update smoothly)

OUTPUT FORMAT:
Complete TSX file ready to render.
```

---

## 🎬 Video 4: Node Library Showcase (8 seconds)

Copy this entire prompt to Claude:

```
Create a Remotion TSX composition for NodeAI node library showcase.

REQUIREMENTS:
- Duration: 8 seconds (240 frames at 30fps)
- Dimensions: 1280x960 (4:3 aspect ratio)
- FPS: 30
- Style: Grid layout, category-based organization

COMPOSITION DETAILS:
Show node library palette opening and displaying available nodes.

SCENE BREAKDOWN:
0-2s: Node palette opens
  - Side panel slides in from left
  - Title: "Add Node" appears
  - Search bar fades in

2-4s: Categories expand
  - "LLM" category expands (shows: Chat, Completion, Embedding)
  - "Agent" category expands (shows: CrewAI, LangChain)
  - "Storage" category expands (shows: Vector Store, S3, PostgreSQL)
  - Each category has icon + name

4-6s: Node icons animate in
  - Icons appear one by one with scale animation
  - Each node card shows:
    - Icon (emoji or symbol)
    - Name (e.g., "Chat", "Vector Store")
    - Color-coded border
  - Grid layout: 3 columns

6-8s: Hover effect demonstration
  - One node (Chat) gets hover effect:
    - Scales up (1.05x)
    - Amber glow appears
    - Border brightens
  - Drag preview shows node being dragged out
  - Tooltip appears: "Chat with any LLM"

VISUAL STYLE:
- Node cards: 
  - Background: rgba(255, 255, 255, 0.02)
  - Border: 1px solid rgba(255, 255, 255, 0.1)
  - Border-radius: 12px
  - Padding: 16px
  - Hover: Amber glow, scale transform
- Categories:
  - Header: Bold, 14px
  - Collapsible with chevron icon
- Icons: 32px, centered
- Smooth animations: Fade + scale

TECHNICAL:
- Export as NodeLibrary.tsx
- Use stagger animations for icons
- Hover effect: Scale + glow
- Grid layout with flexbox

OUTPUT FORMAT:
Complete TSX file ready to render.
```

---

## 🚀 Quick Render Commands

After generating each TSX file, render with:

```bash
# Hero Video
npx remotion render HeroWorkflow --codec=h264 --crf=22 --output=output/hero-workflow.mp4

# RAG Pipeline
npx remotion render RAGPipeline --codec=h264 --crf=22 --output=output/rag-pipeline.mp4

# Observability
npx remotion render Observability --codec=h264 --crf=22 --output=output/observability.mp4

# Node Library
npx remotion render NodeLibrary --codec=h264 --crf=22 --output=output/node-library.mp4
```

---

## 📝 Notes

- All videos should loop seamlessly (end frame = start frame)
- Use consistent brand colors throughout
- Keep animations smooth and professional
- Test at different playback speeds
- Optimize file sizes for web (target: <2MB per video)
