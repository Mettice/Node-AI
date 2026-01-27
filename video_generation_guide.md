# Video Generation Guide for NodeAI Landing Page

## Overview
This guide explains how to use Remotion + Claude to generate videos for the landing page placeholders.

---

## 🎬 Video Placeholders Identified

### 1. **Hero Section Video** (Line 1561-1565)
- **Location**: Main hero section, above the fold
- **Current Placeholder**: "Your App Screenshot Here - Use the Research Crew execution screenshot"
- **Dimensions**: 16:10 aspect ratio (1100px max width)
- **What it should show**: 
  - NodeAI canvas with a workflow being built
  - Nodes connecting in real-time
  - Execution animation (nodes lighting up as they run)
  - Data flowing through edges
  - Cost/token tracking appearing

### 2. **RAG Pipeline Feature Video** (Line 1751-1754)
- **Location**: Features section - "Build RAG Pipelines in Minutes"
- **Current Placeholder**: "File → Chunk → Embed → Vector Store → Search → Chat"
- **Dimensions**: 4:3 aspect ratio
- **What it should show**:
  - File upload animation
  - Document being chunked (text splitting)
  - Embedding process (vectors being created)
  - Vector store filling up
  - Search query → retrieval → chat response
  - Visual data flow with arrows

### 3. **Observability Feature Video** (Line 1775-1778)
- **Location**: Features section - "See Every Token, Every Cost"
- **Current Placeholder**: "Execution Results Panel - Costs, tokens, timeline, traces"
- **Dimensions**: 4:3 aspect ratio
- **What it should show**:
  - Execution panel opening
  - Real-time cost counter ($0.0012 → $0.0024 → $0.0036)
  - Token usage bars filling up
  - Timeline with nodes executing
  - Trace logs scrolling
  - Node-by-node breakdown

### 4. **Node Library Feature Video** (Line 1799-1802)
- **Location**: Features section - "Everything You Need, Pre-Built"
- **Current Placeholder**: "Node Library Grid - Icons for each category"
- **Dimensions**: 4:3 aspect ratio
- **What it should show**:
  - Node palette opening
  - Categories expanding (LLM, Agent, Storage, etc.)
  - Icons animating in
  - Hover effects on nodes
  - Drag-and-drop preview

---

## 🛠️ Remotion Setup Instructions

### Step 1: Install Remotion

```bash
npm init video
# Choose: TypeScript, 1920x1080, 30fps
```

### Step 2: Project Structure

```
remotion-videos/
├── src/
│   ├── Root.tsx          # Main Remotion root
│   ├── Compositions/
│   │   ├── HeroVideo.tsx
│   │   ├── RAGPipeline.tsx
│   │   ├── Observability.tsx
│   │   └── NodeLibrary.tsx
│   └── components/       # Reusable components
├── render.bat            # Render script
└── package.json
```

### Step 3: Create Render Script (`render.bat`)

```batch
@echo off
echo Rendering Remotion video...
npx remotion render %1 --codec=h264 --crf=18 --pixel-format=yuv420p --output=output/%1.mp4
echo Done! Video saved to output/%1.mp4
```

---

## 📝 Claude Prompt Template

Use this prompt structure for each video:

```
Create a Remotion TSX composition for NodeAI landing page video.

REQUIREMENTS:
- Duration: [X] seconds
- Dimensions: [1920x1080] or [1280x720]
- FPS: 30
- Style: Dark theme (#030712 background), amber/pink/cyan accents
- Brand colors: #f0b429 (amber), #f472b6 (pink), #22d3ee (cyan)

COMPOSITION DETAILS:
[Describe what should happen in the video]

VISUAL ELEMENTS:
- [List specific UI elements to show]
- [Animation style]
- [Text overlays if needed]

OUTPUT FORMAT:
Export a complete TSX file that can be rendered directly with Remotion.
The file should:
1. Import from 'remotion'
2. Define a composition with id, durationInFrames, fps, width, height
3. Export a default component that renders the video
4. Use Remotion hooks (useCurrentFrame, interpolate, etc.) for animations
```

---

## 🎨 Video Specifications

### Video 1: Hero Workflow Demo
**Prompt for Claude:**
```
Create a 15-second Remotion video showing NodeAI workflow execution.

SCENE BREAKDOWN:
0-3s: Canvas appears, nodes fade in (File Loader, Chunk, Embed, Vector Store, Chat)
3-6s: Connections animate between nodes (lines drawing)
6-9s: Execution starts - nodes pulse amber when active
9-12s: Data packets flow along edges (small dots moving)
12-15s: Results appear in chat node, cost counter shows $0.0003

VISUAL STYLE:
- Dark background (#030712)
- Nodes: Rounded rectangles with gradient borders (amber/pink)
- Edges: Animated lines with flowing particles
- Active nodes: Glow effect (amber, 0.3 opacity)
- Typography: Inter font, white text

TECHNICAL:
- 1920x1080, 30fps, 15 seconds (450 frames)
- Smooth easing animations
- Export as HeroWorkflow.tsx
```

### Video 2: RAG Pipeline Flow
**Prompt for Claude:**
```
Create a 12-second Remotion video showing RAG pipeline execution.

SCENE BREAKDOWN:
0-2s: File icon drops in, document preview appears
2-4s: Document splits into chunks (rectangles breaking apart)
4-6s: Chunks transform into vector embeddings (geometric shapes)
6-8s: Vectors flow into vector store (database icon filling)
8-10s: Search query appears, vectors light up (similarity matching)
10-12s: Retrieved chunks flow to chat, response generates

VISUAL STYLE:
- Step-by-step process with labels
- Color coding: File (cyan), Chunk (purple), Embed (pink), Store (emerald), Chat (amber)
- Arrows showing data flow
- Progress indicators

TECHNICAL:
- 1280x960 (4:3), 30fps, 12 seconds (360 frames)
- Export as RAGPipeline.tsx
```

### Video 3: Observability Dashboard
**Prompt for Claude:**
```
Create a 10-second Remotion video showing execution observability.

SCENE BREAKDOWN:
0-2s: Execution panel slides in from right
2-4s: Cost counter animates: $0.0000 → $0.0012 → $0.0024 → $0.0036
4-6s: Token bars fill up (Input: 1500, Output: 800 tokens)
6-8s: Timeline shows nodes executing (colored bars)
8-10s: Trace logs scroll, showing node details

VISUAL STYLE:
- Dashboard UI with cards
- Real-time updating numbers
- Progress bars with gradients
- Code-like trace logs
- Amber accents for active elements

TECHNICAL:
- 1280x960 (4:3), 30fps, 10 seconds (300 frames)
- Export as Observability.tsx
```

### Video 4: Node Library Showcase
**Prompt for Claude:**
```
Create a 8-second Remotion video showing node library.

SCENE BREAKDOWN:
0-2s: Node palette opens, categories expand
2-4s: Icons animate in by category (LLM, Agent, Storage, etc.)
4-6s: Hover effect on nodes (scale + glow)
6-8s: Drag preview shows node being dragged out

VISUAL STYLE:
- Grid layout with node cards
- Category headers (LLM, Agent, Storage, etc.)
- Icon animations (fade + scale)
- Hover states with amber glow
- Smooth transitions

TECHNICAL:
- 1280x960 (4:3), 30fps, 8 seconds (240 frames)
- Export as NodeLibrary.tsx
```

---

## 🚀 Implementation Steps

### For Each Video:

1. **Generate TSX with Claude**
   - Use the prompt template above
   - Claude will output a complete TSX file
   - Save as `src/Compositions/[VideoName].tsx`

2. **Register in Root.tsx**
   ```tsx
   import { HeroWorkflow } from './Compositions/HeroWorkflow';
   
   export const RemotionRoot: React.FC = () => {
     return (
       <>
         <Composition
           id="HeroWorkflow"
           component={HeroWorkflow}
           durationInFrames={450}
           fps={30}
           width={1920}
           height={1080}
         />
         {/* Add other compositions */}
       </>
     );
   };
   ```

3. **Render Video**
   ```bash
   npx remotion render HeroWorkflow --codec=h264 --crf=18 --output=output/hero-workflow.mp4
   ```

4. **Optimize for Web**
   ```bash
   # Convert to web-optimized format
   ffmpeg -i output/hero-workflow.mp4 -c:v libx264 -preset slow -crf 22 -c:a aac -b:a 128k -movflags +faststart output/hero-workflow-optimized.mp4
   ```

5. **Add to Landing Page**
   ```html
   <!-- Replace placeholder -->
   <video 
     autoplay 
     loop 
     muted 
     playsinline
     class="hero-visual-video"
   >
     <source src="/videos/hero-workflow-optimized.mp4" type="video/mp4">
   </video>
   ```

---

## 🎯 Quick Start Checklist

- [ ] Install Remotion: `npm init video`
- [ ] Create `render.bat` script
- [ ] Generate Video 1 (Hero) with Claude
- [ ] Generate Video 2 (RAG Pipeline) with Claude
- [ ] Generate Video 3 (Observability) with Claude
- [ ] Generate Video 4 (Node Library) with Claude
- [ ] Register all compositions in Root.tsx
- [ ] Render all videos
- [ ] Optimize videos for web
- [ ] Replace placeholders in landing page
- [ ] Test on different devices

---

## 💡 Pro Tips

1. **Start with Hero Video** - Most important, sets first impression
2. **Keep videos short** - 8-15 seconds max (attention span)
3. **Loop seamlessly** - End frame should match start frame
4. **Optimize file size** - Use CRF 22-28 for web (balance quality/size)
5. **Test on mobile** - Videos should work on all devices
6. **Add fallback** - Show static image if video fails to load

---

## 📦 File Structure After Setup

```
Nodeflow/
├── remotion-videos/          # New folder
│   ├── src/
│   │   ├── Root.tsx
│   │   └── Compositions/
│   │       ├── HeroWorkflow.tsx
│   │       ├── RAGPipeline.tsx
│   │       ├── Observability.tsx
│   │       └── NodeLibrary.tsx
│   ├── render.bat
│   └── package.json
├── public/
│   └── videos/              # Rendered videos go here
│       ├── hero-workflow.mp4
│       ├── rag-pipeline.mp4
│       ├── observability.mp4
│       └── node-library.mp4
└── nodeai-landing-animated.html  # Update placeholders
```

---

## 🎬 Next Steps

1. **Copy this guide to Claude**
2. **Start with Hero Video** - Use the prompt template
3. **Generate TSX file** - Claude will create it
4. **Test in Remotion** - Preview before rendering
5. **Render and optimize** - Create final MP4 files
6. **Update landing page** - Replace placeholders

Ready to generate your first video? Start with the Hero video prompt above! 🚀
