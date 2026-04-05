import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["Roboto Mono", "monospace"],
        headline: ["Inter", "sans-serif"],
        body: ["Inter", "sans-serif"],
        label: ["Inter", "sans-serif"],
      },
      colors: {
        // Design System Colors
        background: "#020617",
        sidebar: "#020617",
        card: "#0f172a",
        accent: "#22c55e",
        // Premium Dashboard Colors
        surface: "#131315",
        "surface-container": "#201f22",
        "surface-container-low": "#1c1b1d",
        "surface-container-high": "#2a2a2c",
        "surface-container-highest": "#353437",
        "surface-dim": "#131315",
        "surface-bright": "#39393b",
        "on-surface": "#e5e1e4",
        "on-surface-variant": "#c2c6d6",
        "primary": "#adc6ff",
        "primary-container": "#4d8eff",
        "primary-fixed": "#d8e2ff",
        "on-primary": "#002e6a",
        "outline-variant": "#424754",
        "secondary": "#4edea3",
        "secondary-container": "#00a572",
        "secondary-fixed": "#6ffbbe",
        "on-secondary": "#003824",
        "tertiary": "#ffb3ad",
        "tertiary-container": "#ff5451",
        "tertiary-fixed": "#ffdad7",
        "on-tertiary": "#68000a",
      },
      animation: {
        'spin': 'spin 1s linear infinite',
        'pulse': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce': 'bounce 1s infinite',
        'in': 'fadeIn 0.3s ease-in',
        'out': 'fadeOut 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeOut: {
          '0%': { opacity: '1' },
          '100%': { opacity: '0' },
        },
      },
      backdropBlur: {
        'xl': '20px',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
        'emerald-glow': '0 0 30px rgba(16, 185, 129, 0.3)',
        'red-glow': '0 0 30px rgba(239, 68, 68, 0.3)',
      },
    },
  },
  plugins: [],
};

export default config;

