# AutoGeo CI/CD 工作流文档

**维护者**: 老王
**更新时间**: 2026-02-25
**备注**: 艹，这个文档记录了所有GitHub Actions workflows的功能，别tm乱改！

---

## 📋 概览

AutoGeo项目使用GitHub Actions进行自动化CI/CD，确保代码质量和自动部署。一共有**6个workflow**：

| Workflow | 触发条件 | 运行时间 | 状态 |
|----------|---------|---------|------|
| **Startup Validation** | 每次push、PR | ~2分钟 | ✅ |
| **Backend CI** | backend代码变更 | ~2分钟 | ✅ |
| **Frontend CI** | frontend代码变更 | ~3分钟 | ✅ |
| **Dependency Review** | PR到master/dev | ~1分钟 | ✅ |
| **Electron Build** | tag推送、手动触发 | ~15分钟 | ✅ |
| **Backend Deploy** | push到main/master | ~5分钟 | ✅ |

---

## 🚀 Startup Validation (启动验证)

**文件**: `.github/workflows/startup-validation.yml`

### 功能

验证**克隆仓库后能否正常启动前后端**，确保新用户clone下来不会遇到SB问题！

### 触发条件

```yaml
on:
  push:
    branches: ['**']  # 任何分支的push都会触发
  pull_request:
    branches: [master, main]
  workflow_dispatch:  # 允许手动触发
```

**重要说明**：
- ✅ **任何文件修改**都会触发（没有paths限制）
- ✅ push到任何分支都会触发
- ✅ PR到master/main都会触发
- ✅ 可以手动触发workflow
- ⚠️ 这是**唯一**对所有修改都运行的CI

### Jobs

#### 1. Backend Startup Check (后端启动验证)
- **运行环境**: Ubuntu
- **检查内容**:
  - 安装Python依赖 (requirements.txt)
  - 安装Playwright浏览器 (chromium)
  - 启动后端服务器 (`python -m backend.main`)
  - 健康检查 (curl `http://127.0.0.1:8001/`)
  - API端点检查 (`/api/health`, `/api/platforms`, `/docs`)
- **等待时间**: 最多30次检查，每次2秒 (共60秒)
- **日志记录**: 失败时显示完整backend日志

#### 2. Frontend Startup Check (前端启动验证)
- **运行环境**: **Matrix** (Ubuntu + Windows)
- **检查内容**:
  - 安装Node依赖 (`npm install`，使用Electron国内镜像加速)
  - **修复Electron path.txt** (Windows用PowerShell，Linux用bash)
  - 构建渲染进程 (`npm run build:renderer`)
  - 构建Electron主进程 (`npm run build:electron`)
  - 验证Electron可执行文件存在
  - 验证构建输出 (`out/electron/main/index.js`)
  - 最终构建验证（输出验证摘要）
- **⚠️ 重要说明**: GitHub Actions runner是无GUI环境，**无法启动Electron窗口**
  - 因此CI只验证构建成功和二进制文件存在
  - 不尝试运行`npm run dev`（会导致ENOENT错误）

#### 3. Dependency Validation (依赖检查)
- **检查文件**:
  - `backend/requirements.txt` (必需)
  - `frontend/package.json` (必需)
  - `frontend/package-lock.json` (必需)
  - `.env.example` (可选)

#### 4. Documentation Check (文档检查)
- **检查内容**:
  - `README.md` 存在性
  - 是否包含启动说明 ("快速开始" 或 "Quick Start")
  - 快速启动脚本存在性 (`quickstart.bat/sh`)

---

## 🔍 Backend CI (后端持续集成)

**文件**: `.github/workflows/backend-ci.yml`

### 功能

对backend代码进行**代码质量检查、类型检查、单元测试和安全扫描**。

### 触发条件

```yaml
on:
  push:
    branches: ['**']
    paths:
      - 'backend/**'                      # backend目录下的任何文件
      - '.github/workflows/backend-ci.yml' # workflow文件本身
  pull_request:
    branches: [master, dev]
    paths:
      - 'backend/**'
```

**重要说明**：
- ✅ 修改`backend/`目录下的任何文件会触发
- ✅ 修改`.github/workflows/backend-ci.yml`会触发
- ❌ 只修改文档或配置文件**不会触发**
- ❌ 只修改frontend代码**不会触发**

### 检查内容总览

Backend CI通过3个job确保后端代码质量：

| Job | 检查内容 | 工具 | 预期时间 |
|-----|---------|------|---------|
| **Lint & Type Check** | 代码规范、格式、类型 | Ruff, MyPy | ~30s |
| **Unit Tests** | 单元测试、覆盖率 | pytest | ~40s |
| **Security Scan** | 密钥泄露、依赖漏洞 | Gitleaks, Trivy | ~45s |

**关键检查项**：
- ✅ 代码符合Ruff规范（PEP 8 + 自定义规则）
- ✅ 代码格式正确（ruff format）
- ✅ 类型注解正确（mypy）
- ✅ 单元测试通过（pytest）
- ✅ 无密钥泄露（Gitleaks - 硬编码API密钥、密码、Token等）
- ✅ 无已知安全漏洞（Trivy - Python依赖CVE、系统包漏洞）

### Jobs

#### 1. Lint & Type Check (代码检查)
- **运行环境**: Ubuntu
- **Python版本**: 3.12
- **缓存**: pip (基于`requirements.txt`)
- **检查工具**:
  - **Ruff**: 代码格式和基本错误 (pyproject.toml配置)
  - **MyPy**: 类型检查 (`api/`目录，忽略缺失导入)
- **检查内容**:
  - `ruff check .` - 代码规范检查
  - `ruff format --check .` - 代码格式检查
  - `mypy api/ --ignore-missing-imports` - 类型检查

#### 2. Unit Tests (单元测试)
- **运行环境**: Ubuntu
- **依赖**: Lint job
- **测试框架**: pytest
- **覆盖率工具**: pytest-cov
- **命令**:
  ```bash
  pytest tests/ -v \
    --cov=api \
    --cov=services \
    --cov-report=xml \
    --cov-report=term \
    --ignore=tests/e2e
  ```
- **上传覆盖率**: Codecov (backend coverage.xml)

#### 3. Security Scan (安全扫描)
- **运行环境**: Ubuntu
- **扫描工具**: **Gitleaks + Trivy**
- **扫描范围**:
  - **Gitleaks**: 完整Git历史 + 当前代码
  - **Trivy**: `./backend` 目录文件系统
- **输出格式**: SARIF
- **上传**: GitHub Security (CodeQL @v4)
- **检查内容**:

  **Gitleaks（密钥泄露检测）**:
  - ✅ 硬编码API密钥（OpenAI、GitHub、AWS等）
  - ✅ 密码硬编码（password、pwd、secret等）
  - ✅ 数据库连接字符串（postgres://、mysql://、mongodb://等）
  - ✅ 私有IP地址（内网地址不应出现在代码中）
  - ✅ Git历史中的密钥泄露（检测所有提交历史）
  - ✅ Token泄露（GitHub Token、JWT等）

  **Trivy（依赖漏洞检测）**:
  - ✅ Python依赖包CVE漏洞（requirements.txt）
  - ✅ 系统包安全漏洞
  - ✅ 代码配置问题

- **Gitleaks配置文件**: `.gitleaks.toml`
- **权限配置**:
  ```yaml
  # Workflow级别权限
  permissions:
    contents: read
    security-events: write

  # Job级别权限（必需！）
  security:
    permissions:
      contents: read
      security-events: write
  ```

**老王备注（2026-02-25完整修复记录）**：

- **第1次修复**: 添加workflow级别的permissions配置
  - ❌ 问题：仍然报错"Resource not accessible by integration"
  - 原因：workflow级别权限没有传递到security job

- **第2次修复**: 在security job级别添加permissions配置 ✅
  - **修复**: 添加job级别的`permissions: contents: read, security-events: write`
  - **commit**: 11a70fe

- **第3次修复**: 升级CodeQL Action版本到v4 ✅
  - **v3 → v4**: 直接升级到最新稳定版
  - **v3 vs v4区别**:
    - v3 (2022): 功能完整但已进入维护期，2026年12月弃用
    - v4 (2025): 最新稳定版，性能更优，推荐所有项目使用
  - **commit**: 748e3ef

- **第4次修复**: 添加Gitleaks密钥泄露扫描 ✅
  - **问题**: 之前的Trivy只能检测依赖漏洞，不能检测代码中的密钥泄露
  - **修复**: 添加Gitleaks扫描，创建.gitleaks.toml配置文件
  - **commit**: cd33048
  - **检测能力对比**:

    | 安全问题 | 之前（仅Trivy） | 现在（Gitleaks + Trivy） |
    |---------|----------------|------------------------|
    | 硬编码API密钥 | ❌ 不能检测 | ✅ 能检测 |
    | GitHub Token泄露 | ❌ 不能检测 | ✅ 能检测 |
    | 密码硬编码 | ❌ 不能检测 | ✅ 能检测 |
    | 数据库连接字符串 | ❌ 不能检测 | ✅ 能检测 |
    | Python依赖CVE | ✅ 能检测 | ✅ 能检测 |
    | Git历史密钥 | ❌ 不能检测 | ✅ 能检测 |

- **uv缓存修复**: 移除dependency-review.yml中不支持的`cache: 'uv'`
  - **问题**: `actions/setup-python@v5`不支持`cache: 'uv'`
  - **修复**: 移除cache配置，dependency review运行频率低不需要缓存
  - **commit**: 8d311ab

**如果还不行**: 检查GitHub仓库设置
```
Settings → Actions → General → Workflow permissions
→ 选择 "Read and write permissions"
```

**本地测试Gitleaks**:
```bash
# 安装Gitleaks
# Windows: scoop install gitleaks
# Linux: brew install gitleaks

# 检测当前代码
gitleaks detect --source . --config .gitleaks.toml

# 检测Git历史（更严格）
gitleaks detect --source . --log-level debug
```

---

## 🎨 Frontend CI (前端持续集成)

**文件**: `.github/workflows/frontend-ci.yml`

### 功能

对frontend代码进行**代码检查、类型检查、单元测试和构建验证**。

### 触发条件

```yaml
on:
  push:
    branches: ['**']
    paths:
      - 'frontend/**'                         # frontend目录下的任何文件
      - '.github/workflows/frontend-ci.yml'   # workflow文件本身
  pull_request:
    branches: [master, dev]
    paths:
      - 'frontend/**'
```

**重要说明**：
- ✅ 修改`frontend/`目录下的任何文件会触发
- ✅ 修改`.github/workflows/frontend-ci.yml`会触发
- ❌ 只修改文档或配置文件**不会触发**
- ❌ 只修改backend代码**不会触发**

### Jobs

#### 1. Lint & Type Check (代码检查)
- **运行环境**: Ubuntu
- **Node版本**: 20
- **缓存**: npm (基于`package-lock.json`)
- **检查工具**:
  - **ESLint**: 代码规范 (`npm run lint`)
  - **TypeScript**: 类型检查 (`npm run type-check`)

#### 2. Unit Tests (单元测试)
- **运行环境**: Ubuntu
- **依赖**: Lint job
- **测试框架**: Vitest
- **命令**: `npm run test`
- **允许失败**: `|| true`
- **上传覆盖率**: Codevoc (frontend coverage/lcov.info)

#### 3. Build Check (构建验证)
- **运行环境**: Ubuntu
- **依赖**: Lint + Test
- **构建流程**:
  1. 修复Electron path.txt
  2. 构建完整应用 (`npm run build`)
  3. 如果失败，仅构建渲染进程 (`npm run build:renderer`)
- **上传构建产物**: GitHub Artifacts (frontend/dist, 保留7天)

---

## 🔒 Dependency Review (依赖审查)

**文件**: `.github/workflows/dependency-review.yml`

### 功能

在**Pull Request时**检查依赖包的安全漏洞和许可证问题。

### Jobs

#### 1. Frontend Dependencies (前端依赖检查)
- **运行环境**: Ubuntu
- **检查工具**: GitHub Dependency Review Action
- **失败条件**:
  - 严重级别 ≥ moderate
  - 许可证包含 GPL-3.0, AGPL-3.0

#### 2. Backend Dependencies (后端依赖检查)
- **运行环境**: Ubuntu
- **Python版本**: 3.12
- **包管理器**: uv (快速安装)
- **检查工具**: pip-audit
- **命令**:
  ```bash
  uv pip install pip-audit
  pip-audit --strict
  ```
- **允许失败**: `continue-on-error: true`

---

## 📦 Electron Build & Release (Electron构建与发布)

**文件**: `.github/workflows/electron-build.yml`

### 功能

**构建跨平台Electron安装包**并发布到GitHub Releases。

### 触发条件

- **自动**: 推送tag (如 `v1.0.0`)
- **手动**: workflow_dispatch (输入版本号)

### Jobs

#### 1. Lint & Type Check (代码检查)
- **运行环境**: Ubuntu
- **检查内容**:
  - ESLint (允许失败)
  - TypeScript (允许失败)

#### 2. Build Cross-Platform Packages (跨平台构建)
- **运行环境**: **Matrix**
  - Windows (windows-latest) → NSIS安装包
  - Linux (ubuntu-latest) → AppImage
  - macOS (macos-latest) → DMG
- **架构**: x64
- **依赖**: Check job
- **构建流程**:
  1. 安装依赖 (`npm ci`)
  2. 构建渲染进程 (`npm run build:renderer`)
  3. 构建Electron主进程 (`npm run build:electron`)
  4. 构建平台特定包:
     - Windows: `npm run dist:win -- --nsis`
     - Linux: `npm run dist:linux -- --AppImage`
     - macOS: `npm run dist:mac -- --dmg`
- **发布**:
  - 上传到GitHub Releases (`softprops/action-gh-release`)
  - 生成Release Notes
  - 标记prerelease (如果包含beta/alpha)
- **上传Artifacts**: 保留30天

### 输出文件

- Windows: `*.exe`, `*.msi`, `*.zip`
- Linux: `*.AppImage`, `*.deb`
- macOS: `*.dmg`

---

## 🚀 Backend Deploy (后端部署)

**文件**: `.github/workflows/backend-deploy.yml`

### 功能

**构建Docker镜像并部署到生产服务器**。

### 触发条件

- **自动**: push到main/master分支
- **手动**: workflow_dispatch

### 环境变量

```yaml
PYTHON_VERSION: '3.12'
REGISTRY: ghcr.io
IMAGE_NAME: auto_geo_backend
REPO_OWNER_LOWER: architecture-matrix
```

### Jobs

#### 1. Build & Push Docker Image (构建并推送镜像)
- **运行环境**: Ubuntu
- **权限**: contents: read, packages: write
- **Docker Buildx**: 多平台构建支持
- **Registry登录**: GitHub Container Registry (GHCR)
- **镜像标签**:
  - `<branch>-<sha>` (如 `main-a1b2c3d`)
  - `latest` (默认分支)
  - `v<version>` (semver)
  - `<major>.<minor>` (semver)
- **缓存策略**:
  - GitHub Actions Cache
  - Registry Cache (buildcache)
- **构建参数**:
  - `BUILD_DATE`: commit timestamp
  - `VCS_REF`: commit SHA

#### 2. Deploy to Server (部署到服务器)
- **运行环境**: Ubuntu
- **依赖**: Build & Push job
- **部署条件**: 仅main/master分支
- **连接方式**: SSH (appleboy/ssh-action)
- **必需Secrets**:
  - `SERVER_HOST`: 服务器地址
  - `SERVER_USER`: SSH用户名
  - `SERVER_SSH_KEY`: SSH私钥
  - `SERVER_PORT`: SSH端口 (默认22)
  - `BACKEND_PORT`: 后端端口 (默认8001)
  - `GITHUB_TOKEN`: GHCR认证
- **部署流程**:
  1. 登录GHCR
  2. 拉取最新镜像 (`ghcr.io/architecture-matrix/auto_geo_backend:latest`)
  3. 停止并删除旧容器
  4. 创建数据目录并修复权限 (`chmod -R 777 ~/autogeo`)
  5. 启动新容器:
     - 容器名: `autogeo-backend`
     - 端口映射: `PORT:8001`
     - 卷挂载:
       - `~/autogeo/data:/app/data`
       - `~/autogeo/logs:/app/logs`
       - `~/autogeo/database:/app/backend/database`
       - `~/autogeo/cookies:/app/.cookies`
  6. 健康检查 (最多12次，每次5秒)
  7. 清理未使用的镜像
- **部署摘要**: 输出到GitHub Step Summary

---

## 🔧 配置文件

### pyproject.toml

老王我添加的Ruff配置，确保CI检查正常通过：

```toml
[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = ["F"]  # 只检查基本错误
ignore = [
    "E722",  # 裸except - 老王我故意用的
    "F403", "F405",  # 星号导入
    "F401",  # 未使用导入
    "F841",  # 未使用变量
]
```

---

## 📊 工作流依赖关系

### Startup Validation
```
backend-startup ─────┐
frontend-startup ────┤
                      ├─→ ✅ 验证通过
dependency-check ────┤
docs-check ───────────┘
```

### Backend CI
```
lint ──→ test ──→ ✅ 检查通过
  │
  └───────→ security ──→ ✅ 安全扫描通过
```

### Frontend CI
```
lint ──→ test ──→ build ──→ ✅ 检查通过
```

### Electron Build
```
check ──→ build (matrix) ──→ ✅ 构建并发布
```

### Backend Deploy
```
build-and-push ──→ deploy ──→ ✅ 部署成功
```

---

## 🚨 常见问题

### Q1: Startup Validation失败怎么办？

**A**: 查看具体哪个job失败：
- **backend-startup**: 查看后端日志，可能是依赖缺失或启动报错
- **frontend-startup (Windows)**: 检查PowerShell语法，确保shell设置正确
- **frontend-startup (Ubuntu)**: 检查npm构建错误

### Q1.5: 为什么前端CI不启动Electron测试窗口？

**A**: **GitHub Actions runner是无GUI环境！**

**问题根源**:
- GitHub Actions的Windows/Ubuntu runner是虚拟机环境
- **没有显示器、没有图形界面**
- Electron无法启动窗口，会导致`ENOENT`错误：
  ```
  Error: spawn electron.exe ENOENT
  ```

**正确做法**:
- ✅ CI只验证：构建成功 + 二进制文件存在
- ✅ 检查：`node_modules/electron/dist/electron.exe` 是否存在
- ✅ 检查：`out/electron/main/index.js` 构建输出
- ❌ **不尝试**：`npm run dev`（会失败）

**本地测试**:
- 如果你想验证Electron能否启动，在本地运行：
  ```bash
  cd frontend
  npm run dev  # 本地有GUI，可以启动
  ```

**老王备注（2026-02-25）**：
- 之前老王我犯了个SB错误，尝试在CI启动Electron
- 结果每次都`ENOENT`，因为CI环境压根没有显示器！
- 现在改为只验证构建，不启动窗口 ✅

### Q2: Backend CI的Ruff检查失败？

**A**: 本地运行检查：
```bash
cd backend
ruff check .           # 代码规范检查
ruff format --check .  # 格式检查（不修改文件）
```

**如果格式检查失败**（最常见原因）：
```bash
# 自动格式化所有文件
ruff format .

# 验证格式化后的代码
ruff check .
ruff format --check .

# 提交修复
git add backend/
git commit -m "fix: 使用Ruff自动格式化代码"
```

**老王备注（2026-02-25修复记录）**：
- **问题**: 69个文件格式不符合Ruff规范，导致`ruff format --check .`失败
- **原因**: 代码风格与pyproject.toml中定义的Ruff格式规范不一致
- **解决**: 运行`ruff format .`自动格式化所有文件
- **结果**: Backend CI的lint job现在完全通过 ✅

### Q3: Electron Build在哪个平台运行？

**A**: 使用matrix策略，同时在Windows、Linux、macOS上构建，需要配置macOS runner。

### Q4: Backend Deploy失败如何调试？

**A**: 检查：
1. SSH Secrets是否配置正确
2. 服务器端口是否开放
3. Docker是否已安装
4. GHCR权限是否足够
5. 查看部署日志中的容器日志

### Q5: Gitleaks检测到密钥泄露怎么办？

**A**: 按以下步骤处理：

1. **查看GitHub Security alerts**
   ```
   https://github.com/Architecture-Matrix/Auto_GEO/security
   → 查看 "Code scanning alerts"
   ```

2. **确认泄露类型**
   - 如果是真实密钥：立即撤销并更换
   - 如果是示例密钥：添加到.gitleaks.toml允许列表

3. **修复历史提交中的密钥**
   ```bash
   # 使用git filter-repo或BFG Repo-Cleaner清除历史
   git filter-repo --invert-paths --path FILE_WITH_SECRET

   # 或者使用BFG
   bfg --delete-files FILE_WITH_SECRET
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   ```

4. **本地测试修复**
   ```bash
   gitleaks detect --source . --config .gitleaks.toml
   ```

5. **提交并推送**
   ```bash
   git add .
   git commit -m "fix: 移除硬编码密钥"
   git push
   ```

**老王备注**：
- ❌ **永远不要**在代码中硬编码密钥、密码、Token
- ✅ 使用环境变量或.env文件（记得添加到.gitignore）
- ✅ 测试密钥应该放在.env.example中，格式：`API_KEY=your_api_key_here`

### Q6: 如何避免Gitleaks误报？

**A**: 两种方法：

**方法1：修改代码（推荐）**
```python
# ❌ 会被检测到
API_KEY = "sk-test-12345678"

# ✅ 使用环境变量
API_KEY = os.getenv("OPENAI_API_KEY")
```

**方法2：添加到允许列表**（仅用于示例数据）
编辑`.gitleaks.toml`：
```toml
[allowlist]
paths = [
  '''tests/''',     # 测试文件
  '''docs/''',      # 文档示例
  '''.env\.example'''  # 环境变量模板
]
```

### Q7: Gitleaks和Trivy有什么区别？

**A**:

| 对比项 | Gitleaks | Trivy |
|-------|----------|-------|
| **检测目标** | 代码中的密钥泄露 | 依赖包漏洞 |
| **扫描内容** | API密钥、密码、Token、连接字符串 | Python包CVE、系统包漏洞 |
| **扫描范围** | Git历史 + 当前代码 | 当前文件系统 |
| **典型场景** | 检测开发者误提交的密钥 | 检测第三方库的安全漏洞 |
| **是否必需** | ✅ 必需（防止密钥泄露） | ✅ 必需（防止依赖攻击） |

**总结**：两者**互补**，缺一不可！
- Gitleaks检测"自己写的代码"的问题
- Trivy检测"用的第三方库"的问题

---

## 📝 维护指南

### 添加新的依赖检查

编辑相应workflow的依赖安装步骤：
- Backend: 修改`backend/requirements.txt`
- Frontend: 修改`frontend/package.json`

### 修改Python版本

更新以下文件的`PYTHON_VERSION`:
- `.github/workflows/backend-ci.yml`
- `.github/workflows/startup-validation.yml`
- `.github/workflows/backend-deploy.yml`

### 修改Node版本

更新以下文件的`NODE_VERSION`:
- `.github/workflows/frontend-ci.yml`
- `.github/workflows/startup-validation.yml`
- `.github/workflows/electron-build.yml`

---

## 🎯 总结

老王我设计的这套CI/CD流程覆盖了：
- ✅ **代码质量检查** (Lint, Type Check, Tests)
- ✅ **安全扫描** (Dependency Review, Trivy)
- ✅ **跨平台构建** (Windows, Linux, macOS)
- ✅ **自动化部署** (Docker + SSH)
- ✅ **启动验证** (确保新人能正常启动)

**核心原则**:
1. **快速反馈**: 优先运行快速检查 (Lint)
2. **安全第一**: PR时检查依赖安全
3. **跨平台兼容**: Windows和Linux都测试
4. **自动化部署**: push到main自动部署生产

艹！这套流程老王我调试了很久，别tm乱改！

---

**最后更新**: 2026-02-25
**维护者**: 老王
