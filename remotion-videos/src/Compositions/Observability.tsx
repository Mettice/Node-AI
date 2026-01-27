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

export const Observability: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  // Dashboard fade in
  const dashboardOpacity = interpolate(
    frame,
    [0, 30],
    [0, 1],
    { extrapolateRight: 'clamp' }
  );

  // Cost counter
  const costValue = interpolate(
    frame,
    [30, 90],
    [0, 0.0038],
    { extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  // Token counters
  const inputTokens = Math.floor(interpolate(
    frame,
    [60, 120],
    [0, 1500],
    { extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  ));

  const outputTokens = Math.floor(interpolate(
    frame,
    [90, 150],
    [0, 800],
    { extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  ));

  // Timeline nodes animation
  const timelineNodes = [
    { name: 'Text Input', duration: 120, delay: 120 },
    { name: 'Vector Search', duration: 240, delay: 150 },
    { name: 'Rerank', duration: 180, delay: 180 },
    { name: 'Chat', duration: 450, delay: 210 },
  ];

  // Cost chart bars
  const chartBars = [40, 60, 45, 70, 55, 80, 65];
  const chartProgress = interpolate(
    frame,
    [240, 300],
    [0, 1],
    { extrapolateRight: 'clamp' }
  );

  // Metrics
  const successRate = interpolate(
    frame,
    [150, 210],
    [0, 99.2],
    { extrapolateRight: 'clamp' }
  );

  const avgLatency = interpolate(
    frame,
    [180, 240],
    [0, 1.2],
    { extrapolateRight: 'clamp' }
  );

  const costPerExec = interpolate(
    frame,
    [210, 270],
    [0, 0.12],
    { extrapolateRight: 'clamp' }
  );

  return (
    <AbsoluteFill
      style={{
        background: BRAND_COLORS.dark,
        fontFamily: 'Inter, sans-serif',
        color: 'white',
        padding: 40,
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
          fontSize: 28,
          fontWeight: 700,
          marginBottom: 30,
          color: BRAND_COLORS.amber,
          opacity: dashboardOpacity,
        }}
      >
        Execution Dashboard
      </div>

      {/* Main Dashboard Container */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 24,
          opacity: dashboardOpacity,
        }}
      >
        {/* Left Column - Execution Trace */}
        <div
          style={{
            background: BRAND_COLORS.darkCard,
            borderRadius: 12,
            border: `1px solid ${BRAND_COLORS.slate[800]}`,
            padding: 24,
            boxShadow: '0 4px 24px rgba(0, 0, 0, 0.4)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <h4 style={{ fontSize: 14, fontWeight: 600, color: 'white' }}>Execution Trace</h4>
            <span style={{ fontSize: 12, color: BRAND_COLORS.green }}>Completed</span>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {timelineNodes.map((node, idx) => {
              const nodeOpacity = interpolate(
                frame,
                [node.delay, node.delay + 30],
                [0, 1],
                { extrapolateRight: 'clamp' }
              );

              const isCompleted = frame > node.delay + 30;

              return (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: 8,
                    background: 'rgba(15, 23, 42, 0.5)',
                    borderRadius: 8,
                    border: `1px solid ${BRAND_COLORS.slate[800]}`,
                    opacity: nodeOpacity,
                  }}
                >
                  <div
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      background: isCompleted ? BRAND_COLORS.green : BRAND_COLORS.slate[600],
                      boxShadow: isCompleted ? `0 0 8px ${BRAND_COLORS.green}40` : 'none',
                    }}
                  />
                  <span style={{ fontSize: 12, color: BRAND_COLORS.slate[300], flex: 1 }}>
                    {node.name}
                  </span>
                  <span style={{ fontSize: 12, color: BRAND_COLORS.slate[500], fontFamily: 'monospace' }}>
                    {node.duration}ms
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column - Cost Forecast */}
        <div
          style={{
            background: BRAND_COLORS.darkCard,
            borderRadius: 12,
            border: `1px solid ${BRAND_COLORS.slate[800]}`,
            padding: 24,
            boxShadow: '0 4px 24px rgba(0, 0, 0, 0.4)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <h4 style={{ fontSize: 14, fontWeight: 600, color: 'white' }}>Cost Forecast</h4>
            <span style={{ fontSize: 12, color: BRAND_COLORS.blue }}>Next 30 days</span>
          </div>
          
          {/* Chart */}
          <div
            style={{
              height: 96,
              background: 'rgba(15, 23, 42, 0.5)',
              borderRadius: 8,
              border: `1px solid ${BRAND_COLORS.slate[800]}`,
              padding: 8,
              display: 'flex',
              alignItems: 'flex-end',
              justifyContent: 'space-around',
              gap: 4,
            }}
          >
            {chartBars.map((height, idx) => {
              const barHeight = height * chartProgress;
              const barOpacity = interpolate(
                frame,
                [240 + idx * 5, 240 + idx * 5 + 10],
                [0, 1],
                { extrapolateRight: 'clamp' }
              );

              return (
                <div
                  key={idx}
                  style={{
                    width: 24,
                    height: `${barHeight}%`,
                    background: BRAND_COLORS.blue,
                    borderRadius: '4px 4px 0 0',
                    opacity: barOpacity,
                    transition: 'height 0.3s',
                  }}
                />
              );
            })}
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 12, fontSize: 12, color: BRAND_COLORS.slate[500] }}>
            <span>Est: $245</span>
            <span>Current: $189</span>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 20,
          marginTop: 24,
          opacity: dashboardOpacity,
        }}
      >
        {/* Success Rate */}
        <div
          style={{
            background: BRAND_COLORS.darkCard,
            borderRadius: 12,
            border: `1px solid ${BRAND_COLORS.slate[800]}`,
            padding: 20,
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: 24, fontWeight: 700, color: 'white', marginBottom: 4 }}>
            {successRate.toFixed(1)}%
          </div>
          <div style={{ fontSize: 12, color: BRAND_COLORS.slate[400] }}>Success Rate</div>
        </div>

        {/* Avg Latency */}
        <div
          style={{
            background: BRAND_COLORS.darkCard,
            borderRadius: 12,
            border: `1px solid ${BRAND_COLORS.slate[800]}`,
            padding: 20,
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: 24, fontWeight: 700, color: 'white', marginBottom: 4 }}>
            {avgLatency.toFixed(1)}s
          </div>
          <div style={{ fontSize: 12, color: BRAND_COLORS.slate[400] }}>Avg Latency</div>
        </div>

        {/* Cost Per Execution */}
        <div
          style={{
            background: BRAND_COLORS.darkCard,
            borderRadius: 12,
            border: `1px solid ${BRAND_COLORS.slate[800]}`,
            padding: 20,
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: 24, fontWeight: 700, color: 'white', marginBottom: 4 }}>
            ${costPerExec.toFixed(2)}
          </div>
          <div style={{ fontSize: 12, color: BRAND_COLORS.slate[400] }}>Per Execution</div>
        </div>
      </div>

      {/* Cost and Token Stats */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 20,
          marginTop: 24,
          opacity: dashboardOpacity,
        }}
      >
        {/* Total Cost */}
        <div
          style={{
            background: BRAND_COLORS.darkCard,
            borderRadius: 12,
            border: `2px solid ${BRAND_COLORS.amber}`,
            padding: 20,
          }}
        >
          <div style={{ fontSize: 12, color: BRAND_COLORS.slate[400], marginBottom: 8 }}>
            Total Cost
          </div>
          <div style={{ fontSize: 32, fontWeight: 700, color: BRAND_COLORS.amber }}>
            ${costValue.toFixed(4)}
          </div>
        </div>

        {/* Input Tokens */}
        <div
          style={{
            background: BRAND_COLORS.darkCard,
            borderRadius: 12,
            border: `2px solid ${BRAND_COLORS.cyan}`,
            padding: 20,
          }}
        >
          <div style={{ fontSize: 12, color: BRAND_COLORS.slate[400], marginBottom: 8 }}>
            Input Tokens
          </div>
          <div style={{ fontSize: 32, fontWeight: 700, color: BRAND_COLORS.cyan }}>
            {inputTokens.toLocaleString()}
          </div>
        </div>

        {/* Output Tokens */}
        <div
          style={{
            background: BRAND_COLORS.darkCard,
            borderRadius: 12,
            border: `2px solid ${BRAND_COLORS.blue}`,
            padding: 20,
          }}
        >
          <div style={{ fontSize: 12, color: BRAND_COLORS.slate[400], marginBottom: 8 }}>
            Output Tokens
          </div>
          <div style={{ fontSize: 32, fontWeight: 700, color: BRAND_COLORS.blue }}>
            {outputTokens.toLocaleString()}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
