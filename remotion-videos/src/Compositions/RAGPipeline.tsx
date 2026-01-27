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
  input: '#22d3ee',       // Cyan - File Loader, Text Input
  processing: '#fb923c',  // Orange - Chunk
  embedding: '#a78bfa',    // Purple - Embed
  storage: '#34d399',     // Emerald - Vector Store
  retrieval: '#60a5fa',   // Blue - Vector Search
  llm: '#f0b429',         // Amber - Chat
  dark: '#030712',
  darkCard: 'rgba(15, 23, 42, 0.95)', // slate-900 with opacity
};

interface WorkflowNodeProps {
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

const WorkflowNode: React.FC<WorkflowNodeProps> = ({ 
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
        [0.3, 1, 0.3],
        { extrapolateRight: 'clamp' }
      )
    : isCompleted
    ? 0.5
    : 0.2;

  // Status badge
  const statusBadgeOpacity = isActive || isCompleted
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
      {/* Node container - matches actual design */}
      <div
        style={{
          minWidth: 180,
          maxWidth: 200,
          padding: '12px 16px',
          background: NODE_COLORS.darkCard,
          borderRadius: 12,
          border: `2px solid ${color}`,
          boxShadow: `0 0 ${glowIntensity * 30}px ${color}${Math.floor(glowIntensity * 60).toString(16).padStart(2, '0')}, 0 4px 24px rgba(0, 0, 0, 0.4)`,
          color: 'white',
          fontFamily: 'Inter, sans-serif',
          position: 'relative',
          transition: 'all 0.3s',
        }}
      >
        {/* Status badge - top left */}
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
            }}
          >
            {isCompleted ? '✓' : '⟳'}
          </div>
        )}

        {/* Node header with icon */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: `${color}20`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: color,
              fontSize: 18,
            }}
          >
            {type === 'file_loader' && '📁'}
            {type === 'chunk' && '✂️'}
            {type === 'embed' && '🧠'}
            {type === 'vector_store' && '💾'}
            {type === 'vector_search' && '🔍'}
            {type === 'chat' && '💬'}
            {type === 'text_input' && '📝'}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#f1f5f9' }}>
              {label}
            </div>
            <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>
              {type.replace('_', ' ')}
            </div>
          </div>
        </div>

        {/* Active indicator */}
        {isActive && (
          <div
            style={{
              position: 'absolute',
              inset: -2,
              borderRadius: 12,
              border: `2px solid ${color}`,
              opacity: glowIntensity,
              animation: 'pulse 1.5s ease-in-out infinite',
            }}
          />
        )}
      </div>
    </AbsoluteFill>
  );
};

interface WorkflowEdgeProps {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  color: string;
  frame: number;
  delay: number;
  isActive: boolean;
  dashArray?: string;
}

const WorkflowEdge: React.FC<WorkflowEdgeProps> = ({ 
  x1, y1, x2, y2, color, frame, delay, isActive, dashArray = 'none' 
}) => {
  const progress = interpolate(
    frame,
    [delay, delay + 40],
    [0, 1],
    { extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) }
  );

  // Bezier curve for smooth connection
  const cp1x = x1 + (x2 - x1) * 0.5;
  const cp1y = y1;
  const cp2x = x1 + (x2 - x1) * 0.5;
  const cp2y = y2;

  const pathLength = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
  const strokeDashoffset = pathLength * (1 - progress);

  // Animated particle
  const particleProgress = interpolate(
    frame,
    [delay, delay + 40],
    [0, 1],
    { extrapolateRight: 'clamp' }
  );

  const particleX = x1 + (x2 - x1) * particleProgress;
  const particleY = y1 + (y2 - y1) * particleProgress;

  const edgeOpacity = isActive ? 1 : 0.4;

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
          <linearGradient id={`edge-gradient-${color}`} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={color} stopOpacity="0.6" />
            <stop offset="100%" stopColor={color} stopOpacity="1" />
          </linearGradient>
          <filter id={`glow-${color}`}>
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        
        {/* Edge path */}
        <path
          d={`M ${x1} ${y1} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${x2} ${y2}`}
          stroke={`url(#edge-gradient-${color})`}
          strokeWidth={isActive ? 3 : 2}
          fill="none"
          strokeDasharray={dashArray === 'none' ? 'none' : '10 5'}
          strokeDashoffset={dashArray !== 'none' ? strokeDashoffset : 0}
          opacity={edgeOpacity}
          style={{
            filter: isActive ? `url(#glow-${color})` : 'none',
            transition: 'all 0.3s',
          }}
        />

        {/* Animated particle */}
        {isActive && particleProgress > 0 && particleProgress < 1 && (
          <circle
            cx={particleX}
            cy={particleY}
            r={4}
            fill={color}
            opacity={0.9}
            style={{
              filter: `drop-shadow(0 0 6px ${color})`,
            }}
          />
        )}
      </svg>
    </AbsoluteFill>
  );
};

export const RAGPipeline: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  // All 6 nodes in a single horizontal row, centered vertically
  // Account for title at top (40px) and center the nodes in remaining space
  const titleHeight = 80; // Title area height
  const availableHeight = height - titleHeight;
  const centerY = titleHeight + (availableHeight / 2); // True center accounting for title
  
  const nodes = [
    { 
      id: 'file_loader', 
      x: width * 0.08, 
      y: centerY,  // CENTERED vertically (accounting for title)
      label: 'File Upload', 
      type: 'file_loader',
      color: NODE_COLORS.input, 
      delay: 0 
    },
    { 
      id: 'chunk', 
      x: width * 0.24, 
      y: centerY,  // CENTERED vertically
      label: 'Chunk', 
      type: 'chunk',
      color: NODE_COLORS.processing, 
      delay: 30 
    },
    { 
      id: 'embed', 
      x: width * 0.40, 
      y: centerY,  // CENTERED vertically
      label: 'Embed', 
      type: 'embed',
      color: NODE_COLORS.embedding, 
      delay: 60 
    },
    { 
      id: 'vector_store', 
      x: width * 0.56, 
      y: centerY,  // CENTERED vertically
      label: 'Vector Store', 
      type: 'vector_store',
      color: NODE_COLORS.storage, 
      delay: 90 
    },
    { 
      id: 'vector_search', 
      x: width * 0.72, 
      y: centerY,  // CENTERED vertically
      label: 'Vector Search', 
      type: 'vector_search',
      color: NODE_COLORS.retrieval, 
      delay: 120 
    },
    { 
      id: 'chat', 
      x: width * 0.88, 
      y: centerY,  // CENTERED vertically
      label: 'Chat', 
      type: 'chat',
      color: NODE_COLORS.llm, 
      delay: 150 
    },
  ];

  // Determine active node
  const getActiveNodeId = () => {
    if (frame < 60) return 'file_loader';
    if (frame < 90) return 'chunk';
    if (frame < 120) return 'embed';
    if (frame < 150) return 'vector_store';
    if (frame < 180) return 'vector_search';
    if (frame < 210) return 'chat';
    return null;
  };

  const activeNodeId = getActiveNodeId();

  // Determine completed nodes
  const isCompleted = (nodeId: string) => {
    const nodeDelays: Record<string, number> = {
      file_loader: 0,
      chunk: 30,
      embed: 60,
      vector_store: 90,
      vector_search: 120,
      chat: 150,
    };
    return frame > (nodeDelays[nodeId] || 0) + 60;
  };

  // Chat result
  const chatResultOpacity = interpolate(
    frame,
    [240, 270],
    [0, 1],
    { extrapolateRight: 'clamp' }
  );

  return (
    <AbsoluteFill
      style={{
        background: NODE_COLORS.dark,
        fontFamily: 'Inter, sans-serif',
        color: 'white',
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
          top: 40,
          left: 0,
          right: 0,
          textAlign: 'center',
        }}
      >
        <div
          style={{
            fontSize: 28,
            fontWeight: 700,
            color: NODE_COLORS.llm,
            marginBottom: 8,
          }}
        >
          RAG Pipeline Flow
        </div>
      </AbsoluteFill>

      {/* All 6 nodes in horizontal flow */}
      {nodes.map((node) => (
        <WorkflowNode
          key={node.id}
          x={node.x}
          y={node.y}
          label={node.label}
          type={node.type}
          color={node.color}
          frame={frame}
          delay={node.delay}
          isActive={activeNodeId === node.id}
          isCompleted={isCompleted(node.id)}
        />
      ))}

      {/* Edges between nodes */}
      {nodes.slice(0, -1).map((node, index) => {
        const nextNode = nodes[index + 1];
        // Use dashed line for Vector Store → Vector Search connection
        const isDashed = node.id === 'vector_store' && nextNode.id === 'vector_search';
        
        return (
          <WorkflowEdge
            key={`edge-${index}`}
            x1={node.x}
            y1={node.y}
            x2={nextNode.x}
            y2={nextNode.y}
            color={node.color}
            frame={frame}
            delay={node.delay + 40}
            isActive={activeNodeId === nextNode.id || isCompleted(node.id)}
            dashArray={isDashed ? "10 5" : "none"}
          />
        );
      })}

      {/* Chat result */}
      {frame >= 240 && (
        <AbsoluteFill
          style={{
            left: nodes[5].x,
            top: nodes[5].y + 120,
            transform: 'translateX(-50%)',
            opacity: chatResultOpacity,
          }}
        >
          <div
            style={{
              width: 280,
              padding: '20px',
              background: NODE_COLORS.darkCard,
              borderRadius: 12,
              border: `2px solid ${NODE_COLORS.llm}`,
              fontSize: 14,
              lineHeight: 1.6,
            }}
          >
            <div style={{ marginBottom: 12, fontWeight: 600, color: '#f1f5f9' }}>
              Response Generated
            </div>
            <div style={{ marginBottom: 8, color: '#94a3b8', fontSize: 12 }}>
              Cost: $0.0003
            </div>
            <div style={{ color: '#94a3b8', fontSize: 12 }}>
              Tokens: 1,500
            </div>
            <div
              style={{
                marginTop: 12,
                fontSize: 20,
                color: '#22c55e',
              }}
            >
              ✓ Completed
            </div>
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
