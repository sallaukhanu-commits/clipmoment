import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0e1015",
        surface: "#151925",
        surface2: "#1b2133",
        border: "#272e42",
        accent: { DEFAULT: "#7c5cff", hover: "#6a49f0", soft: "#7c5cff22" },
        muted: "#9aa3b8",
      },
      borderRadius: { xl: "0.9rem" },
    },
  },
  plugins: [],
};

export default config;
