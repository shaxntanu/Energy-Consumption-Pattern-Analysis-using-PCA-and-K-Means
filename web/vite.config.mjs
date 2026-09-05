import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// @vitejs/plugin-react turns on the automatic JSX runtime. Without it Vite has
// no config, and esbuild then compiles every .jsx with the *classic* transform,
// which injects `React.createElement(...)` calls into each file. Most components
// here import only named hooks (`import { useState } from "react"`), so they
// never put the `React` namespace in scope — the first one React renders throws
// `React is not defined` and the page comes up blank.
//
// With the plugin active, JSX compiles through react/jsx-runtime instead, so a
// file needs `React` only if it references it explicitly (e.g. React.useState).
export default defineConfig({
  plugins: [react()],
});