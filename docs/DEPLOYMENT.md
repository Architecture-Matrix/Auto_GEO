# Auto_GEO 混合架构部署指南

> **版本**: v3.2.0 - CDP支持
> **更新**: 新增CDP连接本地浏览器方案

## 架构概述

Auto_GEO现在支持三种部署模式，适应不同的使用场景：

### 1. Local模式（本地模式）
**适用场景：** 开发环境、调试阶段
- 所有浏览器操作在本地执行
- 浏览器有GUI显示，方便调试
- 授权需要手动登录

### 2. Cloud模式（云端模式）
**适用场景：** 生产环境（已保存会话）
- 所有浏览器操作headless执行
- 需要预先获取并保存登录会话
- Linux环境需要安装xvfb

### 3. Hybrid模式（混合模式）✨推荐
**适用场景：** 生产环境 + 需要手动授权
- 授权操作在本地客户端执行（通过CDP）
- 自动化任务在服务器headless执行
- 灵活性和效率兼顾

## CDP连接方案（核心）

### 为什么需要CDP？

```
┌────────────────────────────────────────────────────────────────────┐
│  传统架构（有问题）                                                  │
├────────────────────────────────────────────────────────────────────┤
│  用户点击"授权知乎" → 云端启动浏览器 → 用户在云端登录 ← 看不到！   │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  CDP架构（正确）                                                    │
├────────────────────────────────────────────────────────────────────┤
│  用户点击"授权知乎" → 云端通过CDP连接本地浏览器 → 用户本地登录 ✓  │
└────────────────────────────────────────────────────────────────────┘
```

### CDP方案优势

| 特性 | 说明 |
|-----|------|
| **浏览器本地** | Chrome在用户本地运行，看得见 |
| **云端控制** | 通过CDP协议远程控制浏览器 |
| **会话复用** | 授权后的会话可被发布任务复用 |
| **无需Cookie** | 直接使用浏览器登录状态 |

## 快速开始

### 前置条件

1. **本地（Electron）**：启动浏览器桥接服务
2. **云端**：配置CDP连接地址

### 配置部署模式

编辑 `.env` 文件（或创建 `.env` 文件）：

```bash
# 部署模式选择：local, cloud, hybrid
DEPLOYMENT_MODE=hybrid

# 强制headless模式（可选）
HEADLESS_MODE=false

# 本地浏览器CDP端口
LOCAL_BROWSER_CDP_PORT=9222

# ============================================
# CDP配置（核心）
# ============================================

# 本地浏览器公网地址（通过内网穿透暴露）
# 格式: http://xxxxx.xxx.io 或 http://IP:PORT
LOCAL_BROWSER_URL=

# 强制使用本地浏览器（通过CDP连接）
# true=强制CDP模式，false=云端启动浏览器
FORCE_LOCAL_BROWSER=true
```

### 内网穿透配置

为了让云端能访问本地浏览器，需要做内网穿透：

#### 方案1：使用localtunnel（推荐开发测试）

```bash
# 在Electron端安装
npm install -g localtunnel

# 启动穿透服务
lt --port 9222 --subdomain your-unique-subdomain
```

#### 方案2：使用frp（推荐生产环境）

```ini
# frpc.ini 配置
[common]
server_addr = your-frp-server.com
server_port = 7000

[local_cdp]
type = tcp
local_port = 9222
remote_port = 9222
```

#### 方案3：使用cloudflare tunnel（推荐）

```bash
# 安装cloudflared
brew install cloudflare/cloudflare/cloudflared

# 创建隧道
cloudflared tunnel create my-tunnel

# 运行
cloudflared tunnel --url localhost:9222
```

### 本地模式启动

```bash
# 默认就是本地模式
cd backend
python main.py
```

### 云端模式启动

```bash
# 1. 设置环境变量
export DEPLOYMENT_MODE=cloud

# 2. Linux无GUI环境需要xvfb
sudo apt-get install xvfb
xvfb-run python backend/main.py
```

### 混合模式启动

**服务器端：**
```bash
export DEPLOYMENT_MODE=hybrid
export FORCE_LOCAL_BROWSER=true
export LOCAL_BROWSER_URL=http://your-tunnel-url.io
cd backend
python main.py
```

**本地客户端：**
1. 启动Electron应用（会自动启动浏览器桥接服务）
2. 配置内网穿透
3. 在云端配置 `LOCAL_BROWSER_URL`

## API接口

### 1. 查询部署配置
```
GET /api/deployment/config
```

### 2. 查询任务执行位置
```
GET /api/deployment/task-location/{task_type}
```

### 3. 本地浏览器控制
```
POST /api/browser/start - 启动本地浏览器
GET /api/browser/status - 查询浏览器状态
POST /api/browser/stop - 停止浏览器
```

## 使用示例

### 本地浏览器授权

```python
import requests

# 1. 启动本地浏览器
response = requests.post('http://localhost:8001/api/browser/start', json={
    'headless': False,
    'use_cdp': True
})

# 2. 执行授权任务（会打开浏览器窗口让你登录）
# ... 授权流程会自动检测登录状态并保存会话
```

### 服务器端自动发布

```python
# 服务器端使用已保存的会话自动发布文章
# headless模式执行，无需GUI
```

## 部署建议

### 小型团队（1-5人）
- 推荐模式：**Local**
- 部署方式：本地运行
- 优势：简单直接，方便调试

### 中型团队（5-20人）
- 推荐模式：**Hybrid**
- 部署方式：云服务器 + 本地客户端
- 优势：
  - 授权在本地完成（安全）
  - 发布在服务器自动执行（高效）

### 大型团队（20+人）
- 推荐模式：**Hybrid + 分布式**
- 部署方式：
  - 多台服务器分担任务
  - 本地授权客户端可单独部署
- 优势：可扩展性强

## 注意事项

### Linux服务器（无GUI）
```bash
# 安装虚拟显示
sudo apt-get install xvfb

# 使用xvfb运行
xvfb-run -a python backend/main.py
```

### Docker部署
```dockerfile
FROM python:3.11
# 安装xvfb
RUN apt-get update && apt-get install -y xvfb
# 使用xvfb启动
CMD ["xvfb-run", "python", "backend/main.py"]
```

### 会话管理
- Cloud模式下，授权会话需要在Local模式下预先获取
- Hybrid模式下，授权在本地完成，会话自动同步到服务器

## 故障排除

### 问题：浏览器启动失败
```
错误：Executable doesn't exist
解决：安装Chrome或设置HEADLESS_MODE=true
```

### 问题：授权超时
```
错误：Login timeout
解决：增加LOGIN_MAX_WAIT_TIME配置或使用Hybrid模式
```

### 问题：会话失效
```
错误：Session invalid
解决：重新执行授权流程获取新会话
```
