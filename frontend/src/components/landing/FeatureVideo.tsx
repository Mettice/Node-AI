interface FeatureVideoProps {
  videoSrc: string;
  fallbackSrc: string;
  alt: string;
  className?: string;
}

export function FeatureVideo({ 
  videoSrc, 
  fallbackSrc, 
  alt,
  className = "w-full h-full object-cover rounded-3xl"
}: FeatureVideoProps) {
  // Add cache busting with version 2 to force reload of updated videos
  const videoSrcWithCache = `${videoSrc}?v=2`;
  
  return (
    <video
      autoPlay
      loop
      muted
      playsInline
      className={className}
      key={videoSrc} // Force remount when video source changes
    >
      <source src={videoSrcWithCache} type="video/mp4" />
      <img src={fallbackSrc} alt={alt} className={className} />
    </video>
  );
}
