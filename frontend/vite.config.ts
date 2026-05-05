import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    // Limite indicative au lieu de 500kB (les vendor chunks ont du mal à descendre sous)
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        // Code-splitting par groupe fonctionnel : améliore le cache navigateur
        // entre déploiements (un changement applicatif n'invalide pas les vendors)
        manualChunks: {
          'react-vendor':  ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor':     ['framer-motion', '@headlessui/react', '@heroicons/react'],
          'charts':        ['recharts', 'chart.js', 'react-chartjs-2'],
          'data-vendor':   ['@tanstack/react-query', '@tanstack/react-table', 'zustand'],
          'utils-vendor':  ['axios', 'date-fns'],
          'dnd-vendor':    ['@dnd-kit/core', '@dnd-kit/sortable', 'react-dropzone'],
        },
      },
    },
  },
})
