/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/renderer/**/*.{js,ts,jsx,tsx,html}'],
  darkMode: 'class',
  theme: {
    extend: {
      // Font family - mapped from CSS variables
      fontFamily: {
        sans: ['var(--font-family-geist)'],
        mono: ['var(--font-family-mono)']
      },
      colors: {
        // Brand colors - mapped from CSS variables
        primary: {
          50: 'var(--color-primary-50)',
          100: 'var(--color-primary-100)',
          200: 'var(--color-primary-200)',
          300: 'var(--color-primary-300)',
          400: 'var(--color-primary-400)',
          500: 'var(--color-primary-500)',
          600: 'var(--color-primary-600)',
          700: 'var(--color-primary-700)',
          800: 'var(--color-primary-800)',
          900: 'var(--color-primary-900)',
          950: 'var(--color-primary-950)'
        },
        // Background colors - mapped from CSS variables
        bg: {
          primary: 'var(--color-bg-primary)',
          secondary: 'var(--color-bg-secondary)',
          tertiary: 'var(--color-bg-tertiary)',
          elevated: 'var(--color-bg-elevated)'
        },
        // Border colors - mapped from CSS variables
        border: {
          subtle: 'var(--color-border-subtle)',
          DEFAULT: 'var(--color-border-default)',
          strong: 'var(--color-border-strong)'
        },
        // Semantic colors - mapped from CSS variables
        success: {
          50: 'var(--color-success-50)',
          100: 'var(--color-success-100)',
          200: 'var(--color-success-200)',
          300: 'var(--color-success-300)',
          400: 'var(--color-success-400)',
          500: 'var(--color-success-500)',
          600: 'var(--color-success-600)',
          700: 'var(--color-success-700)',
          800: 'var(--color-success-800)',
          900: 'var(--color-success-900)',
          950: 'var(--color-success-950)'
        },
        warning: {
          50: 'var(--color-warning-50)',
          100: 'var(--color-warning-100)',
          200: 'var(--color-warning-200)',
          300: 'var(--color-warning-300)',
          400: 'var(--color-warning-400)',
          500: 'var(--color-warning-500)',
          600: 'var(--color-warning-600)',
          700: 'var(--color-warning-700)',
          800: 'var(--color-warning-800)',
          900: 'var(--color-warning-900)',
          950: 'var(--color-warning-950)'
        },
        error: {
          50: 'var(--color-error-50)',
          100: 'var(--color-error-100)',
          200: 'var(--color-error-200)',
          300: 'var(--color-error-300)',
          400: 'var(--color-error-400)',
          500: 'var(--color-error-500)',
          600: 'var(--color-error-600)',
          700: 'var(--color-error-700)',
          800: 'var(--color-error-800)',
          900: 'var(--color-error-900)',
          950: 'var(--color-error-950)'
        },
        info: {
          50: 'var(--color-info-50)',
          100: 'var(--color-info-100)',
          200: 'var(--color-info-200)',
          300: 'var(--color-info-300)',
          400: 'var(--color-info-400)',
          500: 'var(--color-info-500)',
          600: 'var(--color-info-600)',
          700: 'var(--color-info-700)',
          800: 'var(--color-info-800)',
          900: 'var(--color-info-900)',
          950: 'var(--color-info-950)'
        }
      },
      // Spacing tokens - mapped from CSS variables (keep Tailwind defaults for compatibility)
      spacing: {
        'token-xs': 'var(--spacing-xs)',
        'token-sm': 'var(--spacing-sm)',
        'token-md': 'var(--spacing-md)',
        'token-lg': 'var(--spacing-lg)',
        'token-xl': 'var(--spacing-xl)',
        'token-2xl': 'var(--spacing-2xl)',
        'token-3xl': 'var(--spacing-3xl)'
      },
      // Typography tokens - mapped from CSS variables
      fontSize: {
        'token-xs': 'var(--font-size-xs)',
        'token-sm': 'var(--font-size-sm)',
        'token-base': 'var(--font-size-base)',
        'token-lg': 'var(--font-size-lg)',
        'token-xl': 'var(--font-size-xl)',
        'token-2xl': 'var(--font-size-2xl)',
        'token-3xl': 'var(--font-size-3xl)',
        'token-4xl': 'var(--font-size-4xl)',
        'token-5xl': 'var(--font-size-5xl)'
      },
      fontWeight: {
        'token-regular': 'var(--font-weight-regular)',
        'token-medium': 'var(--font-weight-medium)',
        'token-semibold': 'var(--font-weight-semibold)'
      },
      lineHeight: {
        'token-tight': 'var(--line-height-tight)',
        'token-normal': 'var(--line-height-normal)',
        'token-label': 'var(--line-height-label)'
      },
      // Shadow tokens - mapped from CSS variables
      boxShadow: {
        sm: 'var(--shadow-sm)',
        md: 'var(--shadow-md)',
        lg: 'var(--shadow-lg)',
        inner: 'var(--shadow-inner)',
        focus: 'var(--shadow-focus)'
      },
      // Border radius tokens - mapped from CSS variables
      borderRadius: {
        'token-sm': 'var(--radius-sm)',
        'token-md': 'var(--radius-md)',
        'token-lg': 'var(--radius-lg)',
        'token-xl': 'var(--radius-xl)'
      },
      // Transition tokens - mapped from CSS variables
      transitionDuration: {
        'token-fast': 'var(--transition-duration-fast)',
        'token-default': 'var(--transition-duration-default)',
        'token-slow': 'var(--transition-duration-slow)'
      },
      transitionTimingFunction: {
        spring: 'var(--transition-easing)'
      },
      animation: {
        'pulse-recording': 'pulse-recording 1.5s ease-in-out infinite'
      },
      keyframes: {
        'pulse-recording': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' }
        }
      }
    }
  },
  plugins: []
}
