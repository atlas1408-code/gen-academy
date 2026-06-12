import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxy backend routes so the dev server is same-origin (no CORS; clean SSE).
const backend = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/status": backend,
      "/query": backend,
      "/ingest": backend,
      "/upload": backend,
    },
  },
});
