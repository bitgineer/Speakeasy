/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/renderer/**/*.{js,ts,jsx,tsx,html}'],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-ui)'],
        mono: ['var(--font-mono)']
      },
      fontSize: {
        page: 'var(--text-page)',
        heading: 'var(--text-heading)',
        body: 'var(--text-body)',
        ui: 'var(--text-ui)',
        small: 'var(--text-small)',
        caption: 'var(--text-caption)',
        label: 'var(--text-label)'
      },
      borderRadius: {
        xs: 'var(--radius-xs)',
        control: 'var(--radius-control)',
        panel: 'var(--radius-panel)',
        pill: 'var(--radius-pill)'
      },
      transitionDuration: {
        fast: 'var(--motion-fast)',
        base: 'var(--motion-base)'
      },
      transitionTimingFunction: {
        standard: 'var(--ease-standard)'
      },
      colors: {
        surface: {
          canvas: 'var(--surface-canvas)',
          sidebar: 'var(--surface-sidebar)',
          panel: 'var(--surface-panel)',
          raised: 'var(--surface-raised)',
          sunken: 'var(--surface-sunken)',
          input: 'var(--surface-input)',
          hover: 'var(--surface-hover)',
          selected: 'var(--surface-selected)',
          scrim: 'var(--surface-scrim)'
        },
        content: {
          primary: 'var(--text-primary)',
          secondary: 'var(--text-secondary)',
          muted: 'var(--text-muted)',
          faint: 'var(--text-faint)'
        },
        edge: {
          subtle: 'var(--border-subtle)',
          DEFAULT: 'var(--border-default)',
          control: 'var(--border-control)',
          strong: 'var(--border-strong)'
        },
        accent: {
          solid: 'var(--accent-solid)',
          'solid-hover': 'var(--accent-solid-hover)',
          'solid-active': 'var(--accent-solid-active)',
          'on-solid': 'var(--accent-on-solid)',
          text: 'var(--accent-text)',
          muted: 'var(--accent-muted)',
          border: 'var(--accent-border)'
        },
        success: {
          text: 'var(--success-text)',
          solid: 'var(--success-solid)',
          muted: 'var(--success-muted)',
          border: 'var(--success-border)'
        },
        warning: {
          text: 'var(--warning-text)',
          solid: 'var(--warning-solid)',
          muted: 'var(--warning-muted)',
          border: 'var(--warning-border)'
        },
        danger: {
          text: 'var(--danger-text)',
          solid: 'var(--danger-solid)',
          muted: 'var(--danger-muted)',
          border: 'var(--danger-border)'
        },
        focus: 'var(--focus)'
      }
    }
  },
  plugins: []
}
