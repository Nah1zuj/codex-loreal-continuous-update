import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import runtime from '../runtime.json'

const loopback = '127.0.0.1'
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', 'TRACE_')
  return {
    plugins: [react()],
    server: {
      host: loopback,
      port: Number(env.TRACE_FRONTEND_PORT ?? runtime.frontend),
      strictPort: true,
      proxy: {
        '/api': `http://${loopback}:${env.TRACE_BACKEND_PORT ?? runtime.backend}`,
        '/local-voice': {
          target: `http://${loopback}:${env.TRACE_VOICE_PORT ?? runtime.voice}`,
          ws: true,
          rewrite: path => path.replace(/^\/local-voice/, '/voice'),
        },
      },
    },
  }
})
