import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
export default defineConfig({
  publicDir: "../../private/assets",
  plugins: [react(), tailwindcss()],
  server: { proxy: { "/api": "http://127.0.0.1:3101" } },
  preview: { proxy: { "/api": "http://127.0.0.1:3101" } },
});
