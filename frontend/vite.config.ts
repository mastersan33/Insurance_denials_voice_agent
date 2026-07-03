import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  build: {
    // Warn on chunks > 500 KB
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      output: {
        // Manual chunk splitting for optimal caching
        manualChunks: {
          // React core — changes rarely
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          // Data layer
          'vendor-query': ['@tanstack/react-query'],
          'vendor-state': ['zustand'],
          // Charts (large — keep separate)
          'vendor-charts': ['recharts', 'react-is'],
          // Animations
          'vendor-motion': ['framer-motion'],
          // Forms
          'vendor-forms': ['react-hook-form', '@hookform/resolvers', 'zod'],
          // Icons
          'vendor-icons': ['lucide-react'],
          // Date utils
          'vendor-date': ['date-fns'],
        },
      },
    },
  },
});
