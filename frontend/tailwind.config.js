/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        'dark-bg': '#121212',
        'dark-surface': '#1E1E1E',
        'dark-surface-2': '#262626',
      },
    },
  },
  plugins: [],
} 