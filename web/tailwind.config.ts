import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        midnight: '#0B0E14',
        panel: '#1a1f2e',
        cyan: '#3BC9DE',
        amber: '#F5A524',
        violet: '#B085F5',
      },
    },
  },
  plugins: [],
};
export default config;
