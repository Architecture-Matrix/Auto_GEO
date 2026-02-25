# RAGFlow API 接入文档

> **GEO_AUTO 系统自动化文章生成与去重功能接入指南**

，这份文档是开发者我熬夜整理出来的，别tm乱改！

---

## 一、概述

### 1.1 RAGFlow 是个什么玩意儿

RAGFlow 是一个开源的 RAG（检索增强生成）引擎，专门用来做知识库问答的。核心功能：
- 深度文档理解（PDF、Word、TXT、Markdown 等格式）
- 混合检索（向量 + 关键词）
- OpenAI 兼容的 API
- 工作流 Agent

### 1.2 GEO_AUTO 系统接入场景

| 场景 | 说明 | 对应 API |
|------|------|----------|
| 文章生成 | 基于知识库内容生成新文章 | Chat Completions |
| 去重检测 | 检查新文章与已有内容的相似度 | Retrieval API |
| 内容增强 | 用已有内容丰富新文章 | Retrieval + Chat |

---

## 二、认证机制

### 2.1 获取 API Key

```bash
# RAGFlow 默认 API Key 格式
ragflow-xxxxxxxxxxxxx
```

### 2.2 请求头格式

```http
Authorization: Bearer <YOUR_API_KEY>
Content-Type: application/json
```

---

## 三、知识库管理 API

### 3.1 创建知识库

```http
POST /api/v1/datasets
```

**请求体：**
```json
{
  "name": "geo_articles_kb",
  "description": "GEO_AUTO 文章知识库",
  "chunk_method": "naive",
  "parser_config": {
    "chunk_token_num": 8192,
    "delimiter": "\\n\\n",
    "layout_recognize": true
  }
}
```

**响应示例：**
```json
{
  "code": 0,
  "data": {
    "id": "6e211ee0723611efa10a0242ac120007",
    "name": "geo_articles_kb",
    "chunk_count": 0,
    "document_count": 0
  }
}
```

### 3.2 列出知识库

```http
GET /api/v1/datasets?page=1&page_size=30&orderby=create_time&desc=true
```

### 3.3 更新知识库

```http
PUT /api/v1/datasets/{dataset_id}
```

### 3.4 删除知识库

```http
DELETE /api/v1/datasets
```

**请求体：**
```json
{
  "ids": ["dataset_id_1", "dataset_id_2"]
}
```

---

## 四、文档管理 API

### 4.1 上传文档

```http
POST /api/v1/datasets/{dataset_id}/documents
Content-Type: multipart/form-data
```

**cURL 示例：**
```bash
curl -X POST "http://localhost:9380/api/v1/datasets/{dataset_id}/documents" \
  -H "Authorization: Bearer ragflow-xxxxxxxxxxxxx" \
  -F "file=@article1.pdf" \
  -F "file=@article2.docx"
```

**响应示例：**
```json
{
  "code": 0,
  "data": [
    {
      "id": "b330ec2e91ec11efbc510242ac120004",
      "name": "article1.pdf",
      "size": 17966,
      "run": "UNSTART"
    }
  ]
}
```

### 4.2 解析文档（触发分块）

```http
POST /api/v1/datasets/{dataset_id}/chunks
```

**请求体：**
```json
{
  "document_ids": ["doc_id_1", "doc_id_2"]
}
```

### 4.3 列出文档

```http
GET /api/v1/datasets/{dataset_id}/documents?page=1&page_size=10
```

**查询参数：**
| 参数 | 说明 | 默认值 |
|------|------|--------|
| page | 页码 | 1 |
| page_size | 每页数量 | 30 |
| orderby | 排序字段 | create_time |
| desc | 降序 | true |
| keywords | 标题关键词 | - |
| suffix | 文件后缀 | pdf,txt,docx |
| run | 处理状态 | DONE, RUNNING, FAIL |

**状态码说明：**
- `0` / `UNSTART` - 未开始
- `1` / `RUNNING` - 处理中
- `2` / `CANCEL` - 已取消
- `3` / `DONE` - 已完成
- `4` / `FAIL` - 失败

### 4.4 删除文档

```http
DELETE /api/v1/datasets/{dataset_id}/documents
```

**请求体：**
```json
{
  "ids": ["doc_id_1", "doc_id_2"]
}
```

---

## 五、检索 API（去重核心）

### 5.1 基础检索

```http
POST /api/v1/retrieval
```

**请求体：**
```json
{
  "question": "文章内容摘要或关键词",
  "dataset_ids": ["dataset_id_1"],
  "page": 1,
  "page_size": 10,
  "similarity_threshold": 0.7,
  "vector_similarity_weight": 0.3,
  "top_k": 1024,
  "keyword": true,
  "highlight": true
}
```

### 5.2 去重检测参数说明

| 参数 | 去重场景建议值 | 说明 |
|------|----------------|------|
| similarity_threshold | `0.85 - 0.95` | 相似度阈值，越高越严格 |
| vector_similarity_weight | `0.5 - 0.7` | 向量相似度权重 |
| top_k | `1024` | 参与计算的候选数量 |
| keyword | `true` | 启用关键词匹配 |

### 5.3 去重响应示例

```json
{
  "code": 0,
  "data": {
    "total": 3,
    "chunks": [
      {
        "id": "chunk_123",
        "content": "相似的文章内容片段...",
        "document_id": "doc_456",
        "document_name": "existing_article.pdf",
        "similarity": 0.92,
        "vector_similarity": 0.90,
        "term_similarity": 0.95,
        "highlight": "<em>相似</em>的内容..."
      }
    ]
  }
}
```

### 5.4 去重判断逻辑

```python
def is_duplicate_article(retrieval_result, threshold=0.85):
    """
    判断文章是否重复

    Args:
        retrieval_result: 检索API返回结果
        threshold: 相似度阈值，默认0.85

    Returns:
        (is_duplicate, similar_articles): 是否重复及相似文章列表
    """
    if retrieval_result.get("code") != 0:
        return False, []

    chunks = retrieval_result.get("data", {}).get("chunks", [])

    # 过滤出高相似度的chunk
    similar_chunks = [
        c for c in chunks
        if c.get("similarity", 0) >= threshold
    ]

    if not similar_chunks:
        return False, []

    # 按文档聚合，避免同一文档的多个chunk重复统计
    article_similarity = {}
    for chunk in similar_chunks:
        doc_id = chunk.get("document_id")
        if doc_id not in article_similarity:
            article_similarity[doc_id] = {
                "document_id": doc_id,
                "document_name": chunk.get("document_name"),
                "max_similarity": chunk.get("similarity"),
                "chunks": []
            }
        article_similarity[doc_id]["chunks"].append(chunk)
        article_similarity[doc_id]["max_similarity"] = max(
            article_similarity[doc_id]["max_similarity"],
            chunk.get("similarity")
        )

    similar_articles = list(article_similarity.values())
    return True, similar_articles
```

---

## 六、聊天对话 API（文章生成）

### 6.1 创建聊天助手

```http
POST /api/v1/chats
```

**请求体：**
```json
{
  "name": "geo_article_writer",
  "dataset_ids": ["dataset_id_1"],
  "llm_id": "deepseek-chat",
  "prompt": [
    {
      "role": "system",
      "content": "你是一个专业的地理内容文章写作助手，基于知识库内容生成高质量原创文章。"
    }
  ]
}
```

### 6.2 生成文章

```http
POST /api/v1/chats/{chat_id}/completions
```

**请求体：**
```json
{
  "question": "请根据知识库内容，生成一篇关于'某某地理现象'的800字原创文章",
  "stream": false
}
```

**响应示例：**
```json
{
  "code": 0,
  "data": {
    "answer": "生成的文章内容...",
    "reference": {
      "chunks": [
        {
          "document_name": "reference.pdf",
          "content": "参考内容片段..."
        }
      ]
    },
    "session_id": "session_id_xxx"
  }
}
```

### 6.3 OpenAI 兼容接口

```http
POST /api/v1/chats_openai/{chat_id}
```

**Python SDK 示例：**
```python
from openai import OpenAI

client = OpenAI(
    api_key="ragflow-xxxxxxxxxxxxx",
    base_url="http://localhost:9380/api/v1/chats_openai/{chat_id}"
)

response = client.chat.completions.create(
    model="model",
    messages=[
        {"role": "user", "content": "生成一篇关于XXX的文章"}
    ],
    stream=False,
    extra_body={"reference": True}
)

print(response.choices[0].message.content)
```

---

## 七、Agent API（工作流）

### 7.1 创建 Agent

```http
POST /api/v1/agents
```

**请求体：**
```json
{
  "title": "geo_article_agent",
  "description": "GEO_AUTO 文章生成工作流Agent",
  "dsl": {
    "graph": {
      "nodes": [],
      "edges": []
    }
  }
}
```

### 7.2 Agent 对话

```http
POST /api/v1/agents/{agent_id}/completions
```

**OpenAI 兼容接口：**
```http
POST /api/v1/agents_openai/{agent_id}/chat/completions
```

---

## 八、Python SDK 使用

### 8.1 安装

```bash
pip install ragflow-sdk
```

### 8.2 初始化

```python
from ragflow_sdk import RAGFlow

rag = RAGFlow(
    api_key="ragflow-xxxxxxxxxxxxx",
    base_url="http://localhost:9380"
)
```

### 8.3 完整工作流示例

```python
from ragflow_sdk import RAGFlow

# 初始化
rag = RAGFlow(api_key="ragflow-xxxxx", base_url="http://localhost:9380")

# 1. 创建知识库
dataset = rag.create_dataset(
    name="geo_articles",
    chunk_method="naive"
)

# 2. 上传文档
dataset.upload_documents([
    {"name": "article1.pdf", "blob": open("article1.pdf", "rb").read()}
])

# 3. 解析文档
docs = dataset.list_documents()
doc_ids = [doc.id for doc in docs]
dataset.parse_documents(doc_ids)

# 4. 创建聊天助手
chat = rag.create_chat(
    name="geo_writer",
    dataset_ids=[dataset.id],
    prompt=[{
        "role": "system",
        "content": "你是地理文章写作助手"
    }]
)

# 5. 生成文章
session = chat.create_session()
response = session.ask("写一篇关于XX地理现象的文章", stream=False)
print(response["answer"])
```

---

## 九、GEO_AUTO 系统接入架构

### 9.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      GEO_AUTO 系统                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │  文章生成   │───>│  去重检测    │───>│  发布管理    │   │
│  └─────────────┘    └──────────────┘    └──────────────┘   │
│         │                   │                                │
│         ▼                   ▼                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              RAGFlow 集成层                          │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  • 知识库管理  • 文档管理  • 检索  • 对话            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAGFlow 服务                              │
│  知识库 | 文档解析 | 向量检索 | LLM 对话 | Agent 工作流      │
└─────────────────────────────────────────────────────────────┘
```

### 9.2 推荐的技术实现方案

```python
# backend/services/ragflow_client.py（推荐新建这个文件）

import requests
from typing import List, Dict, Optional, Tuple
import os

class RAGFlowClient:
    """RAGFlow API 客户端封装 - 开发者出品"""

    def __init__(self):
        self.base_url = os.getenv("RAGFLOW_BASE_URL", "http://localhost:9380")
        self.api_key = os.getenv("RAGFLOW_API_KEY")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

    # ========== 知识库管理 ==========
    def create_dataset(self, name: str, description: str = None) -> Dict:
        """创建知识库"""
        payload = {"name": name}
        if description:
            payload["description"] = description
        resp = self.session.post(f"{self.base_url}/api/v1/datasets", json=payload)
        resp.raise_for_status()
        return resp.json()

    def list_datasets(self, name: str = None) -> Dict:
        """列出知识库"""
        params = {}
        if name:
            params["name"] = name
        resp = self.session.get(f"{self.base_url}/api/v1/datasets", params=params)
        resp.raise_for_status()
        return resp.json()

    # ========== 文档管理 ==========
    def upload_document(self, dataset_id: str, file_path: str) -> Dict:
        """上传文档到知识库"""
        # 需要用新的session处理multipart
        import requests
        with open(file_path, "rb") as f:
            files = {"file": f}
            headers = {"Authorization": f"Bearer {self.api_key}"}
            resp = requests.post(
                f"{self.base_url}/api/v1/datasets/{dataset_id}/documents",
                files=files,
                headers=headers
            )
        resp.raise_for_status()
        return resp.json()

    def parse_documents(self, dataset_id: str, document_ids: List[str]) -> Dict:
        """触发文档解析"""
        resp = self.session.post(
            f"{self.base_url}/api/v1/datasets/{dataset_id}/chunks",
            json={"document_ids": document_ids}
        )
        resp.raise_for_status()
        return resp.json()

    def list_documents(self, dataset_id: str, **kwargs) -> Dict:
        """列出知识库中的文档"""
        resp = self.session.get(
            f"{self.base_url}/api/v1/datasets/{dataset_id}/documents",
            params=kwargs
        )
        resp.raise_for_status()
        return resp.json()

    # ========== 检索（去重核心）==========
    def retrieve(self, question: str, dataset_ids: List[str],
                 similarity_threshold: float = 0.85,
                 top_k: int = 1024) -> Dict:
        """
        检索相似内容（用于去重）

        Args:
            question: 待检测的文章内容摘要
            dataset_ids: 知识库ID列表
            similarity_threshold: 相似度阈值，0-1之间
            top_k: 候选数量
        """
        resp = self.session.post(
            f"{self.base_url}/api/v1/retrieval",
            json={
                "question": question,
                "dataset_ids": dataset_ids,
                "similarity_threshold": similarity_threshold,
                "vector_similarity_weight": 0.5,
                "top_k": top_k,
                "keyword": True,
                "highlight": True
            }
        )
        resp.raise_for_status()
        return resp.json()

    def check_duplicate(self, content: str, dataset_ids: List[str],
                       threshold: float = 0.85) -> Tuple[bool, List[Dict]]:
        """
        检查文章是否重复

        Returns:
            (is_duplicate, similar_articles)
        """
        # 生成内容摘要（实际可用更复杂的摘要算法）
        summary = content[:500] if len(content) > 500 else content

        result = self.retrieve(summary, dataset_ids, similarity_threshold=threshold)

        if result.get("code") != 0:
            return False, []

        chunks = result.get("data", {}).get("chunks", [])
        similar_chunks = [c for c in chunks if c.get("similarity", 0) >= threshold]

        if not similar_chunks:
            return False, []

        # 按文档聚合
        articles = {}
        for chunk in similar_chunks:
            doc_id = chunk.get("document_id")
            if doc_id not in articles:
                articles[doc_id] = {
                    "document_id": doc_id,
                    "document_name": chunk.get("document_name"),
                    "max_similarity": chunk.get("similarity"),
                    "similar_content": chunk.get("content", "")[:200]
                }
            articles[doc_id]["max_similarity"] = max(
                articles[doc_id]["max_similarity"],
                chunk.get("similarity")
            )

        return True, list(articles.values())

    # ========== 聊天（文章生成）==========
    def create_chat(self, name: str, dataset_ids: List[str],
                    system_prompt: str = None) -> Dict:
        """创建聊天助手"""
        payload = {
            "name": name,
            "dataset_ids": dataset_ids
        }
        if system_prompt:
            payload["prompt"] = [{"role": "system", "content": system_prompt}]

        resp = self.session.post(f"{self.base_url}/api/v1/chats", json=payload)
        resp.raise_for_status()
        return resp.json()

    def chat_completion(self, chat_id: str, question: str,
                        stream: bool = False) -> Dict:
        """发送对话请求生成文章"""
        resp = self.session.post(
            f"{self.base_url}/api/v1/chats/{chat_id}/completions",
            json={"question": question, "stream": stream}
        )
        resp.raise_for_status()
        return resp.json()
```

### 9.3 环境变量配置

在 `.env` 文件中添加：

```bash
# RAGFlow 配置
RAGFLOW_BASE_URL=http://localhost:9380
RAGFLOW_API_KEY=ragflow-xxxxxxxxxxxxx
RAGFLOW_DATASET_ID=your_dataset_id
RAGFLOW_CHAT_ID=your_chat_id

# 去重阈值配置
DUPLICATE_THRESHOLD=0.85
```

---

## 十、快速接入步骤

### Step 1: 部署 RAGFlow 服务

```bash
# Docker 方式部署
docker pull infiniflow/ragflow:v0.13.0
docker run -d --name ragflow \
  -p 9380:9380 \
  -v /data/ragflow:/ragflow/server \
  infiniflow/ragflow:v0.13.0

# 访问 http://localhost:9380 获取 API Key
```

### Step 2: 创建知识库并上传历史文章

```bash
# 使用上面的 RAGFlowClient
python -c "
from backend.services.ragflow_client import RAGFlowClient

client = RAGFlowClient()
dataset = client.create_dataset('geo_articles_kb')
print(f'知识库ID: {dataset}')

# 上传历史文章...
"
```

### Step 3: 集成去重功能

```python
# 在文章发布前调用去重检测

from backend.services.ragflow_client import RAGFlowClient

client = RAGFlowClient()
dataset_ids = [os.getenv("RAGFLOW_DATASET_ID")]

is_dup, similar = client.check_duplicate(
    content=article_content,
    dataset_ids=dataset_ids,
    threshold=0.85
)

if is_dup:
    print(f"警告：文章可能重复！")
    for art in similar:
        print(f"  - {art['document_name']} (相似度: {art['max_similarity']:.2%})")
    # 中止发布或要求确认
else:
    # 继续发布流程
    pass
```

### Step 4: 集成文章生成功能

```python
# 使用 RAGFlow 生成新文章

from backend.services.ragflow_client import RAGFlowClient

client = RAGFlowClient()

# 创建或获取聊天助手
chat = client.create_chat(
    name="geo_writer",
    dataset_ids=[os.getenv("RAGFLOW_DATASET_ID")],
    system_prompt="你是一个专业的地理内容文章写作助手..."
)

# 生成文章
result = client.chat_completion(
    chat_id=chat["data"]["id"],
    question=f"请写一篇关于{keyword}的800字原创地理科普文章"
)

generated_article = result["data"]["answer"]
```

---

## 十一、API 参考

### 完整 API 端点列表

| 功能 | 方法 | 端点 | 说明 |
|------|------|------|------|
| 知识库 | POST | `/api/v1/datasets` | 创建 |
| 知识库 | GET | `/api/v1/datasets` | 列表 |
| 知识库 | PUT | `/api/v1/datasets/{id}` | 更新 |
| 知识库 | DELETE | `/api/v1/datasets` | 批量删除 |
| 文档 | POST | `/api/v1/datasets/{id}/documents` | 上传 |
| 文档 | GET | `/api/v1/datasets/{id}/documents` | 列表 |
| 文档 | POST | `/api/v1/datasets/{id}/chunks` | 解析 |
| 文档 | DELETE | `/api/v1/datasets/{id}/documents` | 批量删除 |
| 检索 | POST | `/api/v1/retrieval` | 混合检索 |
| 聊天 | POST | `/api/v1/chats` | 创建助手 |
| 聊天 | POST | `/api/v1/chats/{id}/completions` | 对话 |
| Agent | POST | `/api/v1/agents` | 创建 |
| Agent | POST | `/api/v1/agents/{id}/completions` | 执行 |

---

## 十二、常见问题

### Q1: 如何调整去重灵敏度？

```python
# 相似度阈值建议值
STRICT_THRESHOLD = 0.90    # 严格模式，极少误报
NORMAL_THRESHOLD = 0.85    # 正常模式，平衡
LOOSE_THRESHOLD = 0.75     # 宽松模式，可能误报
```

### Q2: 检索结果为空？

检查以下几点：
1. 文档是否已解析完成（`run=DONE`）
2. `similarity_threshold` 是否设置过高
3. 知识库是否有内容

### Q3: 如何提高生成文章质量？

1. 完善 system_prompt
2. 向知识库添加更多高质量参考文章
3. 调整 parser_config 的 chunk_token_num

---

**文档版本**: v1.0
**最后更新**: 2025-01-13
**整理人**: 开发者
**备注**: ，写这份文档开发者我可是费了不少劲，别tm到处乱传！
