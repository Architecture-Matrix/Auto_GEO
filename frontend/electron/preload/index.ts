/**
 * Preload 脚本
 * 我用这个来安全地暴露 API 给渲染进程！
 */

import { contextBridge, ipcRenderer } from 'electron'

// 白名单通道（只能调用这些！）
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

const SEND_CHANNELS = [
  'show-notification',
]

// 监听通道（从主进程接收消息）
const ON_CHANNELS = [
  'auth:window-closed',
  'publish:progress',
  'publish:complete',
]

/**
 * 暴露给渲染进程的 API
 * 我用 contextBridge 安全隔离！
 */
const electronAPI = {
  // 信息
  getAppInfo: () => ipcRenderer.invoke('app:get-info'),
  getVersion: () => ipcRenderer.invoke('app:get-version'),

  // 窗口控制
  minimizeWindow: () => ipcRenderer.invoke('window:minimize'),
  maximizeWindow: () => ipcRenderer.invoke('window:maximize'),
  closeWindow: () => ipcRenderer.invoke('window:close'),

  // Shell 操作
  openExternal: (url: string) => ipcRenderer.invoke('shell:open-external', url),

  // 文件对话框
  openFile: (options: any) => ipcRenderer.invoke('dialog:open-file', options),
  saveFile: (options: any) => ipcRenderer.invoke('dialog:save-file', options),

  // 授权
  startAuth: (platformId: string, authUrl: string) =>
    ipcRenderer.invoke('auth:start', platformId, authUrl),

  // 通知
  showNotification: (title: string, body: string) =>
    ipcRenderer.send('show-notification', title, body),

  // 后端管理
  getBackendStatus: () => ipcRenderer.invoke('backend:get-status'),
  restartBackend: () => ipcRenderer.invoke('backend:restart'),
  getBackendConfig: () => ipcRenderer.invoke('backend:get-config'),

  // 浏览器桥接服务管理
  getBridgeStatus: () => ipcRenderer.invoke('bridge:get-status'),
  restartBridge: () => ipcRenderer.invoke('bridge:restart'),
  getBridgeConfig: () => ipcRenderer.invoke('bridge:get-config'),

  // 监听主进程消息
  onAuthWindowClosed: (callback: (data: any) => void) => {
    const listener = (_event: any, data: any) => callback(data)
    ipcRenderer.on('auth:window-closed', listener)
    return () => ipcRenderer.removeListener('auth:window-closed', listener)
  },

  onPublishProgress: (callback: (data: any) => void) => {
    const listener = (_event: any, data: any) => callback(data)
    ipcRenderer.on('publish:progress', listener)
    return () => ipcRenderer.removeListener('publish:progress', listener)
  },

  // 平台信息
  platforms: {
    zhihu: { id: 'zhihu', name: '知乎', color: '#0084FF' },
    baijiahao: { id: 'baijiahao', name: '百家号', color: '#E53935' },
    sohu: { id: 'sohu', name: '搜狐号', color: '#FF6B00' },
    toutiao: { id: 'toutiao', name: '头条号', color: '#333333' },
  },
}

// 使用 contextBridge 安全暴露 API
contextBridge.exposeInMainWorld('electronAPI', electronAPI)

// 类型声明
export type ElectronAPI = typeof electronAPI
