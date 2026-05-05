/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      colors: {
        base:     '#06080f',
        surface:  '#0b0e1a',
        card:     '#0f1220',
        'card-hi':'#141828',
        rim:      '#1a2035',
        'rim-hi': '#2d3d6a',
        ink:      '#dde4f0',
        'ink-dim':'#909cba',
        'ink-off':'#606d8a',
        accent:   '#3d7fff',
        crit:     '#ff3d52',
        hi:       '#ff7340',
        med:      '#ffc107',
        safe:     '#22d48e',
        vuln:     '#a855f7',
      },
      animation: {
        'fade-up':   'fade-up 0.35s ease-out both',
        'fade-in':   'fade-in 0.25s ease-out both',
        'pulse-dot': 'pulse-dot 2.4s ease-in-out infinite',
        'scan':      'scan 3s linear infinite',
      },
      keyframes: {
        'fade-up': {
          from: { opacity: 0, transform: 'translateY(10px)' },
          to:   { opacity: 1, transform: 'translateY(0)' },
        },
        'fade-in': {
          from: { opacity: 0 },
          to:   { opacity: 1 },
        },
        'pulse-dot': {
          '0%, 100%': { opacity: 1 },
          '50%':      { opacity: 0.25 },
        },
        'scan': {
          from: { transform: 'translateY(-100%)' },
          to:   { transform: 'translateY(100vh)' },
        },
      },
    },
  },
  plugins: [],
}
