/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        neifit: {
          bg: '#F6E7D8',
          coffee: '#7A4E2D',
          'coffee-dark': '#4B2E1F',
          'coffee-light': '#9C6E4A',
          green: '#5F8D4E',
          'green-dark': '#486E3A',
          'green-light': '#8CBF7B',
          pink: '#D98CA4',
          'pink-light': '#F7D6E0',
          cream: '#FFF8F2',
          card: '#FFF8F2'
        }
      },
      fontFamily: {
        sans: ['Inter', 'Nunito', 'sans-serif'],
        display: ['Poppins', 'Montserrat', 'sans-serif']
      }
    },
  },
  plugins: [],
}

