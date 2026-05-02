import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'url'
import { dirname, resolve } from 'path'

const __dirname = dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [react()],
  // Sirve data/results/ desde la raiz del proyecto como archivos estáticos
  publicDir: resolve(__dirname, '../data'),
  server: {
    port: 5173,
    host: '0.0.0.0',
    fs: {
      allow: [resolve(__dirname, '..')],
    },
  },
})
