# Landing Page Video Replacement Guide

## 📍 Exact Locations to Replace

### 1. Hero Section Video (Line 1561-1565)

**Current Code:**
```html
<div class="hero-visual-placeholder">
    <span style="font-size: 48px; margin-bottom: 16px;">🎬</span>
    <span>Your App Screenshot Here</span>
    <span style="font-size: 12px; opacity: 0.5;">Use the Research Crew execution screenshot</span>
</div>
```

**Replace With:**
```html
<video 
    autoplay 
    loop 
    muted 
    playsinline
    class="hero-visual-video"
    style="width: 100%; height: 100%; object-fit: cover; border-radius: 20px;"
>
    <source src="/videos/hero-workflow.mp4" type="video/mp4">
    <!-- Fallback image -->
    <img src="/images/hero-workflow-fallback.jpg" alt="NodeAI Workflow Demo" style="width: 100%; height: 100%; object-fit: cover;">
</video>
```

---

### 2. RAG Pipeline Feature Video (Line 1751-1754)

**Current Code:**
```html
<div class="feature-visual-placeholder">
    [RAG Pipeline Screenshot]<br>
    File → Chunk → Embed → Vector Store → Search → Chat
</div>
```

**Replace With:**
```html
<video 
    autoplay 
    loop 
    muted 
    playsinline
    class="feature-visual-video"
    style="width: 100%; height: 100%; object-fit: cover; border-radius: 20px;"
>
    <source src="/videos/rag-pipeline.mp4" type="video/mp4">
    <img src="/images/rag-pipeline-fallback.jpg" alt="RAG Pipeline Flow" style="width: 100%; height: 100%; object-fit: cover;">
</video>
```

---

### 3. Observability Feature Video (Line 1775-1778)

**Current Code:**
```html
<div class="feature-visual-placeholder">
    [Execution Results Panel]<br>
    Costs, tokens, timeline, traces
</div>
```

**Replace With:**
```html
<video 
    autoplay 
    loop 
    muted 
    playsinline
    class="feature-visual-video"
    style="width: 100%; height: 100%; object-fit: cover; border-radius: 20px;"
>
    <source src="/videos/observability.mp4" type="video/mp4">
    <img src="/images/observability-fallback.jpg" alt="Execution Observability" style="width: 100%; height: 100%; object-fit: cover;">
</video>
```

---

### 4. Node Library Feature Video (Line 1799-1802)

**Current Code:**
```html
<div class="feature-visual-placeholder">
    [Node Library Grid]<br>
    Icons for each category
</div>
```

**Replace With:**
```html
<video 
    autoplay 
    loop 
    muted 
    playsinline
    class="feature-visual-video"
    style="width: 100%; height: 100%; object-fit: cover; border-radius: 20px;"
>
    <source src="/videos/node-library.mp4" type="video/mp4">
    <img src="/images/node-library-fallback.jpg" alt="Node Library" style="width: 100%; height: 100%; object-fit: cover;">
</video>
```

---

## 🎨 CSS Updates Needed

Add these styles to your `<style>` section (around line 1083):

```css
.hero-visual-video,
.feature-visual-video {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(13, 17, 23, 0.9), rgba(20, 25, 35, 0.9));
}

/* Ensure video doesn't break layout */
.hero-visual-container video,
.feature-visual video {
    display: block;
}

/* Loading state */
video[loading] {
    opacity: 0;
    transition: opacity 0.5s;
}

video[loaded] {
    opacity: 1;
}
```

---

## 📁 File Structure

After rendering videos, organize like this:

```
Nodeflow/
├── public/
│   └── videos/
│       ├── hero-workflow.mp4          (15s, ~2-3MB)
│       ├── rag-pipeline.mp4           (12s, ~1.5-2MB)
│       ├── observability.mp4           (10s, ~1-1.5MB)
│       └── node-library.mp4           (8s, ~1MB)
│   └── images/
│       ├── hero-workflow-fallback.jpg
│       ├── rag-pipeline-fallback.jpg
│       ├── observability-fallback.jpg
│       └── node-library-fallback.jpg
└── nodeai-landing-animated.html
```

---

## ✅ Checklist

- [ ] Generate all 4 videos using Claude prompts
- [ ] Render videos with Remotion
- [ ] Optimize videos (CRF 22-28, web-optimized)
- [ ] Create fallback images (first frame of each video)
- [ ] Upload videos to `/public/videos/`
- [ ] Replace placeholders in HTML
- [ ] Add CSS for video styling
- [ ] Test on desktop (Chrome, Firefox, Safari)
- [ ] Test on mobile (iOS, Android)
- [ ] Check file sizes (should be <3MB each)
- [ ] Verify autoplay works (muted, playsinline)
- [ ] Test fallback images load if video fails

---

## 🚀 Quick Implementation

1. **Generate videos** using prompts in `claude_video_prompts.md`
2. **Render videos** using Remotion
3. **Optimize** for web (see commands below)
4. **Replace** placeholders in HTML (use this guide)
5. **Test** on multiple devices

### Optimization Commands:

```bash
# Optimize for web (smaller file size, faster loading)
ffmpeg -i hero-workflow.mp4 -c:v libx264 -preset slow -crf 24 -c:a aac -b:a 128k -movflags +faststart -vf "scale=1920:1080" hero-workflow-optimized.mp4

# Create fallback image (first frame)
ffmpeg -i hero-workflow.mp4 -ss 00:00:01 -vframes 1 hero-workflow-fallback.jpg
```

---

## 💡 Pro Tips

1. **Start with Hero video** - Most impactful
2. **Keep file sizes small** - Use CRF 24-28 for web
3. **Test autoplay** - Must be muted for autoplay to work
4. **Add loading states** - Show placeholder until video loads
5. **Mobile optimization** - Use `playsinline` attribute
6. **Lazy load** - Only load videos when in viewport (optional)

Ready to replace those placeholders! 🎬
