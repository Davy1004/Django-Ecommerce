import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-body)"],
        display: ["var(--font-display)"],
      },
      colors: {
        brand: {
          50: "#fdf8f0",
          100: "#f9edda",
          500: "#c8873a",
          600: "#b5722e",
          900: "#3d2008",
        },
        ink: "#1a1208",
      },
    },
  },
  plugins: [],
};
export default config;
