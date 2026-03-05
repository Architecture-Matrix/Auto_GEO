# -*- coding: utf-8 -*-
"""
文档信息提取服务 - AI驱动
从上传的文档中自动提取客户信息（公司名称、联系人、电话、邮箱、行业、地址等）
"""

import json
import re
from typing import Dict, Optional, List
from loguru import logger

try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    logger.warning("httpx未安装，AI信息提取功能可能受限")

from backend.config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL


class DocumentExtractor:
    """
    文档信息提取服务
    使用AI从文档内容中提取结构化的客户信息
    """

    def __init__(self, api_key: str = None, api_url: str = None):
        """
        初始化文档提取器

        Args:
            api_key: DeepSeek API Key（默认从配置读取）
            api_url: DeepSeek API URL（默认从配置读取）
        """
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.api_url = api_url or DEEPSEEK_API_URL
        self.timeout = 60

    def is_configured(self) -> bool:
        """检查是否已配置API"""
        return bool(self.api_key and self.api_url and HAS_HTTPX)

    def extract_from_text(self, text: str) -> Dict:
        """
        从文本中提取客户信息

        Args:
            text: 文档文本内容

        Returns:
            提取的客户信息字典
        """
        if not self.is_configured():
            logger.warning("AI服务未配置，使用正则表达式提取")
            return self._extract_with_regex(text)

        try:
            return self._extract_with_ai(text)
        except Exception as e:
            logger.error(f"AI提取失败，使用正则表达式: {e}")
            return self._extract_with_regex(text)

    def _extract_with_ai(self, text: str) -> Dict:
        """
        使用AI提取客户信息

        Args:
            text: 文档文本内容

        Returns:
            提取的客户信息字典
        """
        if not HAS_HTTPX:
            raise ImportError("httpx未安装，无法使用AI提取功能")

        # 截取前5000字符（避免token超限）
        text = text[:5000]

        prompt = f"""请从以下文档内容中提取客户信息，并以JSON格式返回：

文档内容：
{text}

请提取以下信息（如果文档中存在）：
- company_name: 公司名称
- contact_person: 联系人姓名
- phone: 联系电话
- email: 邮箱地址
- industry: 所属行业
- address: 公司地址
- description: 公司/业务描述

返回格式要求：
1. 必须是有效的JSON格式
2. 只返回提取到的信息，未提取到的字段返回null
3. 不要添加任何其他说明文字

返回示例：
{{
    "company_name": "绿阳环保科技有限公司",
    "contact_person": "张三",
    "phone": "13800138000",
    "email": "zhangsan@example.com",
    "industry": "环保工程",
    "address": "北京市朝阳区xxx路xxx号",
    "description": "专注于环保工程和清洁服务..."
}}
"""

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.api_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,  # 降低温度提高稳定性
                        "max_tokens": 1000,
                    },
                )
                response.raise_for_status()
                result = response.json()

                # 提取AI返回的JSON
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

                # 尝试解析JSON
                try:
                    # 清理可能的markdown代码块标记
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.startswith("```"):
                        content = content[3:]
                    if content.endswith("```"):
                        content = content[:-3]
                    content = content.strip()

                    extracted = json.loads(content)
                    logger.info(f"AI提取成功: {extracted}")
                    return extracted
                except json.JSONDecodeError as e:
                    logger.warning(f"AI返回的不是有效JSON: {content[:200]}")
                    return self._extract_with_regex(text)

        except httpx.HTTPError as e:
            logger.error(f"AI API请求失败: {e}")
            raise
        except Exception as e:
            logger.error(f"AI提取失败: {e}")
            raise

    def _extract_with_regex(self, text: str) -> Dict:
        """
        使用正则表达式提取客户信息（降级方案）

        Args:
            text: 文档文本内容

        Returns:
            提取的客户信息字典
        """
        result = {}

        # 提取邮箱
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        emails = re.findall(email_pattern, text)
        if emails:
            result["email"] = emails[0]

        # 提取电话（手机号或座机）
        phone_patterns = [
            r"1[3-9]\d{9}",  # 手机号
            r"\d{3,4}-?\d{7,8}",  # 座机
            r"\d{11}",  # 11位数字（可能是手机号）
        ]
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                result["phone"] = phones[0]
                break

        # 提取可能的行业关键词
        industry_keywords = [
            "环保工程",
            "工业清洗",
            "无人机服务",
            "电商",
            "教育培训",
            "金融服务",
            "医疗健康",
            "制造业",
            "房地产",
            "餐饮美食",
            "旅游出行",
            "物流运输",
            "新能源",
            "化工行业",
            "建筑工程",
            "SaaS软件",
            "互联网",
            "科技",
        ]
        for industry in industry_keywords:
            if industry in text:
                result["industry"] = industry
                break

        logger.info(f"正则表达式提取结果: {result}")
        return result

    def extract_from_ragflow_document(self, dataset_id: str, document_id: str, ragflow_client) -> Dict:
        """
        从RAGFlow文档中提取客户信息

        Args:
            dataset_id: RAGFlow知识库ID
            document_id: RAGFlow文档ID
            ragflow_client: RAGFlow客户端实例

        Returns:
            提取的客户信息字典
        """
        try:
            # 获取文档内容
            doc_result = ragflow_client.get_document_content(dataset_id, document_id)

            if doc_result.get("code") != 0:
                logger.error(f"获取RAGFlow文档内容失败: {doc_result.get('message')}")
                return {}

            content = doc_result.get("data", {}).get("content", "")
            if not content:
                logger.warning("RAGFlow文档内容为空")
                return {}

            # 提取客户信息
            return self.extract_from_text(content)

        except Exception as e:
            logger.error(f"从RAGFlow文档提取信息失败: {e}")
            return {}


# 全局单例
_extractor: Optional[DocumentExtractor] = None


def get_document_extractor() -> DocumentExtractor:
    """获取文档提取器单例"""
    global _extractor
    if _extractor is None:
        _extractor = DocumentExtractor()
    return _extractor
