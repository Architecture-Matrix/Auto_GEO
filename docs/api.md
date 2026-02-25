# AutoGeo API 文档

> **API完整文档** - 所有后端API端点详细说明

**Base URL**: `http://127.0.0.1:8001`
**API文档**: [Swagger UI](http://127.0.0.1:8001/docs) | [ReDoc](http://127.0.0.1:8001/redoc)

---

## 📋 目录

- [基础 API](#基础-api)
- [账号管理 API](#账号管理-api)
- [文章管理 API](#文章管理-api)
- [发布管理 API](#发布管理-api)
- [GEO/关键词 API](#geo关键词-api)
- [收录检测 API](#收录检测-api)
- [候选人管理 API](#候选人管理-api)
- [知识库管理 API](#知识库管理-api)
- [报表 API](#报表-api)
- [预警通知 API](#预警通知-api)
- [定时任务 API](#定时任务-api)
- [智能建站 API](#智能建站-api)
- [文件上传 API](#文件上传-api)

---

## 基础 API

### 健康检查

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/` | 服务健康检查 |

**响应示例**：
```json
{
  "status": "ok",
  "message": "AutoGeo Backend is running"
}
```

### 服务状态

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 详细的服务状态信息 |

**响应示例**：
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "database": "connected",
  "services": {
    "playwright": "ready",
    "n8n": "connected"
  }
}
```

### 支持的平台列表

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/platforms` | 获取所有支持的平台列表 |

**响应示例**：
```json
{
  "platforms": [
    {"id": "zhihu", "name": "知乎"},
    {"id": "baijiahao", "name": "百家号"},
    {"id": "sohu", "name": "搜狐号"},
    {"id": "toutiao", "name": "头条号"}
  ]
}
```

---

## 账号管理 API

### 获取账号列表

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/accounts` | 获取所有账号 |

**查询参数**：
- `platform`: (可选) 平台ID筛选
- `page`: (可选) 页码，默认1
- `page_size`: (可选) 每页数量，默认20

### 创建账号

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/accounts` | 创建新账号 |

**请求体**：
```json
{
  "platform": "zhihu",
  "username": "用户名",
  "cookies": "加密的cookie字符串"
}
```

### 获取账号详情

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/accounts/{account_id}` | 获取指定账号详情 |

### 更新账号信息

| 方法 | 端点 | 说明 |
|------|------|------|
| `PUT` | `/api/accounts/{account_id}` | 更新账号信息 |

**请求体**：
```json
{
  "username": "新用户名",
  "cookies": "新的加密cookie"
}
```

### 删除账号

| 方法 | 端点 | 说明 |
|------|------|------|
| `DELETE` | `/api/accounts/{account_id}` | 删除指定账号 |

### 账号授权

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/accounts/{account_id}/authorize` | 启动浏览器进行账号授权 |

**响应示例**：
```json
{
  "status": "success",
  "message": "请在浏览器中完成授权"
}
```

---

## 文章管理 API

### 获取文章列表

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/articles` | 获取所有文章 |

**查询参数**：
- `status`: (可选) 按状态筛选
- `page`: (可选) 页码
- `page_size`: (可选) 每页数量

### 创建文章

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/articles` | 创建新文章 |

**请求体**：
```json
{
  "title": "文章标题",
  "content": "文章内容（HTML或Markdown）",
  "platform": "zhihu",
  "tags": ["标签1", "标签2"]
}
```

### 获取文章详情

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/articles/{article_id}` | 获取指定文章详情 |

### 更新文章

| 方法 | 端点 | 说明 |
|------|------|------|
| `PUT` | `/api/articles/{article_id}` | 更新文章内容 |

### 删除文章

| 方法 | 端点 | 说明 |
|------|------|------|
| `DELETE` | `/api/articles/{article_id}` | 删除指定文章 |

---

## 发布管理 API

### 发布文章

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/publish/{article_id}` | 发布文章到指定平台 |

**请求体**：
```json
{
  "platform": "zhihu",
  "account_id": 123
}
```

### 获取发布任务列表

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/publish/tasks` | 获取所有发布任务 |

**查询参数**：
- `status`: (可选) 按状态筛选（pending/running/success/failed）

### 获取发布任务详情

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/publish/tasks/{task_id}` | 获取指定任务详情 |

### 重试发布

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/publish/tasks/{task_id}/retry` | 重新执行失败的任务 |

---

## GEO/关键词 API

### 获取项目列表

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/geo/projects` | 获取所有GEO项目 |

### 创建项目

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/geo/projects` | 创建新GEO项目 |

**请求体**：
```json
{
  "name": "项目名称",
  "description": "项目描述",
  "target_keywords": ["关键词1", "关键词2"]
}
```

### 获取项目关键词

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/geo/projects/{id}/keywords` | 获取项目的所有关键词 |

### 关键词蒸馏

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/geo/distill` | AI关键词蒸馏，扩展相关关键词 |

**请求体**：
```json
{
  "seed_keywords": ["种子关键词"],
  "count": 10
}
```

### 生成GEO文章

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/geo/generate-article` | 基于关键词生成SEO优化文章 |

**请求体**：
```json
{
  "keyword": "目标关键词",
  "project_id": 123,
  "style": "professional"
}
```

---

## 收录检测 API

### 执行收录检测

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/index-check/check` | 执行AI搜索引擎收录检测 |

**请求体**：
```json
{
  "keyword_id": 123,
  "engines": ["doubao", "qianwen", "deepseek"]
}
```

### 获取检测记录

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/index-check/records` | 获取所有检测记录 |

**查询参数**：
- `keyword_id`: (可选) 筛选指定关键词
- `start_date`: (可选) 开始日期
- `end_date`: (可选) 结束日期

### 获取关键词趋势

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/index-check/trend/{keyword_id}` | 获取关键词的收录趋势数据 |

---

## 候选人管理 API

### 获取候选人列表

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/candidates` | 获取所有候选人 |

### 创建候选人

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/candidates` | 创建新候选人记录 |

**请求体**：
```json
{
  "name": "候选人姓名",
  "email": "email@example.com",
  "phone": "联系电话",
  "resume_url": "简历链接"
}
```

### 获取候选人详情

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/candidates/{candidate_id}` | 获取指定候选人详情 |

### 更新候选人信息

| 方法 | 端点 | 说明 |
|------|------|------|
| `PUT` | `/api/candidates/{candidate_id}` | 更新候选人信息 |

### 删除候选人

| 方法 | 端点 | 说明 |
|------|------|------|
| `DELETE` | `/api/candidates/{candidate_id}` | 删除指定候选人 |

---

## 知识库管理 API

### 获取知识库列表

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/knowledge` | 获取所有知识库 |

### 创建知识库

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/knowledge` | 创建新知识库 |

**请求体**：
```json
{
  "name": "知识库名称",
  "type": "ragflow",
  "endpoint": "知识库API地址"
}
```

### 上传知识库文档

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/knowledge/{kb_id}/upload` | 上传文档到知识库 |

**请求体**：
```json
{
  "file_path": "/path/to/document.pdf",
  "metadata": {"title": "文档标题"}
}
```

### 删除知识库

| 方法 | 端点 | 说明 |
|------|------|------|
| `DELETE` | `/api/knowledge/{kb_id}` | 删除指定知识库 |

---

## 报表 API

### 数据总览

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/reports/overview` | 获取整体数据概览 |

**响应示例**：
```json
{
  "total_keywords": 150,
  "total_articles": 45,
  "indexed_count": 120,
  "indexing_rate": 0.8
}
```

### 收录趋势

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/reports/trend/index` | 获取收录趋势数据 |

**查询参数**：
- `days`: (可选) 最近N天，默认30

### 关键词排名

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/reports/ranking/keywords` | 获取关键词排名数据 |

---

## 预警通知 API

### 检查预警

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/notifications/check` | 手动触发预警检查 |

### 预警汇总

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/notifications/summary` | 获取所有预警通知汇总 |

### 预警规则

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/notifications/rules` | 获取当前预警规则配置 |

---

## 定时任务 API

### 定时任务列表

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/scheduler/jobs` | 获取所有定时任务 |

### 创建定时任务

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/scheduler/jobs` | 创建新的定时任务 |

**请求体**：
```json
{
  "job_id": "daily_index_check",
  "func": "backend.services.index_check_service:check_all_keywords",
  "trigger": "cron",
  "args": ["--daily"],
  "hours": 2,
  "minutes": 0
}
```

### 更新定时任务

| 方法 | 端点 | 说明 |
|------|------|------|
| `PUT` | `/api/scheduler/jobs/{job_id}` | 更新定时任务配置 |

### 删除定时任务

| 方法 | 端点 | 说明 |
|------|------|------|
| `DELETE` | `/api/scheduler/jobs/{job_id}` | 删除定时任务 |

### 启动定时任务服务

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/scheduler/start` | 启动定时任务调度器 |

### 停止定时任务服务

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/scheduler/stop` | 停止定时任务调度器 |

---

## 智能建站 API

### 构建站点

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/sites/build` | 使用Jinja2模板渲染构建静态站点 |

**请求体**：
```json
{
  "site_id": 123,
  "template": "blog",
  "output_dir": "/dist/"
}
```

### 部署站点

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/sites/deploy` | 部署站点到服务器（SFTP/S3） |

**请求体**：
```json
{
  "site_id": 123,
  "method": "sftp",
  "host": "example.com",
  "remote_path": "/var/www/html/"
}
```

---

## 文件上传 API

### 上传图片

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/upload/image` | 上传图片文件 |

**请求类型**: `multipart/form-data`

**表单字段**：
- `file`: 图片文件

**响应示例**：
```json
{
  "url": "/uploads/images/20240224_abc123.jpg",
  "filename": "image.jpg",
  "size": 102400
}
```

---

## WebSocket API

### 连接端点

| 端点 | 说明 |
|------|------|
| `ws://127.0.0.1:8001/ws` | WebSocket连接端点 |

**消息格式**：
```json
{
  "type": "progress_update",
  "data": {
    "task_id": 123,
    "progress": 50,
    "status": "processing"
  }
}
```

---

## 错误码说明

| HTTP状态码 | 说明 |
|-----------|------|
| `200` | 成功 |
| `400` | 请求参数错误 |
| `401` | 未授权 |
| `404` | 资源不存在 |
| `500` | 服务器内部错误 |

**错误响应格式**：
```json
{
  "detail": "错误详细信息"
}
```

---

## 在线API文档

启动后端服务后，访问以下地址查看交互式API文档：

- **Swagger UI**: http://127.0.0.1:8001/docs
- **ReDoc**: http://127.0.0.1:8001/redoc

这些文档提供在线测试功能，可以直接发送请求查看响应！

---

**维护者**: 小a
**更新日期**: 2026-02-24
