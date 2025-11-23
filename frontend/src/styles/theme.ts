/**
 * Centralized Theme Configuration
 * Dark Glassmorphism Design System
 * 
 * This file contains all theme tokens for easy customization
 * Modify colors, effects, and styles here - changes propagate throughout the app
 */

// ============================================
// COLOR PALETTE - Alternative vibrant colors
// ============================================

export const theme = {
  // Canvas & Background
  canvas: {
    // Deep gradient background
    from: '#0a0a0f',      // Deep navy-black
    via: '#13111c',       // Purple-black
    to: '#1a1625',        // Darker purple
    
    // Grid/mesh color
    grid: 'rgba(139, 92, 246, 0.15)',
    gridGlow: 'rgba(139, 92, 246, 0.3)',
  },

  // Node Category Colors (Optimized for dark backgrounds)
  categories: {
    input: {
      main: '#a78bfa',      // Soft purple
      light: '#c4b5fd',     // Lighter purple
      dark: '#8b5cf6',      // Deeper purple
      glow: 'rgba(167, 139, 250, 0.4)',
      glassBg: 'rgba(167, 139, 250, 0.1)',
    },
    processing: {
      main: '#fb923c',      // Vibrant orange
      light: '#fdba74',     // Lighter orange
      dark: '#f97316',      // Deeper orange
      glow: 'rgba(251, 146, 60, 0.4)',
      glassBg: 'rgba(251, 146, 60, 0.1)',
    },
    embedding: {
      main: '#22d3ee',      // Bright cyan
      light: '#67e8f9',     // Lighter cyan
      dark: '#06b6d4',      // Deeper cyan
      glow: 'rgba(34, 211, 238, 0.4)',
      glassBg: 'rgba(34, 211, 238, 0.1)',
    },
    storage: {
      main: '#34d399',      // Emerald green
      light: '#6ee7b7',     // Lighter green
      dark: '#10b981',      // Deeper green
      glow: 'rgba(52, 211, 153, 0.4)',
      glassBg: 'rgba(52, 211, 153, 0.1)',
    },
    retrieval: {
      main: '#60a5fa',      // Sky blue
      light: '#93c5fd',     // Lighter blue
      dark: '#3b82f6',      // Deeper blue
      glow: 'rgba(96, 165, 250, 0.4)',
      glassBg: 'rgba(96, 165, 250, 0.1)',
    },
    llm: {
      main: '#f472b6',      // Hot pink
      light: '#f9a8d4',     // Lighter pink
      dark: '#ec4899',      // Deeper pink
      glow: 'rgba(244, 114, 182, 0.4)',
      glassBg: 'rgba(244, 114, 182, 0.1)',
    },
  },

  // Text Colors
  text: {
    primary: '#f8fafc',     // Off-white
    secondary: '#94a3b8',   // Slate gray
    tertiary: '#64748b',    // Darker slate
    muted: '#475569',       // Very muted
  },

  // Glassmorphism Effects (Medium intensity)
  glass: {
    background: 'rgba(30, 27, 45, 0.7)',
    backgroundLight: 'rgba(30, 27, 45, 0.5)',
    backgroundStrong: 'rgba(30, 27, 45, 0.85)',
    border: 'rgba(255, 255, 255, 0.1)',
    borderHover: 'rgba(255, 255, 255, 0.2)',
    shine: 'rgba(255, 255, 255, 0.05)',
    blur: '20px',
    blurLight: '12px',
    blurStrong: '32px',
  },

  // Shadows & Glows
  shadows: {
    card: '0 8px 32px rgba(0, 0, 0, 0.3)',
    cardHover: '0 12px 48px rgba(0, 0, 0, 0.4)',
    inner: 'inset 0 1px 0 rgba(255, 255, 255, 0.1)',
    glow: (color: string) => `0 0 20px ${color}, 0 0 40px ${color}20`,
  },

  // Animation speeds
  animation: {
    fast: '150ms',
    base: '300ms',
    slow: '500ms',
  },
} as const;

// ============================================
// UTILITY FUNCTIONS
// ============================================

/**
 * Get category color by name
 */
export function getCategoryColor(category: string) {
  const key = category as keyof typeof theme.categories;
  return theme.categories[key] || theme.categories.input;
}

/**
 * Get category glow for shadows
 */
export function getCategoryGlow(category: string) {
  const colors = getCategoryColor(category);
  return `0 0 20px ${colors.glow}, 0 0 40px ${colors.glow}`;
}

