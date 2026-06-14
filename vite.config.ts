import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Renderer는 Electron file:// 로딩을 위해 상대경로 base 사용
export default defineConfig({
  root: "src",
  base: "./",
  plugins: [react()],
  build: {
    outDir: "../dist",
    emptyOutDir: true,
  },
  server: {
    port: 5173,
  },
});
