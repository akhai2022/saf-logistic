import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      colors: {
        primary: {
          50: "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          DEFAULT: "#2563eb",
          600: "#2563eb",
          700: "#1d4ed8",
          dark: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
        },
        sidebar: "#0f172a",
        accent: {
          DEFAULT: "#0d9488",
          50: "#f0fdfa",
          100: "#ccfbf1",
          500: "#14b8a6",
          600: "#0d9488",
          700: "#0f766e",
        },
        success: { DEFAULT: "#16a34a", light: "#dcfce7", dark: "#166534" },
        warning: { DEFAULT: "#d97706", light: "#fef3c7", dark: "#92400e" },
        danger: { DEFAULT: "#dc2626", light: "#fee2e2", dark: "#991b1b" },
      },
      boxShadow: {
        card: "0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.06)",
        "card-hover": "0 4px 6px -1px rgb(0 0 0 / 0.08), 0 2px 4px -2px rgb(0 0 0 / 0.05)",
      },
    },
  },
  plugins: [],
};
export default config;
