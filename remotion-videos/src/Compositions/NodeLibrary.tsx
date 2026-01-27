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
  pink: '#f472b6',
  cyan: '#22d3ee',
  purple: '#a78bfa',
  emerald: '#34d399',
  dark: '#030712',
  darkCard: 'rgba(13, 17, 23, 0.9)',
};

const NODE_CATEGORIES = [
  {
    name: 'LLM',
    nodes: [
      { icon: '🤖', label: 'OpenAI' },
      { icon: '🧠', label: 'Anthropic' },
      { icon: '🔮', label: 'Google' },
      { icon: '☁️', label: 'Azure' },
    ],
    color: BRAND_COLORS.amber,
  },
  {
    name: 'Agent',
    nodes: [
      { icon: '👥', label: 'CrewAI' },
      { icon: '🔗', label: 'LangChain' },
      { icon: '🤝', label: 'Multi-Agent' },
    ],
    color: BRAND_COLORS.pink,
  },
  {
    name: 'Storage',
    nodes: [
      { icon: '🗄️', label: 'Vector DB' },
      { icon: '💾', label: 'S3' },
      { icon: '📊', label: 'PostgreSQL' },
      { icon: '📁', label: 'Drive' },
    ],
    color: BRAND_COLORS.cyan,
  },
  {
    name: 'Processing',
    nodes: [
      { icon: '✂️', label: 'Chunk' },
      { icon: '👁️', label: 'OCR' },
      { icon: '🎤', label: 'Transcribe' },
      { icon: '🔤', label: 'NLP' },
    ],
    color: BRAND_COLORS.purple,
  },
];

export const NodeLibrary: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  // Palette opens
  const paletteScale = spring({
    frame: Math.max(0, frame - 0),
    fps: 30,
    config: { damping: 10, stiffness: 100 },
    from: 0.8,
    to: 1,
  });

  const paletteOpacity = interpolate(
    frame,
    [0, 30],
    [0, 1],
    { extrapolateRight: 'clamp' }
  );

  // Categories expand
  const categoryExpansion = interpolate(
    frame,
    [30, 90],
    [0, 1],
    { extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  // Nodes animate in
  const nodeAnimationStart = 60;
  const nodeDelay = 5;

  // Hover effect (on last node)
  const hoverFrame = 180;
  const hoverScale = interpolate(
    frame,
    [hoverFrame, hoverFrame + 15, hoverFrame + 30, hoverFrame + 45],
    [1, 1.15, 1.1, 1],
    { extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) }
  );

  const hoverGlow = interpolate(
    frame,
    [hoverFrame, hoverFrame + 15, hoverFrame + 30, hoverFrame + 45],
    [0, 1, 0.8, 0],
    { extrapolateRight: 'clamp' }
  );

  // Drag preview
  const dragProgress = interpolate(
    frame,
    [210, 240],
    [0, 1],
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
            linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
        }}
      />

      {/* Node Palette Container */}
      <div
        style={{
          width: '100%',
          height: '100%',
          background: BRAND_COLORS.darkCard,
          borderRadius: 16,
          border: `2px solid rgba(255, 255, 255, 0.1)`,
          padding: 30,
          opacity: paletteOpacity,
          transform: `scale(${paletteScale})`,
        }}
      >
        <div
          style={{
            fontSize: 24,
            fontWeight: 700,
            marginBottom: 30,
            color: BRAND_COLORS.amber,
          }}
        >
          Node Library
        </div>

        {/* Categories */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {NODE_CATEGORIES.map((category, catIndex) => {
            const categoryDelay = 30 + catIndex * 15;
            const categoryOpacity = interpolate(
              frame,
              [categoryDelay, categoryDelay + 20],
              [0, 1],
              { extrapolateRight: 'clamp' }
            );

            const categoryHeight = spring({
              frame: Math.max(0, frame - categoryDelay),
              fps: 30,
              config: { damping: 10, stiffness: 100 },
              from: 0,
              to: 1,
            });

            return (
              <div
                key={category.name}
                style={{
                  opacity: categoryOpacity,
                  overflow: 'hidden',
                  height: `${categoryHeight * 100}%`,
                }}
              >
                {/* Category Header */}
                <div
                  style={{
                    fontSize: 16,
                    fontWeight: 600,
                    color: category.color,
                    marginBottom: 12,
                    paddingBottom: 8,
                    borderBottom: `1px solid ${category.color}40`,
                  }}
                >
                  {category.name}
                </div>

                {/* Nodes Grid */}
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(4, 1fr)',
                    gap: 12,
                  }}
                >
                  {category.nodes.map((node, nodeIndex) => {
                    const globalNodeIndex =
                      NODE_CATEGORIES.slice(0, catIndex).reduce(
                        (sum, cat) => sum + cat.nodes.length,
                        0
                      ) + nodeIndex;

                    const nodeDelay = nodeAnimationStart + globalNodeIndex * nodeDelay;
                    const nodeOpacity = interpolate(
                      frame,
                      [nodeDelay, nodeDelay + 15],
                      [0, 1],
                      { extrapolateRight: 'clamp' }
                    );

                    const nodeScale = spring({
                      frame: Math.max(0, frame - nodeDelay),
                      fps: 30,
                      config: { damping: 15, stiffness: 200 },
                      from: 0,
                      to: 1,
                    });

                    const isHovered =
                      frame >= hoverFrame &&
                      frame < hoverFrame + 60 &&
                      globalNodeIndex === NODE_CATEGORIES.reduce(
                        (sum, cat) => sum + cat.nodes.length,
                        0
                      ) - 1;

                    return (
                      <div
                        key={node.label}
                        style={{
                          background: BRAND_COLORS.darkCard,
                          borderRadius: 10,
                          padding: 16,
                          border: `2px solid ${category.color}40`,
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          gap: 8,
                          opacity: nodeOpacity,
                          transform: `scale(${
                            isHovered ? hoverScale : nodeScale
                          })`,
                          boxShadow:
                            isHovered && hoverGlow > 0
                              ? `0 0 20px ${category.color}${Math.floor(
                                  hoverGlow * 255
                                ).toString(16)}`
                              : 'none',
                          transition: 'all 0.3s',
                          cursor: 'pointer',
                        }}
                      >
                        <div style={{ fontSize: 32 }}>{node.icon}</div>
                        <div style={{ fontSize: 12, fontWeight: 500 }}>
                          {node.label}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>

        {/* Drag Preview */}
        {frame >= 210 && (
          <AbsoluteFill
            style={{
              pointerEvents: 'none',
              left: width / 2,
              top: height / 2,
              transform: `translate(-50%, -50%) translateY(${-100 * (1 - dragProgress)}px)`,
              opacity: dragProgress,
            }}
          >
            <div
              style={{
                background: BRAND_COLORS.darkCard,
                borderRadius: 10,
                padding: 16,
                border: `2px solid ${BRAND_COLORS.amber}`,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 8,
                boxShadow: `0 0 30px ${BRAND_COLORS.amber}40`,
              }}
            >
              <div style={{ fontSize: 32 }}>🤖</div>
              <div style={{ fontSize: 12, fontWeight: 500 }}>OpenAI</div>
            </div>
          </AbsoluteFill>
        )}
      </div>
    </AbsoluteFill>
  );
};
