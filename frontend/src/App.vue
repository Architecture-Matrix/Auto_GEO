<template>
  <el-config-provider :locale="zhCn">
    <!-- 启动画面 -->
    <SplashScreen
      :visible="showSplash"
      :version="appVersion"
      :loading="isLoading"
      :progress="loadingProgress"
      :status-text="loadingStatus"
      :error="loadingError"
      :ready="isReady"
      :is-first-run="isFirstRun"
      @retry="checkBackendHealth"
    />
    <router-view />
  </el-config-provider>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import SplashScreen from './components/common/SplashScreen.vue'
import { ElNotification } from 'element-plus'

// ==================== 常量配置 ====================
const APP_VERSION = '3.1.3'  // 与 package.json 保持同步
const HEALTH_CHECK_URL = 'http://127.0.0.1:8001/api/health'
const HEALTH_CHECK_INTERVAL = 2000  // 健康检查间隔（毫秒）
const MAX_WAIT_TIME = 120000  // 最大等待时间（2分钟）
const FIRST_RUN_STORAGE_KEY = 'autogeo_first_run_v3'

// ==================== 状态管理 ====================
const showSplash = ref(true)  // 显示启动画面
const isLoading = ref(true)   // 正在加载
const loadingProgress = ref(0)  // 加载进度 0-100
const loadingStatus = ref('正在启动后端服务...')  // 状态文本
const loadingError = ref('')   // 错误信息
const isReady = ref(false)     // 后端就绪
const isFirstRun = ref(false)  // 是否首次运行

// 从 package.json 读取版本号（开发环境动态获取）
const appVersion = ref(APP_VERSION)

// ==================== 健康检查逻辑 ====================
let healthCheckTimer: NodeJS.Timeout | null = null
let healthCheckStartTime = 0

/**
 * 检查后端健康状态
 */
async function checkBackendHealth(): Promise<boolean> {
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 5000)  // 5秒超时

    const response = await fetch(HEALTH_CHECK_URL, {
      method: 'GET',
      signal: controller.signal
    })

    clearTimeout(timeoutId)
    return response.ok
  } catch {
    return false
  }
}

/**
 * 检查是否首次运行
 */
function checkFirstRun(): boolean {
  const firstRun = localStorage.getItem(FIRST_RUN_STORAGE_KEY)
  if (firstRun === null) {
    isFirstRun.value = true
    return true
  }
  return false
}

/**
 * 标记首次运行完成
 */
function markFirstRunComplete(): void {
  localStorage.setItem(FIRST_RUN_STORAGE_KEY, 'false')
  isFirstRun.value = false
}

/**
 * 更新加载进度
 */
function updateProgress(progress: number, status: string): void {
  loadingProgress.value = Math.min(progress, 100)
  loadingStatus.value = status
}

/**
 * 启动健康检查循环
 */
function startHealthCheck(): void {
  healthCheckStartTime = Date.now()
  let progressStage = 0

  healthCheckTimer = setInterval(async () => {
    const elapsed = Date.now() - healthCheckStartTime

    // 更新进度阶段
    if (elapsed > 10000 && progressStage < 1) {
      progressStage = 1
      updateProgress(20, '正在等待后端服务启动...')
    } else if (elapsed > 30000 && progressStage < 2) {
      progressStage = 2
      if (isFirstRun.value) {
        updateProgress(40, '正在初始化浏览器组件（首次运行，请耐心等待）...')
      } else {
        updateProgress(40, '正在连接后端服务...')
      }
    } else if (elapsed > 60000 && progressStage < 3) {
      progressStage = 3
      updateProgress(60, '正在验证服务状态...')
    } else if (elapsed > 90000 && progressStage < 4) {
      progressStage = 4
      updateProgress(80, '即将完成...')
    }

    // 检查健康状态
    const isHealthy = await checkBackendHealth()

    if (isHealthy) {
      // 健康检查通过
      clearInterval(healthCheckTimer!)
      onBackendReady()
    } else if (elapsed > MAX_WAIT_TIME) {
      // 超时
      clearInterval(healthCheckTimer!)
      loadingError.value = '后端服务启动超时，请确保后端服务正常运行'
      isLoading.value = false
    }
  }, HEALTH_CHECK_INTERVAL)
}

/**
 * 后端就绪处理
 */
function onBackendReady(): void {
  isReady.value = true
  isLoading.value = false
  loadingProgress.value = 100
  loadingStatus.value = '初始化完成！'

  // 如果是首次运行，标记完成并显示通知
  if (isFirstRun.value) {
    markFirstRunComplete()

    // 延迟关闭启动画面，让用户看到成功状态
    setTimeout(() => {
      showSplash.value = false

      ElNotification({
        title: '欢迎使用 AutoGeo!',
        message: '初始化完成，现在可以开始使用了',
        type: 'success',
        duration: 5000,
        position: 'top-right'
      })
    }, 2000)
  } else {
    // 非首次运行，快速关闭启动画面
    setTimeout(() => {
      showSplash.value = false
    }, 500)
  }
}

// ==================== 生命周期 ====================
onMounted(() => {
  // 检查是否首次运行
  checkFirstRun()

  // 开始健康检查
  startHealthCheck()

  // 获取实际版本号（从 package.json，如果可用）
  fetch('/version.json')
    .then(res => res.json())
    .then(data => {
      if (data.version) {
        appVersion.value = data.version
      }
    })
    .catch(() => {
      // 忽略错误，使用默认版本
    })
})

// 组件卸载时清理定时器
onUnmounted(() => {
  if (healthCheckTimer) {
    clearInterval(healthCheckTimer)
  }
})
</script>

<style>
/* 全局样式 */
html,
body,
#app {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

/* 暗色主题变量 */
:root {
  --bg-primary: #1e1e1e;
  --bg-secondary: #252526;
  --bg-tertiary: #2d2d30;
  --primary: #4a90e2;
  --success: #4caf50;
  --warning: #ff9800;
  --danger: #e53935;
  --text-primary: #ffffff;
  --text-secondary: #aaaaaa;
  --border: #3e3e42;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>
