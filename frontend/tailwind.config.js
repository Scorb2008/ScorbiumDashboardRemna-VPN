/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{svelte,js}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        bg: '#0d0d12',
        surface: {
          DEFAULT: '#16161d',
          2: '#1c1c24',
          3: '#24242d',
          4: '#2f2f39',
        },
        border: '#2a2a35',
        muted: '#8a8a9e',
        subtle: '#b0b0c0',
        accent: {
          DEFAULT: '#5b8def',
          hover: '#7aa3ff',
          muted: '#3a6bd0',
        },
        danger: {
          DEFAULT: '#ef4450',
          hover: '#ff5a65',
          muted: '#b8303a',
        },
        success: {
          DEFAULT: '#22c55e',
          hover: '#3dd977',
          muted: '#169445',
        },
        warning: {
          DEFAULT: '#eab308',
          hover: '#facc15',
          muted: '#a18408',
        },
        text: '#f0f0f2',
      },
      borderRadius: {
        'card': '14px',
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.2s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'slide-in-right': 'slideInRight 0.25s ease-out',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { opacity: '0', transform: 'translateY(6px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        scaleIn: { '0%': { opacity: '0', transform: 'scale(0.96)' }, '100%': { opacity: '1', transform: 'scale(1)' } },
        slideInRight: { '0%': { opacity: '0', transform: 'translateX(8px)' }, '100%': { opacity: '1', transform: 'translateX(0)' } },
        pulseGlow: { '0%, 100%': { opacity: '0.6' }, '50%': { opacity: '1' } },
      },
    },
  },
  plugins: [],
};
