# -*- coding: utf-8 -*-
"""
DeepSeek检测器
用这个来检测DeepSeek的收录情况！
"""

from typing import Dict, Any
from playwright.async_api import Page
import asyncio

from .base import AIPlatformChecker


class DeepSeekChecker(AIPlatformChecker):
    """
    DeepSeek检测器

    URL: https://chat.deepseek.com
    """

    SELECTORS = {
        "input_box": [
            "textarea[id='chat-input']",
            "textarea[placeholder*='Message']",
            "textarea[placeholder*='DeepSeek']",
            "textarea[placeholder*='输入']",
            "textarea",
            "[contenteditable='true']",
        ],
        "submit_button": ["div[class*='ds-button']", "[class*='send-button']", "button[type='submit']"],
        "new_chat": ["div[class*='new-chat']", "[class*='new-chat']"],
    }

    async def navigate_to_page(self, page: Page) -> bool:
        """
        DeepSeek特殊导航逻辑
        优化：减少等待时间

        Returns:
            是否成功导航
        """
        try:
            url = "https://chat.deepseek.com"
            self._log("info", f"正在导航到DeepSeek页面: {url}")

            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # 使用基类的智能等待
            try:
                indicators = ["textarea[placeholder*='输入']", "[class*='login']", "button*='登录'"]
                await self.wait_for_selector(page, indicators, timeout=10000)
            except Exception:
                pass

            # 检查登录
            login_indicators = ["[class*='login']", "button*='登录'", "[class*='auth']"]

            has_login = False
            for indicator in login_indicators:
                try:
                    element = await page.query_selector(indicator)
                    if element and await element.is_visible():
                        has_login = True
                        break
                except Exception:
                    continue

            if has_login:
                self._log("info", "检测到登录页面，请手动完成登录")
                # 修复：给用户90秒时间完成登录（原来30秒不够）
                await asyncio.sleep(90)
                await page.wait_for_load_state("domcontentloaded", timeout=30000)

            return True
        except Exception as e:
            self._log("error", f"DeepSeek导航失败: {e}")
            return False

    async def get_answer_content(self, page: Page, question: str) -> Dict[str, Any]:
        """
        DeepSeek专用的回答提取逻辑
        """
        self._log("info", "使用DeepSeek专用逻辑获取回答")

        # DeepSeek的回答容器选择器（基于观察）
        deepseek_selectors = [
            "[class*='ds-message']",
            "[class*='chat-response']",
            "[class*='assistant-message']",
            "[class*='markdown']",
        ]

        answer_text = ""
        matched_selector = None

        for selector in deepseek_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    # 获取最后一个非用户消息
                    for element in reversed(elements):
                        text = await element.inner_text()
                        if len(text) > 50 and question not in text[:50]:
                            answer_text = text
                            matched_selector = selector
                            break
                    if answer_text:
                        break
            except Exception:
                continue

        if answer_text:
            return {
                "success": True,
                "answer": answer_text[:5000],
                "selector": matched_selector,
                "length": len(answer_text),
            }

        # 如果专用选择器失败，回退到基类逻辑
        return await super().get_answer_content(page, question)

    async def check(self, page: Page, question: str, keyword: str, company: str) -> Dict[str, Any]:
        """
        检测DeepSeek收录情况

        Returns:
            检测结果详细信息
        """
        self._log("info", f"开始检测, 问题: {question[:50]}...")
        self._log("info", f"目标关键词: {keyword}, 公司: {company}")

        try:

            async def navigate_operation():
                if await self.navigate_to_page(page):
                    return {"success": True}
                return {"success": False, "error_msg": "导航失败"}

            nav_result = await self._retry_operation(navigate_operation, "导航到DeepSeek", max_retries=2)

            if not nav_result["success"]:
                return {
                    "success": False,
                    "answer": None,
                    "keyword_found": False,
                    "company_found": False,
                    "error_msg": nav_result.get("error_msg", "导航失败"),
                }

            async def clear_operation():
                if await self.clear_chat_history(page):
                    return {"success": True}
                return {"success": False, "error_msg": "清理失败"}

            await self._retry_operation(clear_operation, "清理聊天历史", max_retries=1)

            input_selectors = self.SELECTORS["input_box"]

            success, matched_selector = await self.wait_for_selector(page, input_selectors, timeout=20000)

            if not success:
                self._log("error", "未找到输入框")
                return {
                    "success": False,
                    "answer": None,
                    "keyword_found": False,
                    "company_found": False,
                    "error_msg": "输入框未找到",
                }

            self._log("info", f"找到输入框: {matched_selector}")

            # 使用基类稳健的提交方法
            submit_selectors = self.SELECTORS.get("submit_button", [])
            submit_btn = submit_selectors[0] if submit_selectors else None

            await self.submit_question(
                page=page, question=question, input_selector=matched_selector, submit_button_selector=submit_btn
            )

            self._log("info", "已提交问题")

            initial_content = await page.inner_text("body")

            wait_result = await self.wait_for_answer_generation(
                page, initial_content, timeout=60000, check_interval=2.0
            )

            if wait_result["success"]:
                self._log("info", f"回答生成成功, 长度: {wait_result['content_length']} 字符")
            else:
                self._log("warning", f"回答生成未完成, 长度: {wait_result.get('content_length', 0)} 字符")

            answer_result = await self.get_answer_content(page, question)

            if not answer_result["success"]:
                self._log("warning", "未能获取到AI回答内容")

            answer_text = answer_result.get("answer", "")

            if not answer_text.strip():
                answer_text = await page.inner_text("body")
                self._log("info", f"使用页面全文作为回答, 长度: {len(answer_text)}")

            check_result = self.check_keywords_in_text(answer_text, keyword, company)

            self._log("info", "检测完成")
            self._log("info", f"关键词 '{keyword}' 检测结果: {check_result['keyword_found']}")
            self._log("info", f"公司名 '{company}' 检测结果: {check_result['company_found']}")

            operation_logs = self.get_operation_log()

            return {
                "success": True,
                "answer": answer_text[:5000],
                "keyword_found": check_result["keyword_found"],
                "company_found": check_result["company_found"],
                "keyword_count": check_result.get("keyword_count", 0),
                "company_count": check_result.get("company_count", 0),
                "confidence": check_result.get("confidence", 0.0),
                "answer_length": len(answer_text),
                "wait_info": wait_result,
                "answer_selector": answer_result.get("selector"),
                "operation_logs": operation_logs,
                "error_msg": None,
            }

        except Exception as e:
            self._log("error", f"检测过程发生异常: {e}")
            return {
                "success": False,
                "answer": None,
                "keyword_found": False,
                "company_found": False,
                "error_msg": str(e),
            }
