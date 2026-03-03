# 📦 AutoGeo 打包与分发指南

**更新日期**: 2026-02-24
**版本**: v3.1.0

---

## ⚠️ pkg工具问题说明

### 问题

pkg工具在Windows上打包时可能会遇到以下错误：

```
AssertionError [ERR_ASSERTION]: The expression evaluated to a falsy value:
(!this.bar)
```

**原因**：pkg-fetch在下载Node.js源代码时的bug

**影响**：无法使用pkg打包成真正的独立可执行文件

---

## 🎯 替代方案（推荐）

### 方案1：智能包装器（推荐）⭐⭐⭐⭐⭐

**文件**：`start.bat`

**优点**：
- ✅ 无需Node.js也能运行
- ✅ 自动选择最佳版本
- ✅ 双击即可使用
- ✅ 体积小（不到1KB）

**使用方法**：
```bash
# 用户双击运行即可
start.bat
```

**工作原理**：
```batch
1. 检测系统是否有Node.js
2. 有Node.js → 运行功能最全的scripts/startup/quickstart.js
3. 没有Node.js → 运行批处理版本scripts/startup/quickstart-cmd.bat
```

---

### 方案2：批处理启动器（Windows用户）⭐⭐⭐⭐

**文件**：`scripts/startup/quickstart-cmd.bat`（已增强）

**优点**：
- ✅ 纯Windows，无需任何依赖
- ✅ 增强的依赖检查
- ✅ 自动修复Electron

**使用方法**：
```bash
# 双击运行
scripts/startup/quickstart-cmd.bat
```

---

### 方案3：Shell启动器（Linux/macOS用户）⭐⭐⭐⭐

**文件**：`scripts/start.sh`

**优点**：
- ✅ 原生Linux/macOS支持
- ✅ 彩色输出
- ✅ 功能完整

**使用方法**：
```bash
# 添加执行权限
chmod +x scripts/start.sh

# 运行
./scripts/start.sh
```

---

### 方案4：Node.js启动器（跨平台）⭐⭐⭐⭐⭐

**文件**：`scripts/startup/quickstart.js`

**优点**：
- ✅ 完全跨平台
- ✅ 功能最强大
- ✅ 代码易维护

**使用方法**：
```bash
# 需要Node.js环境
node scripts/startup/quickstart.js
```

---

## 📊 方案对比

| 方案 | Windows | Linux | macOS | 需Node.js | 推荐度 |
|------|---------|-------|-------|-----------|--------|
| **智能包装器** | ✅ | ❌ | ❌ | ❌ | ⭐⭐⭐⭐⭐ |
| **批处理CMD** | ✅ | ❌ | ❌ | ❌ | ⭐⭐⭐⭐ |
| **Shell脚本** | ❌ | ✅ | ✅ | ❌ | ⭐⭐⭐⭐ |
| **Node.js脚本** | ✅ | ✅ | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| **pkg打包EXE** | ⚠️ | ❌ | ❌ | ❌ | ⭐ (有bug) |

---

## 🚀 分发建议

### Windows用户

**分发包内容**：
```
AutoGeo-v3.1.0-Windows/
├── start.bat    # ⭐ 双击这个
├── scripts/startup/quickstart-cmd.bat             # 备用
├── scripts/startup/quickstart.js              # 有Node.js时使用
├── backend/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── package.json
│   └── ...
└── scripts/
    ├── fix-electron.bat
    └── ...
```

**用户操作**：
1. 解压
2. 双击 `start.bat`
3. 选择功能
4. 完成！

**安装说明**：
```markdown
## 安装要求

1. **后端依赖**：
   - Python 3.10+
   - 运行启动器会自动安装

2. **前端依赖**：
   - Node.js 18+（可选）
   - 或让启动器自动安装

3. **首次运行**：
   - 双击 start.bat
   - 选择 [2] 启动前端
   - 等待自动安装依赖
```

---

### Linux/macOS用户

**分发包内容**：
```
AutoGeo-v3.1.0-Linux/
├── scripts/start.sh               # ⭐ 运行这个
├── scripts/startup/quickstart.js               # 备用
├── backend/
├── frontend/
└── scripts/
```

**用户操作**：
```bash
# 1. 添加执行权限
chmod +x scripts/start.sh

# 2. 运行
./scripts/start.sh
```

---

## 🔧 其他打包工具（如果pkg失败）

### 工具1：Bat To Exe Converter

**适用**：纯Windows

**网址**：http://www.f2ko.de/en/b2e.php

**步骤**：
1. 下载并安装 Bat To Exe Converter
2. 打开 `scripts/startup/quickstart-cmd.bat`
3. 选择输出为 `quickstart.exe`
4. 点击转换

**优点**：
- 简单
- 可自定义图标
- 可加密

**缺点**：
- 只支持Windows
- 仍然是批处理语法

---

### 工具2：Advanced BAT to EXE Converter

**适用**：纯Windows

**网址**：http://www.battoexe.net/

**特点**：
- 专业版本
- 支持更多功能
- 可以嵌入资源

---

### 工具3：nexe（pkg的替代品）

**安装**：
```bash
npm install -g nexe
```

**使用**：
```bash
nexe scripts/startup/quickstart.js -o quickstart.exe
```

**优点**：
- 比pkg更稳定
- 支持更多Node.js版本

**缺点**：
- 体积较大
- 打包速度慢

---

## 💡 最终推荐

### 给普通Windows用户

**使用智能包装器**：
```
start.bat
```

**为什么**：
- ✅ 双击运行
- ✅ 无需任何依赖
- ✅ 自动选择最佳版本
- ✅ 已测试通过

### 给技术用户

**使用Node.js版本**：
```bash
node scripts/startup/quickstart.js
```

**为什么**：
- ✅ 功能最完整
- ✅ 跨平台
- ✅ 易于调试和修改

---

## 📋 分发清单

### Windows用户包

**文件**：
- ✅ `start.bat` （主启动器）
- ✅ `scripts/startup/quickstart-cmd.bat` （备用）
- ✅ `scripts/startup/quickstart.js` （高级用户）
- ✅ `backend/` 目录
- ✅ `frontend/` 目录
- ✅ `scripts/` 目录
- ✅ `README.md` 说明文档

### Linux/macOS用户包

**文件**：
- ✅ `scripts/start.sh` （主启动器）
- ✅ `scripts/startup/quickstart.js` （备用）
- ✅ `backend/` 目录
- ✅ `frontend/` 目录
- ✅ `scripts/` 目录
- ✅ `README.md` 说明文档

---

## 🎯 最佳实践

### 开发时

- 使用 `scripts/startup/quickstart.js`（功能最全）
- 或使用平台特定的脚本（CMD/SH）

### 分发时

- Windows：提供 `start.bat`
- Linux/macOS：提供 `scripts/start.sh`
- 高级用户：提供 `scripts/startup/quickstart.js`

### 文档说明

在README中添加：
```markdown
## 快速启动

### Windows用户
双击运行 `start.bat`

### Linux/macOS用户
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

### 技术用户
```bash
node scripts/startup/quickstart.js
```
```

---

## 🔍 故障排除

### Q: 为什么不使用pkg打包？

A: pkg在Windows上有已知bug，打包失败。测试了多次都报错。智能包装器是更可靠的方案。

### Q: 包装器能在所有Windows上运行吗？

A: ✅ 是的！批处理是Windows原生支持，不需要任何额外依赖。

### Q: 如果用户有Node.js会怎样？

A: 智能包装器会自动检测并使用功能更强大的Node.js版本。

### Q: 如何自定义图标？

A: 使用Bat To Exe Converter可以添加图标。

---

**更新日期**: 2026-02-24
**版本**: v3.1.0
