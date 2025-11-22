/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dark theme base colors
        dark: {
          bg: '#0a0a0f',
          surface: '#1a1625',
          elevated: '#252034',
          border: 'rgba(255, 255, 255, 0.1)',
          text: '#f8fafc',
        },
        // Glass effect colors
        glass: {
          bg: 'rgba(30, 27, 45, 0.7)',
          light: 'rgba(30, 27, 45, 0.5)',
          strong: 'rgba(30, 27, 45, 0.85)',
          border: 'rgba(255, 255, 255, 0.1)',
        },
        // Node categories (vibrant for dark theme)
        node: {
          input: '#a78bfa',
          processing: '#fb923c',
          embedding: '#22d3ee',
          storage: '#34d399',
          retrieval: '#60a5fa',
          llm: '#f472b6',
        },
      },
      // Backdrop blur
      backdropBlur: {
        xs: '4px',
        sm: '8px',
        md: '12px',
        lg: '20px',
        xl: '32px',
      },
      spacing: {
        xs: '0.25rem',
        sm: '0.5rem',
        md: '1rem',
        lg: '1.5rem',
        xl: '2rem',
        '2xl': '3rem',
      },
      borderRadius: {
        sm: '0.25rem',
        md: '0.5rem',
        lg: '0.75rem',
        xl: '1rem',
      },
      transitionDuration: {
        fast: '150ms',
        base: '200ms',
        slow: '300ms',
      },
    },
  },
  plugins: [],
}

