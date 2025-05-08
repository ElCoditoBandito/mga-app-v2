/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}', // Main one for us
    "./index.html",         // For Vite
  ],
  prefix: "",
  theme: {
    container: { /* ... */ },
    extend: {
      colors: { /* ... */ },
      borderRadius: { /* ... */ },
      keyframes: { /* ... */ },
      animation: { /* ... */ },
    },
  },
  plugins: [require("tailwindcss-animate")],
}