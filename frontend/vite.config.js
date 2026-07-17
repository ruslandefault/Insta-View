import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // /api so'rovlarini FastAPI backendga yo'naltirish
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
