/**
 * Sistema de diseño MediMatch IA.
 * Paleta "ice": blancos y azules hielo. Los tonos 600–900 cumplen contraste
 * AA sobre blanco para texto; los 50–300 se usan en fondos y brillos.
 * @type {import('tailwindcss').Config}
 */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ice: {
          50: '#f5faff',
          100: '#eaf4ff',
          200: '#d6eaff',
          300: '#b5d9ff',
          400: '#84bfff',
          500: '#4d9bf2',
          600: '#1f6fd1',
          700: '#1a5aab',
          800: '#1a4a89',
          900: '#183d6e',
          950: '#0f2747',
        },
      },
      fontFamily: {
        sans: [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          '"SF Pro Text"',
          '"Segoe UI"',
          'Roboto',
          'sans-serif',
        ],
      },
      keyframes: {
        drift: {
          '0%': { transform: 'translate3d(0, 0, 0) scale(1)' },
          '100%': { transform: 'translate3d(4%, 6%, 0) scale(1.08)' },
        },
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        drift: 'drift 26s ease-in-out infinite alternate',
        'fade-up': 'fade-up 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) both',
      },
    },
  },
  plugins: [],
};
