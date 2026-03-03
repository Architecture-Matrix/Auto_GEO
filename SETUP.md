# 🚀 AutoGeo 项目设置指南

**更新日期**: 2026-02-25

---

## 📋 目录

1. [前置要求](#前置要求)
2. [快速开始](#快速开始)
3. [详细设置步骤](#详细设置步骤)
4. [常见问题](#常见问题)
5. [CI/CD说明](#cicd说明)
   - [工作流概览](#工作流列表)
   - [后端部署](#backend-deploy-部署流程)
   - [启动验证](#启动验证工作流详解)
6. [开发工作流](#开发工作流)

---

## 前置要求

### 必需软件

| 软件 | 版本要求 | 用途 | 下载地址 |
|------|---------|------|---------|
| **Node.js** | 18+ | 前端运行时 | https://nodejs.org/ |
| **Python** | 3.10+ | 后端运行时 | https://www.python.org/ |
| **Git** | 最新版 | 版本控制 | https://git-scm.com/ |

### 可选软件

| 软件 | 用途 | 说明 |
|------|------|------|
| **Docker** | 运行n8n容器 | 推荐使用云端n8n，无需本地安装 |
| **VS Code** | 代码编辑器 | 推荐编辑器 |
| **Postman** | API测试 | 可选，后端有自带文档 |

### 操作系统支持

- ✅ **Windows 10/11** - 完全支持
- ✅ **macOS** - 完全支持
- ✅ **Linux** - 完全支持

---

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/Architecture-Matrix/Auto_GEO.git
cd Auto_GEO
```

### 2. 一键启动（推荐）

**Windows用户**：
```bash
# 双击运行或在命令行执行
quickstart.bat
```

**Linux/macOS用户**：
```bash
chmod +x quickstart.sh
./quickstart.sh
```

### 3. 选择启动选项

启动后会显示菜单：
```
[1] 启动后端服务（新窗口）
[2] 启动前端 Electron 应用（新窗口）
[3] 重启后端服务
[4] 重启前端服务
[5] 清理项目缓存
[6] 退出（关闭所有服务）
```

**首次启动请按顺序选择 1 → 2**

---

## 详细设置步骤

### 步骤1: 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

**如果pip安装失败**，尝试：
```bash
# 使用国内镜像源加速
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 步骤2: 安装Playwright浏览器

```bash
playwright install chromium
```

**说明**：这个SB的浏览器自动化工具需要下载Chromium，大概300MB，耐心等待！

### 步骤3: 配置环境变量

```bash
# 复制环境变量模板
cd ..
cp .env.example .env

# 编辑.env文件（可选，使用云端n8n无需修改）
# Windows用户:
notepad .env

# Linux/macOS用户:
nano .env
```

**默认配置**（使用云端n8n）：
```bash
N8N_WEBHOOK_URL=https://n8n.opencaio.cn/webhook
```

### 步骤4: 启动后端服务

```bash
cd backend
python main.py
```

**验证启动成功**：
- 浏览器访问: http://127.0.0.1:8001
- API文档: http://127.0.0.1:8001/docs
- 看到 `Uvicorn running on http://127.0.0.1:8001` 表示成功！

### 步骤5: 安装前端依赖

```bash
cd frontend
npm install
```

**如果npm安装失败**，尝试：
```bash
# 清理缓存重试
npm cache clean --force
npm install

# 或使用国内镜像
npm install --registry=https://registry.npmmirror.com
```

### 步骤6: 修复Electron安装问题

**Windows用户**：
```bash
cd ..
scripts\fix-electron.bat
```

**Linux/macOS用户**：
```bash
cd ..
chmod +x scripts/fix-electron.sh
./scripts/fix-electron.sh
```

**说明**：这个Electron安装经常半途失败，写了修复脚本自动处理！

### 步骤7: 启动前端应用

```bash
cd frontend
npm run dev
```

**验证启动成功**：
- 看到Electron窗口弹出
- 或者浏览器访问: http://127.0.0.1:5173
- 看到AutoGeo界面表示成功！

---

## 常见问题

### Q1: 后端启动失败 `ModuleNotFoundError`

**原因**：Python依赖未正确安装

**解决方案**：
```bash
cd backend
pip install -r requirements.txt
```

### Q2: 前端启动失败 `Electron failed to install correctly`

**原因**：Electron的`path.txt`文件缺失

**解决方案**：
```bash
# Windows
scripts\fix-electron.bat

# Linux/macOS
./scripts/fix-electron.sh
```

### Q3: Playwright浏览器未安装

**错误信息**：`Executable doesn't exist at ...`

**解决方案**：
```bash
playwright install chromium
```

### Q4: 端口被占用

**错误信息**：`Address already in use` 或 `端口已被占用`

**解决方案**：

**Windows**：
```bash
# 查找占用端口的进程
netstat -ano | findstr ":8001"

# 结束进程（替换PID）
taskkill /F /PID <进程ID>
```

**Linux/macOS**：
```bash
# 查找占用端口的进程
lsof -i :8001

# 结束进程
kill -9 <进程ID>
```

### Q5: npm install速度慢或失败

**解决方案**：
```bash
# 使用国内镜像
npm config set registry https://registry.npmmirror.com
npm install

# 临时使用镜像
npm install --registry=https://registry.npmmirror.com
```

### Q6: pip install速度慢或失败

**解决方案**：
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## CI/CD说明

### GitHub Actions 工作流

项目配置了自动化CI/CD，确保每次代码变更都能正常启动！

#### 工作流列表 <a name="工作流列表"></a>

| 工作流 | 触发条件 | 验证内容 | 配置文件 |
|-------|---------|---------|---------|
| **Startup Validation** | push/PR | ✅ 后端启动<br>✅ 前端构建<br>✅ 依赖安全检查<br>✅ 文档检查 | [`.github/workflows/startup-validation.yml`](.github/workflows/startup-validation.yml) |
| **Frontend CI** | push/PR到frontend | ✅ 代码检查<br>✅ 类型检查<br>✅ 单元测试<br>✅ 构建验证 | [`.github/workflows/frontend-ci.yml`](.github/workflows/frontend-ci.yml) |
| **Backend CI** | push/PR到backend | ✅ 代码检查<br>✅ 类型检查<br>✅ 单元测试<br>✅ 安全扫描 | [`.github/workflows/backend-ci.yml`](.github/workflows/backend-ci.yml) |
| **Backend Deploy** | push到main | ✅ Docker构建<br>✅ 推送到阿里云ACR<br>✅ 自动部署到服务器 | [`.github/workflows/backend-deploy.yml`](.github/workflows/backend-deploy.yml) |
| **Electron Build** | push/PR到frontend | ✅ 跨平台打包<br>✅ 构建安装包 | [`.github/workflows/electron-build.yml`](.github/workflows/electron-build.yml) |

#### Backend Deploy 部署流程

**备注**：这个工作流负责后端自动部署，使用阿里云ACR加速镜像拉取！

**部署架构**：
```
GitHub Actions → 构建Docker镜像
                      ├── 推送到 GHCR (备用)
                      └── 推送到 阿里云ACR (优先) ⚡

服务器部署 → 优先从阿里云ACR拉取（广州内网速度飞快）
                  └── 失败则从GHCR拉取
```

**镜像仓库地址**：
| 仓库 | 地址 | 说明 |
|-----|------|------|
| 阿里云ACR（广州） | `crpi-lwz264sedmauvivo.cn-guangzhou.personal.cr.aliyuncs.com/opencaio/auto_geo_backend` | 优先拉取，速度快 |
| GHCR | `ghcr.io/architecture-matrix/auto_geo_backend` | 备用仓库 |

**所需GitHub Secrets**：
| Secret名称 | 说明 | 获取方式 |
|-----------|------|---------|
| `ALIYUN_ACR_USERNAME` | 阿里云账号全名（如 xxx@aliyun.com） | 阿里云控制台 |
| `ALIYUN_ACR_PASSWORD` | ACR Registry登录密码 | [访问凭证设置](https://cr.console.aliyun.com/) → 设置Registry登录密码 |
| `SERVER_HOST` | 服务器IP地址 | - |
| `SERVER_USER` | SSH登录用户名 | - |
| `SERVER_SSH_KEY` | SSH私钥 | `cat ~/.ssh/id_rsa` |
| `BACKEND_PORT` | 后端端口（可选，默认8001） | - |

**部署策略**：
1. 先拉取新镜像（失败不影响旧服务）
2. 镜像拉取成功后才停止旧容器
3. 启动新容器并健康检查
4. 自动清理旧镜像

#### 启动验证工作流详解 <a name="启动验证工作流详解"></a>

**备注**：这个工作流专门验证clone后能否启动，包含以下检查：

1. **后端启动检查** (`backend-startup`)：
   - 安装Python依赖
   - 安装Playwright浏览器
   - 启动后端服务
   - 健康检查API端点
   - 验证关键API可用性

2. **前端启动检查** (`frontend-startup`)：
   - 安装Node.js依赖（使用Electron国内镜像）
   - 自动修复Electron path.txt
   - 构建渲染进程
   - 构建Electron主进程
   - 验证Electron可执行文件存在
   - 验证构建输出完整性
   - **⚠️ 注意**：CI环境无GUI，不启动Electron窗口，只验证构建成功

3. **依赖安全检查** (`dependency-check`)：
   - **前端依赖审查**：检查已知漏洞、许可证合规性
   - **后端依赖审计**：使用pip-audit检查安全漏洞
   - 验证依赖文件存在性

4. **文档检查** (`docs-check`)：
   - 检查README.md
   - 验证包含启动说明
   - 检查快速启动脚本

#### 查看CI/CD状态

访问项目的Actions页面：
```
https://github.com/Architecture-Matrix/Auto_GEO/actions
```

**状态标识**：
- ✅ 绿色勾 = 所有检查通过
- ❌ 红色叉 = 检查失败，需要修复
- 🟡 黄色圆 = 运行中

#### 本地测试CI/CD

使用 [act](https://github.com/nektos/act) 在本地运行GitHub Actions：

```bash
# 安装act（macOS/Linux）
brew install act

# 安装act（Windows）
choco install act-cli

# 运行启动验证工作流
act -W .github/workflows/startup-validation.yml
```

---

## 开发工作流

### 分支策略

```bash
# 1. 从main创建功能分支
git checkout -b feature/your-feature-name

# 2. 开发并提交
git add .
git commit -m "feat: 添加功能描述"

# 3. 推送到远程
git push origin feature/your-feature-name

# 4. 创建Pull Request
# 在GitHub上创建PR，CI会自动运行

# 5. 等待CI检查通过
# 所有绿色勾后才能合并

# 6. 合并到main
git checkout main
git pull origin main
```

### 提交规范

```bash
# 格式: <type>(<scope>): <subject>

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
git commit -m "feat(backend): 添加关键词蒸馏API端点"
git commit -m "fix(frontend): 修复Electron启动失败问题"
git commit -m "docs: 更新SETUP.md添加CI/CD说明"
```

### 本地开发检查清单

在提交代码前，确保：

- [ ] 后端能正常启动 (`python main.py`)
- [ ] 前端能正常启动 (`npm run dev`)
- [ ] 没有代码格式错误
- [ ] 没有类型检查错误
- [ ] 新功能有对应的测试
- [ ] 文档已更新

---

## 一键修复脚本

项目提供了自动修复脚本，解决常见安装问题：

### fix-electron.bat (Windows)

```bash
scripts\fix-electron.bat
```

**功能**：
- 自动检测Electron安装状态
- 创建缺失的path.txt文件
- 验证修复结果

### fix-electron.sh (Linux/macOS)

```bash
./scripts/fix-electron.sh
```

**功能**：
- 自动检测操作系统
- 创建对应的path.txt文件
- 验证修复结果

---

## 需要帮助？

### 查看日志

**后端日志**：
```bash
tail -f logs/backend.log
```

**前端日志**：
查看Electron窗口的控制台输出

### 报告问题

如果遇到问题：

1. 查看 [常见问题](#常见问题) 章节
2. 搜索已有Issue: https://github.com/Architecture-Matrix/Auto_GEO/issues
3. 创建新Issue并附上：
   - 操作系统版本
   - 错误信息截图
   - 复现步骤

### 联系方式

- **GitHub Issues**: https://github.com/Architecture-Matrix/Auto_GEO/issues
- **维护者**: 小a

---

**祝你设置顺利！** 💪
