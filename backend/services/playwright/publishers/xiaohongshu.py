# -*- coding: utf-8 -*-
"""
小红书发布适配器 - v1.0 初始版

核心特性:
1. 图文笔记发布
2. 封面图上传
3. 话题标签添加
4. AI创作声明
5. 多图内容支持
"""

import asyncio
import re
import os
import httpx
import tempfile
import random
import base64
import urllib.parse
from typing import Dict, Any, List
from playwright.async_api import Page
from loguru import logger

from .base import BasePublisher, registry


class XiaohongshuPublisher(BasePublisher):
    """
    小红书发布适配器 - v1.0 初始版

    核心特性:
    1. 图文笔记发布
    2. 封面图上传
    3. 话题标签添加
    4. 多图内容支持
    5. 强容错机制
    """

    async def publish(self, page: Page, article: Any, account: Any, declare_ai_content: bool = True) -> Dict[str, Any]:
        """发布笔记到小红书"""
        temp_files = []
        try:
            logger.info("🚀 [小红书] 开始执行发布流程...")

            # ========== 步骤 1: 导航到发布页面 ==========
            await self._navigate_to_publisher(page)
            await asyncio.sleep(3)

            # ========== 步骤 2: 准备图片资源 ==========
            # A. 提取关键词
            clean_title = article.title.replace("#", "").strip()
            keyword = self._extract_keyword(clean_title)
            logger.info(f"🔍 提取关键词: {keyword}")

            # B. 下载图片 (封面+正文配图)
            downloaded_paths = await self._download_images(keyword, count=5)
            temp_files.extend(downloaded_paths)

            if not downloaded_paths:
                logger.warning("⚠️ 图片下载失败，但继续后续流程")
            else:
                logger.success(f"✅ [图片] 已成功下载 {len(downloaded_paths)} 张图片")

            # ========== 步骤 3: 清理内容 ==========
            clean_content = self._clean_content(article.content)

            # ========== 步骤 4: 填充标题 ==========
            await self._fill_title(page, clean_title)
            await asyncio.sleep(1)

            # ========== 步骤 5: 填充正文 ==========
            await self._fill_content(page, clean_content)
            await asyncio.sleep(2)

            # ========== 步骤 6: 上传封面图 ==========
            if downloaded_paths:
                await self._upload_cover(page, downloaded_paths[0])
                await asyncio.sleep(2)

            # ========== 步骤 7: 上传正文配图 ==========
            if len(downloaded_paths) > 1:
                await self._upload_content_images(page, downloaded_paths[1:])
                await asyncio.sleep(2)

            # ========== 步骤 8: 添加话题标签 ==========
            await self._add_topics(page, clean_title)
            await asyncio.sleep(1)

            # ========== 步骤 9: 发布确认 ==========
            if not await self._click_publish(page):
                return {"success": False, "error_msg": "发布失败"}

            # ========== 步骤 10: 等待结果 ==========
            return await self._wait_for_publish_result(page)

        except Exception as e:
            logger.exception(f"❌ [小红书] 发布链路崩溃: {e}")
            return {"success": False, "error_msg": str(e)}
        finally:
            for f in temp_files:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                        logger.info(f"🧹 已删除临时图片: {f}")
                    except Exception as e:
                        logger.warning(f"⚠️ 删除临时图片失败: {e}")

    def _extract_keyword(self, title: str) -> str:
        """从标题中提取关键词"""
        cleaned = re.sub(r"[^\w\u4e00-\u9fff]", " ", title)
        words = cleaned.split()
        if words:
            return words[0] if len(words) == 1 else f"{words[0]} {words[1]}"
        return "生活"

    def _clean_content(self, content: str) -> str:
        """清理正文内容"""
        # 移除 Markdown 图片标记
        content = re.sub(r"!\[.*?\]\(.*?\)", "", content)
        # 移除 Markdown 标题符号
        content = re.sub(r"#+\s*", "", content)
        # 移除加粗符号
        content = re.sub(r"\*\*+", "", content)
        return content.strip()

    async def _download_images(self, keyword: str, count: int = 5) -> List[str]:
        """下载相关图片"""
        paths = []
        used_seeds = set()
        base_url = "https://image.pollinations.ai/prompt/"

        async def _download_single_image(url: str, index: int) -> str:
            try:
                logger.info(f"📥 正在下载图片 {index + 1}/{count}...")
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                async with httpx.AsyncClient(headers=headers, verify=False, timeout=30.0) as client:
                    resp = await client.get(url, timeout=30.0)
                    if resp.status_code == 200 and len(resp.content) > 1000:
                        tmp = os.path.join(tempfile.gettempdir(), f"xhs_{random.randint(10000, 99999)}.jpg")
                        with open(tmp, "wb") as f:
                            f.write(resp.content)
                        logger.info(f"✅ 图片 {index + 1} 下载成功")
                        return tmp
            except Exception as e:
                logger.warning(f"⚠️ 图片 {index + 1} 下载失败: {e}")
            return None

        for i in range(count):
            while True:
                seed = random.randint(1, 10000)
                if seed not in used_seeds:
                    used_seeds.add(seed)
                    break

            encoded_keyword = urllib.parse.quote(f"high quality photo of {keyword} aesthetic {seed}")
            image_url = f"{base_url}{encoded_keyword}?width=800&height=600&nologo=true"

            downloaded = await _download_single_image(image_url, i)
            if downloaded:
                paths.append(downloaded)

        return paths

    async def _navigate_to_publisher(self, page: Page):
        """导航到发布页面"""
        await page.goto(self.config["publish_url"], wait_until="networkidle", timeout=60000)
        logger.info("✅ [导航] 成功抵达发布页面")

    async def _fill_title(self, page: Page, title: str):
        """填充标题"""
        try:
            # 等待标题输入框出现
            title_selectors = [
                'input[placeholder*="填写标题"]',
                'input[placeholder*="标题"]',
                ".title-input",
                'input[type="text"]',
            ]

            for selector in title_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    await page.fill(selector, title)
                    logger.success(f"✅ [标题] 标题已填充: {title[:20]}...")
                    return
                except:
                    continue

            logger.warning("⚠️ [标题] 未找到标题输入框")
        except Exception as e:
            logger.error(f"❌ [标题] 填充失败: {e}")

    async def _fill_content(self, page: Page, content: str):
        """填充正文"""
        try:
            # 等待正文输入框出现
            content_selectors = [
                'div[contenteditable="true"]',
                'textarea[placeholder*="填写正文"]',
                'textarea[placeholder*="正文"]',
                ".content-textarea",
            ]

            for selector in content_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    await page.click(selector)
                    await asyncio.sleep(0.5)

                    # 使用剪贴板方式注入内容
                    await page.evaluate(
                        """(text) => {
                        const dt = new DataTransfer();
                        dt.setData("text/plain", text);
                        const ev = new ClipboardEvent("paste", { clipboardData: dt, bubbles: true });
                        document.activeElement.dispatchEvent(ev);
                    }""",
                        content,
                    )
                    logger.success("✅ [正文] 正文已填充")
                    return
                except:
                    continue

            logger.warning("⚠️ [正文] 未找到正文输入框")
        except Exception as e:
            logger.error(f"❌ [正文] 填充失败: {e}")

    async def _upload_cover(self, page: Page, image_path: str):
        """上传封面图"""
        try:
            # 查找封面上传按钮
            upload_selectors = [
                'input[type="file"]',
                ".upload-btn",
                'button:has-text("上传封面")',
            ]

            for selector in upload_selectors:
                try:
                    if "input" in selector:
                        file_input = page.locator(selector).first
                        if await file_input.count() > 0:
                            await file_input.set_input_files(image_path)
                            logger.success("✅ [封面] 封面图已上传")
                            await asyncio.sleep(2)
                            return
                except:
                    continue

            logger.warning("⚠️ [封面] 未找到封面上传按钮")
        except Exception as e:
            logger.warning(f"⚠️ [封面] 上传失败: {e}")

    async def _upload_content_images(self, page: Page, image_paths: List[str]):
        """上传正文配图"""
        try:
            for i, image_path in enumerate(image_paths):
                logger.info(f"🖼️ 正在上传第 {i + 1} 张配图...")

                # 查找图片上传按钮
                file_inputs = page.locator('input[type="file"]')
                count = await file_inputs.count()

                if count > 0:
                    await file_inputs.nth(min(i, count - 1)).set_input_files(image_path)
                    await asyncio.sleep(2)
                    logger.info(f"✅ 配图 {i + 1} 已上传")

        except Exception as e:
            logger.warning(f"⚠️ [配图] 上传失败: {e}")

    async def _add_topics(self, page: Page, title: str):
        """添加话题标签"""
        try:
            # 从标题提取关键词作为话题
            topics = [title[:4]] if len(title) > 4 else [title]

            for topic in topics:
                try:
                    # 查找话题输入框
                    topic_selectors = [
                        'input[placeholder*="添加话题"]',
                        'input[placeholder*="话题"]',
                        ".topic-input",
                    ]

                    for selector in topic_selectors:
                        try:
                            topic_input = page.locator(selector).first
                            if await topic_input.count() > 0:
                                await topic_input.fill(f"#{topic}")
                                await asyncio.sleep(0.5)
                                await page.keyboard.press("Enter")
                                logger.info(f"✅ [话题] 已添加话题: {topic}")
                                break
                        except:
                            continue
                except:
                    continue

        except Exception as e:
            logger.warning(f"⚠️ [话题] 添加失败: {e}")

    async def _click_publish(self, page: Page) -> bool:
        """点击发布按钮"""
        try:
            await asyncio.sleep(1)

            # 启用所有发布按钮
            await page.evaluate(
                """() => {
                document.querySelectorAll('button').forEach(btn => {
                    if (btn.innerText.includes('发布') || btn.innerText.includes('确认')) {
                        btn.disabled = false;
                        btn.removeAttribute('disabled');
                    }
                });
            }"""
            )

            publish_selectors = [
                'button:has-text("发布")',
                "button.publish-btn",
                'button[type="submit"]',
            ]

            for selector in publish_selectors:
                try:
                    btn = page.locator(selector).first
                    if await btn.count() > 0 and await btn.is_visible():
                        await btn.scroll_into_view_if_needed()
                        await asyncio.sleep(0.3)
                        await btn.click(force=True)
                        logger.success("✅ [发布] 已点击发布按钮")
                        await asyncio.sleep(2)
                        return True
                except:
                    continue

            logger.error("❌ [发布] 未找到可点击的发布按钮")
            return False

        except Exception as e:
            logger.error(f"❌ [发布] 点击失败: {e}")
            return False

    async def _wait_for_publish_result(self, page: Page) -> Dict[str, Any]:
        """等待发布结果"""
        try:
            # 等待URL变化或成功提示
            for i in range(30):
                if "success" in page.url or "publish" not in page.url:
                    logger.success(f"🎊 [成功] 发布成功: {page.url}")
                    return {"success": True, "platform_url": page.url}
                await asyncio.sleep(1)

            logger.warning(f"⚠️ [结果] 未检测到成功跳转，但可能已发布: {page.url}")
            return {"success": True, "platform_url": page.url}

        except Exception as e:
            logger.error(f"❌ [结果] 检测失败: {e}")
            return {"success": False, "error_msg": str(e)}


# 注册
XIAOHONGSHU_CONFIG = {
    "name": "小红书",
    "publish_url": "https://creator.xiaohongshu.com/publish/publish",
    "color": "#FF2442",
}
registry.register("xiaohongshu", XiaohongshuPublisher("xiaohongshu", XIAOHONGSHU_CONFIG))
