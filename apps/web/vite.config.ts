/// <reference types="vitest" />
import { defineConfig } from "vitest/config";

export default defineConfig({
  root: ".",
  build: {
    outDir: "dist",
    emptyOutDir: true,
    sourcemap: true,
    target: "es2022",
  },
  server: {
    port: 5173,
    strictPort: true,
  },
  test: {
    environment: "jsdom",
    globals: true,
    include: ["src/**/__tests__/**/*.test.ts"],
  },
});
