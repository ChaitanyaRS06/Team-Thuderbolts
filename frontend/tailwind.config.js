/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'uva-orange': '#E57200',
        'uva-blue': '#232D4B',
      }
    },
  },
  plugins: [],
}
