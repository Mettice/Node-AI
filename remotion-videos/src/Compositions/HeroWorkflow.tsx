import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  spring,
  Easing,
} from 'remotion';

// ACTUAL NODE CATEGORY COLORS from frontend/src/constants/index.ts
const NODE_COLORS = {
  input: '#22d3ee',       // Cyan
  processing: '#fb923c',  // Orange
  embedding: '#a78bfa',  // Purple
  storage: '#34d399',     // Emerald
  retrieval: '#60a5fa',   // Blue
  llm: '#f0b429',         // Amber
  dark: '#030712',
  darkCard: 'rgba(15, 23, 42, 0.95)',
};

interface NodeProps {
  x: number;
  y: number;
  label: string;
  type: string;
  color: string;
  frame: number;
  delay: number;
  isActive: boolean;
  isCompleted: boolean;
}

const Node: React.FC<NodeProps> = ({ 
  x, y, label, type, color, frame, delay, isActive, isCompleted 
}) => {
  const opacity = interpolate(
    frame,
    [delay, delay + 20],
    [0, 1],
    { extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  const scale = spring({
    frame: Math.max(0, frame - delay),
    fps: 30,
    config: { damping: 12, stiffness: 150 },
    from: 0,
    to: 1,
  });

  // Active glow animation
  const glowIntensity = isActive
    ? interpolate(
        frame,
        [delay + 60, delay + 90, delay + 120],
        [0.4, 1, 0.4],
        { extrapolateRight: 'clamp' }
      )
    : isCompleted
    ? 0.6
    : 0.2;

  // Status badge
  const statusBadgeOpacity = (isActive || isCompleted)
    ? interpolate(frame, [delay + 40, delay + 50], [0, 1], { extrapolateRight: 'clamp' })
    : 0;

  return (
    <AbsoluteFill
      style={{
        left: x,
        top: y,
        transform: `translate(-50%, -50%) scale(${scale})`,
        opacity,
      }}
    >
      <div
        style={{
          minWidth: 190,
          maxWidth: 210,
          padding: '12px 16px',
          background: NODE_COLORS.darkCard,
          borderRadius: 12,
          border: `2px solid ${color}`,
          boxShadow: `0 0 ${glowIntensity * 35}px ${color}${Math.floor(glowIntensity * 70).toString(16).padStart(2, '0')}, 0 4px 24px rgba(0, 0, 0, 0.4)`,
          color: 'white',
          fontFamily: 'Inter, sans-serif',
          position: 'relative',
        }}
      >
        {/* Status badge */}
        {(isActive || isCompleted) && (
          <div
            style={{
              position: 'absolute',
              top: -8,
              left: -8,
              width: 24,
              height: 24,
              borderRadius: '50%',
              background: isCompleted ? '#22c55e' : '#3b82f6',
              border: '2px solid white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              opacity: statusBadgeOpacity,
              boxShadow: `0 0 12px ${isCompleted ? '#22c55e' : '#3b82f6'}`,
              fontSize: 12,
              fontWeight: 'bold',
            }}
          >
            {isCompleted ? '✓' : '⟳'}
          </div>
        )}

        {/* Node header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: 8,
              background: `${color}20`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: color,
              fontSize: 20,
              boxShadow: `0 0 20px ${color}40`,
            }}
          >
            {type === 'file_loader' && '📁'}
            {type === 'chunk' && '✂️'}
            {type === 'embed' && '🧠'}
            {type === 'vector_store' && '💾'}
            {type === 'vector_search' && '🔍'}
            {type === 'chat' && '💬'}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#f1f5f9' }}>
              {label}
            </div>
            <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>
              {type.replace('_', ' ')}
            </div>
          </div>
        </div>

        {/* Active pulse ring */}
        {isActive && (
          <div
            style={{
              position: 'absolute',
              inset: -3,
              borderRadius: 14,
              border: `2px solid ${color}`,
              opacity: glowIntensity * 0.6,
            }}
          />
        )}
      </div>
    </AbsoluteFill>
  );
};

interface EdgeProps {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  color: string;
  frame: number;
  delay: number;
  isActive: boolean;
}

const Edge: React.FC<EdgeProps> = ({ x1, y1, x2, y2, color, frame, delay, isActive }) => {
  const progress = interpolate(
    frame,
    [delay, delay + 50],
    [0, 1],
    { extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) }
  );

  // Bezier curve
  const cp1x = x1 + (x2 - x1) * 0.5;
  const cp1y = y1;
  const cp2x = x1 + (x2 - x1) * 0.5;
  const cp2y = y2;

  // Particle position
  const t = progress;
  const particleX = (1 - t) * (1 - t) * (1 - t) * x1 +
                    3 * (1 - t) * (1 - t) * t * cp1x +
                    3 * (1 - t) * t * t * cp2x +
                    t * t * t * x2;
  const particleY = (1 - t) * (1 - t) * (1 - t) * y1 +
                    3 * (1 - t) * (1 - t) * t * cp1y +
                    3 * (1 - t) * t * t * cp2y +
                    t * t * t * y2;

  const edgeOpacity = isActive ? 1 : 0.5;

  return (
    <AbsoluteFill>
      <svg
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
          overflow: 'visible',
        }}
      >
        <defs>
          <linearGradient id={`hero-gradient-${color}`} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={color} stopOpacity="0.7" />
            <stop offset="100%" stopColor={color} stopOpacity="1" />
          </linearGradient>
          <filter id={`hero-glow-${color}`}>
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        
        {/* Edge path */}
        <path
          d={`M ${x1} ${y1} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${x2} ${y2}`}
          stroke={`url(#hero-gradient-${color})`}
          strokeWidth={isActive ? 3 : 2.5}
          fill="none"
          opacity={edgeOpacity}
          style={{
            filter: isActive ? `url(#hero-glow-${color})` : 'none',
          }}
        />

        {/* Animated particle */}
        {isActive && progress > 0 && progress < 1 && (
          <circle
            cx={particleX}
            cy={particleY}
            r={5}
            fill={color}
            opacity={0.95}
            style={{
              filter: `drop-shadow(0 0 8px ${color})`,
            }}
          />
        )}
      </svg>
    </AbsoluteFill>
  );
};

export const HeroWorkflow: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  // Simplified workflow for hero - shows key RAG steps
  const nodes = [
    { 
      id: 'file_loader', 
      x: width * 0.2, 
      y: height * 0.5, 
      label: 'File Loader', 
      type: 'file_loader',
      color: NODE_COLORS.input, 
      delay: 30 
    },
    { 
      id: 'chunk', 
      x: width * 0.4, 
      y: height * 0.5, 
      label: 'Chunk', 
      type: 'chunk',
      color: NODE_COLORS.processing, 
      delay: 90 
    },
    { 
      id: 'embed', 
      x: width * 0.6, 
      y: height * 0.5, 
      label: 'Embed', 
      type: 'embed',
      color: NODE_COLORS.embedding, 
      delay: 150 
    },
    { 
      id: 'vector_store', 
      x: width * 0.8, 
      y: height * 0.5, 
      label: 'Vector Store', 
      type: 'vector_store',
      color: NODE_COLORS.storage, 
      delay: 210 
    },
  ];

  // Determine active node
  const getActiveNodeIndex = () => {
    if (frame < 120) return 0;
    if (frame < 180) return 1;
    if (frame < 240) return 2;
    if (frame < 300) return 3;
    return -1;
  };

  const activeNodeIndex = getActiveNodeIndex();

  // Determine completed nodes
  const isCompleted = (index: number) => {
    return activeNodeIndex > index;
  };

  // Final result
  const resultOpacity = interpolate(
    frame,
    [330, 360],
    [0, 1],
    { extrapolateRight: 'clamp' }
  );

  const resultScale = spring({
    frame: Math.max(0, frame - 330),
    fps: 30,
    config: { damping: 10, stiffness: 100 },
    from: 0.8,
    to: 1,
  });

  return (
    <AbsoluteFill
      style={{
        background: NODE_COLORS.dark,
        fontFamily: 'Inter, sans-serif',
      }}
    >
      {/* Background grid */}
      <AbsoluteFill
        style={{
          backgroundImage: `
            radial-gradient(circle at 1px 1px, rgba(255, 255, 255, 0.03) 1px, transparent 0)
          `,
          backgroundSize: '32px 32px',
        }}
      />

      {/* Title */}
      <AbsoluteFill
        style={{
          top: 60,
          left: 0,
          right: 0,
          textAlign: 'center',
        }}
      >
        <div
          style={{
            fontSize: 48,
            fontWeight: 800,
            background: 'linear-gradient(to right, #f0b429, #f472b6, #22d3ee)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: 12,
          }}
        >
          Build RAG Pipelines
        </div>
        <div
          style={{
            fontSize: 20,
            color: '#94a3b8',
            fontWeight: 500,
          }}
        >
          Visual Workflow Builder
        </div>
      </AbsoluteFill>

      {/* Render nodes */}
      {nodes.map((node, index) => (
        <Node
          key={node.id}
          x={node.x}
          y={node.y}
          label={node.label}
          type={node.type}
          color={node.color}
          frame={frame}
          delay={node.delay}
          isActive={index === activeNodeIndex}
          isCompleted={isCompleted(index)}
        />
      ))}

      {/* Render edges */}
      {nodes.slice(0, -1).map((node, index) => (
        <Edge
          key={`edge-${index}`}
          x1={node.x}
          y1={node.y}
          x2={nodes[index + 1].x}
          y2={nodes[index + 1].y}
          color={node.color}
          frame={frame}
          delay={node.delay + 60}
          isActive={index + 1 === activeNodeIndex || isCompleted(index)}
        />
      ))}

      {/* Success result */}
      {frame >= 330 && (
        <AbsoluteFill
          style={{
            left: width * 0.8,
            top: height * 0.5 + 120,
            transform: `translateX(-50%) scale(${resultScale})`,
            opacity: resultOpacity,
          }}
        >
          <div
            style={{
              width: 320,
              padding: '24px',
              background: NODE_COLORS.darkCard,
              borderRadius: 16,
              border: `2px solid ${NODE_COLORS.storage}`,
              boxShadow: `0 0 30px ${NODE_COLORS.storage}40`,
            }}
          >
            <div style={{ fontSize: 18, fontWeight: 700, color: '#f1f5f9', marginBottom: 12 }}>
              ✓ Pipeline Complete
            </div>
            <div style={{ fontSize: 14, color: '#94a3b8', marginBottom: 8 }}>
              Documents processed and indexed
            </div>
            <div style={{ fontSize: 12, color: '#64748b' }}>
              Ready for queries
            </div>
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
