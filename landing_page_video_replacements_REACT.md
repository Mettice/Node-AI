# Landing Page Video Integration Guide (React Components)

## 📍 Video Placement Locations

### 1. Hero Section Video
**File:** `frontend/src/components/landing/Hero.tsx`  
**Lines:** 107-111

**Current Code:**
```tsx
<div className="relative aspect-video bg-gradient-to-br from-slate-900 to-slate-950 flex flex-col items-center justify-center gap-4 p-8">
    <span className="text-5xl mb-4">🎬</span>
    <span className="text-slate-300 text-lg">App Screenshot Here</span>
    <span className="text-slate-500 text-sm">App Screenshot Here</span>
</div>
```

**Replace With:**
```tsx
<video
    autoPlay
    loop
    muted
    playsInline
    className="w-full h-full object-cover rounded-3xl"
    style={{ aspectRatio: '16/9' }}
>
    <source src="/videos/hero-workflow.mp4" type="video/mp4" />
    {/* Fallback image */}
    <img 
        src="/images/hero-workflow-fallback.jpg" 
        alt="NodeAI Workflow Demo" 
        className="w-full h-full object-cover"
    />
</video>
```

**Video:** `HeroWorkflow.mp4` (15s, 1920x1080)

---

### 2. Features Section Videos
**File:** `frontend/src/components/landing/FeaturesSection.tsx`  
**Line:** 112 (inside the feature loop)

**Current Code:**
```tsx
<div className="text-center p-10 text-slate-500 text-sm relative z-10">
    [Feature Visual Placeholder]
</div>
```

**Replace With:**
```tsx
{/* Video based on feature index */}
{index === 0 && (
    <video
        autoPlay
        loop
        muted
        playsInline
        className="w-full h-full object-cover rounded-3xl"
    >
        <source src="/videos/cost-intelligence.mp4" type="video/mp4" />
        <img src="/images/cost-intelligence-fallback.jpg" alt="Cost Intelligence" className="w-full h-full object-cover" />
    </video>
)}
{index === 1 && (
    <video
        autoPlay
        loop
        muted
        playsInline
        className="w-full h-full object-cover rounded-3xl"
    >
        <source src="/videos/rag-pipeline.mp4" type="video/mp4" />
        <img src="/images/rag-pipeline-fallback.jpg" alt="RAG Pipeline" className="w-full h-full object-cover" />
    </video>
)}
{index === 2 && (
    <video
        autoPlay
        loop
        muted
        playsInline
        className="w-full h-full object-cover rounded-3xl"
    >
        <source src="/videos/multi-agent.mp4" type="video/mp4" />
        <img src="/images/multi-agent-fallback.jpg" alt="Multi-Agent Systems" className="w-full h-full object-cover" />
    </video>
)}
{index === 3 && (
    <video
        autoPlay
        loop
        muted
        playsInline
        className="w-full h-full object-cover rounded-3xl"
    >
        <source src="/videos/observability.mp4" type="video/mp4" />
        <img src="/images/observability-fallback.jpg" alt="Observability" className="w-full h-full object-cover" />
    </video>
)}
```

**Videos:**
- Feature 0 (Cost Intelligence): Use `Observability.mp4` or create a cost-focused video
- Feature 1 (Production RAG): `RAGPipeline.mp4` (12s, 1280x960)
- Feature 2 (Multi-Agent Systems): Create a multi-agent video or use `HeroWorkflow.mp4`
- Feature 3 (Enterprise Observability): `Observability.mp4` (10s, 1280x960)

---

## 🎬 Video Mapping

| Component | Feature | Video File | Duration | Dimensions |
|-----------|---------|------------|----------|------------|
| Hero | Hero Section | `hero-workflow.mp4` | 15s | 1920x1080 |
| FeaturesSection | Production RAG | `rag-pipeline.mp4` | 12s | 1280x960 |
| FeaturesSection | Enterprise Observability | `observability.mp4` | 10s | 1280x960 |
| FeaturesSection | Multi-Agent Systems | `hero-workflow.mp4` or new | 15s | 1920x1080 |
| FeaturesSection | Cost Intelligence | `observability.mp4` or new | 10s | 1280x960 |

---

## 📁 File Structure

After rendering videos, organize like this:

```
frontend/
├── public/
│   └── videos/
│       ├── hero-workflow.mp4          (15s, ~2-3MB)
│       ├── rag-pipeline.mp4           (12s, ~1.5-2MB)
│       ├── observability.mp4           (10s, ~1-1.5MB)
│       └── multi-agent.mp4            (15s, ~2-3MB) [optional]
│   └── images/
│       ├── hero-workflow-fallback.jpg
│       ├── rag-pipeline-fallback.jpg
│       ├── observability-fallback.jpg
│       └── multi-agent-fallback.jpg
└── src/
    └── components/
        └── landing/
            ├── Hero.tsx
            └── FeaturesSection.tsx
```

---

## 🔧 Implementation Steps

### Step 1: Render Videos
```bash
cd remotion-videos
npm install
npm run render:hero
npm run render:rag
npm run render:observability
```

### Step 2: Copy Videos to Public Folder
```bash
# Copy rendered videos to frontend/public/videos/
cp remotion-videos/output/HeroWorkflow.mp4 frontend/public/videos/hero-workflow.mp4
cp remotion-videos/output/RAGPipeline.mp4 frontend/public/videos/rag-pipeline.mp4
cp remotion-videos/output/Observability.mp4 frontend/public/videos/observability.mp4
```

### Step 3: Create Fallback Images
```bash
# Extract first frame as fallback image
ffmpeg -i frontend/public/videos/hero-workflow.mp4 -ss 00:00:01 -vframes 1 frontend/public/images/hero-workflow-fallback.jpg
ffmpeg -i frontend/public/videos/rag-pipeline.mp4 -ss 00:00:01 -vframes 1 frontend/public/images/rag-pipeline-fallback.jpg
ffmpeg -i frontend/public/videos/observability.mp4 -ss 00:00:01 -vframes 1 frontend/public/images/observability-fallback.jpg
```

### Step 4: Update React Components
- Replace placeholder in `Hero.tsx` (line 107-111)
- Replace placeholder in `FeaturesSection.tsx` (line 112)

### Step 5: Test
```bash
cd frontend
npm run dev
```

---

## 💡 Alternative: Conditional Video Component

Create a reusable video component:

**File:** `frontend/src/components/landing/FeatureVideo.tsx`
```tsx
interface FeatureVideoProps {
  videoSrc: string;
  fallbackSrc: string;
  alt: string;
}

export function FeatureVideo({ videoSrc, fallbackSrc, alt }: FeatureVideoProps) {
  return (
    <video
      autoPlay
      loop
      muted
      playsInline
      className="w-full h-full object-cover rounded-3xl"
    >
      <source src={videoSrc} type="video/mp4" />
      <img src={fallbackSrc} alt={alt} className="w-full h-full object-cover" />
    </video>
  );
}
```

Then in `FeaturesSection.tsx`:
```tsx
import { FeatureVideo } from './FeatureVideo';

// Inside the feature loop:
const videoMap = [
  { video: '/videos/observability.mp4', fallback: '/images/observability-fallback.jpg', alt: 'Cost Intelligence' },
  { video: '/videos/rag-pipeline.mp4', fallback: '/images/rag-pipeline-fallback.jpg', alt: 'RAG Pipeline' },
  { video: '/videos/hero-workflow.mp4', fallback: '/images/hero-workflow-fallback.jpg', alt: 'Multi-Agent Systems' },
  { video: '/videos/observability.mp4', fallback: '/images/observability-fallback.jpg', alt: 'Observability' },
];

// Replace placeholder with:
<FeatureVideo 
  videoSrc={videoMap[index].video}
  fallbackSrc={videoMap[index].fallback}
  alt={videoMap[index].alt}
/>
```

---

## ✅ Checklist

- [ ] Render all videos using Remotion
- [ ] Copy videos to `frontend/public/videos/`
- [ ] Create fallback images
- [ ] Update `Hero.tsx` with video
- [ ] Update `FeaturesSection.tsx` with videos
- [ ] Test on desktop (Chrome, Firefox, Safari)
- [ ] Test on mobile (iOS, Android)
- [ ] Verify autoplay works (muted, playsInline)
- [ ] Check file sizes (should be <3MB each)
- [ ] Verify fallback images load if video fails

---

**Ready to integrate videos into your React landing page! 🎬**
