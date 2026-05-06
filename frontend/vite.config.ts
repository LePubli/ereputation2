import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/',
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
        manualChunks: undefined, // Désactivé pour éviter les problèmes de chargement
      },
    },
  },
})
