import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        rf: {
          bg: "#111215",
          "bg-secondary": "#191A1E",
          surface: "#202126",
          crimson: "#9F1733",
          "crimson-hover": "#B51D3E",
          "crimson-muted": "#6D2233",
          border: "#34353A",
          text: "#E9E9EC",
          "text-secondary": "#92939A",
          "text-muted": "#696A72",
          // Semantic
          success: "#2E7D32",
          warning: "#C57B14",
          error: "#D32F2F",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
        mono: ["var(--font-mono)", "JetBrains Mono", "monospace"],
      },
      borderRadius: {
        DEFAULT: "6px",
        md: "6px",
        lg: "8px",
        xl: "10px",
      },
      transitionDuration: {
        DEFAULT: "150ms",
      },
    },
  },
  plugins: [],
};

export default config;
