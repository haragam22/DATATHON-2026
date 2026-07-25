import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    include: ['leaflet', 'react-leaflet'],
  },
  server: {
    proxy: {
      // Proxy all /server/... calls to the local Catalyst backend.
      // This eliminates CORS in dev — the browser always talks to localhost:5173.
      // In production the React SPA is hosted on Catalyst Slate and the function
      // is on the same Catalyst origin, so no proxy is needed.
      '/server': {
        target: 'http://localhost:3000',
        changeOrigin: true,
      },
    },
  },
})

