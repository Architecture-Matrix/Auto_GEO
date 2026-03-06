# -*- coding: utf-8 -*-
"""
n8n 服务封装 - v3.0 TLS指纹伪装版
1. 支持环境变量配置 N8N 地址 (Docker/生产环境必备)
2. 使用 curl_cffi 模拟真实浏览器 TLS 指纹，绕过 Cloudflare/WAF 拦截
3. 增强响应解析兼容性
4. 支持异步回调模式，n8n生成完成后通过回调通知

v3.0 更新：用 curl_cffi 替换 httpx，解决 TLS 指纹检测问题
"""

import asyncio
import json
import os
from typing import Any, Literal, Optional, List, Dict
from loguru import logger
from pydantic import BaseModel, ConfigDict

# 使用 curl_cffi 绕过 TLS 指纹检测
try:
    from curl_cffi import requests as curl_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    # 降级到 httpx
    import httpx
    CURL_CFFI_AVAILABLE = False
    logger.warning("curl_cffi 未安装，降级使用 httpx（可能被 Cloudflare 拦截）")

from backend.config import N8N_CALLBACK_URL


# ==================== 配置 ====================


class N8nConfig:
    # 🌟 优先读取环境变量，适配 Docker/生产环境
    # 格式示例：http://n8n:5678/webhook 或 http://192.168.1.10:5678/webhook
    WEBHOOK_BASE = os.getenv("N8N_WEBHOOK_URL", "https://n8n.opencaio.cn/webhook")

    # 超时配置
    TIMEOUT_SHORT = 45.0
    TIMEOUT_LONG = 300.0  # 长文章生成

    # 重试配置
    MAX_RETRIES = 1

    # 回调URL（异步回调模式下使用）
    CALLBACK_URL = N8N_CALLBACK_URL

    # SSL 验证（某些网络环境可能需要禁用）
    VERIFY_SSL = os.getenv("N8N_VERIFY_SSL", "true").lower() == "true"

    # TLS 指纹伪装（使用浏览器指纹绕过检测）
    IMPERSONATE = os.getenv("N8N_IMPERSONATE", "chrome")


# ==================== 请求模型 ====================


class KeywordDistillRequest(BaseModel):
    keywords: Optional[List[str]] = None
    project_id: Optional[int] = None
    core_kw: Optional[str] = None
    target_info: Optional[str] = None
    prefixes: Optional[str] = None
    suffixes: Optional[str] = None


class GenerateQuestionsRequest(BaseModel):
    question: str
    count: int = 10


class GeoArticleRequest(BaseModel):
    keyword: str
    requirements: str = ""
    word_count: int = 1200
    # 异步回调模式新增字段
    callback_url: Optional[str] = None
    article_id: Optional[int] = None


class IndexCheckAnalysisRequest(BaseModel):
    keyword: str
    doubao_indexed: bool
    qianwen_indexed: bool
    deepseek_indexed: bool
    history: List[Dict] = []


# ==================== 响应模型 ====================


class N8nResponse(BaseModel):
    """n8n 统一响应格式"""

    status: Literal["success", "error", "processing"]
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== 服务类 ====================


class N8nService:
    """
    n8n 服务类
    v3.0 使用 curl_cffi 模拟真实浏览器，绕过 Cloudflare/WAF TLS 指纹检测
    """

    def __init__(self, config: Optional[N8nConfig] = None):
        self.config = config or N8nConfig()
        self.log = logger.bind(module="AI中台")
        self._client = None
        self._use_curl_cffi = CURL_CFFI_AVAILABLE

        if self._use_curl_cffi:
            self.log.info("🌟 使用 curl_cffi (Chrome TLS 指纹) 连接 n8n")
        else:
            self.log.warning("⚠️ curl_cffi 不可用，使用 httpx（可能被拦截）")

    async def close(self):
        """关闭 HTTP 客户端"""
        # curl_cffi 不需要显式关闭
        pass

    def _sync_call_webhook(
        self, endpoint: str, payload: Dict[str, Any], timeout: Optional[float] = None
    ) -> N8nResponse:
        """底层同步调用逻辑（curl_cffi 用）"""
        path = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        base = self.config.WEBHOOK_BASE.rstrip("/")
        url = f"{base}{path}"

        timeout_val = timeout or self.config.TIMEOUT_SHORT

        self.log.info(f"🛰️ 正在外发 AI 请求: {url}")
        self.log.debug(f"📦 请求数据: {json.dumps(payload, ensure_ascii=False)}")

        for attempt in range(self.config.MAX_RETRIES + 1):
            try:
                # 使用 curl_cffi 模拟 Chrome 浏览器
                resp = curl_requests.post(
                    url,
                    json=payload,
                    timeout=timeout_val,
                    impersonate=self.config.IMPERSONATE,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                        "Accept": "application/json, text/plain, */*",
                        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                        "Content-Type": "application/json",
                    },
                    verify=self.config.VERIFY_SSL,
                )
                raw_text = resp.text

                # 检查 HTTP 状态码
                if resp.status_code != 200:
                    err_msg = f"HTTP {resp.status_code}: {raw_text[:200]}"
                    self.log.error(f"❌ n8n 返回错误: {err_msg}")
                    return N8nResponse(status="error", error=err_msg)

                # 解析 JSON
                try:
                    res_data = resp.json()

                    # 如果返回数组，取第一个
                    if isinstance(res_data, list):
                        res_data = res_data[0] if len(res_data) > 0 else {}

                    # 兼容性处理
                    if isinstance(res_data, dict) and "status" not in res_data:
                        return N8nResponse(status="success", data=res_data)

                    return N8nResponse(**res_data)

                except Exception:
                    if raw_text and not raw_text.strip().startswith(("{", "[")):
                        self.log.warning("⚠️ n8n 返回了非 JSON 文本")
                        return N8nResponse(status="success", data={"text_content": raw_text})

                    self.log.error("❌ n8n 响应解析失败")
                    self.log.error(f"🔍 原始响应:\n{raw_text[:500]}")
                    return N8nResponse(status="error", error=f"JSON解析失败: {raw_text[:100]}")

            except curl_requests.RequestsError as e:
                self.log.error(f"🚨 n8n 连接失败: {type(e).__name__}: {str(e)}")
                self.log.error(f"🔗 目标URL: {url}")
                if attempt == self.config.MAX_RETRIES:
                    return N8nResponse(
                        status="error",
                        error=f"无法连接到 n8n 服务 ({url})，请检查网络或服务是否运行"
                    )

            except Exception as e:
                self.log.error(f"🚨 传输层异常: {type(e).__name__}: {str(e)}")
                self.log.error(f"🔗 目标URL: {url}")
                return N8nResponse(status="error", error=f"{type(e).__name__}: {str(e)}")

        return N8nResponse(status="error", error="未知错误")

    async def _call_webhook(
        self, endpoint: str, payload: Dict[str, Any], timeout: Optional[float] = None
    ) -> N8nResponse:
        """底层统一调用逻辑"""
        if self._use_curl_cffi:
            # curl_cffi 是同步的，在线程池中运行
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self._sync_call_webhook(endpoint, payload, timeout)
            )
        else:
            # 降级使用 httpx（异步）
            return await self._httpx_call_webhook(endpoint, payload, timeout)

    async def _httpx_call_webhook(
        self, endpoint: str, payload: Dict[str, Any], timeout: Optional[float] = None
    ) -> N8nResponse:
        """httpx 降级方案"""
        import httpx

        path = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        base = self.config.WEBHOOK_BASE.rstrip("/")
        url = f"{base}{path}"
        timeout_val = timeout or self.config.TIMEOUT_SHORT

        self.log.info(f"🛰️ 正在外发 AI 请求 (httpx): {url}")

        async with httpx.AsyncClient(
            timeout=timeout_val,
            verify=self.config.VERIFY_SSL,
            trust_env=False,
        ) as client:
            try:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    return N8nResponse(status="error", error=f"HTTP {resp.status_code}")

                res_data = resp.json()
                if isinstance(res_data, list):
                    res_data = res_data[0] if len(res_data) > 0 else {}

                if isinstance(res_data, dict) and "status" not in res_data:
                    return N8nResponse(status="success", data=res_data)

                return N8nResponse(**res_data)

            except Exception as e:
                self.log.error(f"❌ httpx 请求失败: {e}")
                return N8nResponse(status="error", error=str(e))

    # ==================== 业务方法 ====================

    async def distill_keywords(
        self,
        *,
        core_kw: Optional[str] = None,
        target_info: Optional[str] = None,
        prefixes: Optional[str] = None,
        suffixes: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        project_id: Optional[int] = None,
    ) -> N8nResponse:
        self.log.info("🧹 正在蒸馏提纯关键词...")
        self.log.debug(f"📝 输入参数: core_kw={core_kw}, target_info={target_info}")
        payload = KeywordDistillRequest(
            keywords=keywords,
            project_id=project_id,
            core_kw=core_kw,
            target_info=target_info,
            prefixes=prefixes,
            suffixes=suffixes,
        ).model_dump(exclude_none=True)
        return await self._call_webhook("keyword-distill", payload)

    async def generate_questions(self, question: str, count: int = 10) -> N8nResponse:
        self.log.info("❓ 正在基于原题扩展变体...")
        payload = GenerateQuestionsRequest(question=question, count=count).model_dump()
        return await self._call_webhook("generate-questions", payload)

    async def generate_geo_article(
        self,
        keyword: str,
        requirements: str = "",
        word_count: int = 1200,
        callback_url: Optional[str] = None,
        article_id: Optional[int] = None,
    ) -> N8nResponse:
        """异步生成GEO文章"""
        final_callback_url = callback_url or self.config.CALLBACK_URL
        self.log.info(f"📝 正在撰写GEO文章 (关键词: {keyword})...")
        payload = GeoArticleRequest(
            keyword=keyword,
            requirements=requirements,
            word_count=word_count,
            callback_url=final_callback_url,
            article_id=article_id,
        ).model_dump(exclude_none=True)
        return await self._call_webhook("geo-article-generate", payload, timeout=self.config.TIMEOUT_LONG)

    async def analyze_index_check(
        self,
        keyword: str,
        doubao_indexed: bool,
        qianwen_indexed: bool,
        deepseek_indexed: bool,
        history: Optional[List[Dict]] = None,
    ) -> N8nResponse:
        self.log.info("📊 正在请求 AI 深度分析收录趋势...")
        payload = IndexCheckAnalysisRequest(
            keyword=keyword,
            doubao_indexed=doubao_indexed,
            qianwen_indexed=qianwen_indexed,
            deepseek_indexed=deepseek_indexed,
            history=history or [],
        ).model_dump()
        return await self._call_webhook("index-check-analysis", payload)


# ==================== 单例模式 ====================

_instance: Optional[N8nService] = None


async def get_n8n_service() -> N8nService:
    global _instance
    if _instance is None:
        _instance = N8nService()
    return _instance
