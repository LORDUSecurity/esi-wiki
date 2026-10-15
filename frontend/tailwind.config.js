/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      // Values the design actually uses that aren't in the default opacity scale.
      opacity: {
        3: '0.03',
        6: '0.06',
        7: '0.07',
        8: '0.08',
        12: '0.12',
        16: '0.16',
        28: '0.28',
        97: '0.97',
      },
      colors: {
        ink: {
          950: '#05080F',
          900: '#080D18',
          800: '#0D1524',
          700: '#131E33',
          600: '#1B2942',
          500: '#27395A',
        },
        gold: {
          400: '#E8CE8E',
          500: '#D4AF67',
          600: '#C8A15A',
          700: '#A67F3C',
        },
        ivory: '#EDEFF5',
        muted: '#8E9CBA',
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', 'Georgia', 'serif'],
        sans: ['Manrope', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(212,175,103,.28), 0 24px 60px -24px rgba(0,0,0,.85)',
        card: '0 18px 40px -22px rgba(0,0,0,.9)',
      },
      keyframes: {
        kenburns: {
          '0%': { transform: 'scale(1.04) translate3d(0,0,0)' },
          '100%': { transform: 'scale(1.18) translate3d(-1.5%,-1.5%,0)' },
        },
        fadeUp: {
          '0%': { opacity: 0, transform: 'translateY(28px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
        fadeIn: { '0%': { opacity: 0 }, '100%': { opacity: 1 } },
        marquee: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        drift: {
          '0%,100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-12px)' },
        },
      },
      animation: {
        kenburns: 'kenburns 22s ease-out forwards',
        fadeUp: 'fadeUp .8s cubic-bezier(.22,.61,.36,1) forwards',
        fadeIn: 'fadeIn 1.2s ease forwards',
        marquee: 'marquee 38s linear infinite',
        drift: 'drift 7s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};
