# -*- coding: utf-8 -*-
"""
RAGFlow API 客户端封装
用于文章向量化和去重检测！
"""

import os
import requests
from typing import List, Dict, Optional, Tuple
from loguru import logger


class RAGFlowClient:
    """
    RAGFlow API 客户端封装

    功能：
    1. 知识库管理
    2. 文档上传与解析
    3. 检索（用于去重）
    4. 聊天对话（用于生成）
    """

    def __init__(self, base_url: str = None, api_key: str = None):
        """
        初始化 RAGFlow 客户端

        Args:
            base_url: RAGFlow 服务地址，默认从环境变量读取
            api_key: API Key，默认从环境变量读取
        """
        self.base_url = base_url or os.getenv("RAGFLOW_BASE_URL", "http://localhost:9380")
        self.api_key = api_key or os.getenv("RAGFLOW_API_KEY", "")
        self.dataset_id = os.getenv("RAGFLOW_DATASET_ID", "")

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

        # 超时配置
        self.timeout = 30

    def is_configured(self) -> bool:
        """检查是否已配置"""
        return bool(self.api_key and self.base_url)

    # ==================== 知识库管理 ====================

    def create_dataset(self, name: str, description: str = None) -> Dict:
        """
        创建知识库

        Args:
            name: 知识库名称
            description: 描述

        Returns:
            API 响应
        """
        payload = {
            "name": name,
            "chunk_method": "naive",
            "parser_config": {
                "chunk_token_num": 8192,
                "delimiter": "\\n\\n",
                "layout_recognize": True
            }
        }
        if description:
            payload["description"] = description

        try:
            resp = self.session.post(
                f"{self.base_url}/api/v1/datasets",
                json=payload,
                timeout=self.timeout
            )
            resp.raise_for_status()
            result = resp.json()
            logger.info(f"创建知识库成功: {name}")
            return result
        except Exception as e:
            logger.error(f"创建知识库失败: {e}")
            return {"code": -1, "message": str(e)}

    def list_datasets(self, name: str = None) -> Dict:
        """
        列出知识库

        Args:
            name: 可选，按名称筛选

        Returns:
            知识库列表
        """
        params = {"page": 1, "page_size": 100}
        if name:
            params["name"] = name

        try:
            resp = self.session.get(
                f"{self.base_url}/api/v1/datasets",
                params=params,
                timeout=self.timeout
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"列出知识库失败: {e}")
            return {"code": -1, "message": str(e)}

    def get_or_create_dataset(self, name: str) -> Optional[str]:
        """
        获取或创建知识库

        Args:
            name: 知识库名称

        Returns:
            知识库 ID
        """
        # 先尝试查找
        result = self.list_datasets(name=name)
        if result.get("code") == 0:
            datasets = result.get("data", [])
            for ds in datasets:
                if ds.get("name") == name:
                    return ds.get("id")

        # 不存在则创建
        result = self.create_dataset(name, f"{name} - 自动创建")
        if result.get("code") == 0:
            return result.get("data", {}).get("id")

        return None

    # ==================== 文档管理 ====================

    def upload_document_content(self, dataset_id: str, title: str, content: str) -> Dict:
        """
        上传文本内容到知识库（创建为 txt 文档）

        Args:
            dataset_id: 知识库 ID
            title: 文档标题
            content: 文档内容

        Returns:
            API 响应
        """
        try:
            # 创建临时文件内容
            file_content = f"# {title}\n\n{content}"
            file_name = f"{title[:50]}.txt"

            # 使用 multipart/form-data 上传
            files = {
                "file": (file_name, file_content.encode("utf-8"), "text/plain")
            }
            headers = {"Authorization": f"Bearer {self.api_key}"}

            resp = requests.post(
                f"{self.base_url}/api/v1/datasets/{dataset_id}/documents",
                files=files,
                headers=headers,
                timeout=self.timeout
            )
            resp.raise_for_status()
            result = resp.json()

            if result.get("code") == 0:
                logger.info(f"文档上传成功: {title}")
                # 触发解析
                doc_ids = [doc.get("id") for doc in result.get("data", [])]
                if doc_ids:
                    self.parse_documents(dataset_id, doc_ids)

            return result

        except Exception as e:
            logger.error(f"上传文档失败: {e}")
            return {"code": -1, "message": str(e)}

    def parse_documents(self, dataset_id: str, document_ids: List[str]) -> Dict:
        """
        触发文档解析（分块）

        Args:
            dataset_id: 知识库 ID
            document_ids: 文档 ID 列表

        Returns:
            API 响应
        """
        try:
            resp = self.session.post(
                f"{self.base_url}/api/v1/datasets/{dataset_id}/chunks",
                json={"document_ids": document_ids},
                timeout=self.timeout
            )
            resp.raise_for_status()
            result = resp.json()
            logger.info(f"文档解析已触发: {len(document_ids)} 个文档")
            return result
        except Exception as e:
            logger.error(f"文档解析失败: {e}")
            return {"code": -1, "message": str(e)}

    def list_documents(self, dataset_id: str, **kwargs) -> Dict:
        """
        列出知识库中的文档

        Args:
            dataset_id: 知识库 ID
            **kwargs: 其他查询参数

        Returns:
            文档列表
        """
        try:
            resp = self.session.get(
                f"{self.base_url}/api/v1/datasets/{dataset_id}/documents",
                params=kwargs,
                timeout=self.timeout
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"列出文档失败: {e}")
            return {"code": -1, "message": str(e)}

    # ==================== 检索（去重核心）====================

    def retrieve(
        self,
        question: str,
        dataset_ids: List[str],
        similarity_threshold: float = 0.85,
        top_k: int = 1024
    ) -> Dict:
        """
        检索相似内容（用于去重）

        Args:
            question: 待检测的文章内容摘要
            dataset_ids: 知识库 ID 列表
            similarity_threshold: 相似度阈值，0-1 之间
            top_k: 候选数量

        Returns:
            检索结果
        """
        try:
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
                },
                timeout=self.timeout
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"检索失败: {e}")
            return {"code": -1, "message": str(e)}

    def check_duplicate(
        self,
        content: str,
        dataset_ids: List[str] = None,
        threshold: float = 0.85
    ) -> Tuple[bool, List[Dict]]:
        """
        检查文章是否重复

        Args:
            content: 文章内容
            dataset_ids: 知识库 ID 列表（默认使用配置的 dataset_id）
            threshold: 相似度阈值

        Returns:
            (is_duplicate, similar_articles): 是否重复及相似文章列表
        """
        if not dataset_ids:
            dataset_ids = [self.dataset_id] if self.dataset_id else []

        if not dataset_ids:
            logger.warning("未配置知识库 ID，跳过去重检测")
            return False, []

        # 生成内容摘要（取前500字符）
        summary = content[:500] if len(content) > 500 else content
        logger.debug(f"去重检索摘要: {summary[:50]}...")
        logger.debug(f"检索阈值: {threshold}, 知识库: {dataset_ids}")

        result = self.retrieve(summary, dataset_ids, similarity_threshold=threshold)

        if result.get("code") != 0:
            logger.warning(f"去重检测失败: {result.get('message')}")
            return False, []

        chunks = result.get("data", {}).get("chunks", [])
        similar_chunks = [c for c in chunks if c.get("similarity", 0) >= threshold]

        if not similar_chunks:
            return False, []

        # 按文档聚合
        articles = {}
        for chunk in similar_chunks:
            doc_id = chunk.get("document_id")
            if not doc_id:
                continue
                
            if doc_id not in articles:
                articles[doc_id] = {
                    "document_id": doc_id,
                    "document_name": chunk.get("document_name") or chunk.get("docname") or f"Doc_{doc_id[:8]}",
                    "max_similarity": chunk.get("similarity"),
                    "similar_content": chunk.get("content", "")[:200]
                }
            articles[doc_id]["max_similarity"] = max(
                articles[doc_id]["max_similarity"],
                chunk.get("similarity", 0)
            )

        return True, list(articles.values())

    # ==================== 聊天（文章生成）====================

    def create_chat(
        self,
        name: str,
        dataset_ids: List[str],
        system_prompt: str = None
    ) -> Dict:
        """
        创建聊天助手

        Args:
            name: 助手名称
            dataset_ids: 关联的知识库 ID 列表
            system_prompt: 系统提示词

        Returns:
            API 响应
        """
        payload = {
            "name": name,
            "dataset_ids": dataset_ids
        }
        if system_prompt:
            payload["prompt"] = [{"role": "system", "content": system_prompt}]

        try:
            resp = self.session.post(
                f"{self.base_url}/api/v1/chats",
                json=payload,
                timeout=self.timeout
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"创建聊天助手失败: {e}")
            return {"code": -1, "message": str(e)}

    def chat_completion(
        self,
        chat_id: str,
        question: str,
        stream: bool = False
    ) -> Dict:
        """
        发送对话请求

        Args:
            chat_id: 聊天助手 ID
            question: 问题/提示
            stream: 是否流式返回

        Returns:
            API 响应
        """
        try:
            resp = self.session.post(
                f"{self.base_url}/api/v1/chats/{chat_id}/completions",
                json={"question": question, "stream": stream},
                timeout=self.timeout * 2  # 对话可能需要更长时间
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"对话请求失败: {e}")
            return {"code": -1, "message": str(e)}


# 全局单例
_ragflow_client: Optional[RAGFlowClient] = None


def get_ragflow_client() -> RAGFlowClient:
    """获取 RAGFlow 客户端单例"""
    global _ragflow_client
    if _ragflow_client is None:
        _ragflow_client = RAGFlowClient()
    return _ragflow_client
