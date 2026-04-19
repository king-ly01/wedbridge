import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://api:8899',
        changeOrigin: true
      },
      '/worker': {
        target: 'http://worker:8898',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/worker/, '')
      }
    }
  }
})
