/**
 * NodeAI Theme Configuration
 * "Living Intelligence" Design System
 * 
 * A refined dark theme that feels alive and AI-native
 */

export const theme = {
  // ============================================
  // CANVAS & BACKGROUND
  // ============================================
  canvas: {
    // Base background - deep, rich dark
    bg: '#06080d',
    bgGradient: 'radial-gradient(ellipse at 50% 40%, #0d1117 0%, #06080d 70%)',
    
    // Grid - subtle dot pattern
    grid: 'rgba(255, 255, 255, 0.03)',
    gridSize: 24,
    
    // Ambient glows - creates depth and atmosphere
    ambientPrimary: 'rgba(240, 180, 41, 0.08)',    // Warm amber glow
    ambientSecondary: 'rgba(34, 211, 238, 0.06)',  // Cool cyan glow
    ambientTertiary: 'rgba(167, 139, 250, 0.05)',  // Soft purple glow
  },

  // ============================================
  // PRIMARY ACCENT - WARM AMBER
  // Represents AI/Intelligence throughout the app
  // ============================================
  accent: {
    primary: '#f0b429',
    primaryLight: '#fbbf24',
    primaryDark: '#d97706',
    primaryGlow: 'rgba(240, 180, 41, 0.4)',
    primaryGlowSubtle: 'rgba(240, 180, 41, 0.15)',
  },

  // ============================================
  // NODE CATEGORY COLORS
  // Each category has a distinct, purposeful color
  // ============================================
  categories: {
    // Input nodes - Cyan (data entry points)
    input: {
      main: '#22d3ee',
      light: '#67e8f9',
      dark: '#06b6d4',
      glow: 'rgba(34, 211, 238, 0.35)',
      glassBg: 'rgba(34, 211, 238, 0.08)',
      gradient: 'linear-gradient(135deg, rgba(34, 211, 238, 0.15) 0%, rgba(34, 211, 238, 0.05) 100%)',
    },
    // Processing nodes - Orange (transformation)
    processing: {
      main: '#fb923c',
      light: '#fdba74',
      dark: '#f97316',
      glow: 'rgba(251, 146, 60, 0.35)',
      glassBg: 'rgba(251, 146, 60, 0.08)',
      gradient: 'linear-gradient(135deg, rgba(251, 146, 60, 0.15) 0%, rgba(251, 146, 60, 0.05) 100%)',
    },
    // Embedding nodes - Purple (vectors/embeddings)
    embedding: {
      main: '#a78bfa',
      light: '#c4b5fd',
      dark: '#8b5cf6',
      glow: 'rgba(167, 139, 250, 0.35)',
      glassBg: 'rgba(167, 139, 250, 0.08)',
      gradient: 'linear-gradient(135deg, rgba(167, 139, 250, 0.15) 0%, rgba(167, 139, 250, 0.05) 100%)',
    },
    // Storage nodes - Emerald (persistence/database)
    storage: {
      main: '#34d399',
      light: '#6ee7b7',
      dark: '#10b981',
      glow: 'rgba(52, 211, 153, 0.35)',
      glassBg: 'rgba(52, 211, 153, 0.08)',
      gradient: 'linear-gradient(135deg, rgba(52, 211, 153, 0.15) 0%, rgba(52, 211, 153, 0.05) 100%)',
    },
    // Retrieval nodes - Blue (search/fetch)
    retrieval: {
      main: '#60a5fa',
      light: '#93c5fd',
      dark: '#3b82f6',
      glow: 'rgba(96, 165, 250, 0.35)',
      glassBg: 'rgba(96, 165, 250, 0.08)',
      gradient: 'linear-gradient(135deg, rgba(96, 165, 250, 0.15) 0%, rgba(96, 165, 250, 0.05) 100%)',
    },
    // LLM nodes - Amber (AI/intelligence - primary accent)
    llm: {
      main: '#f0b429',
      light: '#fbbf24',
      dark: '#d97706',
      glow: 'rgba(240, 180, 41, 0.4)',
      glassBg: 'rgba(240, 180, 41, 0.1)',
      gradient: 'linear-gradient(135deg, rgba(240, 180, 41, 0.2) 0%, rgba(240, 180, 41, 0.08) 100%)',
    },
    // Agent nodes - Pink (multi-agent systems)
    agent: {
      main: '#f472b6',
      light: '#f9a8d4',
      dark: '#ec4899',
      glow: 'rgba(244, 114, 182, 0.35)',
      glassBg: 'rgba(244, 114, 182, 0.08)',
      gradient: 'linear-gradient(135deg, rgba(244, 114, 182, 0.15) 0%, rgba(244, 114, 182, 0.05) 100%)',
    },
  },

  // ============================================
  // STATUS COLORS
  // Clear visual feedback for execution states
  // ============================================
  status: {
    idle: {
      color: '#64748b',
      glow: 'rgba(100, 116, 139, 0.2)',
      border: 'rgba(100, 116, 139, 0.3)',
    },
    pending: {
      color: '#fbbf24',
      glow: 'rgba(251, 191, 36, 0.4)',
      border: 'rgba(251, 191, 36, 0.5)',
    },
    running: {
      color: '#3b82f6',
      glow: 'rgba(59, 130, 246, 0.5)',
      border: 'rgba(59, 130, 246, 0.6)',
    },
    completed: {
      color: '#22c55e',
      glow: 'rgba(34, 197, 94, 0.4)',
      border: 'rgba(34, 197, 94, 0.5)',
    },
    failed: {
      color: '#ef4444',
      glow: 'rgba(239, 68, 68, 0.4)',
      border: 'rgba(239, 68, 68, 0.5)',
    },
  },

  // ============================================
  // TEXT COLORS
  // Hierarchy through opacity
  // ============================================
  text: {
    primary: 'rgba(255, 255, 255, 0.95)',
    secondary: 'rgba(255, 255, 255, 0.7)',
    tertiary: 'rgba(255, 255, 255, 0.5)',
    muted: 'rgba(255, 255, 255, 0.3)',
  },

  // ============================================
  // GLASS EFFECTS
  // Refined glassmorphism for depth
  // ============================================
  glass: {
    background: 'rgba(13, 17, 23, 0.85)',
    backgroundLight: 'rgba(13, 17, 23, 0.6)',
    backgroundNode: 'rgba(13, 17, 23, 0.75)',
    backgroundStrong: 'rgba(13, 17, 23, 0.92)',
    border: 'rgba(255, 255, 255, 0.08)',
    borderHover: 'rgba(255, 255, 255, 0.15)',
    borderActive: 'rgba(255, 255, 255, 0.2)',
    blur: '20px',
    blurLight: '12px',
    blurStrong: '32px',
  },

  // ============================================
  // SHADOWS & EFFECTS
  // Layered shadows for depth
  // ============================================
  shadows: {
    node: '0 4px 24px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.03)',
    nodeHover: '0 8px 32px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.06)',
    nodeSelected: '0 8px 32px rgba(59, 130, 246, 0.3), 0 0 0 2px rgba(59, 130, 246, 0.5)',
    card: '0 4px 16px rgba(0, 0, 0, 0.3)',
    cardHover: '0 8px 24px rgba(0, 0, 0, 0.4)',
    innerHighlight: 'inset 0 1px 0 rgba(255, 255, 255, 0.06)',
    glow: (color: string, intensity: number = 1) => 
      `0 0 ${20 * intensity}px ${color}, 0 0 ${40 * intensity}px ${color}`,
  },

  // ============================================
  // ANIMATION TIMING
  // Consistent, smooth animations
  // ============================================
  animation: {
    fast: '150ms',
    base: '250ms',
    slow: '400ms',
    breathing: '3s',
    flow: '2s',
    easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
  },

  // ============================================
  // BORDER RADIUS
  // Consistent rounded corners
  // ============================================
  radius: {
    sm: '6px',
    md: '10px',
    lg: '14px',
    xl: '18px',
    full: '9999px',
  },

  // ============================================
  // SPACING
  // Consistent spacing scale
  // ============================================
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
    '2xl': '32px',
  },
} as const;

// ============================================
// TYPE EXPORTS
// ============================================
export type ThemeCategory = keyof typeof theme.categories;
export type ThemeStatus = keyof typeof theme.status;

// ============================================
// UTILITY FUNCTIONS
// ============================================

/**
 * Get category color object by name
 */
export function getCategoryColor(category: string): typeof theme.categories[ThemeCategory] {
  const key = category as ThemeCategory;
  return theme.categories[key] || theme.categories.input;
}

/**
 * Get category glow shadow string
 */
export function getCategoryGlow(category: string, intensity: number = 1): string {
  const colors = getCategoryColor(category);
  return theme.shadows.glow(colors.glow, intensity);
}

/**
 * Get status color object by name
 */
export function getStatusColor(status: string): typeof theme.status[ThemeStatus] {
  const key = status as ThemeStatus;
  return theme.status[key] || theme.status.idle;
}

/**
 * Get node shadow based on state
 */
export function getNodeShadow(
  selected: boolean = false, 
  isActive: boolean = false,
  categoryColor?: string
): string {
  if (selected) return theme.shadows.nodeSelected;
  if (isActive && categoryColor) {
    return `${theme.shadows.node}, 0 0 30px ${categoryColor}40`;
  }
  return theme.shadows.node;
}