# -*- coding: utf-8 -*-
"""
Playwright 自动发布服务
用这个来实现真正的自动化发布！
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from ..config import (
    PLATFORMS,
    BROWSER_ARGS,
)
from .crypto import CryptoService
from ..database.models import Account, GeoArticle, PublishRecord
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(__name__)


class PublishResult:
    """发布结果"""
    def __init__(
        self,
        success: bool = False,
        platform_url: Optional[str] = None,
        error_msg: Optional[str] = None,
    ):
        self.success = success
        self.platform_url = platform_url
        self.error_msg = error_msg


class BasePlatformPublisher:
    """平台发布器基类 - 用抽象模式实现开闭原则！"""

    def __init__(self, platform_id: str):
        self.platform_id = platform_id
        self.config = PLATFORMS.get(platform_id, {})
        self.name = self.config.get("name", platform_id)
        self.publish_url = self.config.get("publish_url", "")

    async def publish(
        self,
        page: Page,
        article: GeoArticle,
        account: Account,
    ) -> PublishResult:
        """
        发布文章 - 子类必须实现
        设计成抽象方法，子类自己实现具体逻辑！
        """
        raise NotImplementedError(f"{self.__class__.__name__}.publish() 必须实现！")

    async def _fill_title(self, page: Page, title: str, selector: str) -> bool:
        """填充标题"""
        try:
            await page.wait_for_selector(selector, timeout=10000)
            await page.fill(selector, title)
            await asyncio.sleep(0.5)  # 等待输入完成
            return True
        except Exception as e:
            logger.error(f"填充标题失败: {e}")
            return False

    async def _fill_content(self, page: Page, content: str, selector: str) -> bool:
        """填充正文"""
        try:
            await page.wait_for_selector(selector, timeout=10000)

            # 对于 contenteditable 元素，需要特殊处理
            is_contenteditable = await page.evaluate(
                f'''() => {{
                    const el = document.querySelector("{selector}");
                    return el && el.getAttribute("contenteditable") === "true";
                }}'''
            )

            if is_contenteditable:
                # contenteditable 元素使用 click + type
                await page.click(selector)
                await page.keyboard.press("Control+A")
                await page.type(selector, content, delay=10)
            else:
                # 普通 textarea/input 使用 fill
                await page.fill(selector, content)

            await asyncio.sleep(0.5)
            return True
        except Exception as e:
            logger.error(f"填充正文失败: {e}")
            return False

    async def _click_publish(self, page: Page, selector: str) -> bool:
        """点击发布按钮"""
        try:
            await page.wait_for_selector(selector, timeout=10000)
            await page.click(selector)
            return True
        except Exception as e:
            logger.error(f"点击发布按钮失败: {e}")
            return False

    async def _wait_publish_result(self, page: Page, timeout: int = 15000) -> tuple[bool, str]:
        """等待发布结果"""
        try:
            await page.wait_for_timeout(3000)  # 至少等待3秒

            # 检查是否有错误提示
            error_selectors = [".error", ".error-message", ".fail", "[class*='error']"]
            for error_sel in error_selectors:
                try:
                    error_el = await page.query_selector(error_sel)
                    if error_el and await error_el.is_visible():
                        error_text = await error_el.text_content()
                        return False, error_text or "发布失败"
                except:
                    pass

            # 检查URL变化（发布成功通常会跳转）
            try:
                current_url = page.url
                if current_url != self.publish_url:
                    return True, current_url
            except:
                pass

            return True, "发布完成"
        except Exception as e:
            logger.error(f"等待发布结果失败: {e}")
            return False, str(e)


# ==================== 各平台发布器实现 ====================

class ZhihuPublisher(BasePlatformPublisher):
    """知乎发布器 - 最爱用知乎！"""

    def __init__(self):
        super().__init__("zhihu")
        self.selectors = {
            "title": 'input[placeholder*="请输入标题"], .Input input',
            "content": '.public-DraftStyleDefault-block, [contenteditable="true"]',
            "publish_button": '.PublishButton, button[class*="Publish"]',
        }

    async def publish(self, page: Page, article: GeoArticle, account: Account) -> PublishResult:
        """发布到知乎"""
        try:
            logger.info(f"开始发布文章到知乎: {article.title}")

            # 1. 打开创作页面
            await page.goto(self.publish_url, wait_until="networkidle")
            await asyncio.sleep(2)

            # 2. 填充标题
            title_success = await self._fill_title(page, article.title, self.selectors["title"])
            if not title_success:
                return PublishResult(False, error_msg="标题输入框未找到")

            # 3. 填充正文
            content_success = await self._fill_content(page, article.content, self.selectors["content"])
            if not content_success:
                return PublishResult(False, error_msg="正文输入框未找到")

            # 4. 等待一下确保内容加载
            await asyncio.sleep(2)

            # 5. 点击发布按钮
            publish_success = await self._click_publish(page, self.selectors["publish_button"])
            if not publish_success:
                return PublishResult(False, error_msg="发布按钮未找到")

            # 6. 等待发布结果
            success, result = await self._wait_publish_result(page)
            if success:
                logger.info(f"知乎发布成功: {article.title}")
                return PublishResult(True, platform_url=result)
            else:
                return PublishResult(False, error_msg=result)

        except Exception as e:
            logger.error(f"知乎发布异常: {e}")
            return PublishResult(False, error_msg=str(e))


class BaijiahaoPublisher(BasePlatformPublisher):
    """百家号发布器 - 重写了！先进入首页再点击图文按钮！"""

    def __init__(self):
        super().__init__("baijiahao")
        self.home_url = self.config.get("home_url", "https://baijiahao.baidu.com/builder/rc/static/edit/index")
        self.selectors = {
            # 图文按钮选择器 - 多种可能的选择器
            "article_button": [
                "span:has-text('图文')",
                "div:has(span:has-text('图文')):not([style*='display: none'])",
                "[data-type='article']",
                ".article-btn",
                "span[class*='article']",
                ".write-btn-article",
                "a:has-text('图文')",
                "button:has-text('图文')",
            ],
            # 标题输入框选择器
            "title": [
                'input[placeholder*="请输入标题"]',
                'input[placeholder*="标题"]',
                'input[class*="title"]',
                '.write-title-input',
                'input[name="title"]',
                '.title-input',
            ],
            # 正文输入框选择器
            "content": [
                '.editor-body[contenteditable="true"]',
                '#ueditor_textarea',
                '[contenteditable="true"]',
                '.editor-content',
                '.write-content',
            ],
            # 发布按钮选择器
            "publish_button": [
                '.submit-btn',
                'button[class*="submit"]',
                '.publish-button',
                'button:has-text("发布")',
                'span:has-text("发布")',
            ],
        }

    async def _click_element_by_selectors(self, page: Page, selectors: List[str], description: str = "元素", timeout: int = 10000) -> bool:
        """
        尝试用多个选择器点击元素

        用这个方法来应对页面结构变化！
        """
        for selector in selectors:
            try:
                logger.info(f"尝试点击 {description}，选择器: {selector}")
                await page.wait_for_selector(selector, timeout=timeout)
                await page.click(selector)
                logger.info(f"成功点击 {description}")
                return True
            except Exception as e:
                logger.debug(f"选择器 {selector} 失败: {e}")
                continue
        return False

    async def _fill_element_by_selectors(self, page: Page, selectors: List[str], value: str, description: str = "元素", timeout: int = 10000) -> bool:
        """
        尝试用多个选择器填充元素

        用这个方法来应对页面结构变化！
        """
        for selector in selectors:
            try:
                logger.info(f"尝试填充 {description}，选择器: {selector}")
                await page.wait_for_selector(selector, timeout=timeout)
                await page.fill(selector, value)
                await asyncio.sleep(0.5)
                logger.info(f"成功填充 {description}")
                return True
            except Exception as e:
                logger.debug(f"选择器 {selector} 失败: {e}")
                continue
        return False

    async def publish(self, page: Page, article: GeoArticle, account: Account) -> PublishResult:
        """发布到百家号 - 重写的发布流程！"""
        try:
            logger.info(f"开始发布文章到百家号: {article.title}")

            # ========== 步骤1: 进入百家号首页 ==========
            logger.info(f"访问百家号首页: {self.home_url}")
            await page.goto(self.home_url, wait_until="domcontentloaded")
            await asyncio.sleep(5)  # 百家号首页加载慢，多等一下

            # 检查是否需要重新登录（可能会跳转到登录页）
            current_url = page.url
            if "login" in current_url.lower():
                return PublishResult(False, error_msg="需要重新登录，请检查账号授权状态")

            logger.info(f"当前页面: {current_url}")

            # ========== 步骤2: 点击"图文"按钮进入图文发布界面 ==========
            logger.info("尝试点击'图文'按钮...")
            点击成功 = await self._click_element_by_selectors(
                page,
                self.selectors["article_button"],
                "图文按钮",
                timeout=10000
            )

            if not 点击成功:
                # 截图保存调试
                try:
                    screenshot_path = f"debug_baijiahao_{article.id}.png"
                    await page.screenshot(path=screenshot_path)
                    logger.info(f"已保存调试截图: {screenshot_path}")
                except:
                    pass
                return PublishResult(False, error_msg="未找到'图文'按钮，可能页面结构已变化")

            await asyncio.sleep(3)  # 等待图文编辑页面加载

            # ========== 步骤3: 填充标题 ==========
            logger.info("填充标题...")
            title_success = await self._fill_element_by_selectors(
                page,
                self.selectors["title"],
                article.title,
                "标题输入框"
            )
            if not title_success:
                return PublishResult(False, error_msg="标题输入框未找到")

            # ========== 步骤4: 填充正文 ==========
            logger.info("填充正文...")
            content_success = await self._fill_element_by_selectors(
                page,
                self.selectors["content"],
                article.content,
                "正文输入框"
            )
            if not content_success:
                return PublishResult(False, error_msg="正文输入框未找到")

            # ========== 步骤5: 等待内容加载 ==========
            await asyncio.sleep(2)

            # ========== 步骤6: 点击发布按钮 ==========
            logger.info("点击发布按钮...")
            publish_success = await self._click_element_by_selectors(
                page,
                self.selectors["publish_button"],
                "发布按钮",
                timeout=10000
            )
            if not publish_success:
                return PublishResult(False, error_msg="发布按钮未找到")

            # ========== 步骤7: 等待发布结果 ==========
            success, result = await self._wait_publish_result(page, timeout=20000)
            if success:
                logger.info(f"百家号发布成功: {article.title}")
                return PublishResult(True, platform_url=result)
            else:
                return PublishResult(False, error_msg=result)

        except Exception as e:
            logger.error(f"百家号发布异常: {e}")
            # 异常时也截图
            try:
                screenshot_path = f"debug_baijiahao_error_{article.id}.png"
                await page.screenshot(path=screenshot_path)
                logger.info(f"已保存错误截图: {screenshot_path}")
            except:
                pass
            return PublishResult(False, error_msg=str(e))


class SohuPublisher(BasePlatformPublisher):
    """搜狐号发布器"""

    def __init__(self):
        super().__init__("sohu")
        self.selectors = {
            "title": '#title, input[name="title"]',
            "content": '#ueditor_textarea, iframe[id*="ueditor"]',
            "publish_button": '.publish-btn, button[class*="publish"]',
        }

    async def publish(self, page: Page, article: GeoArticle, account: Account) -> PublishResult:
        """发布到搜狐号"""
        try:
            logger.info(f"开始发布文章到搜狐号: {article.title}")

            # 1. 打开创作页面
            await page.goto(self.publish_url, wait_until="networkidle")
            await asyncio.sleep(2)

            # 2. 填充标题
            title_success = await self._fill_title(page, article.title, self.selectors["title"])
            if not title_success:
                return PublishResult(False, error_msg="标题输入框未找到")

            # 3. 搜狐用 UEditor，需要特殊处理
            try:
                # 先尝试直接填充 textarea
                await page.wait_for_selector("#ueditor_textarea", timeout=5000)
                await page.fill("#ueditor_textarea", article.content)
            except:
                # 如果失败，尝试填充 iframe 内的内容
                try:
                    frame = page.frame("ueditor_0")
                    if frame:
                        await frame.fill("body", article.content)
                except:
                    return PublishResult(False, error_msg="正文编辑器未找到")

            await asyncio.sleep(1)

            # 4. 点击发布按钮
            publish_success = await self._click_publish(page, self.selectors["publish_button"])
            if not publish_success:
                return PublishResult(False, error_msg="发布按钮未找到")

            # 5. 等待发布结果
            success, result = await self._wait_publish_result(page)
            if success:
                logger.info(f"搜狐号发布成功: {article.title}")
                return PublishResult(True, platform_url=result)
            else:
                return PublishResult(False, error_msg=result)

        except Exception as e:
            logger.error(f"搜狐号发布异常: {e}")
            return PublishResult(False, error_msg=str(e))


class ToutiaoPublisher(BasePlatformPublisher):
    """头条号发布器"""

    def __init__(self):
        super().__init__("toutiao")
        self.selectors = {
            "title": 'input[field="title"], input[name="title"]',
            "content": '.article-container, [class*="editor"]',
            "publish_button": '.submit-btn, button[class*="submit"]',
        }

    async def publish(self, page: Page, article: GeoArticle, account: Account) -> PublishResult:
        """发布到头条号"""
        try:
            logger.info(f"开始发布文章到头条号: {article.title}")

            # 1. 打开创作页面
            await page.goto(self.publish_url, wait_until="networkidle")
            await asyncio.sleep(3)  # 头条号页面加载慢

            # 2. 填充标题
            title_success = await self._fill_title(page, article.title, self.selectors["title"])
            if not title_success:
                return PublishResult(False, error_msg="标题输入框未找到")

            # 3. 填充正文
            content_success = await self._fill_content(page, article.content, self.selectors["content"])
            if not content_success:
                return PublishResult(False, error_msg="正文输入框未找到")

            # 4. 等待内容加载
            await asyncio.sleep(2)

            # 5. 点击发布按钮
            publish_success = await self._click_publish(page, self.selectors["publish_button"])
            if not publish_success:
                return PublishResult(False, error_msg="发布按钮未找到")

            # 6. 等待发布结果
            success, result = await self._wait_publish_result(page, timeout=20000)
            if success:
                logger.info(f"头条号发布成功: {article.title}")
                return PublishResult(True, platform_url=result)
            else:
                return PublishResult(False, error_msg=result)

        except Exception as e:
            logger.error(f"头条号发布异常: {e}")
            return PublishResult(False, error_msg=str(e))


# 平台发布器注册表 - 用注册模式，方便扩展！
PUBLISHERS: Dict[str, BasePlatformPublisher] = {
    "zhihu": ZhihuPublisher(),
    "baijiahao": BaijiahaoPublisher(),
    "sohu": SohuPublisher(),
    "toutiao": ToutiaoPublisher(),
}


def get_publisher(platform_id: str) -> Optional[BasePlatformPublisher]:
    """获取平台发布器"""
    return PUBLISHERS.get(platform_id)


# ==================== 发布任务管理 ====================

class PublishTask:
    """发布任务 - 管理单个发布过程"""

    def __init__(
        self,
        task_id: str,
        article: GeoArticle,
        account: Account,
        db: AsyncSession,
        crypto: CryptoService,
    ):
        self.task_id = task_id
        self.article = article
        self.account = account
        self.db = db
        self.crypto = crypto
        self.publisher = get_publisher(account.platform)
        self.status = "pending"
        self.result: Optional[PublishResult] = None
        self.retry_count = 0

    async def execute(self) -> PublishResult:
        """执行发布任务"""
        if not self.publisher:
            return PublishResult(False, error_msg=f"不支持的发布平台: {self.account.platform}")

        self.status = "publishing"
        logger.info(f"执行发布任务: {self.task_id}")

        playwright = await async_playwright().start()
        browser: Optional[Browser] = None
        context: Optional[BrowserContext] = None

        try:
            # 1. 启动浏览器
            browser = await playwright.chromium.launch(
                headless=False,  # 显示浏览器，方便调试
                args=BROWSER_ARGS,
            )

            # 2. 创建浏览器上下文（模拟独立浏览器环境）
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )

            # 3. 加载已保存的 cookies
            if self.account.cookies:
                cookies_data = self.crypto.decrypt_cookies(self.account.cookies)
                if cookies_data:
                    await context.add_cookies(cookies_data)

            # 4. 加载 storage state（如果有的话）
            if self.account.storage_state:
                storage_state = self.crypto.decrypt_storage_state(self.account.storage_state)
                if storage_state:
                    await context.add_init_script(
                        f"""Object.assign(window, {json.dumps(storage_state)})"""
                    )

            # 5. 创建页面
            page = await context.new_page()

            # 6. 执行发布
            self.result = await self.publisher.publish(page, self.article, self.account)

            # 7. 保存结果
            if self.result.success:
                self.status = "success"
                await self._save_record(self.result.platform_url, None)
            else:
                self.status = "failed"
                await self._save_record(None, self.result.error_msg)

            return self.result

        except Exception as e:
            logger.error(f"发布任务执行异常: {e}")
            self.status = "failed"
            self.result = PublishResult(False, error_msg=str(e))
            await self._save_record(None, str(e))
            return self.result

        finally:
            # 8. 清理资源
            if context:
                await context.close()
            if browser:
                await browser.close()
            await playwright.stop()

    async def _save_record(self, platform_url: Optional[str], error_msg: Optional[str]):
        """保存发布记录到数据库"""
        try:
            record = PublishRecord(
                article_id=self.article.id,
                account_id=self.account.id,
                publish_status=2 if self.result.success else 3,  # 2=成功, 3=失败
                platform_url=platform_url,
                error_msg=error_msg,
                retry_count=self.retry_count,
                published_at=datetime.now() if self.result.success else None,
            )
            self.db.add(record)
            await self.db.commit()
        except Exception as e:
            logger.error(f"保存发布记录失败: {e}")
            await self.db.rollback()


class PublishManager:
    """发布管理器 - 管理多个发布任务"""

    def __init__(self, crypto: CryptoService):
        self.crypto = crypto
        self.active_tasks: Dict[str, PublishTask] = {}
        self.max_concurrent = 3  # 最多3个并发任务

    async def create_task(
        self,
        task_id: str,
        article: GeoArticle,
        account: Account,
        db: AsyncSession,
    ) -> PublishTask:
        """创建发布任务"""
        task = PublishTask(task_id, article, account, db, self.crypto)
        self.active_tasks[task_id] = task
        return task

    async def execute_batch(
        self,
        tasks: List[PublishTask],
        progress_callback: Optional[callable] = None,
    ) -> List[PublishResult]:
        """批量执行发布任务（并发控制）"""
        results = []
        completed = 0
        total = len(tasks)

        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def run_with_limit(task: PublishTask):
            async with semaphore:
                result = await task.execute()
                nonlocal completed
                completed += 1
                if progress_callback:
                    await progress_callback(completed, total, task)
                return result

        # 并发执行所有任务
        results = await asyncio.gather(*[run_with_limit(task) for task in tasks])

        # 清理已完成的任务
        for task in tasks:
            self.active_tasks.pop(task.task_id, None)

        return results

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.active_tasks.get(task_id)
        if not task:
            return None
        return {
            "task_id": task.task_id,
            "status": task.status,
            "article_id": task.article.id,
            "account_id": task.account.id,
            "retry_count": task.retry_count,
        }

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.active_tasks.get(task_id)
        if task:
            task.status = "cancelled"
            self.active_tasks.pop(task_id, None)
            return True
        return False
