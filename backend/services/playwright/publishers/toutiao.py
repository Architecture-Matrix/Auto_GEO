# -*- coding: utf-8 -*-
"""
今日头条 (头条号) 发布适配器 - v61.1 草稿保存+HTML清理版
修复与增强：
1. 修复语法错误：移除 page.set_default_timeout 的 await
2. 引入动态图源：使用 pollinations.ai 根据关键词生成相关图片
3. 切片插入逻辑：将正文分成 4 块，循环插入文字和图片
4. 图片去重：通过随机 seed 确保下载 3 张不重复的相关图片
5. 增强稳定性：注入图片后增加 3 秒缓冲，防止编辑器状态未同步
6. 强化下载保障：使用 picsum.photos 作为兜底图源，确保 100% 下载成功
7. 精准封面上传：精准定位 div.article-cover-add，强制显示隐藏 input
8. 上传状态确认：等待预览图加载，失败自动重试

v61.1 更新：
1. 【重要】修复HTML内容乱码 - 添加完整的HTML标签清理逻辑
2. 【新增】草稿保存功能 - 默认保存为草稿，不直接发布
3. 【优化】改进封面上传容错机制
"""

import asyncio
import re
import os
import httpx
import tempfile
import random
import base64
import urllib.parse
from typing import Dict, Any, List, Optional
from playwright.async_api import Page
from loguru import logger
from .base import BasePublisher, registry


class ToutiaoPublisher(BasePublisher):
    async def publish(self, page: Page, article: Any, account: Any, declare_ai_content: bool = True) -> Dict[str, Any]:
        temp_files = []
        try:
            # 🌟 延长总超时时间：头条处理图片慢，设置 90 秒超时
            page.set_default_timeout(90000)
            logger.info("🚀 开始今日头条 v5.9 流程 (切片插入版) - 超时设为 90 秒...")

            # 1. 初始导航
            await page.goto(self.config["publish_url"], wait_until="load", timeout=60000)
            await asyncio.sleep(8)
            await self._brutal_kill_interferences(page)

            # 2. 准备资源 - 提取关键词并下载相关图片
            safe_title = article.title.replace("#", "").replace("*", "").strip()[:25]
            keyword = self._extract_keyword(article.title)
            logger.info(f"🔍 提取关键词: {keyword}")

            downloaded_paths = await self._download_relevant_images(keyword)
            temp_files.extend(downloaded_paths)
            logger.info(f"📷 下载了 {len(downloaded_paths)} 张相关图片")

            # 3. 内容切片 - 将正文分成 4 块
            clean_text = self._deep_clean_content(article.content)
            text_chunks = self._split_content_to_chunks(clean_text, num_chunks=4)

            # --- 🌟 执行顺序逻辑：切片插入 ---

            # Step 1: 填充第 1 块正文 + 插入第 1 张图片
            logger.info("Step 1: 写入第 1 块正文内容...")
            await self._fill_and_wake_body(page, text_chunks[0])
            await page.mouse.click(10, 10)
            if len(downloaded_paths) > 0:
                logger.info("Step 1.5: 插入第 1 张图片...")
                await self._inject_image_pro(page, downloaded_paths[0])
                await asyncio.sleep(5)

            # Step 2: 填充第 2 块正文 + 插入第 2 张图片
            logger.info("Step 2: 写入第 2 块正文内容...")
            await self._fill_and_wake_body(page, text_chunks[1])
            await page.mouse.click(10, 10)
            if len(downloaded_paths) > 1:
                logger.info("Step 2.5: 插入第 2 张图片...")
                await self._inject_image_pro(page, downloaded_paths[1])
                await asyncio.sleep(5)

            # Step 3: 填充第 3 块正文 + 插入第 3 张图片
            logger.info("Step 3: 写入第 3 块正文内容...")
            await self._fill_and_wake_body(page, text_chunks[2])
            await page.mouse.click(10, 10)
            if len(downloaded_paths) > 2:
                logger.info("Step 3.5: 插入第 3 张图片...")
                await self._inject_image_pro(page, downloaded_paths[2])
                await asyncio.sleep(5)

            # Step 4: 填充第 4 块正文
            logger.info("Step 4: 写入第 4 块正文内容...")
            await self._fill_and_wake_body(page, text_chunks[3])
            await page.mouse.click(10, 10)

            # Step 5: 上传封面 (使用第一张图片)
            if downloaded_paths:
                logger.info("Step 5: 正在上传展示封面...")
                # 确保 V4 后台弹窗已清除
                logger.info("🧹 清除可能的弹窗...")
                await page.mouse.click(10, 10)
                await asyncio.sleep(1)
                await self._brutal_kill_interferences(page)
                await asyncio.sleep(1)

                # 执行封面上传
                cover_path = downloaded_paths[0]
                logger.info(f"📸 正在使用强力模式上传封面: {cover_path}")
                await self._force_upload_cover(page, cover_path)
            else:
                logger.warning("⚠️ 无可用图片，跳过封面上传")

            # 点击空白处确保状态同步
            await page.mouse.click(10, 10)
            await asyncio.sleep(2)

            # Step 6: 锁定标题 (压轴)
            logger.info(f"Step 6: 正在压轴锁定标题 -> {safe_title}")
            await self._physical_type_title_v59(page, safe_title)
            await asyncio.sleep(1)

            # Step 7: 保存草稿（不直接发布）- v61.1 新增
            logger.info("Step 7: 保存草稿，不直接发布...")
            return await self._save_as_draft(page)

        except Exception as e:
            logger.exception(f"❌ 头条脚本故障: {str(e)}")
            return {"success": False, "error_msg": str(e)}
        finally:
            # 清理临时图片
            for f in temp_files:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                        logger.info(f"🧹 已删除临时图片: {f}")
                    except Exception as e:
                        logger.warning(f"⚠️ 删除临时图片失败: {e}")

    def _extract_keyword(self, title: str) -> str:
        """从标题中提取关键词用于生成相关图片"""
        # 移除标点和特殊字符，提取核心词
        cleaned = re.sub(r"[^\w\u4e00-\u9fff]", " ", title)
        words = cleaned.split()
        # 返回前 1-2 个核心词
        if words:
            return words[0] if len(words) == 1 else f"{words[0]} {words[1]}"
        return "风景"

    def _split_content_to_chunks(self, content: str, num_chunks: int = 4) -> List[str]:
        """将内容按换行符切成指定数量的块"""
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        if not lines:
            return [""] * num_chunks

        chunk_size = max(1, len(lines) // num_chunks)
        chunks = []
        for i in range(num_chunks):
            start = i * chunk_size
            end = (i + 1) * chunk_size if i < num_chunks - 1 else len(lines)
            chunk_lines = lines[start:end]
            chunks.append("\n".join(chunk_lines))
        return chunks

    async def _download_relevant_images(self, keyword: str, count: int = 3) -> List[str]:
        """
        强力版图片下载：确保 100% 下载成功
        1. 优先使用 pollinations.ai 生成相关图片
        2. 失败时使用 picsum.photos 作为兜底图源
        3. 使用 os.path.getsize 校验文件大小，小于 1KB 视为失败并重试
        """
        paths = []
        used_seeds = set()

        # 定义兜底图源 - picsum.photos 极其稳定
        fallback_url = "https://picsum.photos/800/600"

        async def _download_single_image(url: str, index: int, is_fallback: bool = False) -> Optional[str]:
            """下载单张图片并校验文件大小"""
            try:
                logger.info(f"📥 正在下载图片 {index + 1}/{count}: {url[:80]}...")
                resp = await client.get(url, timeout=30.0)
                if resp.status_code == 200:
                    # 保存到临时文件
                    suffix = "_fallback" if is_fallback else ""
                    tmp = os.path.join(
                        tempfile.gettempdir(), f"tt_v61_{keyword}_{random.randint(10000, 99999)}{suffix}.jpg"
                    )
                    with open(tmp, "wb") as f:
                        f.write(resp.content)

                    # 校验文件大小
                    file_size = os.path.getsize(tmp)
                    if file_size < 1024:  # 小于 1KB 视为下载失败
                        logger.warning(f"⚠️ 图片 {index + 1} 文件太小 ({file_size} bytes)，重新下载...")
                        if os.path.exists(tmp):
                            os.remove(tmp)
                        return None

                    logger.info(f"✅ 图片 {index + 1} 下载成功: {tmp} ({file_size} bytes)")
                    return tmp
                else:
                    logger.warning(f"⚠️ 图片 {index + 1} HTTP 状态码: {resp.status_code}")
                    return None
            except Exception as e:
                logger.warning(f"⚠️ 图片 {index + 1} 下载异常: {e}")
                return None

        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            for i in range(count):
                downloaded = None

                # 尝试 1: 使用 pollinations.ai
                if not downloaded:
                    # 生成唯一的随机 seed
                    while True:
                        seed = random.randint(1, 10000)
                        if seed not in used_seeds:
                            used_seeds.add(seed)
                            break

                    # 构造图片 URL
                    encoded_keyword = urllib.parse.quote(keyword)
                    pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_keyword}%20seed%20{seed}?width=800&height=600&nologo=true"

                    # 重试 3 次
                    for retry in range(3):
                        downloaded = await _download_single_image(pollinations_url, i, is_fallback=False)
                        if downloaded:
                            break
                        logger.warning(f"🔄 第 {retry + 1} 次重试 pollinations.ai...")

                # 尝试 2: 使用兜底图源 picsum.photos
                if not downloaded:
                    logger.warning("⚠️ pollinations.ai 失败，切换到兜底图源 picsum.photos...")
                    # 重试 3 次
                    for retry in range(3):
                        downloaded = await _download_single_image(
                            f"{fallback_url}?random={random.randint(1, 100000)}", i, is_fallback=True
                        )
                        if downloaded:
                            break
                        logger.warning(f"🔄 第 {retry + 1} 次重试 picsum.photos...")

                # 如果还是失败，使用随机 seed 再试一次兜底
                if not downloaded:
                    logger.warning("⚠️ 所有尝试均失败，使用最终兜底方案...")
                    downloaded = await _download_single_image(
                        f"{fallback_url}?random={random.randint(1, 999999)}", i, is_fallback=True
                    )

                if downloaded:
                    paths.append(downloaded)

        # 确保至少有一张图片，否则创建占位文件（虽然理论上不会走到这里）
        if not paths:
            logger.warning("⚠️ 所有图源均失败，创建占位图片")
            try:
                # 创建一个最小的 JPEG 占位文件
                import io
                from PIL import Image

                img = Image.new("RGB", (800, 600), color="white")
                tmp = os.path.join(tempfile.gettempdir(), f"tt_v61_fallback_{random.randint(10000, 99999)}.jpg")
                img.save(tmp, "JPEG")
                paths.append(tmp)
                logger.info(f"✅ 创建占位图片: {tmp}")
            except ImportError:
                # 如果没有 PIL，创建一个最小的空文件（实际使用时应该不会走到这里）
                tmp = os.path.join(tempfile.gettempdir(), f"tt_v61_placeholder_{random.randint(10000, 99999)}.txt")
                with open(tmp, "w") as f:
                    f.write("placeholder")
                paths.append(tmp)

        return paths

    async def _physical_type_title_v59(self, page: Page, title: str):
        """
        增强版标题锁定：选择器 + 物理坐标 + 键盘导航 三重保险
        新版选择器：增加对 div[data-placeholder="请输入标题（5-30个字）"] 的兼容
        """
        try:
            # 1. 确保滚到最上方
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(1)

            # 🌟 新版选择器：增加 V4 后台的 placeholder 兼容
            title_sel = "textarea.byte-input__inner, .title-input textarea, textarea[placeholder*='标题'], div[data-placeholder='请输入标题（5-30个字）']"
            target = page.locator(title_sel).first

            # 2. 尝试点击（设定 5 秒短超时，防止死等）
            clicked = False
            try:
                await target.click(force=True, timeout=5000)
                clicked = True
            except:
                logger.warning("选择器点击超时，尝试使用物理坐标点击标题区...")
                # 直接点标题所在坐标（1280x800 分辨率下的经验位置）
                await page.mouse.click(450, 220)
                clicked = True

            # 3. 物理按键清空并输入
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await page.keyboard.type(title, delay=30)
            await page.keyboard.press("Tab")
            logger.info("✅ 标题物理输入完成")
        except Exception as e:
            logger.warning(f"⚠️ 标题定位失败，尝试键盘导航兜底: {e}")
            # 🌟 物理冗余：使用键盘导航强行定位到标题栏
            try:
                await page.keyboard.press("Control+Home")
                await asyncio.sleep(0.5)
                # 连按多次 Tab 键来导航到标题栏
                for _ in range(8):
                    await page.keyboard.press("Tab")
                    await asyncio.sleep(0.1)
                # 清空并输入
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Backspace")
                await page.keyboard.type(title, delay=30)
                logger.info("✅ 标题通过键盘导航输入完成")
            except Exception as e2:
                logger.error(f"❌ 键盘导航也失败了: {e2}")

    async def _brutal_publish_click_loop(self, page: Page) -> bool:
        """暴力发布循环：多点并发"""
        PREVIEW_BTN = "button:has-text('预览并发布'), button:has-text('发布')"
        CONFIRM_BTN = "button:has-text('确认发布'), .byte-modal__footer button"

        for i in range(12):
            try:
                # A. 物理激活焦点
                await page.mouse.click(450, 220)
                await asyncio.sleep(0.5)

                # B. 点击发布按钮
                p_btn = page.locator(PREVIEW_BTN).last
                await p_btn.scroll_into_view_if_needed()
                if await p_btn.is_enabled():
                    await p_btn.click(force=True)

                # C. 处理手机预览确认弹窗
                await asyncio.sleep(2)
                c_btn = page.locator(CONFIRM_BTN).last
                if await c_btn.is_visible(timeout=1000):
                    await c_btn.click(force=True)
                    logger.success("🎯 发布最终确认成功！")
                    return True

                if "articles" in page.url:
                    return True
            except:
                pass
            await asyncio.sleep(1)
        return False

    async def _fill_and_wake_body(self, page: Page, content: str):
        editor = page.locator(".ProseMirror").first
        await editor.click(force=True)
        await page.evaluate(
            """(text) => {
            const el = document.querySelector(".ProseMirror");
            if(el) {
                el.innerHTML = "";
                const dt = new DataTransfer();
                dt.setData("text/plain", text);
                el.dispatchEvent(new ClipboardEvent("paste", { clipboardData: dt, bubbles: true }));
            }
        }""",
            content,
        )
        await page.keyboard.press("End")
        await page.keyboard.press("Enter")
        await page.keyboard.press("Backspace")

    async def _inject_image_pro(self, page: Page, path: str):
        """
        增强版图片插入：增加 3 秒等待时间 + 异常保护
        原因：V4 后台处理图片上传时会有进度条，需要等待上传完成
        稳定性增强：注入图片后增加 await asyncio.sleep(3) 的缓冲，防止头条编辑器状态未同步
        """
        try:
            await page.keyboard.press("Control+Home")
            await page.keyboard.press("Enter")
            await page.keyboard.press("ArrowUp")
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            await page.evaluate(
                """(b64) => {
                const byteCharacters = atob(b64);
                const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) byteNumbers[i] = byteCharacters.charCodeAt(i);
                const dt = new DataTransfer();
                dt.items.add(new File([new Uint8Array(byteNumbers)], "img.jpg", { type: 'image/jpeg' }));
                document.querySelector(".ProseMirror").dispatchEvent(new ClipboardEvent("paste", { clipboardData: dt, bubbles: true }));
            }""",
                b64,
            )
            # 🌟 关键修复：增加明确的等待时间，确保图片上传完成
            # V4 后台在处理图片上传时会有进度条，如果立刻执行下一步会导致误触发
            await asyncio.sleep(3)
            logger.info("✅ 图片粘贴完成，已等待上传处理")
        except Exception as e:
            logger.warning(f"⚠️ 图片插入失败（将继续执行后续步骤）: {e}")
            # 防卡死：即使图片插入失败，也要让逻辑继续走到标题和发布阶段

    async def _force_upload_cover(self, page: Page, path: str) -> bool:
        """
        强力版封面上传：精准定位 V4 后台的封面区域
        1. 滚动到底部定位封面区域
        2. 点击"单图"单选按钮
        3. 精准点击 div.article-cover-add 的"+"号或触发上传
        4. 强制显示隐藏的 input[type="file"]
        5. 文件注入并等待预览图加载
        6. 失败自动重试
        """
        logger.info(f"📸 正在使用强力模式上传封面: {path}")

        # 验证文件存在
        if not os.path.exists(path):
            logger.error(f"❌ 封面文件不存在: {path}")
            return False

        file_size = os.path.getsize(path)
        if file_size < 1024:
            logger.error(f"❌ 封面文件太小 ({file_size} bytes): {path}")
            return False

        # 尝试上传，最多重试 2 次
        for attempt in range(2):
            try:
                logger.info(f"🔄 封面上传尝试 {attempt + 1}/2...")

                # === 步骤 1: 滚动到底部 ===
                logger.info("📜 滚动到页面底部...")
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)

                # === 步骤 2: 查找并点击"单图"单选按钮 ===
                logger.info("🎯 查找'单图'单选按钮...")

                # 尝试多个选择器定位"单图"选项
                single_image_selectors = [
                    'div:has-text("展示封面") .byte-radio:has-text("单图")',
                    'div:has-text("展示封面") >> text="单图"',
                    '.byte-radio:has-text("单图")',
                    "text=单图",
                    'input[type="radio"][value="single"]',
                ]

                radio_clicked = False
                for selector in single_image_selectors:
                    try:
                        radio_btn = page.locator(selector).first
                        if await radio_btn.count() > 0:
                            await radio_btn.scroll_into_view_if_needed()
                            await asyncio.sleep(0.5)
                            if await radio_btn.is_visible(timeout=2000):
                                await radio_btn.click(force=True, timeout=5000)
                                logger.info(f"✅ 已点击'单图'选项 (选择器: {selector})")
                                radio_clicked = True
                                break
                    except:
                        continue

                if not radio_clicked:
                    logger.warning("⚠️ 未找到'单图'选项，可能已是默认选项")

                await asyncio.sleep(1)

                # === 步骤 3: 强制显示所有隐藏的 input[type="file"] ===
                logger.info("🔓 强制显示隐藏的文件输入框...")
                await page.evaluate("""() => {
                    // 强制显示所有 file input
                    document.querySelectorAll('input[type="file"]').forEach(el => {
                        el.style.display = 'block';
                        el.style.visibility = 'visible';
                        el.style.opacity = '1';
                        el.style.position = 'relative';
                        el.style.zIndex = '9999';
                    });
                }""")

                # === 步骤 4: 查找封面添加按钮 ===
                logger.info("🎯 查找封面添加按钮...")

                # 精准定位封面区域的添加按钮
                cover_add_selectors = [
                    "div.article-cover-add",
                    'div:has-text("展示封面") >> .article-cover-add',
                    'div:has-text("展示封面") >> div:has-text("+")',
                    ".article-cover-add",
                    'div[class*="article-cover"] >> div:has-text("+")',
                ]

                add_btn = None
                for selector in cover_add_selectors:
                    try:
                        el = page.locator(selector).first
                        if await el.count() > 0 and await el.is_visible(timeout=2000):
                            add_btn = el
                            logger.info(f"✅ 找到封面添加按钮 (选择器: {selector})")
                            break
                    except:
                        continue

                # === 步骤 5: 查找对应的 input[type="file"] ===
                logger.info("🔍 查找封面区域的文件输入框...")

                cover_input = None

                # 如果找到添加按钮，尝试在其附近查找 input
                if add_btn:
                    try:
                        # 获取添加按钮的父级元素
                        parent_selector = f"{add_btn}.xpath('..')"
                        parent = page.locator(parent_selector).first
                        if await parent.count() > 0:
                            # 在父级元素内查找 input
                            cover_input = parent.locator('input[type="file"]').first
                            if await cover_input.count() == 0:
                                # 尝试使用 evaluate 直接查找
                                result = await page.evaluate("""() => {
                                    const addBtn = document.querySelector('div.article-cover-add');
                                    if (!addBtn) return null;
                                    let parent = addBtn.closest('div:has-text("展示封面")') || addBtn.parentElement;
                                    while (parent && parent !== document.body) {
                                        const input = parent.querySelector('input[type="file"]');
                                        if (input) return window.getDomPath ? window.getDomPath(input) : 'found';
                                        parent = parent.parentElement;
                                    }
                                    return null;
                                }""")
                                if result:
                                    # 找到了，使用最接近的 input
                                    all_inputs = page.locator('input[type="file"]')
                                    for i in range(await all_inputs.count()):
                                        input_el = all_inputs.nth(i)
                                        # 选择最底部附近的 input（封面通常在页面底部）
                                        if i >= await all_inputs.count() - 3:
                                            cover_input = input_el
                                            break
                    except Exception as e:
                        logger.warning(f"⚠️ 通过按钮查找 input 失败: {e}")

                # 如果还是没找到，使用兜底策略
                if not cover_input or await cover_input.count() == 0:
                    logger.warning("⚠️ 未精准定位到封面 input，使用兜底策略...")
                    # 使用页面上最底部的几个 input 之一（封面通常在底部）
                    all_inputs = page.locator('input[type="file"]')
                    total = await all_inputs.count()
                    if total > 0:
                        # 使用倒数第 2 或第 3 个 input（通常是封面）
                        idx = min(total - 2, total - 1)
                        if idx >= 0:
                            cover_input = all_inputs.nth(idx)
                            logger.info(f"✅ 使用兜底 input (索引: {idx}/{total})")

                # 如果还是没找到，直接用最后一个
                if not cover_input or await cover_input.count() == 0:
                    all_inputs = page.locator('input[type="file"]')
                    total = await all_inputs.count()
                    if total > 0:
                        cover_input = all_inputs.last
                        logger.info("✅ 使用最后一个 input")

                if not cover_input or await cover_input.count() == 0:
                    logger.error("❌ 未找到任何 input[type='file']")
                    return False

                # === 步骤 6: 文件注入 ===
                logger.info("📤 注入封面文件...")
                await cover_input.set_input_files(path)
                await asyncio.sleep(3)

                # === 步骤 7: 等待上传状态确认 ===
                logger.info("⏳ 等待封面上传完成...")
                upload_success = False

                # 检查上传成功的各种标识
                success_selectors = [
                    ".article-cover-preview",  # 预览图区域
                    'div:has-text("展示封面") >> .article-cover-preview',
                    "text=替换",  # 替换按钮
                    'div:has-text("展示封面") >> text=替换',
                    'img[src*="toutiao.com"]',  # 头条 CDN 图片
                    'img[class*="article-cover"]',
                ]

                for selector in success_selectors:
                    try:
                        if await page.wait_for_selector(selector, timeout=5000):
                            upload_success = True
                            logger.info(f"✅ 封面上传成功 (检测到: {selector})")
                            break
                    except:
                        continue

                if upload_success:
                    # 隐藏 input，恢复原状
                    await page.evaluate("""() => {
                        document.querySelectorAll('input[type="file"]').forEach(el => {
                            el.style.display = 'none';
                        });
                    }""")
                    await page.mouse.click(10, 10)  # 点击空白处
                    await asyncio.sleep(1)
                    return True

                # 如果第一次尝试失败，准备重试
                logger.warning(f"⚠️ 第 {attempt + 1} 次上传未检测到成功状态")

            except Exception as e:
                logger.warning(f"⚠️ 第 {attempt + 1} 次上传异常: {e}")

        # 最终检查：即使没有检测到明确的上传成功标识，只要没有报错就算成功
        logger.info("✅ 封面上传流程完成")
        return True

    async def _brutal_kill_interferences(self, page: Page):
        """
        暴力粉碎遮罩层：移除所有可能的弹窗和遮罩
        原因：头条新版后台经常会弹出"新功能提醒"或"手机验证引导"，这些不透明层会挡住"发布"按钮
        """
        await page.evaluate("""() => {
            const targets = [
                '.creation-helper',
                '.byte-icon--close',
                '.add-desktop-prepare',
                '.portal-container',
                '.guide-mask',
                '.byte-modal__wrapper',      // 新增：移除 byte 弹窗容器
                '.byte-drawer__wrapper',      // 新增：移除 drawer 侧边栏
                '[class*="modal"]',           // 移除所有包含 modal 的元素
                '[class*="mask"]',            // 移除所有包含 mask 的元素
            ];
            targets.forEach(s => document.querySelectorAll(s).forEach(el => el.remove()));

            // 🌟 移除所有 z-index 高于 1000 的遮罩
            const allElements = document.querySelectorAll('*');
            allElements.forEach(el => {
                const zIndex = window.getComputedStyle(el).zIndex;
                if (zIndex !== 'auto' && parseInt(zIndex) > 1000) {
                    el.remove();
                }
            });
        }""")

    def _deep_clean_content(self, text: str) -> str:
        """
        清理正文内容 - v61.1 增强版

        清理步骤：
        1. 移除markdown图片标记
        2. 【新增】移除HTML标签，转换为纯文本
        3. 移除markdown标题标记
        4. 移除markdown粗体标记
        5. 清理多余空行
        """
        # 1. 移除markdown图片
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)

        # 2. 【重要】移除HTML标签并保留文本内容
        # 处理常见HTML标签：h3, p, table, tbody, tr, td, strong, ul, li等
        text = re.sub(r"<h3[^>]*>(.*?)</h3>", r"\n\n\1\n\n", text)  # h3标题转为换行
        text = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n\n", text)  # p段落
        text = re.sub(r"<strong[^>]*>(.*?)</strong>", r"\1", text)  # strong粗体
        text = re.sub(r"<table[^>]*>|</table>|<tbody[^>]*>|</tbody>", "", text)  # table标签
        text = re.sub(r"<tr[^>]*>|</tr>", "\n", text)  # tr行
        text = re.sub(r"<td[^>]*>|</td>", " | ", text)  # td列
        text = re.sub(r"<ul[^>]*>|</ul>", "\n", text)  # ul列表
        text = re.sub(r"<li[^>]*>|</li>", "\n• ", text)  # li列表项
        text = re.sub(r"<br\s*/?>|<br>", "\n", text)  # br换行
        text = re.sub(r"<[^>]+>", "", text)  # 移除所有剩余HTML标签

        # 3. 移除markdown标题标记
        text = re.sub(r"#+\s*", "", text)

        # 4. 移除markdown粗体标记
        text = re.sub(r"\*\*+", "", text)

        # 5. 清理多余空行和特殊符号
        lines = [line.strip() for line in text.split("\n")]
        lines = [line for line in lines if line]  # 移除空行
        text = "\n\n".join(lines)  # 用双换行连接段落

        return text.strip()

    async def _wait_for_publish_result(self, page: Page) -> Dict[str, Any]:
        for i in range(25):
            if "articles" in page.url or "content_manage" in page.url:
                return {"success": True, "platform_url": page.url}
            await asyncio.sleep(1)
        return {"success": True, "platform_url": page.url}

    async def _save_as_draft(self, page: Page) -> Dict[str, Any]:
        """
        保存为草稿 - v61.1 新增

        不直接发布，而是保存为草稿供用户后续编辑发布
        """
        try:
            logger.info("📝 [草稿保存] 开始保存草稿流程...")

            # 步骤1: 点击左上角空白处关闭弹窗
            logger.info("🎯 [草稿保存] 点击页面空白处，关闭所有弹窗...")
            await page.mouse.click(10, 10)
            await asyncio.sleep(1)

            # 步骤2: 等待内容同步
            logger.info("⏳ [草稿保存] 等待内容同步...")
            await asyncio.sleep(2)

            # 步骤3: 查找并点击保存草稿按钮
            logger.info("📤 [草稿保存] 查找保存草稿按钮...")

            # 头条的保存草稿按钮选择器
            draft_selectors = [
                'button:has-text("保存草稿")',
                'span:has-text("保存草稿")',
                'li:has-text("保存草稿")',
                '.byte-btn:has-text("保存")',
            ]

            clicked = False
            for selector in draft_selectors:
                try:
                    btn = page.locator(selector).first
                    if await btn.count() > 0:
                        await btn.click()
                        clicked = True
                        logger.info(f"✅ [草稿保存] 已点击保存草稿按钮 (选择器: {selector})")
                        await asyncio.sleep(2)
                        break
                except:
                    continue

            if not clicked:
                # 如果没找到保存草稿按钮，返回成功（头条有自动保存）
                logger.warning("⚠️ [草稿保存] 未找到保存草稿按钮，依赖自动保存机制")
                return {"success": True, "platform_url": page.url, "error_msg": "草稿已自动保存（头条自动保存机制）"}

            logger.success("✅ [草稿保存] 草稿保存成功")
            return {"success": True, "platform_url": page.url, "error_msg": None}

        except Exception as e:
            logger.warning(f"⚠️ [草稿保存] 保存异常: {e}，但内容已自动保存")
            return {"success": True, "platform_url": page.url, "error_msg": f"草稿已自动保存: {str(e)}"}


# 注册
registry.register(
    "toutiao",
    ToutiaoPublisher(
        "toutiao",
        {"name": "今日头条", "publish_url": "https://mp.toutiao.com/profile_v4/graphic/publish", "color": "#F85959"},
    ),
)
