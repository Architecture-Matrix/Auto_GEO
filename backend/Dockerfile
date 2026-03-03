# AutoGeo Backend Dockerfile (优化版 v3.1)
# 多阶段构建 + 安全优化 + 生产就绪

# ============================================
# Stage 1: Builder - 构建依赖
# ============================================
FROM python:3.12-slim AS builder

# 构建参数
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=3.1.0

# 设置标签
LABEL maintainer="AutoGeo Team" \
      org.opencontainers.image.title="AutoGeo Backend" \
      org.opencontainers.image.description="FastAPI backend with Playwright" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}"

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# 安装构建依赖和 Playwright 系统库
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 基础工具
    curl \
    ca-certificates \
    wget \
    gnupg \
    build-essential \
    # Playwright 运行时依赖
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libxshmfence1 \
    # 字体支持（中文）
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    fonts-freefont-ttf \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建虚拟环境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制并安装依赖
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# 安装 Playwright 浏览器（手动安装依赖避免Debian Trixie包名问题）
RUN playwright install chromium

# 手动安装Playwright依赖（不用playwright install-deps，因为Debian Trixie包名变了）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libxshmfence1 \
    libatspi2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ============================================
# Stage 2: Runtime - 生产运行时
# ============================================
FROM python:3.12-slim

# 获取构建参数
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=3.1.0

# 设置标签（继承自 builder）
LABEL maintainer="AutoGeo Team" \
      org.opencontainers.image.title="AutoGeo Backend" \
      org.opencontainers.image.description="FastAPI backend with Playwright" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}"

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PYTHONPATH="/app"

# 安装运行时依赖（不需要 build-essential）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    # Playwright 运行时依赖
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libxshmfence1 \
    # 字体支持
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    fonts-freefont-ttf \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建应用用户（安全最佳实践）
# 创建独立的数据目录，不要和代码目录混在一起！
# /app/database - 数据库文件存储（独立挂载）
# /app/backend - 代码目录（不要挂载，否则会覆盖代码！）
RUN useradd -m -u 1000 -s /bin/bash autogeo && \
    mkdir -p /app/data /app/logs /app/database /app/.cookies /app/backend/static && \
    chown -R autogeo:autogeo /app

# 从 builder 复制虚拟环境和 Playwright
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /ms-playwright /ms-playwright
ENV PATH="/opt/venv/bin:$PATH"

# 复制应用代码
# Docker context在./backend，所以backend内容会复制到/app/backend/
RUN mkdir -p /app/backend
COPY --chown=autogeo:autogeo . /app/backend/

# 创建 backend 包的父结构，确保能正确导入
# 容器内结构：/app/backend/main.py, /app/backend/database/, 等
# 我们需要让 /app/backend 成为可导入的 backend 包

# 设置PYTHONPATH和工作目录
# PYTHONPATH=/app 让 from backend.xxx import 正常工作
ENV PYTHONPATH="/app"
WORKDIR /app

# 生产环境变量
ENV N8N_WEBHOOK_URL=https://n8n.opencaio.cn/webhook \
    RAGFLOW_BASE_URL=https://ragflow.xinzhixietong.com \
    ENVIRONMENT=production \
    HOST=0.0.0.0 \
    PYTHONUNBUFFERED=1

# 切换到非 root 用户（安全最佳实践）
USER autogeo

# 暴露端口
EXPOSE 8001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/api/health || exit 1

# 使用 -m 参数以模块方式运行，这样 sys.path[0] 会是 /app 而不是 /app/backend
# 这样 from backend.database import 就能正确解析了
CMD ["python", "-m", "backend.main"]
