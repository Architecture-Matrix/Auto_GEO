#!/bin/bash
# ========================================
# Electron Auto-Fix Script
# Purpose: 自动修复Electron安装问题
# Updated: 2026-02-24
# ========================================
#
# 备注：
# 这个脚本专门修复Electron的path.txt缺失问题
# Electron安装经常半途失败，二进制文件有了，配置文件没有！
#

set -e  # 遇到错误立即退出

FRONTEND_DIR="../../frontend"
ELECTRON_DIR="$FRONTEND_DIR/node_modules/electron"
PATH_FILE="$ELECTRON_DIR/path.txt"

echo "🔧 检查Electron安装..."

if [ ! -d "$ELECTRON_DIR" ]; then
  echo "❌ Electron未安装！请先运行: cd ../../frontend && npm install"
  exit 1
fi

echo "✅ Electron目录存在"

# 检测操作系统
OS="$(uname -s)"
case "$OS" in
  Linux*)     PLATFORM="linux";;
  Darwin*)    PLATFORM="macos";;
  MINGW*|MSYS*|CYGWIN*)
    PLATFORM="windows"
    # Windows下Git Bash路径转换
    ELECTRON_EXECUTABLE="$ELECTRON_DIR/dist/electron.exe"
    ;;
  *)          PLATFORM="unknown";;
esac

if [ "$PLATFORM" = "windows" ]; then
  # Windows处理
  if [ -f "$ELECTRON_EXECUTABLE" ]; then
    echo "📁 找到Electron可执行文件: $ELECTRON_EXECUTABLE"
    printf "electron.exe" > "$PATH_FILE"
    echo "✅ 已创建path.txt (Windows)"
  else
    echo "❌ 未找到electron.exe，Electron安装不完整！"
    echo "请运行: cd ../../frontend && npm install electron --force"
    exit 1
  fi
else
  # Linux/macOS处理
  ELECTRON_EXECUTABLE="$ELECTRON_DIR/dist/electron"

  if [ -f "$ELECTRON_EXECUTABLE" ]; then
    echo "📁 找到Electron可执行文件: $ELECTRON_EXECUTABLE"
    printf "electron" > "$PATH_FILE"
    echo "✅ 已创建path.txt (Linux/macOS)"
  else
    echo "❌ 未找到electron可执行文件，Electron安装不完整！"
    echo "请运行: cd ../../frontend && npm install electron --force"
    exit 1
  fi
fi

# 验证修复结果
echo ""
echo "🔍 验证修复结果..."
if [ -f "$PATH_FILE" ]; then
  CONTENT=$(cat "$PATH_FILE")
  echo "📄 path.txt内容: [$CONTENT]"
  echo "✅ Electron修复完成！"
  echo ""
  echo "现在可以启动前端了："
  echo "  cd ../../frontend"
  echo "  npm run dev"
else
  echo "❌ path.txt创建失败！"
  exit 1
fi
