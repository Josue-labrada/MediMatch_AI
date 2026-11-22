import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Dentro de Docker (macOS/Windows) los archivos montados no siempre emiten
// eventos de cambio; el sondeo (polling) mantiene la recarga en caliente.
const usePolling = process.env.VITE_USE_POLLING === 'true';

// El navegador llama a /api en el mismo origen y Vite lo reenvía al backend:
// sin problemas de CORS y sin URLs fijas en el código del frontend.
const apiTarget = process.env.API_PROXY_TARGET ?? 'http://localhost:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    strictPort: true,
    watch: usePolling ? { usePolling: true, interval: 300 } : undefined,
    proxy: {
      '/api': { target: apiTarget, changeOrigin: true },
      '/health': { target: apiTarget, changeOrigin: true },
    },
  },
});
