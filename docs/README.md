# AutoGeo 文档中心

---

## 📁 目录结构

```
docs/
├── README.md          # 本文档
├── CHANGELOG.md       # [待创建] 变更日志
├── PRD.md             # 产品需求文档
├── api.md             # API 接口文档
├── architecture/      # 架构设计
├── features/          # 功能设计
├── guides/           # 使用指南
└── security/         # 安全配置
```

---

## 📖 文档索引

### 📋 核心文档

| 文档 | 说明 |
|-----|------|
| [PRD.md](PRD.md) | GEO 自动化产品需求文档 |
| [api.md](api.md) | 后端 API 接口文档 |

---

### 🏗️ 架构设计 (`architecture/`)

| 文档 | 说明 |
|-----|------|
| [ARCHITECTURE.md](architecture/ARCHITECTURE.md) | 系统架构 - Vite/Electron/Python 通信 |
| [FRONTEND-ARCHITECTURE.md](architecture/FRONTEND-ARCHITECTURE.md) | 前端架构 - Vue3 + Pinia |

---

### ⚙️ 功能设计 (`features/`)

| 文档 | 说明 |
|-----|------|
| [AUTH.md](features/AUTH.md) | 用户认证功能 |
| [AUTH_FLOW_DESIGN.md](features/AUTH_FLOW_DESIGN.md) | 认证流程设计 |
| [SITE-BUILDER.md](features/SITE-BUILDER.md) | 站点构建功能 |
| [UI.md](features/UI.md) | UI 设计规范 |

---

### 📚 使用指南 (`guides/`)

| 文档 | 说明 |
|-----|------|
| [LAUNCHER.md](guides/LAUNCHER.md) | 启动器使用指南 |
| [PACKAGE.md](guides/PACKAGE.md) | 打包发布指南 |
| [RAGFLOW.md](guides/RAGFLOW.md) | RAGFlow 集成指南 |

---

### 🔒 安全配置 (`security/`)

| 文档 | 说明 |
|-----|------|
| [SECURITY.md](security/SECURITY.md) | 加密机制、密钥配置 |

---

## 🚀 快速开始

1. **安装依赖**
   ```bash
   pip install -r backend/requirements.txt
   cd frontend && npm install
   ```

2. **启动服务**
   ```bash
   # Windows
   start.bat
   # Linux/macOS
   ./start.sh
   ```

3. **打包发布**
   ```bash
   cd frontend
   npm run dist:win
   ```

---

*最后更新: 2026-02-25*
