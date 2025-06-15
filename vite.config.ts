import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  
  // Tauri expects a fixed port in development
  server: {
    port: 5173,
    strictPort: true,
    watch: {
      // Watch all files for hot reload
      ignored: ['**/src-tauri/**']
    }
  },

  // Enable source maps for debugging
  build: {
    sourcemap: true,
    // Tauri uses different output directory structure
    outDir: 'dist'
  },

  // Environment variables
  envPrefix: ['VITE_', 'TAURI_'],

  // Clear screen on reload
  clearScreen: false,
})
