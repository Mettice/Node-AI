import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  spring,
  Easing,
} from 'remotion';

const BRAND_COLORS = {
  amber: '#f0b429',
  green: '#22c55e',
  blue: '#3b82f6',
  cyan: '#22d3ee',
  purple: '#a78bfa',
  pink: '#f472b6',
  dark: '#030712',
  darkCard: 'rgba(15, 23, 42, 0.95)',
  slate: {
    800: '#1e293b',
    700: '#334155',
    600: '#475569',
    500: '#64748b',
    400: '#94a3b8',
    300: '#cbd5e1',
  },
};

interface AgentProps {
  x: number;
  y: number;
  name: string;
  role: string;
  color: string;
  frame: number;
  delay: number;
  isActive: boolean;
  isSpeaking: boolean;
}

const Agent: React.FC<AgentProps> = ({
  x, y, name, role, color, frame, delay, isActive, isSpeaking
}) => {
  const opacity = interpolate(
    frame,
    [delay, delay + 20],
    [0, 1],
    { extrapolateRight: 'clamp' }
  );

  const scale = spring({
    frame: Math.max(0, frame - delay),
    fps: 30,
    config: { damping: 12, stiffness: 150 },
    from: 0.8,
    to: 1,
  });

  const pulseIntensity = isSpeaking
    ? interpolate(
        frame % 30,
        [0, 15, 30],
        [0.5, 1, 0.5],
        { extrapolateRight: 'clamp' }
      )
    : 0.3;

  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        transform: `translate(-50%, -50%) scale(${scale})`,
        opacity,
      }}
    >
      <div
        style={{
          width: 160,
          padding: '16px',
          background: BRAND_COLORS.darkCard,
          borderRadius: 16,
          border: `2px solid ${color}`,
          boxShadow: isSpeaking
            ? `0 0 ${pulseIntensity * 30}px ${color}80`
            : `0 4px 20px rgba(0, 0, 0, 0.4)`,
          textAlign: 'center',
        }}
      >
        {/* Avatar */}
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: '50%',
            background: `${color}30`,
            border: `3px solid ${color}`,
            margin: '0 auto 12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 24,
            boxShadow: isSpeaking ? `0 0 20px ${color}60` : 'none',
          }}
        >
          {role === 'Researcher' && '🔍'}
          {role === 'Writer' && '✍️'}
          {role === 'Reviewer' && '📋'}
          {role === 'Manager' && '👔'}
        </div>
        <div style={{ fontSize: 14, fontWeight: 600, color: '#f1f5f9', marginBottom: 4 }}>
          {name}
        </div>
        <div style={{ fontSize: 11, color: color, fontWeight: 500 }}>
          {role}
        </div>
      </div>
    </div>
  );
};

interface MessageProps {
  from: { x: number; y: number };
  to: { x: number; y: number };
  color: string;
  frame: number;
  delay: number;
  text: string;
}

const Message: React.FC<MessageProps> = ({ from, to, color, frame, delay, text }) => {
  const progress = interpolate(
    frame,
    [delay, delay + 40],
    [0, 1],
    { extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  const messageOpacity = interpolate(
    frame,
    [delay, delay + 10, delay + 60, delay + 80],
    [0, 1, 1, 0],
    { extrapolateRight: 'clamp' }
  );

  if (progress === 0) return null;

  // Calculate position along path
  const currentX = from.x + (to.x - from.x) * progress;
  const currentY = from.y + (to.y - from.y) * progress;

  // Message bubble position (appears at midpoint then follows)
  const midX = (from.x + to.x) / 2;
  const midY = (from.y + to.y) / 2 - 40;

  return (
    <>
      {/* Connection line */}
      <svg
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
        }}
      >
        <defs>
          <linearGradient id={`msg-gradient-${delay}`} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={color} stopOpacity="0.8" />
            <stop offset="100%" stopColor={color} stopOpacity="0.3" />
          </linearGradient>
        </defs>
        <line
          x1={from.x}
          y1={from.y}
          x2={currentX}
          y2={currentY}
          stroke={`url(#msg-gradient-${delay})`}
          strokeWidth={2}
          strokeDasharray="8 4"
        />
        {/* Particle */}
        <circle
          cx={currentX}
          cy={currentY}
          r={6}
          fill={color}
          style={{ filter: `drop-shadow(0 0 8px ${color})` }}
        />
      </svg>

      {/* Message bubble */}
      {progress > 0.3 && (
        <div
          style={{
            position: 'absolute',
            left: midX,
            top: midY,
            transform: 'translate(-50%, -50%)',
            opacity: messageOpacity,
          }}
        >
          <div
            style={{
              background: BRAND_COLORS.darkCard,
              border: `1px solid ${color}`,
              borderRadius: 12,
              padding: '8px 14px',
              maxWidth: 200,
              boxShadow: `0 0 20px ${color}40`,
            }}
          >
            <div style={{ fontSize: 11, color: '#f1f5f9' }}>{text}</div>
          </div>
        </div>
      )}
    </>
  );
};

export const MultiAgent: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  // Agent positions
  const agents = [
    { id: 'manager', name: 'Project Lead', role: 'Manager', color: BRAND_COLORS.amber, x: width * 0.5, y: height * 0.25 },
    { id: 'researcher', name: 'Research Agent', role: 'Researcher', color: BRAND_COLORS.cyan, x: width * 0.2, y: height * 0.55 },
    { id: 'writer', name: 'Content Agent', role: 'Writer', color: BRAND_COLORS.pink, x: width * 0.5, y: height * 0.7 },
    { id: 'reviewer', name: 'QA Agent', role: 'Reviewer', color: BRAND_COLORS.green, x: width * 0.8, y: height * 0.55 },
  ];

  // Animation phases
  const getActiveAgent = () => {
    if (frame < 60) return 'manager';
    if (frame < 100) return 'researcher';
    if (frame < 150) return 'writer';
    if (frame < 200) return 'reviewer';
    return 'manager';
  };

  const getSpeakingAgent = () => {
    if (frame >= 30 && frame < 60) return 'manager';
    if (frame >= 70 && frame < 100) return 'researcher';
    if (frame >= 120 && frame < 150) return 'writer';
    if (frame >= 170 && frame < 200) return 'reviewer';
    if (frame >= 220) return 'manager';
    return null;
  };

  const activeAgent = getActiveAgent();
  const speakingAgent = getSpeakingAgent();

  // Messages between agents
  const messages = [
    { from: agents[0], to: agents[1], delay: 45, text: '"Research the topic..."', color: BRAND_COLORS.amber },
    { from: agents[1], to: agents[2], delay: 90, text: '"Here are the findings..."', color: BRAND_COLORS.cyan },
    { from: agents[2], to: agents[3], delay: 140, text: '"Draft complete for review"', color: BRAND_COLORS.pink },
    { from: agents[3], to: agents[0], delay: 190, text: '"Approved with edits"', color: BRAND_COLORS.green },
  ];

  // Title animation
  const titleOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });

  // Final result
  const resultOpacity = interpolate(frame, [230, 260], [0, 1], { extrapolateRight: 'clamp' });
  const resultScale = spring({
    frame: Math.max(0, frame - 230),
    fps: 30,
    config: { damping: 12, stiffness: 100 },
    from: 0.8,
    to: 1,
  });

  return (
    <AbsoluteFill
      style={{
        background: BRAND_COLORS.dark,
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
      <div
        style={{
          position: 'absolute',
          top: 30,
          left: 0,
          right: 0,
          textAlign: 'center',
          opacity: titleOpacity,
        }}
      >
        <div
          style={{
            fontSize: 28,
            fontWeight: 700,
            color: BRAND_COLORS.amber,
            marginBottom: 8,
          }}
        >
          Multi-Agent Collaboration
        </div>
        <div style={{ fontSize: 14, color: BRAND_COLORS.slate[400] }}>
          CrewAI agents working together
        </div>
      </div>

      {/* Render messages first (behind agents) */}
      {messages.map((msg, idx) => (
        <Message
          key={idx}
          from={{ x: msg.from.x, y: msg.from.y }}
          to={{ x: msg.to.x, y: msg.to.y }}
          color={msg.color}
          frame={frame}
          delay={msg.delay}
          text={msg.text}
        />
      ))}

      {/* Render agents */}
      {agents.map((agent, idx) => (
        <Agent
          key={agent.id}
          x={agent.x}
          y={agent.y}
          name={agent.name}
          role={agent.role}
          color={agent.color}
          frame={frame}
          delay={idx * 15}
          isActive={activeAgent === agent.id}
          isSpeaking={speakingAgent === agent.id}
        />
      ))}

      {/* Task status panel */}
      <div
        style={{
          position: 'absolute',
          bottom: 40,
          left: 40,
          background: BRAND_COLORS.darkCard,
          borderRadius: 12,
          border: `1px solid ${BRAND_COLORS.slate[800]}`,
          padding: 16,
          width: 200,
        }}
      >
        <div style={{ fontSize: 12, fontWeight: 600, color: '#f1f5f9', marginBottom: 12 }}>
          Task Progress
        </div>
        {['Research', 'Write', 'Review', 'Finalize'].map((task, idx) => {
          const taskDelay = 60 + idx * 50;
          const isComplete = frame > taskDelay + 40;
          const isActive = frame > taskDelay && frame <= taskDelay + 40;
          const taskOpacity = interpolate(frame, [idx * 15, idx * 15 + 20], [0, 1], { extrapolateRight: 'clamp' });

          return (
            <div
              key={task}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                marginBottom: 8,
                opacity: taskOpacity,
              }}
            >
              <div
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: '50%',
                  background: isComplete ? BRAND_COLORS.green : isActive ? BRAND_COLORS.amber : BRAND_COLORS.slate[700],
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 8,
                  color: 'white',
                }}
              >
                {isComplete ? '✓' : isActive ? '⟳' : ''}
              </div>
              <span style={{ fontSize: 11, color: isComplete ? BRAND_COLORS.green : isActive ? BRAND_COLORS.amber : BRAND_COLORS.slate[500] }}>
                {task}
              </span>
            </div>
          );
        })}
      </div>

      {/* Final result */}
      {frame >= 230 && (
        <div
          style={{
            position: 'absolute',
            bottom: 40,
            right: 40,
            transform: `scale(${resultScale})`,
            opacity: resultOpacity,
          }}
        >
          <div
            style={{
              background: BRAND_COLORS.darkCard,
              borderRadius: 12,
              border: `2px solid ${BRAND_COLORS.green}`,
              padding: 16,
              boxShadow: `0 0 30px ${BRAND_COLORS.green}40`,
            }}
          >
            <div style={{ fontSize: 14, fontWeight: 600, color: '#f1f5f9', marginBottom: 8 }}>
              ✓ Crew Task Complete
            </div>
            <div style={{ fontSize: 11, color: BRAND_COLORS.slate[400] }}>
              4 agents • 3.2s total • $0.0042
            </div>
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
