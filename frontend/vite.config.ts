import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        // ЛОКАЛЬНО шлём на Uvicorn на 8080
        target: process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8080',
        changeOrigin: true,
        secure: false,          // не проверять сертификаты, если вдруг https
        // rewrite не нужен — путь /api/... должен идти как есть
      },
    },
  },
})
