# AutoGeo AI搜索引擎优化自动化平台

> 开发者备注：一个用 Electron + Vue3 + FastAPI + n8n + Playwright 搞的智能平台，自动发布文章、检测收录、生成GEO内容！AI能力全部通过n8n工作流调度，解耦设计，想换AI服务商只需改个配置！

## 功能特性

### 核心功能
- ✅ **多平台发布**：知乎、百家号、搜狐、头条号等40+平台
- ✅ **账号管理**：安全的 Cookie 存储和授权
- ✅ **文章编辑**：WangEditor 5 富文本编辑器，所见即所得，支持图片上传
- ✅ **发布任务管理**：创建和管理发布任务，支持后台运行
- ✅ **平台发布监控**：实时监控各平台发布进度和状态

### GEO/AI优化功能 ✨
- ✅ **关键词管理**：项目与关键词管理、关键词蒸馏
- ✅ **收录检测**：自动检测AI搜索引擎收录情况(豆包/千问/DeepSeek)
- ✅ **GEO文章生成**：基于关键词自动生成SEO优化文章
- ✅ **数据报表**：收录趋势、平台分布、关键词排名
- ✅ **预警通知**：命中率下降、零收录、持续低迷预警
- ✅ **定时任务**：每日自动检测、失败重试
- ✅ **WebSocket推送**：实时进度通知

### 管理功能 📊
- ✅ **候选人管理**：HR候选人信息管理与跟踪
- ✅ **知识库管理**：RAGflow知识库接入与管理
- ✅ **智能建站 (AEO)**：Jinja2 模板渲染 + SFTP/S3 部署，双模板风格
- ✅ **定时任务调度**：可视化定时任务配置与管理
- ✅ **数据仪表盘**：实时数据概览与可视化分析

## 技术栈

| 层级 | 技术选型 |
|------|---------|
| 前端 | Vue 3 + TypeScript + Vite + Element Plus + Pinia + ECharts + WangEditor 5 |
| 后端 | FastAPI + SQLAlchemy + Playwright + APScheduler |
| AI中台 | n8n 工作流引擎 + DeepSeek API |
| 桌面 | Electron |
| 数据库 | SQLite |

## 快速开始

> 📘 **需要详细的设置指南？** 查看 [SETUP.md](./SETUP.md) 获取完整的项目设置步骤！

### 环境要求

- **Node.js**: 18+
- **Python**: 3.10+
- **Docker** (可选，用于运行 n8n)
- **操作系统**: Windows / macOS / Linux

### 🚀 一键启动（推荐）

```bash
# 克隆项目
git clone https://github.com/Architecture-Matrix/Auto_GEO.git
cd Auto_GEO

# Windows用户: 双击运行
start.bat

# Linux/macOS用户:
chmod +x start.sh
./start.sh
```

启动菜单：
- [1] 启动后端服务
- [2] 启动前端 Electron 应用
- [3-5] 重启和清理选项

**首次启动请按顺序选择 1 → 2**

### ⚙️ 手动安装

**后端依赖**：

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
```

**前端依赖**：

```bash
cd frontend
npm install

# 如果遇到Electron启动失败，运行修复脚本
# Windows: ..\scripts\fix-electron.bat
# Linux/macOS: ../scripts/fix/fix-electron.sh
```

### 🎯 启动服务

**启动 n8n (AI工作流引擎)**

> **两种部署方式**：

**方式1: 使用云端 n8n** ⭐ 推荐（无需本地运行）

```bash
# 只需配置环境变量即可
# 复制 .env.example 为 .env
cp .env.example .env

# 编辑 .env，设置你的云端 n8n 地址：
# N8N_WEBHOOK_URL=https://n8n.opencaio.cn/webhook
```

**方式2: 本地 Docker 运行**

```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

**方式3: npm 本地运行**

```bash
npm install -g n8n
n8n start
```

然后访问 http://localhost:5678，导入 `n8n/workflows/` 下的工作流文件。

详细配置请查看 [n8n 集成文档](./n8n/README.md)

### 3. 启动后端

```bash
cd backend
python main.py
```

后端服务运行在 `http://127.0.0.1:8001`

### 4. 启动前端

```bash
cd fronted
npm run dev
```

---

## 🔄 CI/CD 自动化

### GitHub Actions 工作流

项目配置了自动化CI/CD，每次push或创建PR都会自动运行！

| 工作流 | 触发条件 | 验证内容 | 状态 |
|-------|---------|---------|------|
| **🚀 Startup Validation** | push/PR | ✅ 后端启动检查<br>✅ 前端构建检查<br>✅ 依赖验证<br>✅ 文档检查 | ✅ 已配置 |
| **🎨 Frontend CI** | push到frontend | ✅ ESLint检查<br>✅ TypeScript检查<br>✅ 单元测试<br>✅ 构建验证 | ✅ 已配置 |
| **⚙️ Backend CI** | push到backend | ✅ Ruff检查<br>✅ MyPy类型检查<br>✅ 单元测试<br>✅ 安全扫描 | ✅ 已配置 |
| **🚀 Backend Deploy** | push到main | ✅ Docker构建<br>✅ 推送镜像<br>⏳ 自动部署（待配置） | ⏳ CD待配置 |
| **📦 Frontend Release** | 发布Release | ✅ 打包应用<br>⏳ 构建安装包（待配置） | ⏳ CD待配置 |

### 启动验证保证

**Startup Validation工作流**确保：
- ✅ clone仓库后后端能正常启动
- ✅ 前端Electron应用能正常构建和启动
- ✅ 所有依赖文件完整
- ✅ 文档齐全

**查看CI/CD状态**：
```
https://github.com/Architecture-Matrix/Auto_GEO/actions
```

### CI徽章

[![Startup Validation](https://github.com/Architecture-Matrix/Auto_GEO/actions/workflows/startup-validation.yml/badge.svg)](https://github.com/Architecture-Matrix/Auto_GEO/actions/workflows/startup-validation.yml)
[![Frontend CI](https://github.com/Architecture-Matrix/Auto_GEO/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/Architecture-Matrix/Auto_GEO/actions/workflows/frontend-ci.yml)
[![Backend CI](https://github.com/Architecture-Matrix/Auto_GEO/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/Architecture-Matrix/Auto_GEO/actions/workflows/backend-ci.yml)

> **注意**：CD（持续部署）部分待后续配置，目前CI（持续集成）已完全可用！

---

## 🛠️ 项目工具

AutoGeo 提供了便捷的工具脚本，帮助你快速启动和清理项目：

### 快速启动工具

**`start.bat` / `scripts/quickstart-cmd.bat`** ⭐ 推荐

一键管理项目的所有操作：启动服务、重启服务、清理缓存

```bash
# 双击运行或在命令行执行
start.bat
```

**主菜单**：
- [1] 启动后端服务（新窗口）
- [2] 启动前端 Electron 应用（新窗口）
- [3] 重启后端服务
- [4] 重启前端服务
- [5] 清理项目缓存
- [6] 退出（关闭所有服务）

**清理子菜单**（选项 5）：
- [1] 快速清理（安全）- Python缓存、Vite缓存、数据库临时文件、日志
- [2] 完全清理（激进）- 包括 node_modules（需重新安装）
- [3] 返回主菜单

**特性**：
- ✅ 自动检查依赖文件
- ✅ 端口占用检测
- ✅ 窗口管理（自动关闭）
- ✅ **集成清理功能**（v2.7.0 新增）

### 独立清理工具

**`scripts/cleanup.bat`**

单独的清理工具，功能与 quickstart 的选项 [5] 相同：

```bash
# 双击运行或在命令行执行
scripts/cleanup.bat
```

提供更多自定义清理选项（8个选项 + 预览功能）

**清理选项**：

| 选项 | 说明 | 可恢复 |
|------|------|--------|
| **[1] 快速清理** | Python缓存、Vite缓存、数据库临时文件、日志 | 自动恢复 |
| **[2] 完全清理** | 包括 node_modules（需重新安装） | `npm install` |
| **[3] 自定义清理** | 选择性清理特定项目 | 按需恢复 |
| **[4] 预览大小** | 查看可清理的文件大小 | - |

**清理内容**：
- 🗑️ Python缓存：`__pycache__/`, `*.pyc`
- 🗑️ Node.js缓存：`.vite/`
- 🗑️ 数据库临时文件：`*.wal`, `*.shm`
- 🗑️ 日志文件：`*.log`
- 🗑️ 系统临时文件：`.DS_Store`, `Thumbs.db`
- 🗑️ 测试缓存：`.pytest_cache/`
- 🗑️ IDE缓存：`.idea/`

**注意**：
- 快速清理是安全的，不影响开发
- 完全清理后需要重新安装依赖
- 数据库文件（`.db`）不会被删除

---

## 📚 文档

### 核心文档

| 文档 | 说明 | 链接 |
|------|------|------|
| 📘 **项目设置** | 详细的项目设置指南，常见问题解答 | [SETUP.md](./SETUP.md) |
| 📖 **API文档** | 完整的API端点说明和示例 | [API文档](./docs/api.md) |
| 📋 **协作规范** | 分支管理、提交规范、PR流程 | [团队协作指南](./docs/TEAM_COLLABORATION_GUIDE.md) |

### 在线API文档

启动后端后访问：
- **Swagger UI**: http://127.0.0.1:8001/docs （交互式文档，可在线测试）
- **ReDoc**: http://127.0.0.1:8001/redoc （精美文档展示）

## 📂 目录结构

```
auto_geo/
├── backend/              # 后端服务 (FastAPI)
│   ├── api/              # API 路由
│   │   ├── account.py       # 账号管理API
│   │   ├── article.py       # 文章管理API
│   │   ├── candidate.py     # 候选人管理API
│   │   ├── geo.py           # GEO/关键词API
│   │   ├── index_check.py   # 收录检测API
│   │   ├── keywords.py      # 关键词管理API
│   │   ├── knowledge.py     # 知识库管理API
│   │   ├── notifications.py # 预警通知API
│   │   ├── publish.py       # 发布管理API
│   │   ├── reports.py       # 数据报表API
│   │   ├── scheduler.py     # 定时任务API
│   │   ├── site_builder.py  # 智能建站API
│   │   └── upload.py        # 文件上传API
│   ├── database/         # 数据库
│   │   ├── models.py       # 数据模型
│   │   └── __init__.py     # 数据库初始化
│   ├── services/         # 业务服务
│   │   ├── crypto.py              # 加密服务
│   │   ├── geo_article_service.py # GEO文章生成
│   │   ├── index_check_service.py # 收录检测服务
│   │   ├── keyword_service.py     # 关键词服务
│   │   ├── n8n_service.py         # n8n webhook封装
│   │   ├── notification_service.py # 预警通知服务
│   │   ├── playwright_mgr.py      # Playwright管理器
│   │   ├── publisher.py           # 发布器
│   │   ├── scheduler_service.py   # 定时任务服务
│   │   └── websocket_manager.py   # WebSocket管理
│   ├── main.py           # 入口文件
│   └── requirements.txt  # Python 依赖
│
├── fronted/              # 前端应用 (Electron + Vue3)
│   ├── electron/         # Electron 主进程
│   ├── src/              # Vue 源码
│   │   ├── views/        # 页面视图
│   │   │   ├── account/    # 账号管理页面
│   │   │   ├── article/    # 文章编辑页面
│   │   │   ├── candidate/  # 候选人管理页面
│   │   │   ├── dashboard/  # 数据仪表盘
│   │   │   ├── geo/        # GEO功能页面
│   │   │   ├── knowledge/  # 知识库管理页面
│   │   │   ├── publish/    # 发布管理页面
│   │   │   ├── scheduler/  # 定时任务页面
│   │   │   ├── site-builder/  # 智能建站页面
│   │   │   └── settings/   # 设置页面
│   │   └── services/api/  # API封装
│   ├── package.json      # Node 依赖
│   └── vite.config.ts    # Vite 配置
│
├── n8n/                  # n8n AI工作流
│   ├── workflows/        # 工作流JSON文件
│   │   ├── geov0.0.1.json     # GEO工作流 v0.0.1
│   │   └── GEOv0.0.2.json     # GEO工作流 v0.0.2
│   └── README.md         # n8n集成文档
│
├── docs/                 # 项目文档
│   ├── TEAM_COLLABORATION_GUIDE.md  # 团队协作规范
│   ├── PROJECT_INFO.md             # 项目信息记录
│   ├── PRD-GEO-Automation.md       # GEO自动化PRD
│   ├── architecture/               # 架构文档
│   ├── features/                   # 功能设计文档
│   ├── testing/                    # 测试文档
│   ├── overview/                   # 概览文档
│   ├── plans/                      # 开发计划
│   ├── changelog/                  # 变更日志
│   └── security/                   # 安全文档
│
├── .github/              # GitHub配置
│   ├── pull_request_template.md    # PR模板
│   └── ISSUE_TEMPLATE/             # Issue模板
│
├── CONTRIBUTING.md       # 贡献者指南
├── CODE_OF_CONDUCT.md    # 行为准则
└── README.md             # 本文件
```

## 开发说明

### 端口配置

| 服务 | 地址 |
|------|------|
| 前端开发服务器 | http://127.0.0.1:5173 |
| 后端 API | http://127.0.0.1:8001 |
| API 文档 | http://127.0.0.1:8001/docs |
| WebSocket | ws://127.0.0.1:8001/ws |

### 环境说明

- **生产环境**: `main` 分支
- **开发环境**: 基于main创建功能分支
- **云n8n配置**: 在项目根目录创建 `.env` 文件，设置 `N8N_WEBHOOK_URL=https://n8n.opencaio.cn/webhook`

### 数据存储

- **数据库**: `backend/database/auto_geo_v3.db`
- **Cookies**: `.cookies/` 目录
- **日志**: `logs/` 目录

## 团队协作规范

> 📖 参与项目开发前，请先阅读以下规范文档，这会让我们的协作更高效！

### 核心文档

| 文档 | 说明 | 链接 |
|------|------|------|
| 📖 **贡献指南** | 如何参与项目开发、提交代码、创建PR | [CONTRIBUTING.md](./CONTRIBUTING.md) |
| 🤝 **行为准则** | 社区行为规范，营造友好的开发环境 | [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) |
| 📋 **协作规范** | 分支管理、提交规范、PR流程等详细规范 | [团队协作指南](./docs/TEAM_COLLABORATION_GUIDE.md) |

### 快速链接

- [🐛 报告Bug](https://github.com/Architecture-Matrix/auto_geo/issues/new?template=bug_report.md)
- [✨ 提交功能建议](https://github.com/Architecture-Matrix/auto_geo/issues/new?template=feature_request.md)
- [💡 技术改进建议](https://github.com/Architecture-Matrix/auto_geo/issues/new?template=improvement.md)
- [📖 报告文档问题](https://github.com/Architecture-Matrix/auto_geo/issues/new?template=documentation.md)

### 开发流程概览

```bash
# 1. Fork并克隆项目
git clone https://github.com/你的用户名/auto_geo.git

# 2. 创建功能分支
git checkout -b feature/your-feature-name

# 3. 开发并提交
git add .
git commit -m "feat: 添加功能描述"

# 4. 推送并创建PR
git push origin feature/your-feature-name
# 然后在GitHub上创建Pull Request

# 5. 等待Code Review，根据意见修改
# 6. 合并后删除分支
```

### 提交规范

```bash
# 提交格式: <type>(<scope>): <subject>

type类型:
- feat: 新功能
- fix: Bug修复
- docs: 文档更新
- style: 代码格式调整
- refactor: 重构
- perf: 性能优化
- test: 测试相关
- chore: 构建/工具相关

# 示例
git commit -m "feat: 添加关键词蒸馏API端点"
git commit -m "fix: 修复知乎发布失败问题"
```

---

## 常见问题

### Q: 前端启动后提示无法连接后端？

A: 需要先启动后端服务。开两个终端，分别运行：
- 终端1: `cd backend && python main.py`
- 终端2: `cd fronted && npm run dev`

### Q: n8n webhook 调用失败？

A: 根据错误类型排查：

**HTTP 404 错误**（工作流未注册）：
- 该工作流未在云端激活，需要登录 n8n 管理界面
- 找到对应工作流，点击右上角 **Active** 开关激活
- 确认 Webhook 路径正确

**超时错误**：
- 检查网络连接是否正常
- 长任务（如文章生成）可能需要 2-5 分钟

**其他错误**：
- 确认 `.env` 文件中 `N8N_WEBHOOK_URL` 配置正确
- DeepSeek API 凭证是否配置正确

**当前云端工作流**（仅两个）：
- ✅ `keyword-distill` - 关键词蒸馏
- ✅ `geo-article-generate` - GEO文章生成

### Q: 如何使用云端 n8n 而不是本地部署？

A:
```bash
# 1. 复制环境变量模板
cp .env.example .env

# 2. 编辑 .env 文件，设置云端地址
N8N_WEBHOOK_URL=https://n8n.opencaio.cn/webhook

# 3. 重启后端服务即可
```

### Q: Windows下构建内存不足？

A: 这是大项目构建的常见问题，使用开发模式即可：`npm run dev`

### Q: 如何启动定时任务？

A: 后端启动后调用 `POST /api/scheduler/start` 即可启动定时检测

### Q: 如何更换 AI 服务商？

A: 只需在 n8n 中修改 AI 节点的凭证配置，无需修改业务代码！

## 更新日志

### v3.0.0 (2026-02-24) - 🚀 CI/CD自动化版本

**CI/CD自动化**：
- ✅ **Startup Validation工作流**：确保clone后能正常启动前后端
- ✅ **前端启动验证**：自动修复Electron path.txt问题
- ✅ **后端启动验证**：健康检查和API端点验证
- ✅ **依赖验证**：自动检查requirements.txt和package.json
- ✅ **文档检查**：确保README和启动文档完整

**Electron修复**：
- ✅ **自动修复脚本**：`scripts/fix/fix-electron.bat` (Windows)
- ✅ **自动修复脚本**：`scripts/fix/fix-electron.sh` (Linux/macOS)
- ✅ **集成到quickstart**：启动时自动检测并修复Electron问题
- ✅ **CI自动修复**：GitHub Actions中自动应用修复

**文档完善**：
- ✅ **新增SETUP.md**：详细的项目设置指南
- ✅ **常见问题解答**：覆盖所有已知安装问题
- ✅ **CI/CD说明**：完整的自动化流程文档
- ✅ **开发工作流**：分支策略和提交规范

**CI配置修复**：
- ✅ 修复前端CI：pnpm → npm
- ✅ 添加启动测试：确保服务真正能运行
- ✅ 跨平台测试：Windows + Linux
- ✅ 允许测试失败：构建和测试不影响合并

### v2.9.0 (2026-02-10)
- ✅ **简化云端 n8n 工作流**：仅保留两个核心 webhook
- ✅ `keyword-distill` - 关键词蒸馏 ✅ 已激活
- ✅ `geo-article-generate` - GEO文章生成 ✅ 已激活
- ❌ 移除 `generate-questions` 和 `index-check-analysis`
- ✅ 更新 FAQ，同步云端工作流状态

### v2.8.0 (2026-02-03)
- ✅ **简化依赖管理**：删除多余的 `requirements-dev.txt`，只保留一个 `requirements.txt`
- ✅ **移除冗余文档**：删除 `backend/DEPENDENCIES.md`，简化项目结构
- ✅ **精简依赖说明**：更新 README，只保留开发环境需要的依赖

### v2.7.0 (2026-02-03)
- ✅ **集成清理功能**：将清理工具集成到 `start.bat` 主菜单
- ✅ **统一管理界面**：一个脚本搞定启动、重启、清理所有操作
- ✅ **清理子菜单**：快速清理/完全清理可选，返回主菜单更方便
- ✅ **版本同步**：`start.bat` 和 `scripts/quickstart-cmd.bat` 保持同步

### v2.4.0 (2026-02-03)
- ✅ **后端依赖大清理**：移除 torch 等冗余包，节省 ~5GB 空间
- ✅ **快速启动工具**：优化 `start.bat`，增加依赖检查和窗口管理
- ✅ **项目清理工具**：新增 `scripts/cleanup.bat`，一键清理缓存和临时文件

### v2.3.0 (2026-02-03)
- ✅ 创建完整的GitHub团队开发规范
- ✅ 更新所有项目文档的负责人信息
- ✅ 建立Issue和PR模板系统
- ✅ 创建项目信息记录文档
- ✅ 更新n8n工作流（GEOv0.0.2）

### v2.2.0 (2025-01-26)
- ✅ 更换富文本编辑器：ByteMD → WangEditor 5
- ✅ WangEditor 支持所见即所得编辑
- ✅ 完善图片上传功能，支持拖拽上传
- ✅ 代码高亮支持 17 种编程语言
- ✅ 深色模式样式优化
- ✅ 创建前端技术文档 `fronted/FRONTEND.md`

### v2.1.0 (2025-01-22)
- ✅ 新增 n8n AI 中台架构
- ✅ AI 能力与业务代码解耦
- ✅ 创建 n8n 工作流（关键词蒸馏、文章生成、收录分析）
- ✅ 后端新增 n8n_service.py 封装
- ✅ 换 AI 服务商只需改 n8n 配置，不动代码

### v2.0.0 (2025-01-17)
- ✅ 完成预警通知系统
- ✅ 完成定时任务系统(集成预警检查)
- ✅ 完成数据统计报表
- ✅ 完成GEO文章生成
- ✅ 完成收录检测功能
- ✅ 前后端对接测试通过
- ✅ 所有API正常工作

### v1.0.0 (2025-01-13)
- ✅ 基础多平台发布功能
- ✅ 账号管理与授权
- ✅ 文章编辑与发布

## 许可证

MIT License

---

**维护者**: 小a
**更新日期**: 2026-02-24
**版本**: v3.0.0 (🚀 CI/CD自动化 - 确保clone后能启动)
