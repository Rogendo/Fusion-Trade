/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        terminal: {
          bg: '#080d18',
          surface: '#0d1526',
          border: '#1a2840',
          muted: '#243454',
        },
      },
    },
  },
  plugins: [],
}
