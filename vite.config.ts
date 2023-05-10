import { defineConfig } from "vite";
import { resolve } from "path";
import react from "@vitejs/plugin-react-swc";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "^/api/.*": {
        target: "http://127.0.0.1:5000",
      },
      "^/public/.*": {
        target: "http://127.0.0.1:5000",
      },
    },
  },
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, "index.html"),
        register: resolve(__dirname, "registration.html"),
        login: resolve(__dirname, "login.html"),
        feedback: resolve(__dirname, "feedback.html"),
        booking: resolve(__dirname, "booking.html"),
      },
    },
    copyPublicDir: false,
  },
});
