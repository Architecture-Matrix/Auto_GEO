# -*- coding: utf-8 -*-
"""
文章收集适配器基类
用适配器模式实现各平台收集，遵循开闭原则！
"""

import asyncio
import random
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from playwright.async_api import Page
from loguru import logger


@dataclass
class CollectedArticle:
    """收集到的文章数据结构"""
    title: str
    url: str
    content: str
    likes: int = 0
    reads: int = 0
    comments: int = 0
    author: str = ""
    platform: str = ""
    publish_time: str = ""


class BaseCollector(ABC):
    """
    基础文章收集适配器
    注意：所有平台收集器都要继承这个类！
    """

    def __init__(self, platform_id: str, config: Dict[str, Any]):
        self.platform_id = platform_id
        self.config = config
        self.name = config.get("name", platform_id)
        self.search_url = config.get("search_url", "")
        self.min_likes = config.get("min_likes", 100)
        self.min_reads = config.get("min_reads", 1000)

    @abstractmethod
    async def search(self, page: Page, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索关键词相关文章

        Args:
            page: Playwright Page对象
            keyword: 搜索关键词

        Returns:
            搜索结果列表：[{title, url, likes, reads, ...}, ...]
        """
        pass

    @abstractmethod
    async def extract_content(self, page: Page, url: str) -> Optional[str]:
        """
        提取文章正文内容

        Args:
            page: Playwright Page对象
            url: 文章URL

        Returns:
            文章正文内容
        """
        pass

    async def collect(self, page: Page, keyword: str) -> List[CollectedArticle]:
        """
        收集爆火文章（主流程）

        Args:
            page: Playwright Page对象
            keyword: 搜索关键词

        Returns:
            符合条件的文章列表
        """
        try:
            # 1. 搜索文章
            search_results = await self.search(page, keyword)
            logger.info(f"[{self.name}] 搜索到 {len(search_results)} 篇文章")

            # 2. 筛选爆火文章
            trending_articles = self._filter_trending(search_results)
            logger.info(f"[{self.name}] 筛选出 {len(trending_articles)} 篇爆火文章")

            # 3. 提取正文内容
            collected = []
            for article in trending_articles:
                content = await self.extract_content(page, article["url"])
                if content:
                    collected.append(CollectedArticle(
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

            return collected

        except Exception as e:
            logger.error(f"[{self.name}] 收集文章失败: {e}")
            return []

    def _filter_trending(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        筛选爆火文章

        筛选逻辑：点赞数 > min_likes 或 阅读量 > min_reads
        """
        trending = []
        for article in articles:
            likes = article.get("likes", 0)
            reads = article.get("reads", 0)

            if likes > self.min_likes or reads > self.min_reads:
                trending.append(article)
                logger.debug(f"[{self.name}] 爆火: {article.get('title', '')[:30]}... "
                           f"(👍{likes}, 👁{reads})")

        return trending

    async def wait_for_selector(self, page: Page, selector: str, timeout: int = 10000) -> bool:
        """等待选择器出现"""
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            logger.warning(f"等待选择器超时: {selector}, {e}")
            return False

    async def navigate_to_search(self, page: Page, keyword: str) -> bool:
        """导航到搜索页面"""
        try:
            search_url = self.search_url.format(keyword=keyword)
            await page.goto(search_url, wait_until="networkidle")
            logger.info(f"[{self.name}] 已导航到搜索页: {keyword}")
            return True
        except Exception as e:
            logger.error(f"[{self.name}] 导航搜索页失败: {e}")
            return False

    async def _random_sleep(self, min_seconds: float = 2.0, max_seconds: float = 5.0):
        """随机等待，模拟真人操作"""
        await asyncio.sleep(random.uniform(min_seconds, max_seconds))

    async def _human_scroll(self, page: Page):
        """模拟真人缓慢滚动"""
        try:
            # 获取页面高度
            total_height = await page.evaluate("document.body.scrollHeight")
            viewport_height = await page.evaluate("window.innerHeight")
            current_position = 0

            # 滚动最多 3 屏或者到底部
            max_scrolls = 3
            scroll_count = 0

            while current_position < total_height and scroll_count < max_scrolls:
                # 每次滚动前检测登录弹窗
                await self._handle_login_popup(page)

                # 随机滚动距离
                scroll_step = random.randint(300, 800)
                current_position += scroll_step
                
                # 执行滚动
                await page.evaluate(f"window.scrollTo(0, {current_position})")
                
                # 随机等待，模拟阅读
                await self._random_sleep(0.5, 1.5)
                
                # 更新高度（处理动态加载）
                new_total_height = await page.evaluate("document.body.scrollHeight")
                if new_total_height > total_height:
                    total_height = new_total_height
                    
                scroll_count += 1
                logger.debug(f"[{self.name}] 模拟滚动 {scroll_count}/{max_scrolls}")
                    
        except Exception as e:
            logger.warning(f"[{self.name}] 滚动模拟异常: {e}")

    async def _handle_login_popup(self, page: Page):
        """处理登录弹窗与拦截"""
        try:
            # 1. 检查 URL 是否包含登录相关词
            current_url = page.url
            if "signin" in current_url or "login" in current_url:
                logger.warning(f"[{self.name}] 当前 URL 包含登录关键词: {current_url}")
                await self._wait_for_manual_login(page)
                return

            # 2. 常见弹窗选择器
            popup_selectors = [
                ".Modal-wrapper", # 知乎登录弹窗
                ".login-modal", 
                ".captcha-box",
                ".sign-flow-modal", # 知乎登录
                "[class*='login-modal']", # 通用登录模态框
                "[class*='LoginModal']",
                ".SignFlow", # 知乎
                ".Button.SignFlow-submitButton", # 知乎登录按钮
                "iframe[src*='login']", # 登录 iframe
                "#captcha-verify-image", # 验证码
                "div[class*='captcha']", # 通用验证码容器
                ".verify-bar-close", # 验证条关闭按钮
            ]
            
            needs_login = False
            for selector in popup_selectors:
                if await page.query_selector(selector):
                    # 确保是可见的
                    if await page.is_visible(selector):
                        needs_login = True
                        logger.warning(f"[{self.name}] 发现登录弹窗选择器: {selector}")
                        break
            
            # 3. 检查页面文本（作为兜底）
            if not needs_login:
                # 检查标题
                title = await page.title()
                if "登录" in title or "安全验证" in title:
                     needs_login = True
                     logger.warning(f"[{self.name}] 页面标题包含登录关键词: {title}")

                # 只获取 body 文本，避免获取完整 HTML 导致过慢
                # 限制文本长度检查，只查前 1000 个字符或者特定区域
                if not needs_login:
                    try:
                        # 快速检查 body 的 textContent，如果太长可能会卡
                        # 优化：只检查特定元素是否存在文本
                        login_keywords = ["登录后查看更多", "请登录", "扫码登录", "验证码", "安全验证", "注册/登录", "依次点击", "拖动滑块"]
                        
                        # 使用 evaluate 快速在浏览器端检查，减少传输
                        js_check = """
                            () => {
                                const text = document.body.innerText;
                                const keywords = ["登录后查看更多", "请登录", "扫码登录", "验证码", "安全验证", "注册/登录", "依次点击", "拖动滑块"];
                                return keywords.some(k => text.includes(k));
                            }
                        """
                        if await page.evaluate(js_check):
                             # 再次确认不是误报（比如文章内容里有这些词）
                             # 这里假设如果包含这些词，大概率是拦截提示
                             needs_login = True
                             logger.warning(f"[{self.name}] 页面文本包含登录关键词")
                    except Exception:
                        pass

            if needs_login:
                await self._wait_for_manual_login(page)
                
        except Exception as e:
            # 这里的异常不应该阻断流程，只是记录日志
            logger.debug(f"[{self.name}] 登录检测异常: {e}")

    async def _wait_for_manual_login(self, page: Page):
        """等待手动登录"""
        logger.warning("\n" + "!"*50)
        logger.warning(f"[{self.name}] 检测到登录弹窗或验证码！")
        logger.warning("请在 45 秒内手动完成登录/验证操作...")
        logger.warning("!"*50 + "\n")
        
        # 给用户 45 秒时间手动操作
        # 每 5 秒检查一次是否登录成功（可选，这里简单等待）
        for i in range(9):
            await asyncio.sleep(5)
            logger.info(f"[{self.name}] 剩余等待时间: {45 - (i+1)*5} 秒...")
            
            # 如果弹窗消失了，提前结束等待
            # 这里简单实现，假设用户操作完后弹窗会消失
            # 实际上很难通用判断，所以还是硬等待比较稳妥
            
        logger.info(f"[{self.name}] 手动操作时间结束，继续执行...")


class CollectorRegistry:
    """
    收集器注册表
    用这个来管理所有平台的收集器！
    """

    def __init__(self):
        self._collectors: Dict[str, BaseCollector] = {}

    def register(self, platform_id: str, collector: BaseCollector):
        """注册收集器"""
        self._collectors[platform_id] = collector
        logger.info(f"收集器已注册: {platform_id}")

    def get(self, platform_id: str) -> Optional[BaseCollector]:
        """获取收集器"""
        return self._collectors.get(platform_id)

    def list_all(self) -> Dict[str, BaseCollector]:
        """列出所有收集器"""
        return self._collectors.copy()


# 全局注册表
collector_registry = CollectorRegistry()


def get_collector(platform_id: str) -> Optional[BaseCollector]:
    """获取平台收集器"""
    return collector_registry.get(platform_id)


def list_collectors() -> Dict[str, BaseCollector]:
    """列出所有收集器"""
    return collector_registry.list_all()
