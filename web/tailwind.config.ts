import type { Config } from "tailwindcss";
import animate from "tailwindcss-animate";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        surface: "var(--surface)",
        "surface-2": "var(--surface-2)",
        ink: "var(--ink)",
        muted: "var(--muted)",
        line: "var(--line)",
        accent: "var(--accent)",
        "accent-strong": "var(--accent-strong)",
        "accent-soft": "var(--accent-soft)",
        "accent-text": "var(--accent-text)",
        clay: "var(--clay)",
        "clay-soft": "var(--clay-soft)",
        "clay-text": "var(--clay-text)",
        saguaro: "var(--saguaro)",
        "saguaro-soft": "var(--saguaro-soft)",
        "saguaro-text": "var(--saguaro-text)",
        amber: "var(--amber)",
        "amber-soft": "var(--amber-soft)",
        "amber-text": "var(--amber-text)",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "Georgia", "serif"],
      },
      borderRadius: { card: "12px" },
      boxShadow: { lift: "0 1px 2px rgba(15,27,45,.06), 0 6px 18px rgba(15,27,45,.08)" },
      keyframes: {
        "fade-in": { from: { opacity: "0" }, to: { opacity: "1" } },
        "slide-up": { from: { transform: "translateY(24px)", opacity: "0" }, to: { transform: "translateY(0)", opacity: "1" } },
      },
      animation: { "fade-in": "fade-in 180ms ease-out", "slide-up": "slide-up 220ms ease-out" },
    },
  },
  plugins: [animate],
};
export default config;
