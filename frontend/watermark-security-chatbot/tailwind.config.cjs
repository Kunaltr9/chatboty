module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0a0a0a',
        primary: '#6b5b95',
        secondary: '#feb236',
        accent: '#d64161',
      },
      gradientColorStops: {
        'primary': '#6b5b95',
        'secondary': '#feb236',
      },
      fontFamily: {
        sans: ['"Helvetica Neue"', 'Arial', 'sans-serif'],
        serif: ['Georgia', 'serif'],
      },
      spacing: {
        '128': '32rem',
        '144': '36rem',
      },
    },
  },
  plugins: [],
}