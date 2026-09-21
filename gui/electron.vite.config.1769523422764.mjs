// electron.vite.config.ts
import { resolve } from "path";
import { defineConfig, externalizeDepsPlugin } from "electron-vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "tailwindcss";
import autoprefixer from "autoprefixer";
import { visualizer } from "rollup-plugin-visualizer";
var __electron_vite_injected_dirname = "/mnt/c/Users/Jack/Coding-Projects/SpeakEasy/gui";
var electron_vite_config_default = defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()],
    build: {
      rollupOptions: {
        input: {
          index: resolve(__electron_vite_injected_dirname, "src/main/index.ts")
        }
      }
    }
  },
  preload: {
    plugins: [externalizeDepsPlugin()],
    build: {
      rollupOptions: {
        input: {
          index: resolve(__electron_vite_injected_dirname, "src/preload/index.ts")
        }
      }
    }
  },
  renderer: {
    root: resolve(__electron_vite_injected_dirname, "src/renderer"),
    build: {
      rollupOptions: {
        input: {
          index: resolve(__electron_vite_injected_dirname, "src/renderer/index.html")
        },
        output: {
          manualChunks: {
            vendor: ["react", "react-dom", "react-router-dom", "zustand"],
            tanstack: ["@tanstack/react-virtual"]
          }
        },
        plugins: [
          visualizer({
            filename: resolve(__electron_vite_injected_dirname, "../out/renderer/stats.html"),
            title: "SpeakEasy Bundle Analysis",
            open: false,
            gzipSize: true,
            brotliSize: true
          })
        ]
      }
    },
    plugins: [react()],
    css: {
      postcss: {
        plugins: [tailwindcss, autoprefixer]
      }
    }
  }
});
export {
  electron_vite_config_default as default
};
