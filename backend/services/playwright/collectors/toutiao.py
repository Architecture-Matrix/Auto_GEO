# -*- coding: utf-8 -*-
"""
今日头条文章收集适配器
爬取头条热门文章！
"""

import re
from typing import Dict, Any, Optional, List
from playwright.async_api import Page
from loguru import logger

from .base import BaseCollector


class ToutiaoCollector(BaseCollector):
    """
    今日头条文章收集适配器

    搜索页面：https://so.toutiao.com/search?keyword={keyword}
    """

    async def search(self, page: Page, keyword: str) -> List[Dict[str, Any]]:
        """搜索头条文章"""
        try:
            # 1. 导航到搜索页
            # 使用更完整的搜索 URL，模拟真实请求
            search_url = f"https://so.toutiao.com/search?keyword={keyword}&enable_druid_v2=1&dvpf=pc&source=search_subtab_switch&pd=information&action_type=search_subtab_switch&page_num=0&search_id=&from=news&cur_tab_title=news"
            await page.goto(search_url, wait_until="networkidle")
            
            # 增加延时，等待页面加载和可能的弹窗
            await self._random_sleep(3, 5)

            # 2. 滚动加载更多
            await self._human_scroll(page)

            # 3. 提取搜索结果
            articles = await self._extract_search_results(page)

            return articles

        except Exception as e:
            logger.error(f"[头条] 搜索失败: {e}")
            return []

    async def _extract_search_results(self, page: Page) -> List[Dict[str, Any]]:
        """提取搜索结果"""
        articles = []

        try:
            # 获取搜索结果项
            cards = await page.query_selector_all("[class*='result-content'], .result-item, .article-card")

            for card in cards:
                try:
                    # 提取标题和链接
                    title_elem = await card.query_selector("a[class*='title'], .title a, h3 a")
                    if not title_elem:
                        continue

                    title = await title_elem.text_content()
                    href = await title_elem.get_attribute("href")

                    # 处理相对链接
                    if href and not href.startswith("http"):
                        href = f"https://www.toutiao.com{href}"

                    # 提取阅读量/评论数（头条通常显示阅读量）
                    reads = 0
                    comments = 0

                    # 尝试提取数据
                    meta_elem = await card.query_selector("[class*='read'], [class*='comment'], .meta")
                    if meta_elem:
                        meta_text = await meta_elem.text_content()
                        reads = self._parse_number(meta_text)

                    # 提取作者
                    author = ""
                    author_elem = await card.query_selector("[class*='source'], [class*='author'], .name")
                    if author_elem:
                        author = await author_elem.text_content()

                    if title and href:
                        articles.append({
                            "title": title.strip(),
                            "url": href,
                            "likes": reads // 100,  # 估算点赞数
                            "reads": reads,
                            "comments": comments,
                            "author": author.strip() if author else "",
                        })

                except Exception as e:
                    logger.debug(f"[头条] 提取单条结果失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"[头条] 提取搜索结果失败: {e}")

        return articles

    async def extract_content(self, page: Page, url: str) -> Optional[str]:
        """提取文章正文"""
        try:
            logger.info(f"[头条] 正在提取文章: {url}")
            await page.goto(url, wait_until="domcontentloaded")
            
            # 增加延时，等待页面加载
            await self._random_sleep(3, 5)

            # 检测登录弹窗
            await self._handle_login_popup(page)
            
            # 尝试多种选择器
            selectors = [
                "article",
                ".article-content",
                ".tt-article-content",
                ".syl-article-base",
                ".syl-page-article",
                ".content",
                "[class*='article-body']",
                ".post-content",
                # 针对不同版面的补充
                "div[class*='article-content']",
                "div[class*='text']"
            ]

            content = None
            for selector in selectors:
                try:
                    # 等待选择器出现，超时时间短一点避免卡太久
                    try:
                        await page.wait_for_selector(selector, timeout=2000)
                    except:
                        pass

                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.text_content()
                        if text and len(text.strip()) > 100:
                            content = text.strip()
                            logger.info(f"[头条] 提取正文成功 (选择器: {selector}): {len(content)} 字符")
                            break
                except Exception as e:
                    logger.debug(f"[头条] 选择器 {selector} 提取失败: {e}")
                    continue

            if not content:
                logger.warning(f"[头条] 未能提取正文: {url}")
                # 保存调试信息
                try:
                    import os
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    debug_dir = "tests/reports/debug"
                    os.makedirs(debug_dir, exist_ok=True)
                    
                    # 保存 HTML
                    html_path = f"{debug_dir}/toutiao_fail_{timestamp}.html"
                    html_content = await page.content()
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    
                    # 保存截图
                    img_path = f"{debug_dir}/toutiao_fail_{timestamp}.png"
                    await page.screenshot(path=img_path)
                    
                    logger.info(f"[头条] 已保存调试文件: {html_path}, {img_path}")
                except Exception as e:
                    logger.error(f"[头条] 保存调试文件失败: {e}")

            return content

        except Exception as e:
            logger.error(f"[头条] 提取正文失败: {e}")
            return None

    def _parse_number(self, text: str) -> int:
        """解析数字"""
        if not text:
            return 0

        text = text.strip().lower()
        match = re.search(r'([\d.]+)\s*([kwm万])?', text)
        if not match:
            return 0

        num = float(match.group(1))
        unit = match.group(2)

        if unit in ['k', 'K']:
            num *= 1000
        elif unit in ['w', 'W', '万']:
            num *= 10000
        elif unit in ['m', 'M']:
            num *= 1000000

        return int(num)
