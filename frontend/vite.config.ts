import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// https://vitejs.dev/config/
export default defineConfig({
  // 使用相对路径，避免Electron打包后资源加载失败导致黑屏
  base: './',
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
      imports: ['vue', 'vue-router', 'pinia'],
      dts: 'src/types/auto-imports.d.ts',
    }),
    Components({
      resolvers: [ElementPlusResolver()],
      dts: 'src/types/components.d.ts',
    }),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    // 🌟 修复点 1：将 host 设为 0.0.0.0 以获得更好的本地兼容性
    host: '0.0.0.0', 
    port: 5173,
    strictPort: true, 
    proxy: {
      // 🌟 修复点 2：优化 API 代理配置
      '/api': {
        target: 'http://127.0.0.1:8001', // 确保指向 FastAPI 的实际端口
        changeOrigin: true,
        secure: false,
        // 🌟 修复点 3：显式指定路径改写规则
        // 我们的后端接口本身就带 /api 前缀，所以这里确保路径原封不动传递
        rewrite: (path) => path.replace(/^\/api/, '/api'),
        // 🌟 修复点 4：增加超时限制
        // 因为 AI 生成文章可能需要很久，防止 Vite 代理提前断开连接
        timeout: 600000, 
        proxyTimeout: 600000,
      },
      // 🌟 修复点 5：优化 WebSocket 代理
      '/ws': {
        target: 'ws://127.0.0.1:8001',
        ws: true,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'out/renderer',
    emptyOutDir: true,
    chunkSizeWarningLimit: 2000,
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'element-plus': ['element-plus', '@element-plus/icons-vue'],
          'echarts': ['echarts'],
          'editor': ['@wangeditor/editor', '@wangeditor/editor-for-vue', 'markdown-it'],
        },
      },
    },
  },
})