import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [tailwindcss()],
  base: '/wolf/',
  server: {
    host: '0.0.0.0',
    port: 5173,
  },
})
