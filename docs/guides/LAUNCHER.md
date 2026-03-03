# 🚀 AutoGeo 跨平台启动指南

**更新日期**: 2026-02-24
**版本**: v3.1.0

---

## 📋 启动脚本对比

| 文件 | 平台 | 说明 | 推荐度 |
|------|------|------|--------|
| `scripts/startup/quickstart-cmd.bat` | Windows | 批处理脚本（已增强） | ⭐⭐⭐ Windows推荐 |
| `scripts/start.sh` | Linux/macOS | Shell脚本 | ⭐⭐⭐ Linux/macOS推荐 |
| `scripts/startup/quickstart.js` | **跨平台** | Node.js脚本 | ⭐⭐⭐⭐⭐ 最佳方案 |

---

## 🎯 方案一：Node.js版本（强烈推荐）

### 优点

✅ **完全跨平台**：同一套代码支持Windows/Linux/macOS
✅ **可打包成EXE**：双击运行，无需Node.js环境
✅ **功能完整**：所有功能与批处理版本一致
✅ **易于维护**：代码清晰，易于修改

### 使用方法

#### 方式1：直接运行（需要Node.js）

```bash
# Windows
node scripts/startup/quickstart.js

# Linux/macOS
chmod +x scripts/startup/quickstart.js
./scripts/startup/quickstart.js
```

#### 方式2：打包成EXE（无需Node.js）

**打包工具选择**：

| 工具 | 优点 | 缺点 | 推荐 |
|------|------|------|------|
| **pkg** | 简单，体积小 | 不支持所有Node.js模块 | ⭐⭐⭐⭐⭐ |
| **nexe** | 功能强大 | 体积大 | ⭐⭐⭐⭐ |
| **box** | 兼容性好 | 配置复杂 | ⭐⭐⭐ |

#### 使用pkg打包（推荐）

**步骤1：安装pkg**

```bash
npm install -g pkg
```

**步骤2：打包成可执行文件**

```bash
# Windows
pkg scripts/startup/quickstart.js -t node18-win-x64 -o quickstart.exe

# Linux
pkg scripts/startup/quickstart.js -t node18-linux-x64 -o quickstart

# macOS
pkg scripts/startup/quickstart.js -t node18-macos-x64 -o quickstart
```

**步骤3：运行**

```bash
# Windows: 双击运行
quickstart.exe

# Linux/macOS
chmod +x quickstart
./quickstart
```

#### 一次性打包所有平台

```bash
# 创建package.json配置
cat > package.json << EOF
{
  "name": "autogeo-launcher",
  "version": "3.1.0",
  "main": "scripts/startup/quickstart.js",
  "bin": "scripts/startup/quickstart.js",
  "pkg": {
    "assets": [],
    "targets": [
      "node18-win-x64",
      "node18-linux-x64",
      "node18-macos-x64"
    ],
    "outputPath": "dist"
  }
}
EOF

# 打包所有平台
npm install -g pkg
pkg .
```

打包后会生成：
```
dist/
├── quickstart-win.exe       # Windows版本
├── quickstart-linux         # Linux版本
└── quickstart-macos         # macOS版本
```

---

## 🐧 方案二：Shell脚本（Linux/macOS）

### 使用方法

```bash
# 添加执行权限
chmod +x scripts/start.sh

# 运行
./scripts/start.sh
```

### 特性

✅ 原生支持Linux/macOS
✅ 彩色输出，美观
✅ 自动检测系统类型
✅ 在新终端窗口启动服务

---

## 🪟 方案三：批处理脚本（Windows）

### 使用方法

```bash
# 双击运行
scripts/startup/quickstart-cmd.bat

# 或命令行运行
scripts/startup/quickstart-cmd.bat
```

### 特性

✅ 原生Windows支持
✅ 已增强依赖检查
✅ 自动修复Electron问题

---

## 📊 功能对比

| 功能 | CMD | SH | JS | EXE |
|------|-----|----|----|-----|
| 启动后端 | ✅ | ✅ | ✅ | ✅ |
| 启动前端 | ✅ | ✅ | ✅ | ✅ |
| 重启服务 | ✅ | ✅ | ✅ | ✅ |
| 清理缓存 | ✅ | ✅ | ✅ | ✅ |
| 重置数据库 | ✅ | ✅ | ✅ | ✅ |
| **跨平台** | ❌ | ❌ | ✅ | ✅ |
| **双击运行** | ✅ | ⚠️ | ❌ | ✅ |
| **无需依赖** | ✅ | ✅ | ❌ | ✅ |
| **彩色输出** | ❌ | ✅ | ✅ | ✅ |

---

## 🛠️ 打包成EXE详细步骤

### 方案1：使用pkg（推荐）

#### 1. 全局安装pkg

```bash
npm install -g pkg
```

#### 2. 创建package.json

在项目根目录创建`package.json`：

```json
{
  "name": "autogeo-launcher",
  "version": "3.1.0",
  "description": "AutoGeo跨平台启动器",
  "main": "scripts/startup/quickstart.js",
  "bin": "scripts/startup/quickstart.js",
  "scripts": {
    "build": "pkg .",
    "build:win": "pkg scripts/startup/quickstart.js -t node18-win-x64 -o quickstart.exe",
    "build:linux": "pkg scripts/startup/quickstart.js -t node18-linux-x64 -o quickstart",
    "build:mac": "pkg scripts/startup/quickstart.js -t node18-macos-x64 -o quickstart"
  },
  "pkg": {
    "assets": [],
    "targets": [
      "node18-win-x64",
      "node18-linux-x64",
      "node18-macos-x64"
    ],
    "outputPath": "dist"
  },
  "dependencies": {}
}
```

#### 3. 打包

```bash
# 打包所有平台
npm run build

# 或只打包Windows
npm run build:win
```

#### 4. 运行

```bash
# Windows会生成
dist/quickstart-win.exe

# 双击运行即可！
```

### 方案2：使用Bat To Exe Converter（纯Windows）

**下载地址**：http://www.f2ko.de/en/b2e.php

**步骤**：
1. 下载并安装 Bat To Exe Converter
2. 打开 `scripts/startup/quickstart-cmd.bat`
3. 选择输出路径
4. 点击转换
5. 生成 `quickstart.exe`

**优点**：
- 简单易用
- 可自定义图标
- 可加密

**缺点**：
- 只支持Windows
- 仍然依赖批处理语法

### 方案3：使用NSIS安装程序（专业方案）

**下载地址**：https://nsis.sourceforge.io/

**创建安装脚本** `installer.nsi`：

```nsis
!define APPNAME "AutoGeo"
!define COMPANYNAME "AutoGeo Team"
!define DESCRIPTION "AutoGeo智能多平台文章发布助手"
!define VERSIONMAJOR 3
!define VERSIONMINOR 1
!define VERSIONBUILD 0

RequestExecutionLevel admin

InstallDir "$PROGRAMFILES\${APPNAME}"

Page directory
Page instfiles

Section "Install Files"
  SetOutPath $INSTDIR
  File /r "backend"
  File /r "frontend"
  File /r "scripts"
  File "quickstart.exe"

  CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\quickstart.exe"
  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\quickstart.exe"
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\${APPNAME}.lnk"
  RMDir /r "$SMPROGRAMS\${APPNAME}"
  RMDir /r $INSTDIR
SectionEnd
```

**编译**：
```bash
makensis installer.nsi
```

会生成安装包 `installer.exe`

---

## 🎯 推荐方案总结

### 开发环境

| 场景 | 推荐方案 |
|------|---------|
| **Windows开发** | `scripts/startup/quickstart-cmd.bat` 或 `scripts/startup/quickstart.js` |
| **Linux/macOS开发** | `scripts/start.sh` 或 `scripts/startup/quickstart.js` |
| **跨平台开发** | `scripts/startup/quickstart.js` |

### 生产环境/分发

| 场景 | 推荐方案 |
|------|---------|
| **Windows用户** | 打包成 `quickstart.exe` |
| **Linux/macOS用户** | 使用 `scripts/start.sh` |
| **技术用户** | 使用 `scripts/startup/quickstart.js` |

---

## 📦 分发包建议

### 完整分发包结构

```
AutoGeo-v3.1.0/
├── README.md
├── SETUP.md
├── quickstart.exe          # Windows用户（打包后）
├── scripts/start.sh           # Linux/macOS用户
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── package.json
│   └── ...
└── scripts/
    ├── fix-electron.bat
    └── fix-electron.sh
```

### Windows安装包

使用NSIS或Inno Setup创建安装程序：
- 自动检测Python和Node.js
- 引导安装依赖
- 创建桌面快捷方式
- 添加到开始菜单

---

## 💡 使用技巧

### 技巧1：创建桌面快捷方式

**Windows**：
```bash
# 右键 quickstart.exe -> 发送到 -> 桌面快捷方式
```

**Linux**：
```bash
# 创建.desktop文件
cat > ~/.local/share/applications/autogeo.desktop << EOF
[Desktop Entry]
Name=AutoGeo
Exec=/path/to/scripts/start.sh
Icon=/path/to/icon.png
Type=Application
Categories=Development;
EOF
```

### 技巧2：开机自启动

**Windows**：
```bash
# Win+R -> shell:startup
# 复制 quickstart.exe 到此目录
```

**Linux**：
```bash
# 创建自启动文件
cp autogeo.desktop ~/.config/autostart/
```

### 技巧3：自定义端口

如果需要修改默认端口：

```javascript
// scripts/startup/quickstart.js中修改
const BACKEND_PORT = 8001;
const FRONTEND_PORT = 5173;
```

---

## 🔧 常见问题

### Q1: pkg打包后体积太大？

A: 使用`--no-bytecode`选项：
```bash
pkg scripts/startup/quickstart.js -t node18-win-x64 --no-bytecode -o quickstart.exe
```

### Q2: 打包后无法运行？

A: 检查是否有外部依赖：
```bash
# 查看依赖
pkg scripts/startup/quickstart.js --debug
```

### Q3: Linux提示权限不足？

A: 添加执行权限：
```bash
chmod +x scripts/start.sh
chmod +x quickstart
```

### Q4: macOS提示无法打开？

A: 移除隔离属性：
```bash
xattr -d com.apple.quarantine quickstart
```

---

## 📚 参考资源

- **pkg文档**: https://github.com/vercel/pkg
- **Node.js文档**: https://nodejs.org/docs
- **NSIS文档**: https://nsis.sourceforge.io/Docs/

---

**更新日期**: 2026-02-24
**版本**: v3.1.0
