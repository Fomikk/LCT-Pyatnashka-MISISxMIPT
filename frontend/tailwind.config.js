/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: '#0b0b0b',
          100: '#121212',
          200: '#1a1a1a',
        },
      },
    },
  },
  plugins: [],
}

