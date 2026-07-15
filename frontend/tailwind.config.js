/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{svelte,js}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { opacity: '0', transform: 'translateY(10px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        slideDown: { '0%': { opacity: '0', transform: 'translateY(-10px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        scaleIn: { '0%': { opacity: '0', transform: 'scale(0.95)' }, '100%': { opacity: '1', transform: 'scale(1)' } },
      },
    },
  },
  plugins: [require('daisyui')],
  daisyui: {
    themes: [
      {
        dark: {
          'primary': '#6366f1',
          'primary-content': '#ffffff',
          'secondary': '#8b5cf6',
          'secondary-content': '#ffffff',
          'accent': '#06b6d4',
          'accent-content': '#ffffff',
          'neutral': '#1e1e2e',
          'neutral-content': '#cdd6f4',
          'base-100': '#11111b',
          'base-200': '#181825',
          'base-300': '#1e1e2e',
          'base-content': '#cdd6f4',
          'info': '#3498db',
          'success': '#2ecc71',
          'warning': '#f39c12',
          'error': '#e74c3c',
        },
        light: {
          'primary': '#6366f1',
          'primary-content': '#ffffff',
          'secondary': '#8b5cf6',
          'accent': '#06b6d4',
          'neutral': '#e2e8f0',
          'neutral-content': '#334155',
          'base-100': '#ffffff',
          'base-200': '#f8fafc',
          'base-300': '#e2e8f0',
          'base-content': '#334155',
          'info': '#3498db',
          'success': '#2ecc71',
          'warning': '#f39c12',
          'error': '#e74c3c',
        },
      },
    ],
  },
};
