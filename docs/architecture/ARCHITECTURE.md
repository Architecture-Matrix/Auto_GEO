# AutoGeo 架构设计文档

> 开发者备注：这个文档专门讲清楚 Vite、Electron、Python 后端和 n8n AI 服务的关系！别tm搞混了！

---

## 一、整体架构概览

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              AutoGeo 应用架构 (v2.1)                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌──────────────────────┐         ┌──────────────────────┐         ┌──────────────┐│
│  │   Electron 主进程    │         │    Python 后端       │         │    n8n AI    ││
│  │  (Node.js 运行时)    │◄───────►│   (FastAPI 服务)     │◄───────►│   工作流引擎  ││
│  │                      │  spawn  │                      │ webhook │              ││
│  │  - 窗口管理          │         │  - 账号管理 API      │         │  - 关键词蒸馏││
│  │  - IPC 通信          │         │  - 文章管理 API      │         │  - 文章生成  ││
│  │  - 后端进程管理      │         │  - 发布管理 API      │         │  - 收录分析  ││
│  │  - 系统托盘          │         │  - GEO/AI API        │         │  - AI中台    ││
│  │                      │         │  - Playwright 自动化 │         │              ││
│  │                      │         │  - 智能建站 API       │         │              ││
│  └──────────┬───────────┘         └──────────┬───────────┘         └──────────────┘│
│             │                                │                                    │
│             │ IPC                            │ HTTP/WebSocket                    │
│             │                                │                                    │
│  ┌──────────▼───────────┐         ┌──────────▼───────────┐                        │
│  │   Preload 脚本       │         │                      │                        │
│  │  (安全隔离层)        │         │   http://127.0.0.1   │                        │
│  │                      │         │      :8001           │                        │
│  │  contextBridge       │         │                      │                        │
│  └──────────┬───────────┘         └──────────────────────┘                        │
│             │                                                                      │
│             │ contextBridge API                                                    │
│             │                                                                      │
│  ┌──────────▼─────────────────────────────────────────────────────────────────┐  │
│  │                    渲染进程 (Renderer Process)                               │  │
│  │  ┌──────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                        Vite Dev Server                               │  │  │
│  │  │  (开发环境: http://127.0.0.1:5173)                                   │  │  │
│  │  │                                                                      │  │  │
│  │  │  ┌────────────────────────────────────────────────────────────────┐  │  │  │
│  │  │  │              Vue 3 应用                                        │  │  │  │
│  │  │  │                                                                │  │  │  │
│  │  │  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌────────────┐ │  │  │  │
│  │  │  │  │  Vue 组件 │  │ Pinia    │  │   API 服务   │  │ WebSocket  │ │  │  │  │
│  │  │  │  │  (Views)  │  │ Stores   │  │  (axios)     │  │  Service   │ │  │  │  │
│  │  │  │  └──────────┘  └──────────┘  └──────────────┘  └────────────┘ │  │  │  │
│  │  │  └────────────────────────────────────────────────────────────────┘  │  │  │
│  │  └──────────────────────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 架构分层说明

| 层级 | 技术栈 | 职责 |
|------|--------|------|
| **桌面层** | Electron | 窗口管理、进程生命周期、系统集成 |
| **前端层** | Vue 3 + Vite + TypeScript | 用户界面、状态管理、API调用 |
| **后端层** | FastAPI + Playwright | 业务逻辑、数据存储、浏览器自动化 |
| **AI层** | n8n + DeepSeek | AI能力统一调度、工作流编排 |

---

## 二、n8n AI 中台架构

### 2.1 为什么用 n8n？

```
旧架构问题:
┌─────────────────────────────────────────────────────────────┐
│  Python 后端硬编码调用 AI API                               │
│  ├── services/keyword_service.py  → 直接调 DeepSeek API     │
│  ├── services/geo_service.py      → 直接调 DeepSeek API     │
│  └── services/analysis_service.py → 直接调 DeepSeek API     │
│                                                             │
│  问题: 换个AI服务商要改一堆代码，Prompt分散，无法可视化      │
└─────────────────────────────────────────────────────────────┘

新架构优势:
┌─────────────────────────────────────────────────────────────┐
│  Python 后端 → n8n Webhook → AI服务商 (可插拔)             │
│                                                             │
│  优势:                                                      │
│  ✓ AI逻辑与业务解耦                                        │
│  ✓ 可视化工作流编辑                                        │
│  ✓ 一处修改全局生效                                        │
│  ✓ 内置执行日志和监控                                      │
│  ✓ 换AI只需改n8n配置，不动代码                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 n8n 工作流清单

| 工作流文件 | Webhook路径 | 功能 | 调用方 |
|-----------|-------------|------|--------|
| `keyword-distill.json` | `/webhook/keyword-distill` | 关键词蒸馏，提取核心词和长尾词 | `geo.py` |
| `geo-article-generate.json` | `/webhook/geo-article-generate` | AI生成SEO优化文章 | `geo.py` |
| `index-check-analysis.json` | `/webhook/index-check-analysis` | 分析收录情况，给优化建议 | `index_check.py` |
| `generate-questions.json` | `/webhook/generate-questions` | 生成问题变体 | `geo.py` |

### 2.3 后端调用示例

```python
# backend/api/geo.py
from backend.services.n8n_service import get_n8n_service

@router.post("/distill")
async def distill_keywords(keywords: list[str]):
    """关键词蒸馏 - 通过 n8n 调用 AI"""
    n8n = await get_n8n_service()
    result = await n8n.distill_keywords(keywords)

    if result.status != "success":
        raise HTTPException(status_code=500, detail=result.error)

    return result.data
```

### 2.4 n8n 配置

```python
# backend/services/n8n_service.py
class N8nConfig:
    # n8n webhook 基础地址
    WEBHOOK_BASE = "http://localhost:5678/webhook"

    # 超时配置
    TIMEOUT_SHORT = 30.0   # 简单任务
    TIMEOUT_LONG = 120.0   # 文章生成
```

---

## 三、Vite 与 Electron 的关系

### 3.1 开发环境

```
用户双击 启动应用.bat
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Electron 主进程启动                                      │
│     - 启动 Python 后端 (spawn)                               │
│     - 创建主窗口                                              │
│     - 加载 Vite 开发服务器地址                               │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Vite 开发服务器                                          │
│     - 运行在 http://127.0.0.1:5173                          │
│     - HMR 热更新（开发超爽）                                 │
│     - 代理 /api 到 Python 后端                              │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Electron 窗口加载                                        │
│     - mainWindow.loadURL('http://127.0.0.1:5173')          │
│     - Preload 脚本注入                                       │
│     - Vue 应用在渲染进程中运行                               │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 生产环境（打包后）

```
┌─────────────────────────────────────────────────────────────┐
│  npm run build                                              │
│     │                                                        │
│     ├─► build:renderer  (Vite 构建 Vue 代码)               │
│     │      输出: out/renderer/                              │
│     │                                                        │
│     └─► build:electron    (TypeScript 编译主进程)          │
│            输出: out/electron/                              │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  electron-builder 打包                                       │
│     - 将前端静态文件打包进 asar                              │
│     - 主进程加载 file:// 协议的 HTML                         │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 关键配置

**vite.config.ts** (`fronted/vite.config.ts`):
```typescript
server: {
  host: '127.0.0.1',        // 必须用 IPv4，Electron 才能连上
  port: 5173,
  strictPort: true,         // 端口被占用时报错，不跳
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8001',  // 代理到 Python 后端
      changeOrigin: true,
    },
    '/ws': {
      target: 'ws://127.0.0.1:8001',    // WebSocket 代理
      ws: true,
    },
  },
}
```

**window-manager.ts** (`fronted/electron/main/window-manager.ts`):
```typescript
const isDev = process.env.NODE_ENV === 'development'
const URL = isDev
  ? 'http://127.0.0.1:5173'      // 开发: Vite 服务器
  : formatFileUrl('index.html')  // 生产: 打包后的文件
```

---

## 四、通信通道详解

### 4.1 通道 1：Vue 渲染进程 ↔ Python 后端 (HTTP/WebSocket)

```
┌──────────────────────┐          ┌──────────────────────┐
│   Vue 渲染进程       │          │    Python 后端       │
│                      │          │   (FastAPI)          │
│  ┌────────────────┐  │          │                      │
│  │  API Service   │  │          │  ┌────────────────┐  │
│  │  (axios)       │◄─┼──────────┼─►│   /api/*       │  │
│  └────────────────┘  │   HTTP   │  └────────────────┘  │
│                      │          │                      │
│  ┌────────────────┐  │          │  ┌────────────────┐  │
│  │  WebSocket     │◄─┼──────────┼─►│   /ws          │  │
│  │  Service       │  │   WS     │  └────────────────┘  │
│  └────────────────┘  │          │                      │
└──────────────────────┘          └──────────────────────┘

实际路径（开发环境）：
  Vue: http://127.0.0.1:5173
    │
    │ Vite Proxy 代理
    ▼
  Python: http://127.0.0.1:8001
```

**API 调用示例**：
```typescript
// fronted/src/services/api/index.ts
export const accountApi = {
  getList: () => get('/accounts'),           // → http://127.0.0.1:8001/api/accounts
  create: (data) => post('/accounts', data), // → POST /api/accounts
}
```

**WebSocket 连接**：
```typescript
// 连接到 ws://127.0.0.1:5173/ws (Vite 代理到 Python)
wsService.connect('ws://127.0.0.1:5173/ws')
```

### 4.2 通道 2：Python 后端 ↔ n8n AI 中台 (Webhook)

```
┌──────────────────────┐          ┌──────────────────────┐
│   Python 后端       │          │      n8n             │
│   (FastAPI)         │          │   工作流引擎          │
│                      │          │                      │
│  ┌────────────────┐  │          │  ┌────────────────┐  │
│  │ N8nService     │  │          │  │  Webhook接收   │  │
│  │ 封装调用       │  │          │  │                │  │
│  └────────┬───────┘  │          │  └────────┬───────┘  │
│           │          │   HTTP    │           │          │
│           │ POST     │◄─────────┼───────────►│          │
│           │          │  Webhook │           │          │
│           │          │          │  ┌────────┴───────┐  │
│           │          │          │  │  AI处理节点    │  │
│           │          │          │  └────────────────┘  │
│           │          │          │           │          │
│           │          │          │  ┌────────┴───────┐  │
│           │          │          │  │  DeepSeek API  │  │
│           │          │          │  └────────────────┘  │
└──────────────────────┘          └──────────────────────┘

Webhook 端点：
  http://localhost:5678/webhook/keyword-distill
  http://localhost:5678/webhook/geo-article-generate
  http://localhost:5678/webhook/index-check-analysis
  http://localhost:5678/webhook/generate-questions
```

### 4.3 通道 3：渲染进程 ↔ Electron 主进程 (IPC)

```
┌──────────────────────┐          ┌──────────────────────┐
│   Vue 渲染进程       │          │  Electron 主进程     │
│                      │          │                      │
│  ┌────────────────┐  │          │  ┌────────────────┐  │
│  │  electronAPI   │◄─┼──────────┼─►│  ipcMain       │  │
│  │  (暴露的API)   │  │  IPC     │  │  handlers       │  │
│  └────────────────┘  │          │  └────────────────┘  │
│       ▲              │          │                      │
│       │ contextBridge│          │                      │
│  ┌────┴─────────────┤          │                      │
│  │ Preload 脚本     │          │                      │
│  └──────────────────┘          └──────────────────────┘

可用的 IPC 通道（白名单）：
  - window:minimize/maximize/close
  - dialog:open-file/save-file
  - auth:start
  - backend:get-status/restart
  - shell:open-external
```

**使用示例**：
```typescript
// Vue 组件中
window.electronAPI.minimizeWindow()  // 调用主进程 API
window.electronAPI.onAuthWindowClosed((data) => {
  // 监听主进程消息
})
```

### 4.4 通道 4：Electron 主进程 ↔ Python 后端 (进程管理)

```
┌──────────────────────┐          ┌──────────────────────┐
│  Electron 主进程     │          │    Python 后端       │
│                      │          │                      │
│  ┌────────────────┐  │          │  ┌────────────────┐  │
│  │ BackendManager │◄─┼──────────┼─►│  FastAPI       │  │
│  │                │  │  spawn   │  │  Uvicorn       │  │
│  └────────────────┘  │          │  └────────────────┘  │
│         │            │          │         │              │
│         │ health     │  HTTP    │         │              │
│         └───────────►│ check    │◄────────┘              │
└──────────────────────┘          └──────────────────────┘

后端管理器职责：
  - 启动: spawn('python', ['main.py'])
  - 健康检查: GET http://127.0.0.1:8001/api/health
  - 停止: taskkill /F /T /PID xxx (Windows)
  - 重启: stop() → start()
```

---

## 五、通信流程示例

### 5.1 用户点击"添加账号"按钮

```
1. 用户点击按钮
   └─► Vue 组件 @click 事件

2. 调用 API 服务
   accountApi.create({ platform: 'zhihu', account_name: '测试' })
   └─► axios.post('/api/accounts', data)
       └─► http://127.0.0.1:5173/api/accounts (Vite)
           └─► http://127.0.0.1:8001/api/accounts (Python 后端)

3. Python 后端处理
   └─► account.py router 处理请求
       └─► SQLAlchemy 写入数据库
           └─► 返回 JSON 响应

4. Vue 更新状态
   └─► accountStore 刷新列表
       └─► Pinia 触发响应式更新
           └─► 页面显示新账号
```

### 5.2 用户点击"生成GEO文章"按钮（新架构）

```
1. 用户点击"生成文章"
   └─► Vue 调用 geoApi.generateArticle(keyword)

2. FastAPI 接收请求
   └─► /api/geo/generate-article
       └─► geo.py 路由处理

3. Python 调用 n8n webhook
   └─► N8nService.generate_geo_article(keyword)
       └─► POST http://localhost:5678/webhook/geo-article-generate

4. n8n 工作流处理
   └─► 接收 webhook
       └─► AI 节点调用 DeepSeek
           └─► Code 节点解析响应
               └─► 返回文章内容

5. 返回给前端
   └─► Python 收到 n8n 响应
       └─► 返回给 Vue
           └─► 页面显示生成的文章
```

### 5.3 批量发布文章（实时进度）

```
1. Vue 创建发布任务
   publishApi.createTask({ article_ids: [1], account_ids: [1] })

2. 后端开始发布，同时建立 WebSocket 连接
   └─► wsService.connect('ws://127.0.0.1:5173/ws')

3. Python 后端推送进度
   WebSocket.send({ type: 'publish:progress', data: { ... } })

4. Vue 实时更新 UI
   on('publish:progress', (data) => {
     progress.value = data.progress
   })
```

---

## 六、关键端口一览

| 服务 | 地址 | 说明 |
|------|------|------|
| **Vite Dev Server** | http://127.0.0.1:5173 | 前端开发服务器（仅开发环境） |
| **Python FastAPI** | http://127.0.0.1:8001 | 后端 API 服务 |
| **WebSocket** | ws://127.0.0.1:8001/ws | 实时通信（开发时通过 Vite 代理） |
| **n8n** | http://127.0.0.1:5678 | AI 工作流引擎（新增） |
| **n8n Webhook** | http://127.0.0.1:5678/webhook/* | AI 服务入口（新增） |

---

## 七、文件路径速查

### Electron 主进程
- 入口：`fronted/electron/main/index.ts`
- 窗口管理：`fronted/electron/main/window-manager.ts`
- IPC 处理：`fronted/electron/main/ipc-handlers.ts`
- 后端管理：`fronted/electron/main/backend-manager.ts`
- Preload：`fronted/electron/preload/index.ts`

### Vue 渲染进程
- 入口：`fronted/src/main.ts`
- API 服务：`fronted/src/services/api/index.ts`
- WebSocket：`fronted/src/services/websocket/index.ts`
- 状态管理：`fronted/src/stores/modules/`

### Python 后端
- 入口：`backend/main.py`
- 路由：`backend/api/`
- 服务：`backend/services/`
- **n8n 服务封装**：`backend/services/n8n_service.py` (新增)
- **智能建站**：`backend/api/site_builder.py`、`backend/services/site_generator.py`

### n8n 工作流
- 工作流目录：`n8n/workflows/`
- 集成文档：`n8n/README.md`

---

## 八、安全机制

### 1. contextBridge 隔离
Preload 脚本使用 `contextBridge.exposeInMainWorld` 安全暴露 API，渲染进程无法直接访问 Node.js API。

### 2. IPC 白名单
所有 IPC 通道都经过白名单验证，未注册的通道会被拒绝。

### 3. 发送者验证
```typescript
function validateSender(frame: any): boolean {
  const allowedProtocols = ['http:', 'https:', 'file:']
  return allowedProtocols.includes(url.protocol)
}
```

### 4. AES-256 加密
Cookies 使用 AES-256 加密存储在本地数据库。

### 5. n8n Webhook 安全
```python
# 生产环境建议：
# 1. 使用 n8n 内置的认证功能
# 2. 设置 webhook 路径密钥
# 3. 限制 n8n 只监听 127.0.0.1
```

---

## 九、技术栈总览

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **桌面** | Electron | ^28.0.0 | 跨平台桌面应用 |
| **前端** | Vue 3 | ^3.4.0 | UI框架 |
| **前端** | TypeScript | ^5.3.0 | 类型安全 |
| **前端** | Vite | ^5.0.0 | 构建工具 |
| **前端** | Element Plus | ^2.5.0 | UI组件库 |
| **前端** | Pinia | ^2.1.7 | 状态管理 |
| **前端** | ECharts | ^5.6.0 | 数据可视化 |
| **后端** | FastAPI | 0.109.0 | Web框架 |
| **后端** | SQLAlchemy | 2.0.25 | ORM |
| **后端** | Playwright | 1.40.0 | 浏览器自动化 |
| **后端** | APScheduler | 3.10.4 | 定时任务 |
| **后端** | Jinja2 | - | 模板引擎（智能建站） |
| **后端** | paramiko | 3.4.0 | SFTP 部署（智能建站） |
| **后端** | boto3 | 1.34.19 | S3/OSS 部署（智能建站） |
| **AI中台** | n8n | latest | 工作流引擎 |
| **AI服务** | DeepSeek | - | 大模型API |
| **数据库** | SQLite | - | 本地存储 |

---

**文档更新时间：** 2025-02-10
**维护者：** 小a
**版本：** v2.2 (新增智能建站模块)
