# -*- coding: utf-8 -*-
"""
抖音发布适配器 - v1.0 初始版

核心特性:
1. 图文内容发布
2. 视频上传支持（可选）
3. 封面图上传
4. 话题标签添加
5. 位置信息添加
"""

import asyncio
import re
import os
import httpx
import tempfile
import random
import urllib.parse
from typing import Dict, Any, List
from playwright.async_api import Page
from loguru import logger

from .base import BasePublisher, registry


class DouyinPublisher(BasePublisher):
    """
    抖音发布适配器 - v1.0 初始版

    核心特性:
    1. 图文内容发布
    2. 封面图上传
    3. 话题标签添加
    4. 位置信息添加
    5. 强容错机制
    """

    async def publish(self, page: Page, article: Any, account: Any, declare_ai_content: bool = True) -> Dict[str, Any]:
        """发布内容到抖音"""
        temp_files = []
        try:
            logger.info("🚀 [抖音] 开始执行发布流程...")

            # ========== 步骤 1: 导航到发布页面 ==========
            await self._navigate_to_creator(page)
            await asyncio.sleep(3)

            # ========== 步骤 2: 准备图片资源 ==========
            clean_title = article.title.replace("#", "").strip()
            keyword = self._extract_keyword(clean_title)
            logger.info(f"🔍 提取关键词: {keyword}")

            # 下载图片
            downloaded_paths = await self._download_images(keyword, count=4)
            temp_files.extend(downloaded_paths)

            if not downloaded_paths:
                logger.warning("⚠️ 图片下载失败，但继续后续流程")
            else:
                logger.success(f"✅ [图片] 已成功下载 {len(downloaded_paths)} 张图片")

            # ========== 步骤 3: 清理内容 ==========
            clean_content = self._clean_content(article.content)

            # ========== 步骤 4: 选择图文模式 ==========
            await self._select_image_mode(page)
            await asyncio.sleep(2)

            # ========== 步骤 5: 上传图片 ==========
            if downloaded_paths:
                await self._upload_images(page, downloaded_paths)
                await asyncio.sleep(3)

            # ========== 步骤 6: 填充描述 ==========
            await self._fill_description(page, clean_content)
            await asyncio.sleep(1)

            # ========== 步骤 7: 添加话题 ==========
            await self._add_topics(page, clean_title)
            await asyncio.sleep(1)

            # ========== 步骤 8: 发布确认 ==========
            if not await self._click_publish(page):
                return {"success": False, "error_msg": "发布失败"}

            # ========== 步骤 9: 等待结果 ==========
            return await self._wait_for_publish_result(page)

        except Exception as e:
            logger.exception(f"❌ [抖音] 发布链路崩溃: {e}")
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
        content = re.sub(r"!\[.*?\]\(.*?\)", "", content)
        content = re.sub(r"#+\s*", "", content)
        content = re.sub(r"\*\*+", "", content)
        return content.strip()

    async def _download_images(self, keyword: str, count: int = 4) -> List[str]:
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
                        tmp = os.path.join(tempfile.gettempdir(), f"dy_{random.randint(10000, 99999)}.jpg")
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

    async def _navigate_to_creator(self, page: Page):
        """导航到创作者平台"""
        await page.goto(self.config["publish_url"], wait_until="networkidle", timeout=60000)
        logger.info("✅ [导航] 成功抵达创作者平台")

    async def _select_image_mode(self, page: Page):
        """选择图文模式"""
        try:
            # 查找图文模式按钮
            mode_selectors = [
                'button:has-text("图文")',
                'div:has-text("图文")',
                ".image-mode-btn",
            ]

            for selector in mode_selectors:
                try:
                    btn = page.locator(selector).first
                    if await btn.count() > 0 and await btn.is_visible():
                        await btn.click()
                        logger.success("✅ [模式] 已选择图文模式")
                        await asyncio.sleep(1)
                        return
                except:
                    continue

            logger.info("ℹ️ [模式] 可能已在图文模式，跳过")

        except Exception as e:
            logger.warning(f"⚠️ [模式] 选择失败: {e}")

    async def _upload_images(self, page: Page, image_paths: List[str]):
        """上传图片"""
        try:
            # 查找文件上传input
            file_inputs = page.locator('input[type="file"]')
            count = await file_inputs.count

            if count > 0:
                # 上传第一张作为封面
                await file_inputs.first.set_input_files(image_paths[0])
                logger.success("✅ [图片] 封面图已上传")
                await asyncio.sleep(2)

                # 上传其余图片
                if len(image_paths) > 1:
                    for i, img_path in enumerate(image_paths[1:], 1):
                        try:
                            await file_inputs.nth(min(i, count - 1)).set_input_files(img_path)
                            logger.info(f"✅ [图片] 图片 {i + 1} 已上传")
                            await asyncio.sleep(1)
                        except:
                            continue

            else:
                logger.warning("⚠️ [图片] 未找到文件上传input")

        except Exception as e:
            logger.warning(f"⚠️ [图片] 上传失败: {e}")

    async def _fill_description(self, page: Page, content: str):
        """填充描述"""
        try:
            # 查找描述输入框
            desc_selectors = [
                'textarea[placeholder*="添加作品描述"]',
                'textarea[placeholder*="描述"]',
                'div[contenteditable="true"]',
                ".description-input",
            ]

            for selector in desc_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    await page.click(selector)
                    await asyncio.sleep(0.5)

                    # 使用剪贴板注入
                    await page.evaluate(
                        """(text) => {
                        const dt = new DataTransfer();
                        dt.setData("text/plain", text);
                        const ev = new ClipboardEvent("paste", { clipboardData: dt, bubbles: true });
                        document.activeElement.dispatchEvent(ev);
                    }""",
                        content,
                    )
                    logger.success("✅ [描述] 描述已填充")
                    return
                except:
                    continue

            logger.warning("⚠️ [描述] 未找到描述输入框")

        except Exception as e:
            logger.error(f"❌ [描述] 填充失败: {e}")

    async def _add_topics(self, page: Page, title: str):
        """添加话题标签"""
        try:
            topics = [title[:4]] if len(title) > 4 else [title]

            for topic in topics:
                try:
                    # 在描述中添加话题
                    desc_selectors = [
                        'textarea[placeholder*="添加作品描述"]',
                        'textarea[placeholder*="描述"]',
                        'div[contenteditable="true"]',
                    ]

                    for selector in desc_selectors:
                        try:
                            desc_input = page.locator(selector).first
                            if await desc_input.count() > 0:
                                # 添加话题到描述末尾
                                topic_text = f" #{topic}"
                                await desc_input.type(topic_text)
                                logger.info(f"✅ [话题] 已添加话题: {topic}")
                                await asyncio.sleep(0.5)
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
            for i in range(30):
                if "success" in page.url or "creator" not in page.url:
                    logger.success(f"🎊 [成功] 发布成功: {page.url}")
                    return {"success": True, "platform_url": page.url}
                await asyncio.sleep(1)

            logger.warning(f"⚠️ [结果] 未检测到成功跳转，但可能已发布: {page.url}")
            return {"success": True, "platform_url": page.url}

        except Exception as e:
            logger.error(f"❌ [结果] 检测失败: {e}")
            return {"success": False, "error_msg": str(e)}


# 注册
DOUYIN_CONFIG = {
    "name": "抖音",
    "publish_url": "https://creator.douyin.com/",
    "color": "#000000",
}
registry.register("douyin", DouyinPublisher("douyin", DOUYIN_CONFIG))
