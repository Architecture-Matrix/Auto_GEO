/**
 * Python 后端进程管理器
 * 我用这个来启动和管理 FastAPI 后端！
 * 支持两种模式：
 * 1. 打包模式：运行 PyInstaller 打包的 .exe
 * 2. 开发模式：直接运行 python main.py
 */

import { spawn, ChildProcess, execSync } from 'child_process'
import { join, dirname } from 'path'
import * as os from 'os'
import { app } from 'electron'
import { existsSync } from 'fs'

// 应用退出标志
let _isAppQuitting = false

export function setAppQuitting(): void {
  _isAppQuitting = true
}

function isAppQuitting(): boolean {
  return _isAppQuitting
}

// 后端配置
const BACKEND_CONFIG = {
  // 获取后端exe路径（打包模式）
  get backendExePath(): string | null {
    if (!app.isPackaged) return null
    // 打包环境：resources 目录下的 exe
    return join(process.resourcesPath, 'AutoGeoBackend.exe')
  },

  // 获取后端目录（开发环境和打包后都适用）
  get backendDir(): string {
    const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged
    if (isDev) {
      // 开发环境：backend 目录在项目根目录
      const currentDir = __dirname
      const rootDir = join(currentDir, '../../../..')
      return join(rootDir, 'backend')
    } else {
      // 生产环境：backend 在 resources 目录
      return join(process.resourcesPath, 'backend')
    }
  },

  // 获取静态文件目录（打包后单独存放）
  get staticDir(): string {
    if (app.isPackaged) {
      return join(process.resourcesPath, 'static')
    }
    return join(this.backendDir, 'static')
  },

  // Python 解释器路径
  get pythonPath(): string {
    // Windows: python.exe, Linux/Mac: python3
    return os.platform() === 'win32' ? 'python' : 'python3'
  },

  // 后端入口文件
  entryFile: 'main.py',

  // 后端地址
  host: '127.0.0.1',
  port: 8001,

  // 是否使用打包的exe（仅打包环境）
  get useExe(): boolean {
    const exePath = this.backendExePath
    return app.isPackaged && exePath !== null && existsSync(exePath)
  },

  // 健康检查 URL
  healthUrl(): string {
    return `http://${this.host}:${this.port}/api/health`
  }
}

// 后端状态
export type BackendStatus = 'stopped' | 'starting' | 'running' | 'error'

/**
 * 检查 Python 是否可用
 */
function checkPython(): boolean {
  try {
    const pythonCmd = os.platform() === 'win32' ? 'python' : 'python3'
    execSync(`${pythonCmd} --version`, { encoding: 'utf8', windowsHide: true })
    return true
  } catch {
    return false
  }
}

/**
 * 检查后端目录是否存在
 */
function checkBackendDir(): boolean {
  const mainPy = join(BACKEND_CONFIG.backendDir, BACKEND_CONFIG.entryFile)
  return existsSync(mainPy)
}

// 后端管理器类
class BackendManager {
  private process: ChildProcess | null = null
  private status: BackendStatus = 'stopped'
  private healthCheckTimer: NodeJS.Timeout | null = null
  private retryCount = 0
  private maxRetries = 3
  private startupTimer: NodeJS.Timeout | null = null

  /**
   * 启动后端进程
   */
  async start(): Promise<boolean> {
    if (this.status === 'running' || this.status === 'starting') {
      console.log('[BackendManager] 后端已在运行或启动中')
      return true
    }

    // 检查是否使用打包的exe
    if (BACKEND_CONFIG.useExe) {
      console.log('[BackendManager] 🚀 使用打包的后端exe...')
      return this.startExeMode()
    }

    // 开发模式：检查 Python
    if (!checkPython()) {
      console.error('[BackendManager] ❌ Python 不可用！请确保已安装 Python 3.10+')
      this.status = 'error'
      return false
    }

    // 检查后端目录
    if (!checkBackendDir()) {
      console.error('[BackendManager] ❌ 后端目录不存在！', BACKEND_CONFIG.backendDir)
      this.status = 'error'
      return false
    }

    console.log('[BackendManager] 🚀 正在启动后端（Python模式）...')
    this.status = 'starting'

    try {
      // 准备启动参数
      const pythonExe = BACKEND_CONFIG.pythonPath
      const backendDir = BACKEND_CONFIG.backendDir
      const entryFile = BACKEND_CONFIG.entryFile

      console.log('[BackendManager] 📂 后端目录:', backendDir)
      console.log('[BackendManager] 🐍 Python 命令:', pythonExe)

      // 启动 Python 进程
      this.process = spawn(pythonExe, [entryFile], {
        cwd: backendDir,
        shell: false,
        // 隐藏控制台窗口（生产环境用户不需要看到后端日志）
        // 开发时如需调试，临时改为 false
        windowsHide: app.isPackaged,
        env: {
          ...process.env,
          // 确保 Python 输出 UTF-8
          PYTHONIOENCODING: 'utf-8',
          // 确保浏览器窗口可见（Playwright）
          DISPLAY: process.env.DISPLAY || ':0'
        },
        // 标准输入/输出需要保留
        stdio: ['ignore', 'pipe', 'pipe']
      })

      const pid = this.process.pid
      console.log('[BackendManager] ✅ 后端进程已启动，PID:', pid)

      // 监听标准输出
      this.process.stdout?.on('data', (data) => {
        const msg = data.toString().trim()
        if (msg) console.log('[Backend-OUT]', msg)
      })

      // 监听错误输出
      this.process.stderr?.on('data', (data) => {
        const msg = data.toString().trim()
        if (msg) console.error('[Backend-ERR]', msg)
      })

      // 监听进程退出
      this.process.on('close', (code) => {
        console.log(`[BackendManager] ⛔ 后端进程退出，代码: ${code}`)
        this.status = 'stopped'
        this.stopHealthCheck()
        this.clearStartupTimer()

        // 如果是非正常退出且应用还在运行，尝试重启
        if (code !== 0 && code !== null && !isAppQuitting()) {
          if (this.retryCount < this.maxRetries) {
            this.retryCount++
            console.log(`[BackendManager] 🔄 尝试重启后端 (${this.retryCount}/${this.maxRetries})`)
            setTimeout(() => this.start(), 2000)
          } else {
            console.error('[BackendManager] ❌ 后端启动失败，已达到最大重试次数')
            this.status = 'error'
          }
        }
      })

      // 监听进程错误
      this.process.on('error', (err) => {
        console.error('[BackendManager] ❌ 进程错误:', err.message)
        this.status = 'error'
      })

      // 启动健康检查
      this.startHealthCheck()

      // 设置启动超时
      this.startupTimer = setTimeout(() => {
        if (this.status === 'starting') {
          console.warn('[BackendManager] ⚠️ 后端启动超时，可能需要检查配置')
        }
      }, 30000) // 30 秒超时

      return true
    } catch (error) {
      console.error('[BackendManager] ❌ 启动失败:', error)
      this.status = 'error'
      return false
    }
  }

  /**
   * 启动打包的exe模式
   */
  private async startExeMode(): Promise<boolean> {
    this.status = 'starting'

    const exePath = BACKEND_CONFIG.backendExePath
    console.log('[BackendManager] 📦 exe路径:', exePath)

    try {
      this.process = spawn(exePath!, {
        shell: false,
        // 隐藏控制台窗口（生产环境用户不需要看到后端日志）
        windowsHide: true,
        env: {
          ...process.env,
          PYTHONIOENCODING: 'utf-8',
        },
        stdio: ['ignore', 'pipe', 'pipe']
      })

      const pid = this.process.pid
      console.log('[BackendManager] ✅ 后端exe已启动，PID:', pid)

      // 监听输出
      this.process.stdout?.on('data', (data) => {
        const msg = data.toString().trim()
        if (msg) console.log('[Backend-Exe-OUT]', msg)
      })

      this.process.stderr?.on('data', (data) => {
        const msg = data.toString().trim()
        if (msg) console.error('[Backend-Exe-ERR]', msg)
      })

      this.process.on('close', (code) => {
        console.log(`[BackendManager] ⛔ exe进程退出，代码: ${code}`)
        this.status = 'stopped'
        this.stopHealthCheck()
      })

      this.startHealthCheck()

      // 超时检测
      this.startupTimer = setTimeout(() => {
        if (this.status === 'starting') {
          console.warn('[BackendManager] ⚠️ exe启动超时')
        }
      }, 30000)

      return true
    } catch (error) {
      console.error('[BackendManager] ❌ exe启动失败:', error)
      this.status = 'error'
      return false
    }
  }

  /**
   * 停止后端进程
   */
  stop(): void {
    console.log('[BackendManager] 🛑 正在停止后端...')

    this.clearStartupTimer()
    this.stopHealthCheck()

    if (this.process) {
      const pid = this.process.pid
      // Windows 下使用 taskkill 强制结束进程树（包括 Playwright 的浏览器）
      if (os.platform() === 'win32') {
        try {
          execSync(`taskkill /F /T /PID ${pid}`, { windowsHide: true })
          console.log('[BackendManager] ✅ 已强制结束后端进程树:', pid)
        } catch (e) {
          // 进程可能已经结束
          this.process.kill('SIGTERM')
        }
      } else {
        this.process.kill('SIGTERM')
      }

      this.process = null
    }

    this.status = 'stopped'
    this.retryCount = 0
  }

  /**
   * 重启后端
   */
  async restart(): Promise<boolean> {
    console.log('[BackendManager] 🔄 正在重启后端...')
    this.stop()
    await new Promise(resolve => setTimeout(resolve, 1500))
    return this.start()
  }

  /**
   * 获取后端状态
   */
  getStatus(): BackendStatus {
    return this.status
  }

  /**
   * 获取后端配置
   */
  getConfig() {
    return {
      backendDir: BACKEND_CONFIG.backendDir,
      pythonPath: BACKEND_CONFIG.pythonPath,
      entryFile: BACKEND_CONFIG.entryFile,
      host: BACKEND_CONFIG.host,
      port: BACKEND_CONFIG.port,
      healthUrl: BACKEND_CONFIG.healthUrl(),
      status: this.status,
      pid: this.process?.pid || null,
    }
  }

  /**
   * 启动健康检查
   */
  private startHealthCheck(): void {
    this.stopHealthCheck()

    // 延迟开始检查，给后端启动时间
    setTimeout(async () => {
      await this.checkHealth()
    }, 3000)

    // 定期检查
    this.healthCheckTimer = setInterval(async () => {
      await this.checkHealth()
    }, 10000) // 每 10 秒检查一次
  }

  /**
   * 停止健康检查
   */
  private stopHealthCheck(): void {
    if (this.healthCheckTimer) {
      clearInterval(this.healthCheckTimer)
      this.healthCheckTimer = null
    }
  }

  /**
   * 清除启动超时计时器
   */
  private clearStartupTimer(): void {
    if (this.startupTimer) {
      clearTimeout(this.startupTimer)
      this.startupTimer = null
    }
  }

  /**
   * 检查后端健康状态
   */
  private async checkHealth(): Promise<void> {
    try {
      const response = await fetch(BACKEND_CONFIG.healthUrl(), {
        method: 'GET',
        signal: AbortSignal.timeout(5000) // 5 秒超时
      })

      if (response.ok) {
        if (this.status === 'starting') {
          console.log('[BackendManager] ✅ 后端启动成功！健康检查通过')
          this.retryCount = 0
          this.clearStartupTimer()
        }
        this.status = 'running'
      } else {
        console.warn('[BackendManager] ⚠️ 健康检查失败:', response.status)
      }
    } catch (error) {
      // 静默处理网络错误，避免日志刷屏
      // console.debug('[BackendManager] 健康检查异常:', error)
    }
  }
}

// 导出单例
export const backendManager = new BackendManager()
