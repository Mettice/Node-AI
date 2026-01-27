# 🚀 Quick Start Guide

## Step 1: Install Dependencies

```bash
cd remotion-videos
npm install
```

This will install:
- Remotion (video framework)
- React & TypeScript
- All necessary dependencies

## Step 2: Preview Videos (Optional)

Open Remotion Studio to preview and test:

```bash
npm run dev
```

This opens `http://localhost:3000` where you can:
- Preview all 4 videos
- Test animations
- Adjust timing
- See real-time changes

## Step 3: Render Videos

### Render All Videos at Once:
```bash
npm run render:all
```

### Or Render Individually:
```bash
npm run render:hero          # Hero workflow (15s)
npm run render:rag           # RAG pipeline (12s)
npm run render:observability # Dashboard (10s)
npm run render:library       # Node library (8s)
```

## Step 4: Find Your Videos

Rendered videos will be in:
```
remotion-videos/output/
├── HeroWorkflow.mp4
├── RAGPipeline.mp4
├── Observability.mp4
└── NodeLibrary.mp4
```

## Step 5: Use in Landing Page

1. Copy videos to your public folder (or wherever you host static assets)
2. Update `nodeai-landing-animated.html` using the guide in `landing_page_video_replacements.md`

---

**That's it!** You now have all 4 videos ready for your landing page. 🎬
