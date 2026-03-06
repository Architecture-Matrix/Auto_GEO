<template>
  <div class="splash-container" :class="{ 'splash-hidden': !visible }">
    <div class="splash-content">
      <!-- Logo/图标 -->
      <div class="splash-logo">
        <div class="logo-icon">
          <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="32" cy="32" r="30" stroke="currentColor" stroke-width="2" class="logo-ring"/>
            <path d="M32 12v40M22 22l20 20M42 22l-20 20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
      </div>

      <!-- 应用名称 -->
      <h1 class="splash-title">AutoGeo</h1>
      <p class="splash-subtitle">AI 智能多平台文章发布助手</p>

      <!-- 版本信息 -->
      <p class="splash-version">v{{ version }}</p>

      <!-- 加载进度 -->
      <div class="splash-progress" v-if="loading">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progress + '%' }"></div>
        </div>
        <p class="progress-text">{{ statusText }}</p>
      </div>

      <!-- 首次运行提示 -->
      <div class="splash-first-run" v-if="isFirstRun">
        <el-icon class="first-run-icon"><InfoFilled /></el-icon>
        <p>首次启动需要初始化浏览器组件，请稍候...</p>
        <p class="first-run-note">此过程仅需一次，大约需要 1-2 分钟</p>
      </div>

      <!-- 错误状态 -->
      <div class="splash-error" v-if="error">
        <el-icon class="error-icon"><CircleCloseFilled /></el-icon>
        <p class="error-title">启动失败</p>
        <p class="error-message">{{ error }}</p>
        <el-button type="primary" size="small" @click="retry">重试</el-button>
      </div>

      <!-- 成功状态 -->
      <div class="splash-success" v-if="ready">
        <el-icon class="success-icon"><CircleCheckFilled /></el-icon>
        <p>初始化完成！</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { InfoFilled, CircleCloseFilled, CircleCheckFilled } from '@element-plus/icons-vue'
import { ElNotification } from 'element-plus'

/** Props */
interface Props {
  visible?: boolean
  version?: string
  loading?: boolean
  progress?: number
  statusText?: string
  error?: string
  ready?: boolean
  isFirstRun?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  visible: true,
  version: '3.1.3',
  loading: false,
  progress: 0,
  statusText: '正在初始化...',
  error: '',
  ready: false,
  isFirstRun: false
})

/** Emits */
interface Emits {
  (e: 'retry'): void
}

const emit = defineEmits<Emits>()

/** 重试 */
function retry() {
  emit('retry')
}
</script>

<style scoped>
.splash-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  transition: opacity 0.5s ease, visibility 0.5s ease;
}

.splash-hidden {
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
}

.splash-content {
  text-align: center;
  color: var(--text-primary);
  animation: fadeIn 0.6s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Logo */
.splash-logo {
  margin-bottom: 2rem;
}

.logo-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto;
  color: var(--primary);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.05);
  }
}

.logo-ring {
  animation: spin 8s linear infinite;
  transform-origin: center;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 标题 */
.splash-title {
  font-size: 2.5rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  background: linear-gradient(135deg, #4a90e2 0%, #67b7dc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.splash-subtitle {
  font-size: 1rem;
  color: var(--text-secondary);
  margin: 0 0 2rem 0;
}

.splash-version {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0 0 3rem 0;
  opacity: 0.7;
}

/* 进度条 */
.splash-progress {
  width: 300px;
  max-width: 80vw;
  margin: 0 auto;
}

.progress-bar {
  height: 4px;
  background: var(--bg-tertiary);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 1rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4a90e2 0%, #67b7dc 100%);
  border-radius: 2px;
  transition: width 0.3s ease;
  position: relative;
}

.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.progress-text {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0;
}

/* 首次运行提示 */
.splash-first-run {
  margin-top: 2rem;
  padding: 1rem 1.5rem;
  background: rgba(74, 144, 226, 0.1);
  border: 1px solid rgba(74, 144, 226, 0.3);
  border-radius: 8px;
  display: inline-block;
}

.first-run-icon {
  font-size: 2rem;
  color: var(--primary);
  margin-bottom: 0.5rem;
}

.splash-first-run p {
  margin: 0.5rem 0;
  color: var(--text-secondary);
}

.first-run-note {
  font-size: 0.75rem;
  opacity: 0.7;
}

/* 错误状态 */
.splash-error {
  margin-top: 2rem;
  padding: 1.5rem;
  background: rgba(229, 57, 53, 0.1);
  border: 1px solid rgba(229, 57, 53, 0.3);
  border-radius: 8px;
}

.error-icon {
  font-size: 3rem;
  color: var(--danger);
  margin-bottom: 0.5rem;
}

.error-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0.5rem 0;
  color: var(--danger);
}

.error-message {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0.5rem 0 1rem 0;
}

/* 成功状态 */
.splash-success {
  margin-top: 2rem;
}

.success-icon {
  font-size: 3rem;
  color: var(--success);
  animation: successPop 0.5s ease-out;
}

@keyframes successPop {
  0% {
    transform: scale(0);
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
  }
}

.splash-success p {
  font-size: 1rem;
  color: var(--success);
  margin: 0.5rem 0 0 0;
}
</style>
