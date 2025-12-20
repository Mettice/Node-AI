/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: {
          DEFAULT: '#06080d',
          surface: '#0d1117',
          elevated: '#161b22',
        },
        accent: {
          DEFAULT: '#f0b429',
          light: '#fbbf24',
          dark: '#d97706',
        },
        glass: {
          bg: 'rgba(13, 17, 23, 0.75)',
          light: 'rgba(13, 17, 23, 0.6)',
          strong: 'rgba(13, 17, 23, 0.92)',
          border: 'rgba(255, 255, 255, 0.08)',
        },
        node: {
          input: '#22d3ee',
          processing: '#fb923c',
          embedding: '#a78bfa',
          storage: '#34d399',
          retrieval: '#60a5fa',
          llm: '#f0b429',
          agent: '#f472b6',
        },
        status: {
          idle: '#64748b',
          pending: '#fbbf24',
          running: '#3b82f6',
          completed: '#22c55e',
          failed: '#ef4444',
        },
      },
      backdropBlur: {
        xs: '4px',
        lg: '20px',
        xl: '32px',
      },
      borderRadius: {
        sm: '6px',
        md: '10px',
        lg: '14px',
        xl: '18px',
      },
      animation: {
        'breathing': 'breathing 3s ease-in-out infinite',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
      },
      keyframes: {
        breathing: {
          '0%, 100%': { opacity: '0.85', transform: 'scale(1)' },
          '50%': { opacity: '1', transform: 'scale(1.02)' },
        },
        glowPulse: {
          '0%, 100%': { opacity: '0.6' },
          '50%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}