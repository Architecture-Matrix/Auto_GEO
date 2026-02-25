# -*- coding: utf-8 -*-
"""
知乎文章收集适配器
爬取知乎热门文章！
"""

import re
from typing import Dict, Any, Optional, List
from playwright.async_api import Page
from loguru import logger

from .base import BaseCollector, CollectedArticle


class ZhihuCollector(BaseCollector):
    """
    知乎文章收集适配器

    搜索页面：https://www.zhihu.com/search?type=content&q={keyword}
    """

    SELECTORS = {
        "search_results": ".SearchResult-Card",
        "article_title": "h2.ContentItem-title a, .ContentItem-title a",
        "article_link": "h2.ContentItem-title a, .ContentItem-title a",
        "vote_count": ".VoteButton--up, [class*='VoteButton']",
        "comment_count": "button:has-text('评论'), [class*='comment']",
        "author": ".AuthorInfo-name, .UserLink-link",
        "content_body": ".Post-RichText, .RichContent-inner, .RichText, article, .ContentItem-content",
        "next_page_button": "button.Pagination-next, button:has-text('下一页')",
        "pagination_container": ".Pagination",
    }

    async def search(self, page: Page, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索知乎文章，支持多页翻页
        """
        all_articles = []
        try:
            # 1. 导航到搜索页
            search_url = f"https://www.zhihu.com/search?type=content&q={keyword}"
            await page.goto(search_url, wait_until="networkidle")
            
            # 从配置中获取最大页数，默认3页
            max_pages = self.config.get("max_pages", 3)
            
            for current_page in range(1, max_pages + 1):
                logger.info(f"[知乎] 正在搜索第 {current_page} 页...")
                
                # 模拟真人阅读延时
                await self._random_sleep(2, 4)
                await self._handle_login_popup(page)
                
                # 2. 模拟真人滚动加载
                await self._human_scroll(page)

                # 3. 提取当前页搜索结果
                page_articles = await self._extract_search_results(page)
                
                # 去重合并
                for art in page_articles:
                    if not any(a['url'] == art['url'] for a in all_articles):
                        all_articles.append(art)
                
                logger.info(f"[知乎] 第 {current_page} 页搜索完成，当前累计: {len(all_articles)} 篇")

                # 4. 寻找并点击“下一页”
                if current_page < max_pages:
                    next_button = await page.query_selector(self.SELECTORS["next_page_button"])
                    if next_button and await next_button.is_visible():
                        logger.info("[知乎] 发现下一页按钮，准备点击...")
                        await next_button.scroll_into_view_if_needed()
                        await self._random_sleep(1, 2)
                        await next_button.click()
                        await page.wait_for_load_state("networkidle")
                    else:
                        logger.info("[知乎] 未发现更多页码或按钮，停止翻页")
                        break
            
            return all_articles

        except Exception as e:
            logger.error(f"[知乎] 搜索过程中发生异常: {e}")
            return all_articles

    async def collect(self, page: Page, keyword: str) -> List[CollectedArticle]:
        """
        收集知乎爆火文章（重写基类方法以实现分页顺序抓取）
        """
        # 我们这里依然可以使用重写的 collect 来实现更精细的按页顺序存储逻辑
        # 如果直接用基类的 collect，它会先跑完所有页的 search，然后再跑 extract_content
        # 这里的重写能保证“抓到一页，处理一页”，更符合用户“按顺序存储”且防封的需求
        all_collected = []
        try:
            # 1. 导航到搜索页
            search_url = f"https://www.zhihu.com/search?type=content&q={keyword}"
            await page.goto(search_url, wait_until="networkidle")
            
            max_pages = self.config.get("max_pages", 3)
            
            for current_page in range(1, max_pages + 1):
                logger.info(f"[知乎] 正在处理第 {current_page} 页...")
                
                await self._random_sleep(2, 4)
                await self._handle_login_popup(page)
                await self._human_scroll(page)

                # 提取当前页结果
                page_articles = await self._extract_search_results(page)
                
                # 立即筛选并提取正文
                trending_in_page = self._filter_trending(page_articles)
                logger.info(f"[知乎] 第 {current_page} 页筛选出 {len(trending_in_page)} 篇爆火文章")

                for article in trending_in_page:
                    if any(a.url == article["url"] for a in all_collected):
                        continue
                        
                    content = await self.extract_content(page, article["url"])
                    if content:
                        all_collected.append(CollectedArticle(
                            title=article.get("title", ""),
                            url=article.get("url", ""),
                            content=content,
                            likes=article.get("likes", 0),
                            reads=article.get("reads", 0),
                            comments=article.get("comments", 0),
                            author=article.get("author", ""),
                            platform=self.platform_id,
                            publish_time=article.get("publish_time", "")
                        ))
                        await self._random_sleep(1, 3)
                    
                    # 提取完后必须切回搜索结果页
                    if page.url != search_url:
                        await page.goto(search_url, wait_until="networkidle")
                        await self._random_sleep(1, 2)

                logger.info(f"[知乎] 第 {current_page} 页处理完成，当前累计采集: {len(all_collected)} 篇")

                if current_page < max_pages:
                    next_button = await page.query_selector(self.SELECTORS["next_page_button"])
                    if next_button and await next_button.is_visible():
                        await next_button.scroll_into_view_if_needed()
                        await self._random_sleep(1, 2)
                        await next_button.click()
                        await page.wait_for_load_state("networkidle")
                        search_url = page.url
                    else:
                        break
            
            return all_collected

        except Exception as e:
            logger.error(f"[知乎] 采集过程中发生异常: {e}")
            return all_collected

    async def _extract_search_results(self, page: Page) -> List[Dict[str, Any]]:
        """提取搜索结果"""
        articles = []

        try:
            # 获取所有搜索结果卡片
            cards = await page.query_selector_all(".SearchResult-Card, .Card.SearchResult-Card")

            for card in cards:
                try:
                    # 提取标题和链接
                    title_elem = await card.query_selector("h2.ContentItem-title a, .ContentItem-title a")
                    if not title_elem:
                        continue

                    title = await title_elem.text_content()
                    href = await title_elem.get_attribute("href")

                    # 处理相对链接
                    if href and not href.startswith("http"):
                        href = f"https://www.zhihu.com{href}"

                    # 提取点赞数
                    likes = 0
                    vote_elem = await card.query_selector(".VoteButton--up, [class*='VoteButton']")
                    if vote_elem:
                        vote_text = await vote_elem.text_content()
                        likes = self._parse_number(vote_text)

                    # 提取评论数
                    comments = 0
                    comment_elem = await card.query_selector("button:has-text('评论'), [class*='comment']")
                    if comment_elem:
                        comment_text = await comment_elem.text_content()
                        comments = self._parse_number(comment_text)

                    # 提取作者
                    author = ""
                    author_elem = await card.query_selector(".AuthorInfo-name, .UserLink-link")
                    if author_elem:
                        author = await author_elem.text_content()

                    if title and href:
                        articles.append({
                            "title": title.strip(),
                            "url": href,
                            "likes": likes,
                            "reads": likes * 50,  # 知乎没有直接显示阅读量，用点赞估算
                            "comments": comments,
                            "author": author.strip() if author else "",
                        })

                except Exception as e:
                    logger.debug(f"[知乎] 提取单条结果失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"[知乎] 提取搜索结果失败: {e}")

        return articles

    async def extract_content(self, page: Page, url: str) -> Optional[str]:
        """提取文章正文"""
        try:
            logger.info(f"[知乎] 正在提取正文: {url}")
            await page.goto(url, wait_until="networkidle")
            
            # 增加随机延时，模拟真人阅读
            await self._random_sleep(2, 5)

            # 检测并处理登录弹窗
            await self._handle_login_popup(page)
            
            # 尝试从 SELECTORS 中定义的多个选择器提取
            selectors = self.SELECTORS["content_body"].split(", ")

            for selector in selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        # 优先获取 inner_text 保持格式
                        content = await elem.inner_text()
                        if content and len(content) > 100:
                            logger.info(f"[知乎] 提取正文成功: {len(content)} 字符 (选择器: {selector})")
                            return content.strip()
                except Exception:
                    continue

            # 兜底：如果上述选择器都失败，尝试直接获取所有段落文本
            try:
                paragraphs = await page.query_selector_all("p")
                if paragraphs:
                    content = "\n".join([await p.inner_text() for p in paragraphs])
                    if len(content) > 200:
                        logger.info(f"[知乎] 提取正文成功 (兜底策略): {len(content)} 字符")
                        return content.strip()
            except Exception:
                pass

            logger.warning(f"[知乎] 未能提取正文: {url}")
            return None

        except Exception as e:
            logger.error(f"[知乎] 提取正文失败: {e}")
            return None

    def _parse_number(self, text: str) -> int:
        """解析数字（支持 1.2k, 1.5w 等格式）"""
        if not text:
            return 0

        text = text.strip().lower()

        # 移除非数字字符但保留k、w、万
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
