/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    'templates/*.html',
    'templates/registration/*.html',
    'mboard/templates/mboard/*.html',
    'mboard/templates/mboard/includes/*.html',
  ],
  safelist: [
    'text-base-100',
    'text-red-light',
    'text-green-light',
    'text-yellow-light', 
    'text-orange-light',
    'text-magenta-light',
    'text-blue-light',
    'bg-base-100',
    'bg-red-light',
    'bg-green-light',
    'bg-yellow-light', 
    'bg-magenta-light',
    'bg-orange-light',
    'bg-blue-light',
  ],
  theme: {
    extend: {},
    // Tailwind colors for Flexoki theme by Steph Ango. https://stephango.com/flexoki
    colors: {
      base: {
        black: '#100F0F',
        950: '#1C1B1A',
        900: '#282726',
        850: '#343331',
        800: '#403E3C',
        700: '#575653',
        600: '#6F6E69',
        500: '#878580',
        300: '#B7B5AC',
        200: '#CECDC3',
        150: '#DAD8CE',
        100: '#E6E4D9',
        50: '#F2F0E5',
        paper: '#FFFCF0',
      },
      red: {
        DEFAULT: '#AF3029',
        light: '#D14D41',
      },
      orange: {
        DEFAULT: '#BC5215',
        light: '#DA702C',
      },
      yellow: {
        DEFAULT: '#AD8301',
        light: '#D0A215',
      },
      green: {
        DEFAULT: '#66800B',
        light: '#879A39',
      },
      cyan: {
        DEFAULT: '#24837B',
        light: '#3AA99F',
      },
      blue: {
        DEFAULT: '#205EA6',
        light: '#4385BE',
      },
      purple: {
        DEFAULT: '#5E409D',
        light: '#8B7EC8',
      },
      magenta: {
        DEFAULT: '#A02F6F',
        light: '#CE5D97',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}

