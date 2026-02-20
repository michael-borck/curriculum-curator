import { resolve } from 'path'
import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import react from '@vitejs/plugin-react'
import tailwindcss from 'tailwindcss'
import autoprefixer from 'autoprefixer'

export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()]
  },
  preload: {
    plugins: [externalizeDepsPlugin()]
  },
  renderer: {
    root: resolve(__dirname, '../frontend'),
    build: {
      outDir: resolve(__dirname, 'out/renderer'),
      rollupOptions: {
        input: resolve(__dirname, '../frontend/index.html')
      }
    },
    resolve: {
      alias: {
        '@': resolve(__dirname, '../frontend/src')
      }
    },
    plugins: [react()],
    css: {
      postcss: {
        plugins: [
          tailwindcss({
            config: resolve(__dirname, '../frontend/tailwind.config.js')
          }),
          autoprefixer()
        ]
      }
    },
    server: {
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true
        },
        '/auth': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true
        },
        '/health': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true
        }
      }
    }
  }
})
