import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// Dev proxy so the React dev server (port 6173) can talk to the FastAPI
// backend (port 6409) without CORS friction in development. The proxy
// strips the `/api` prefix because the FastAPI app registers routes at
// `/api/<...>` directly.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  server: {
    host: true, // 绑 0.0.0.0，同时监听 IPv4 (127.0.0.1) 和 IPv6 ([::1])。macOS 上 Node 默认只绑 ::1。
    port: 6173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:6409",
        changeOrigin: true,
        ws: true,
      },
    },
  },
});
