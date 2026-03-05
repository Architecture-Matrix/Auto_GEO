/**
 * IPC 通信处理器
 * 我用这个来处理渲染进程和主进程之间的通信！
 */

import { ipcMain, shell, dialog } from 'electron'
import { getMainWindow, createAuthWindow, showNotification } from './window-manager'
import * as backendManager from './backend-manager'
import * as browserBridgeManager from './browser-bridge-manager'

// 允许的调用通道（白名单模式）
const INVOKE_CHANNELS = [
  'app:get-info',
  'app:get-version',
  'window:minimize',
  'window:maximize',
  'window:close',
  'shell:open-external',
  'dialog:open-file',
  'dialog:save-file',
  'auth:start',
  'backend:get-status',
  'backend:restart',
  'backend:get-config',
  'bridge:get-status',
  'bridge:restart',
  'bridge:get-config',
]

// 允许的发送通道
const SEND_CHANNELS = [
  'app:ready',
  'auth:check-status',
]

/**
 * 验证发送者（安全检查）
 * 我用这个来防止攻击！
 */
function validateSender(frame: any): boolean {
  if (!frame) return false
  try {
    const url = new URL(frame.url)
    const allowedProtocols = ['http:', 'https:', 'file:']
    return allowedProtocols.includes(url.protocol)
  } catch {
    return false
  }
}

/**
 * 注册所有 IPC 处理器
 */
export function registerHandlers(): void {
  // ==================== 应用相关 ====================

  ipcMain.handle('app:get-info', (event) => {
    if (!validateSender(event.senderFrame)) return null
    const { app } = require('electron')
    return {
      name: app.getName(),
      version: app.getVersion(),
      platform: process.platform,
      arch: process.arch,
    }
  })

  ipcMain.handle('app:get-version', (event) => {
    if (!validateSender(event.senderFrame)) return null
    return require('electron').app.getVersion()
  })

  // ==================== 窗口控制 ====================

  ipcMain.handle('window:minimize', (event) => {
    if (!validateSender(event.senderFrame)) return
    const win = getMainWindow()
    win?.minimize()
  })

  ipcMain.handle('window:maximize', (event) => {
    if (!validateSender(event.senderFrame)) return
    const win = getMainWindow()
    if (win?.isMaximized()) {
      win.unmaximize()
    } else {
      win?.maximize()
    }
  })

  ipcMain.handle('window:close', (event) => {
    if (!validateSender(event.senderFrame)) return
    const win = getMainWindow()
    win?.close()
  })

  // ==================== Shell 操作 ====================

  ipcMain.handle('shell:open-external', (event, url: string) => {
    if (!validateSender(event.senderFrame)) return
    shell.openExternal(url)
  })

  // ==================== 文件对话框 ====================

  ipcMain.handle('dialog:open-file', async (event, options: any) => {
    if (!validateSender(event.senderFrame)) return { canceled: true }
    const result = await dialog.showOpenDialog(options)
    return result
  })

  ipcMain.handle('dialog:save-file', async (event, options: any) => {
    if (!validateSender(event.senderFrame)) return { canceled: true }
    const result = await dialog.showSaveDialog(options)
    return result
  })

  // ==================== 授权相关 ====================

  ipcMain.handle('auth:start', (event, platformId: string, authUrl: string) => {
    if (!validateSender(event.senderFrame)) return
    const authWindow = createAuthWindow(platformId, authUrl)

    // 监听授权窗口关闭
    authWindow.on('closed', () => {
      // 通知渲染进程授权窗口已关闭
      const mainWin = getMainWindow()
      mainWin?.webContents.send('auth:window-closed', { platformId })
    })
  })

  // ==================== 消息通知 ====================

  ipcMain.on('show-notification', (event, title: string, body: string) => {
    showNotification(title, body)
  })

  // ==================== 后端管理相关 ====================

  /**
   * 获取后端状态
   */
  ipcMain.handle('backend:get-status', (event) => {
    if (!validateSender(event.senderFrame)) return { status: 'unknown' }
    return {
      status: backendManager.backendManager.getStatus(),
      pid: backendManager.backendManager['process']?.pid || null
    }
  })

  /**
   * 重启后端
   */
  ipcMain.handle('backend:restart', async (event) => {
    if (!validateSender(event.senderFrame)) return { success: false }
    const result = await backendManager.backendManager.restart()
    return { success: result }
  })

  /**
   * 获取后端配置
   */
  ipcMain.handle('backend:get-config', (event) => {
    if (!validateSender(event.senderFrame)) return null
    return backendManager.backendManager.getConfig()
  })

  // ==================== 浏览器桥接服务相关 ====================

  /**
   * 获取桥接服务状态
   */
  ipcMain.handle('bridge:get-status', (event) => {
    if (!validateSender(event.senderFrame)) return { status: 'unknown' }
    return {
      status: browserBridgeManager.browserBridgeManager.getStatus(),
      pid: browserBridgeManager.browserBridgeManager['process']?.pid || null
    }
  })

  /**
   * 重启桥接服务
   */
  ipcMain.handle('bridge:restart', async (event) => {
    if (!validateSender(event.senderFrame)) return { success: false }
    const result = await browserBridgeManager.browserBridgeManager.restart()
    return { success: result }
  })

  /**
   * 获取桥接服务配置
   */
  ipcMain.handle('bridge:get-config', (event) => {
    if (!validateSender(event.senderFrame)) return null
    return browserBridgeManager.browserBridgeManager.getConfig()
  })

  // 提示：未注册的通道会被拒绝，安全第一！
  ipcMain.handle('unknown-channel', () => {
    throw new Error('Unknown IPC channel')
  })
}

/**
 * 发送消息到渲染进程
 */
export function sendToRenderer(channel: string, ...args: any[]): void {
  const win = getMainWindow()
  win?.webContents.send(channel, ...args)
}
