import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    strictPort: false,
    open: false,
    hmr: {
      clientPort: 8081
    },
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      'curriculumcurator.serveur.au',
      '.serveur.au'  // Allow any subdomain of serveur.au
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/docs': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/openapi.json': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
    css: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.js',
        '**/coverage/**',
        '**/dist/**'
      ]
    }
  }
})