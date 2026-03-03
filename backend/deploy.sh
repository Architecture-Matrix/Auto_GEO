#!/bin/bash
# AutoGeo 服务器部署脚本

set -e  # 遇到错误就退出

# ==================== 配置区域 ====================
IMAGE_NAME="auto_geo_backend"
CONTAINER_NAME="autogeo-backend"
REGISTRY="ghcr.io"
REPO_OWNER="${GITHUB_REPOSITORY_OWNER:-your-github-username}"
PORT="8001"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ==================== 检查 Docker ====================
echo_info "检查 Docker 安装..."
if ! command -v docker &> /dev/null; then
    echo_error "Docker 未安装！请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo_error "Docker Compose 未安装！请先安装 Docker Compose"
    exit 1
fi

echo_info "Docker 版本: $(docker --version)"
echo_info "Docker Compose 版本: $(docker-compose --version)"

# ==================== 拉取镜像 ====================
echo_info "拉取最新镜像..."
docker pull ${REGISTRY}/${REPO_OWNER}/${IMAGE_NAME}:latest

# ==================== 停止旧容器 ====================
echo_info "停止旧容器..."
if [ "$(docker ps -q -f name=${CONTAINER_NAME})" ]; then
    docker stop ${CONTAINER_NAME}
    docker rm ${CONTAINER_NAME}
    echo_info "旧容器已停止并删除"
fi

# ==================== 创建必要的目录 ====================
echo_info "创建数据目录..."
mkdir -p data logs

# ==================== 启动新容器 ====================
echo_info "启动新容器..."
docker run -d \
  --name ${CONTAINER_NAME} \
  --restart unless-stopped \
  -p ${PORT}:8001 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -e ENVIRONMENT=production \
  -e PYTHONUNBUFFERED=1 \
  ${REGISTRY}/${REPO_OWNER}/${IMAGE_NAME}:latest

# ==================== 等待服务启动 ====================
echo_info "等待服务启动..."
sleep 5

# ==================== 健康检查 ====================
echo_info "进行健康检查..."
if curl -f http://localhost:${PORT}/health > /dev/null 2>&1; then
    echo_info "✅ 后端服务启动成功！"
    echo_info "📍 API 地址: http://$(hostname -I | awk '{print $1'}):${PORT}"
    echo_info "📊 API 文档: http://$(hostname -I | awk '{print $1'}):${PORT}/docs"
else
    echo_error "❌ 后端服务启动失败！请检查日志："
    echo_warn "docker logs ${CONTAINER_NAME}"
    exit 1
fi

# ==================== 清理旧镜像 ====================
echo_warn "清理未使用的 Docker 镜像..."
docker image prune -f

echo_info "🎉 部署完成！"
