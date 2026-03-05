# -*- coding: utf-8 -*-
"""
通义千问检测器
用这个来检测通义千问的收录情况！
"""

from typing import Dict, Any
from playwright.async_api import Page
import asyncio

from .base import AIPlatformChecker


class QianwenChecker(AIPlatformChecker):
    """
    通义千问检测器

    URL: https://tongyi.aliyun.com
    """

    SELECTORS = {
        "input_box": [
            "textarea[placeholder*='向千问提问']",
            "textarea[placeholder*='提问']",
            "textarea[placeholder*='千问']",
            "textarea[class*='ant-input']",
            "div[class*='ant-input']",
            "textarea[id*='input']",
            "textarea",
            "[contenteditable='true']",
        ],
        "submit_button": [
            "div[class*='ant-input-suffix'] button",
            "span[class*='ant-input-suffix'] button",
            "button[class*='ant-btn']",
            "button[type='submit']",
            "div[class*='submit-btn']",
            "[class*='submit']",
        ],
        "new_chat": ["div[class*='new-chat']", "div[class*='add-chat']", "button[class*='new-chat']"],
    }

    async def navigate_to_page(self, page: Page) -> bool:
        """
        通义千问特殊导航逻辑
        优化：减少等待时间

        Returns:
            是否成功导航
        """
        try:
            # 确保使用正确的聊天URL
            url = "https://tongyi.aliyun.com/qianwen/"
            self._log("info", f"正在导航到通义千问页面: {url}")

            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # 使用基类的智能等待
            try:
                indicators = ["textarea[placeholder*='输入']", "[class*='login']", "button*='登录'"]
                await self.wait_for_selector(page, indicators, timeout=10000)
            except Exception:
                pass

            # 检查登录
            login_indicators = ["[class*='login']", "button:has-text('登录')", "text='登录'", "[class*='auth']"]

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
            self._log("error", f"通义千问导航失败: {e}")
            return False

    async def submit_question(
        self, page: Page, question: str, input_selector: str, submit_button_selector: str = None
    ) -> bool:
        """
        通义千问专用的提问提交方法 - 简化版
        使用 fill + Enter 方式
        """
        try:
            self._log("info", f"开始输入问题，长度: {len(question)}")

            # 1. 点击输入框确保聚焦
            await page.click(input_selector)
            await asyncio.sleep(0.3)

            # 2. 使用 fill 填充内容
            await page.fill(input_selector, question)
            self._log("info", "问题输入完成")

            await asyncio.sleep(0.5)

            # 3. 按 Enter 提交
            await page.keyboard.press("Enter")
            self._log("info", "已提交问题")

            return True

        except Exception as e:
            self._log("error", f"提问提交失败: {e}")
            return False

    async def get_answer_content(self, page: Page, question: str) -> Dict[str, Any]:
        """
        通义千问专用的回答提取逻辑 - 终极修复版 v3
        策略调整：
        1. 恢复精确选择器（Markdown 容器），这是提取完整格式化回答的最佳方式。
        2. 智能扫描评分逻辑修正：长度权重 >>> 位置权重，防止选中底部的短提示。
        3. 黑名单优化：避免误杀包含"代码"、"图像"等通用词的长文本。
        """
        self._log("info", "使用通义千问专用逻辑获取回答 - 混合模式")

        candidates = []

        # 1. 精确选择器 (优先尝试)
        # 这些容器通常包含完整的回答
        precise_selectors = [
            "div[class*='markdown-body']",
            "div[class*='answer-content']",
            "div[class*='tongyi-ui-markdown']",
            "div[class*='result-text']",
        ]

        for selector in precise_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    text = await element.inner_text()
                    if text and len(text) > 50:
                        candidates.append(
                            {
                                "text": text,
                                "length": len(text),
                                "selector": selector,
                                "score": len(text) * 10,  # 精确选择器给予极高基础分
                            }
                        )
            except Exception:
                continue

        # 2. 智能扫描 (作为补充)
        try:
            dom_results = await page.evaluate("""() => {
                function isVisible(elem) {
                    if (!elem) return false;
                    const style = window.getComputedStyle(elem);
                    return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
                }

                const results = [];
                const divs = document.querySelectorAll('div');
                
                // 侧边栏/干扰项黑名单 (JS端初步过滤)
                const blacklist = ["指令中心", "百宝箱", "新建对话", "历史记录", "我的智能体", "输入消息"];

                for (const div of divs) {
                    if (!isVisible(div)) continue;
                    
                    const text = div.innerText;
                    if (text.length < 50) continue;
                    
                    // 排除包含子 div 过多的容器 (避免选中整个聊天窗口)
                    // 但要小心，markdown-body 里面可能也有很多 div (代码块等)
                    // 所以这个检查只针对非 markdown 类
                    if (!div.className.includes('markdown') && div.querySelectorAll('div').length > 20) continue;

                    // 黑名单检查
                    let isDirty = false;
                    for (const kw of blacklist) {
                        if (text.indexOf(kw) > -1 && text.indexOf(kw) < 100) {
                            isDirty = true;
                            break;
                        }
                    }
                    if (isDirty) continue;

                    const rect = div.getBoundingClientRect();
                    if (rect.height === 0) continue;

                    results.push({
                        text: text,
                        length: text.length,
                        top: rect.top
                    });
                }
                return results;
            }""")

            if dom_results:
                for item in dom_results:
                    # 评分公式：主要是长度，位置微调
                    # 长度权重 1，位置权重 0.1 (越靠下越好)
                    score = item["length"] + (item["top"] * 0.1)
                    candidates.append(
                        {"text": item["text"], "length": item["length"], "selector": "smart-scan", "score": score}
                    )

        except Exception as e:
            self._log("warning", f"智能扫描异常: {e}")

        # 3. 统一筛选与择优
        best_candidate = ""
        max_score = -1
        matched_selector = None

        # 严格黑名单 (Python端)
        # 这些词如果出现在文本中，且文本较短，极大概率是干扰
        short_text_blacklist = [
            "复制",
            "赞同",
            "异议",
            "重新生成",
            "停止生成",
            "深度思考",
            "深度研究",
            "代码",
            "图像",
            "文档",
            "搜索",
            "PPT",
            "对话分组",
            "最近对话",
            "我的空间",
            "任务助理",
        ]

        # 绝对黑名单 (无论文本多长，只要开头有就是侧边栏)
        prefix_blacklist = ["指令中心", "百宝箱", "新建对话", "历史记录", "我的智能体", "充值", "会员", "下载APP"]

        for item in candidates:
            text = item["text"].strip()
            length = item["length"]
            score = item["score"]

            # A. 排除纯问题复述
            if text == question.strip():
                continue

            # B. 排除包含问题的短文本 (用户气泡)
            if question.strip() in text and length < len(question) + 100:
                continue

            # C. 黑名单检查
            is_dirty = False

            # 检查绝对黑名单 (只查开头)
            for word in prefix_blacklist:
                if word in text[:100]:
                    is_dirty = True
                    break
            if is_dirty:
                continue

            # 检查短文本黑名单
            if length < 300:  # 只有短文本才检查这些通用词
                for word in short_text_blacklist:
                    if word in text:
                        is_dirty = True
                        break
            if is_dirty:
                continue

            # D. 密度检查
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            if len(lines) > 5:
                avg_len = sum(len(l) for l in lines) / len(lines)
                if avg_len < 10:  # 平均每行极短 (菜单)
                    continue

            # E. 择优
            if score > max_score:
                max_score = score
                best_candidate = text
                matched_selector = item["selector"]

        if best_candidate:
            return {
                "success": True,
                "answer": best_candidate,
                "selector": matched_selector,
                "length": len(best_candidate),
            }

        self._log("warning", "未能提取到有效回答")
        return {"success": False, "answer": "", "selector": None, "length": 0}

    async def check(self, page: Page, question: str, keyword: str, company: str) -> Dict[str, Any]:
        """
        检测通义千问收录情况

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

            nav_result = await self._retry_operation(navigate_operation, "导航到通义千问", max_retries=2)

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
