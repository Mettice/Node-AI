# NodeAI Remotion Videos

This directory contains Remotion compositions for generating landing page videos.

## 📁 Project Structure

```
remotion-videos/
├── src/
│   ├── index.tsx              # Entry point
│   ├── Root.tsx               # Registers all compositions
│   └── Compositions/
│       ├── HeroWorkflow.tsx   # Hero section video (15s, 1920x1080)
│       ├── RAGPipeline.tsx    # RAG pipeline demo (12s, 1280x960)
│       ├── Observability.tsx  # Dashboard observability (10s, 1280x960)
│       └── NodeLibrary.tsx     # Node library showcase (8s, 1280x960)
├── output/                    # Rendered videos go here
├── package.json
├── tsconfig.json
└── remotion.config.ts
```

## 🚀 Setup

1. **Install dependencies:**
   ```bash
   cd remotion-videos
   npm install
   ```

2. **Start Remotion Studio (for preview):**
   ```bash
   npm run dev
   ```
   This opens a browser at `http://localhost:3000` where you can preview and test all compositions.

## 🎬 Rendering Videos

### Option 1: Using npm scripts (Recommended)

```bash
# Render individual videos
npm run render:hero
npm run render:rag
npm run render:observability
npm run render:library

# Render all videos at once
npm run render:all
```

### Option 2: Using PowerShell script

```powershell
.\render.ps1 HeroWorkflow
.\render.ps1 RAGPipeline
.\render.ps1 Observability
.\render.ps1 NodeLibrary
```

### Option 3: Using batch script (Windows)

```cmd
render.bat HeroWorkflow
render.bat RAGPipeline
render.bat Observability
render.bat NodeLibrary
```

### Option 4: Direct Remotion CLI

```bash
npx remotion render HeroWorkflow --codec=h264 --crf=18 --pixel-format=yuv420p --output=output/hero-workflow.mp4
```

## 📊 Video Specifications

| Video | Duration | Dimensions | FPS | File Size (est.) |
|-------|----------|------------|-----|------------------|
| HeroWorkflow | 15s | 1920x1080 | 30 | ~2-3MB |
| RAGPipeline | 12s | 1280x960 | 30 | ~1.5-2MB |
| Observability | 10s | 1280x960 | 30 | ~1-1.5MB |
| NodeLibrary | 8s | 1280x960 | 30 | ~1MB |

## 🎨 Brand Colors

All videos use NodeAI brand colors:
- **Amber**: `#f0b429`
- **Pink**: `#f472b6`
- **Cyan**: `#22d3ee`
- **Purple**: `#a78bfa`
- **Emerald**: `#34d399`
- **Dark**: `#030712`

## 🔧 Customization

### Adjust Quality/File Size

Edit the render commands to change `--crf` value:
- **Lower CRF (18-20)**: Higher quality, larger files
- **Higher CRF (24-28)**: Lower quality, smaller files (better for web)

Example:
```bash
npx remotion render HeroWorkflow --codec=h264 --crf=24 --pixel-format=yuv420p --output=output/hero-workflow.mp4
```

### Change Duration

Edit the `durationInFrames` in `src/Root.tsx`:
```tsx
<Composition
  id="HeroWorkflow"
  component={HeroWorkflow}
  durationInFrames={600}  // 20 seconds at 30fps
  fps={30}
  width={1920}
  height={1080}
/>
```

## 📦 Output Files

After rendering, videos will be in the `output/` directory:
- `output/HeroWorkflow.mp4`
- `output/RAGPipeline.mp4`
- `output/Observability.mp4`
- `output/NodeLibrary.mp4`

## 🚀 Next Steps

1. **Render all videos** using `npm run render:all`
2. **Optimize for web** (optional, see below)
3. **Copy to landing page** - Move videos to your public folder
4. **Update HTML** - Replace placeholders in `nodeai-landing-animated.html`

### Web Optimization (Optional)

For smaller file sizes, use FFmpeg:

```bash
# Optimize video (smaller file, faster loading)
ffmpeg -i output/hero-workflow.mp4 -c:v libx264 -preset slow -crf 24 -c:a aac -b:a 128k -movflags +faststart output/hero-workflow-optimized.mp4

# Create fallback image (first frame)
ffmpeg -i output/hero-workflow.mp4 -ss 00:00:01 -vframes 1 output/hero-workflow-fallback.jpg
```

## 🐛 Troubleshooting

### "Command not found: remotion"
- Make sure you've run `npm install` in the `remotion-videos` directory

### Videos not rendering
- Check that Remotion Studio works: `npm run dev`
- Verify all dependencies are installed: `npm install`

### TypeScript errors
- Run `npm install` to ensure all types are installed
- Check `tsconfig.json` is correct

## 📚 Resources

- [Remotion Documentation](https://www.remotion.dev/docs)
- [Remotion Examples](https://github.com/remotion-dev/remotion/tree/main/packages/example)
- [Video Generation Guide](../video_generation_guide.md)
- [Landing Page Replacements](../landing_page_video_replacements.md)

---

**Ready to create amazing videos! 🎬**
