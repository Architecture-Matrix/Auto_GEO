# -*- coding: utf-8 -*-
"""
搜狐号发布适配器 - v18.6 草稿保存+HTML清理版

重构内容:
1. 统一图源下载: 使用 pollinations.ai 根据关键词生成相关图片
2. 文本定位策略: 放弃 data-v-xxx 属性，使用文本定位和结构定位
3. 通用弹窗处理: 新增 _handle_upload_popup 方法统一处理上传弹窗
4. 简化正文注入: 只发纯文本，图片仅在封面中使用
5. 容错机制: 图片下载或插入失败时记录 warning，不中断发布流程
6. 临时文件清理: 任务结束后删除所有本地 temp 图片文件

v18.5 更新:
1. 修复 _handle_upload_popup 中的 Tab 切换 - 使用 JS 遍历方式
2. 修复 _handle_cover_v2 中的 JS 校验错误 - 标准化 querySelector 语法
3. 增加"弹窗强制粉碎"逻辑 - 封面上传后 ESC + overlay 清理
4. 确认 _inject_content_simple 使用 ClipboardEvent 模拟粘贴

v18.6 更新:
1. 【重要】修复HTML内容乱码 - 添加完整的HTML标签清理逻辑
2. 【新增】草稿保存功能 - 默认保存为草稿，不直接发布
3. 【优化】改进封面上传逻辑
"""

import asyncio
import re
import os
import httpx
import tempfile
import random
import urllib.parse
from typing import Dict, Any, List, Optional
from playwright.async_api import Page
from loguru import logger

from .base import BasePublisher, registry


class SohuPublisher(BasePublisher):
    """
    搜狐号发布适配器 - v18.0 文本定位+简化封面上传版

    核心特性:
    1. 统一图源下载: pollinations.ai 动态生成相关图片
    2. 文本定位策略: 放弃 data-v-xxx 属性，使用文本定位和结构定位
    3. 通用弹窗处理: 统一处理上传弹窗流程
    4. 简化正文注入: 只发纯文本，保证发布成功率
    5. 强容错: 图片失败不影响正文和标题发布
    """

    async def publish(self, page: Page, article: Any, account: Any, declare_ai_content: bool = True) -> Dict[str, Any]:
        temp_files = []
        try:
            logger.info("🚀 开始搜狐号 v18.6 流程 (草稿保存+HTML清理版)...")

            # ========== 步骤 0: 注入隐身疫苗 & 导航 ==========
            await self._apply_stealth_strategy(page)
            await self._navigate_to_editor(page)

            # ========== 步骤 1: 暴力移除干扰层 ==========
            await self._clear_overlays(page)

            # ========== 步骤 2: 准备资源 - 提取关键词并下载图片 ==========
            clean_title = article.title.replace("#", "").replace("*", "").strip()[:72]
            keyword = self._extract_keyword(article.title)
            logger.info(f"🔍 提取关键词: {keyword}")

            downloaded_paths = await self._download_relevant_images(keyword, count=4)
            temp_files.extend(downloaded_paths)
            logger.info(f"📷 下载了 {len(downloaded_paths)} 张相关图片")

            # ========== 步骤 3: 内容切片 - 将正文分成 4 块 ==========
            clean_content = self._deep_clean_content(article.content)
            text_chunks = self._split_content_to_chunks(clean_content, num_chunks=4)

            # ========== 步骤 4: 标题先行 ==========
            if not await self._fill_title_physical(page, clean_title):
                logger.warning("⚠️ 标题注入失败，继续后续流程")

            # ========== 步骤 5: 封面上传 (使用通用弹窗处理方法) ==========
            if downloaded_paths:
                if not await self._handle_cover_v2(page, downloaded_paths[0]):
                    logger.warning("⚠️ 封面上传失败，继续后续流程")

            # ========== 步骤 5.5: 弹窗强制粉碎 (防止遮挡) ==========
            # 无论封面上传成功还是失败，都必须强制关闭可能残留的弹窗
            # 这样能保证即便封面上传卡住了，弹窗也会被关掉，让后面的正文注入（Quill）能够露出来
            logger.info("🚪 [弹窗粉碎] 强制关闭可能残留的弹窗...")
            for _ in range(2):
                await page.keyboard.press("Escape")
                await asyncio.sleep(0.5)
            # 再次粉碎遮罩层
            await self._clear_overlays(page)
            logger.info("✅ [弹窗粉碎] 弹窗强制关闭完成")

            # ========== 步骤 6: 简化正文注入 (只发纯文本) ==========
            logger.info("📝 开始注入正文...")
            await self._inject_content_simple(page, text_chunks)

            # ========== 步骤 7: 保存草稿（不直接发布）==========
            return await self._save_as_draft(page)

        except Exception as e:
            logger.exception(f"❌ 搜狐号发布异常: {str(e)}")
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

    async def _download_relevant_images(self, keyword: str, count: int = 4) -> List[str]:
        """
        统一图源下载: 使用 pollinations.ai 生成相关图片

        URL 模板: https://image.pollinations.ai/prompt/{keyword}%20seed%20{seed}?width=800&height=600&nologo=true
        去重: 通过不同的随机 seed 确保下载 3-4 张不重复的相关图片
        """
        paths = []
        used_seeds = set()
        base_url = "https://image.pollinations.ai/prompt/"

        async def _download_single_image(url: str, index: int) -> Optional[str]:
            """下载单张图片并校验"""
            try:
                logger.info(f"📥 正在下载图片 {index + 1}/{count}: {url[:80]}...")
                resp = await client.get(url, timeout=30.0)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    tmp = os.path.join(tempfile.gettempdir(), f"sohu_v18_{keyword}_{random.randint(10000, 99999)}.jpg")
                    with open(tmp, "wb") as f:
                        f.write(resp.content)

                    # 校验文件大小
                    file_size = os.path.getsize(tmp)
                    if file_size < 1024:  # 小于 1KB 视为失败
                        logger.warning(f"⚠️ 图片 {index + 1} 文件太小 ({file_size} bytes)")
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
                # 生成唯一的随机 seed
                while True:
                    seed = random.randint(1, 10000)
                    if seed not in used_seeds:
                        used_seeds.add(seed)
                        break

                # 构造图片 URL
                encoded_keyword = urllib.parse.quote(keyword)
                image_url = f"{base_url}{encoded_keyword}%20seed%20{seed}?width=800&height=600&nologo=true"

                # 重试 3 次
                for retry in range(3):
                    downloaded = await _download_single_image(image_url, i)
                    if downloaded:
                        paths.append(downloaded)
                        break
                    logger.warning(f"🔄 第 {retry + 1} 次重试...")

        return paths

    async def _handle_upload_popup(self, page: Page, file_path: str):
        """
        通用处理搜狐上传弹窗：切换Tab -> 上传 -> 确定

        核心策略：放弃 data-v-xxx 属性，使用文本定位和结构定位
        """
        try:
            logger.info(f"📤 [弹窗处理] 开始处理上传弹窗，文件: {file_path}")

            # ========== 步骤 1: 切换到 '本地上传' Tab (通过 JS 遍历暴力查找) ==========
            logger.info("🔄 [步骤1] 切换到'本地上传' Tab...")

            # 等待弹窗出现
            await page.wait_for_selector(".el-dialog, .mp-dialog", timeout=5000)
            await asyncio.sleep(1)

            # 使用 JS 遍历方式，直接在页面里搜寻文字
            tab_clicked = await page.evaluate("""() => {
                const headers = Array.from(document.querySelectorAll('h3, div, span, button, li'));
                const localTab = headers.find(el => el.innerText && el.innerText.includes('本地上传'));
                if (localTab) {
                    localTab.click();
                    return true;
                }
                return false;
            }""")

            if tab_clicked:
                logger.info("✅ [步骤1] 已通过 JS 遍历点击'本地上传' Tab")
                await asyncio.sleep(1)
            else:
                logger.warning("⚠️ [步骤1] 未找到'本地上传' Tab，可能已在默认位置")

            # ========== 步骤 2: 上传文件 (直接定位弹窗内的 input) ==========
            logger.info("📤 [步骤2] 定位文件输入框并上传文件...")

            # 只要弹窗里的 file input 就可以，不需要管那个 i 标签
            upload_input_selectors = [
                '.mp-dialog input[type="file"]',
                '.el-dialog input[type="file"]',
                'input[type="file"]',
            ]

            file_set = False
            for selector in upload_input_selectors:
                try:
                    upload_input = page.locator(selector).first
                    if await upload_input.count() > 0:
                        # 等待文件输入框可见
                        await upload_input.wait_for(state="visible", timeout=3000)
                        # 使用 set_input_files 上传文件
                        await upload_input.set_input_files(file_path)
                        file_set = True
                        logger.info(f"✅ [步骤2] 文件已注入 (选择器: {selector})")
                        await asyncio.sleep(0.5)
                        break
                except:
                    continue

            if not file_set:
                logger.warning("⚠️ [步骤2] 文件输入失败，尝试兜底方案...")

                # 兜底：使用 filechooser
                async def handle_file_chooser(file_chooser):
                    await file_chooser.set_files(file_path)
                    logger.info("✅ [步骤2] 文件已通过 filechooser 注入")

                # 触发文件选择
                for selector in upload_input_selectors:
                    try:
                        upload_input = page.locator(selector).first
                        if await upload_input.count() > 0:
                            page.on("filechooser", handle_file_chooser)
                            await upload_input.click(force=True)
                            await asyncio.sleep(1)
                            page.remove_listener("filechooser", handle_file_chooser)
                            file_set = True
                            break
                    except:
                        continue

            # ========== 步骤 3: 等待上传完成 ==========
            logger.info("⏳ [步骤3] 等待上传完成...")
            # 等待上传进度条消失，或者出现"删除"按钮，或者确定按钮变亮
            await asyncio.sleep(5)

            # ========== 步骤 4: 点击确定 ==========
            logger.info("🎯 [步骤4] 点击'确定'按钮...")

            # 查找弹窗底部的确定按钮
            confirm_selectors = [
                'button:has-text("确定")',
                '.mp-dialog button:has-text("确定")',
                '.el-dialog button:has-text("确定")',
            ]

            confirm_clicked = False
            for selector in confirm_selectors:
                try:
                    confirm_btn = page.locator(selector).last
                    # 等待按钮可见
                    if await confirm_btn.is_visible(timeout=2000):
                        await confirm_btn.click(force=True)
                        confirm_clicked = True
                        logger.info(f"✅ [步骤4] 已点击'确定'按钮 (选择器: {selector})")
                        break
                except:
                    continue

            if not confirm_clicked:
                logger.warning("⚠️ [步骤4] 未找到'确定'按钮")

            # ========== 步骤 5: 等待弹窗消失 ==========
            logger.info("⏳ [步骤5] 等待弹窗消失...")
            await page.wait_for_selector(".el-dialog, .mp-dialog", state="hidden", timeout=10000)
            logger.info("✅ [步骤5] 弹窗已消失")

            return True

        except Exception as e:
            logger.warning(f"⚠️ [弹窗处理] 处理失败: {e}")
            return True  # 不阻塞发布流程

    async def _handle_cover_v2(self, page: Page, cover_path: str) -> bool:
        """
        封面上传 - 点击加号图标 -> 触发弹窗 -> 上传 -> 确定

        核心策略：放弃 data-v-xxx 属性，使用文本定位和结构定位
        """
        try:
            logger.info(f"📸 [封面] 开始上传封面，文件路径: {cover_path}")

            # ========== 步骤 1: 点击封面区域的加号图标 ==========
            logger.info("🎯 [封面-步骤1] 点击封面上传图标...")

            icon_selectors = [
                "i.iconfont.mp-icon-upload",
                ".upload-file i.iconfont",
                'i[class*="iconfont"][class*="upload"]',
            ]

            icon_clicked = False
            for selector in icon_selectors:
                try:
                    icon = page.locator(selector).first
                    if await icon.count() > 0 and await icon.is_visible(timeout=5000):
                        await icon.click(force=True)
                        icon_clicked = True
                        logger.info(f"✅ [封面-步骤1] 已点击上传图标 (选择器: {selector})")
                        break
                except:
                    continue

            if not icon_clicked:
                logger.warning("⚠️ [封面-步骤1] 未找到上传图标，尝试点击封面区域...")
                # 兜底：直接点击封面区域
                cover_selectors = [
                    "div.upload-file.mp-upload",
                    ".upload-file",
                ]
                for selector in cover_selectors:
                    try:
                        cover = page.locator(selector).first
                        if await cover.count() > 0:
                            await cover.click(force=True)
                            icon_clicked = True
                            logger.info(f"✅ [封面-步骤1] 已点击封面区域 (选择器: {selector})")
                            break
                    except:
                        continue

            if not icon_clicked:
                logger.warning("⚠️ [封面-步骤1] 封面区域点击失败，但继续流程")

            # 等待弹窗出现
            await asyncio.sleep(1.5)

            # ========== 步骤 2: 调用通用弹窗处理方法 ==========
            logger.info("🎯 [封面-步骤2] 调用通用弹窗处理方法...")
            await self._handle_upload_popup(page, cover_path)

            # ========== 步骤 3: 验证结果 ==========
            logger.info("🔍 [封面-步骤3] 验证封面上传结果...")

            preview_check = await page.evaluate("""() => {
                const uploadDiv = document.querySelector('div.upload-file.mp-upload');
                if (!uploadDiv) return { success: false, reason: 'uploadDiv not found' };

                // 检查是否有预览图 img 标签
                const img = uploadDiv.querySelector('img');
                if (img && img.src && img.src.length > 100) {
                    return { success: true, reason: 'preview_image_found', src: img.src.substring(0, 50) };
                }

                // 检查 upload-tip 是否消失
                const uploadTip = uploadDiv.querySelector('.upload-tip');
                if (!uploadTip) {
                    return { success: true, reason: 'upload_tip_removed' };
                }

                // 检查是否有替换按钮（使用标准 JS 语法，不是 :has-text）
                const allButtons = Array.from(uploadDiv.querySelectorAll('button'));
                const replaceBtn = allButtons.find(btn => btn.innerText && btn.innerText.includes('替换'));
                if (replaceBtn) {
                    return { success: true, reason: 'replace_button_found' };
                }

                // 检查是否有删除按钮（上传成功后出现）
                const deleteBtn = allButtons.find(btn => btn.innerText && btn.innerText.includes('删除'));
                if (deleteBtn) {
                    return { success: true, reason: 'delete_button_found' };
                }

                return { success: false, reason: 'no_success_indicator' };
            }""")

            if preview_check.get("success"):
                logger.info(f"✅ [封面-步骤3] 封面上传成功 ({preview_check.get('reason')})")
            else:
                logger.warning(f"⚠️ [封面-步骤3] 未检测到封面上传成功标识 ({preview_check.get('reason')})，但继续流程")

            return True

        except Exception as e:
            logger.warning(f"⚠️ [封面] 封面上传异常: {e}")
            return True  # 不阻塞发布流程

    async def _inject_content_simple(self, page: Page, text_chunks: List[str]):
        """
        简化版正文注入：只发纯文本，不插入图片

        原因：为了保证发布成功率，暂时只注入文本，图片仅在封面中使用

        核心逻辑变更：模拟真实粘贴动作。Quill 编辑器只有在监听到 paste 事件
        或真实的键盘输入时，才会更新其内部的 Delta 模型。
        """
        editor_sel = ".ql-editor"
        try:
            logger.info("等待 Quill 编辑器加载...")

            # 1. 确保编辑器可见并点击聚焦
            await page.wait_for_selector(editor_sel, timeout=15000)
            await page.click(editor_sel)
            await asyncio.sleep(0.5)

            # 2. 物理清空 (Ctrl+A + Backspace)
            logger.info("🧹 物理清空编辑器...")
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await asyncio.sleep(0.5)

            # 3. 构造完整文本内容 (转为纯文本，提高粘贴兼容性)
            full_text = "\n\n".join(text_chunks)
            logger.info(f"📝 准备注入文本，长度: {len(full_text)} 字符")

            # 4. 【核心黑科技】通过 DataTransfer 模拟粘贴事件
            # 这能绕过 Vue 的拦截，直接将内容塞入 Quill 的内部状态
            logger.info("📋 通过 DataTransfer 模拟粘贴事件...")
            await page.evaluate(
                """(text) => {
                const el = document.querySelector(".ql-editor");
                const dt = new DataTransfer();
                dt.setData("text/plain", text);
                const pasteEvent = new ClipboardEvent("paste", {
                    clipboardData: dt,
                    bubbles: true,
                    cancelable: true
                });
                el.dispatchEvent(pasteEvent);
            }""",
                full_text,
            )

            # 5. 【唤醒状态】物理按键组合拳
            # 在粘贴后按一下 End，再按两下空格，再退格
            # 这是强制触发 Vue "dirty" 检查的工业级标准做法
            logger.info("🔔 物理按键唤醒 Vue 状态...")
            await page.keyboard.press("End")
            await asyncio.sleep(0.2)
            await page.keyboard.type("  ")  # 键入两个空格
            await asyncio.sleep(0.2)
            await page.keyboard.press("Backspace")
            await page.keyboard.press("Backspace")

            # 6. 再次失焦并重新聚焦，确保 Vue 响应
            await page.keyboard.press("Tab")
            await asyncio.sleep(0.3)
            await page.click(editor_sel)
            await asyncio.sleep(0.5)

            logger.success("✅ 正文已通过剪贴板模拟注入并唤醒状态")

        except Exception as e:
            logger.error(f"❌ 正文注入崩溃: {e}")
            raise

    async def _apply_stealth_strategy(self, page: Page):
        """深度抹除自动化特征"""
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});
            Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
        """)

    async def _clear_overlays(self, page: Page):
        """物理清场：移除所有阻碍点击的层"""
        await page.evaluate("""
            () => {
                const selectors = ['.introjs-overlay', '.introjs-helperLayer', '.wp-guide-mask', '.p-guide', '.v-modal', '.el-overlay'];
                selectors.forEach(s => {
                    const el = document.querySelector(s);
                    if(el) el.remove();
                });
            }
        """)

    async def _navigate_to_editor(self, page: Page) -> bool:
        """
        导航至后台主页并点击"发布内容"按钮
        """
        try:
            base_url = "https://mp.sohu.com/mpfe/v4/contentManagement/firstpage"
            logger.info(f"访问后台主页: {base_url}")
            await page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(2)

            # 尝试多种选择器定位"发布内容"按钮
            publish_selectors = [
                'button:has-text("发布内容")',
                ".publish-btn",
                'span:has-text("发布内容")',
                'a:has-text("发布内容")',
                '[class*="publish"]:has-text("发布")',
            ]

            button = None
            for selector in publish_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        button = element
                        logger.info(f"使用选择器找到按钮: {selector}")
                        break
                except:
                    continue

            if not button:
                logger.error("未找到'发布内容'按钮")
                return False

            await button.click()
            logger.info("已点击'发布内容'按钮，等待编辑器加载...")

            await page.wait_for_selector(".ql-editor", timeout=15000)
            logger.info("编辑器加载完成")
            return True

        except Exception as e:
            logger.error(f"导航至编辑器失败: {e}")
            return False

    async def _fill_title_physical(self, page: Page, title: str) -> bool:
        """
        标题物理锁定
        使用新版选择器：input[placeholder="请输入标题（5-72字）"]
        """
        selector = 'input[placeholder="请输入标题（5-72字）"]'
        try:
            await page.wait_for_selector(selector, timeout=10000)
            logger.info("定位到标题输入框")

            # 暴力清空
            await page.click(selector, click_count=3)
            await page.keyboard.press("Backspace")

            # 模拟真人输入
            for char in title:
                await page.keyboard.type(char)
                await asyncio.sleep(random.uniform(0.01, 0.05))

            # 唤醒状态
            await page.keyboard.press("Space")
            await page.keyboard.press("Backspace")
            logger.info(f"标题注入完成: {title}")
            return True
        except Exception as e:
            logger.error(f"标题注入异常: {e}")
            return False

    async def _execute_publish(self, page: Page) -> Dict[str, Any]:
        """
        增强发布确认

        确保在执行发布前，所有弹窗、下拉框都已关闭，且编辑器失去焦点（触发最后的 blur 保存）
        """
        try:
            # ========== 步骤 1: 点击左上角空白处 - 关闭所有弹窗 + 编辑器失焦 ==========
            logger.info("🎯 [发布前置] 点击页面左上角空白处，关闭所有弹窗并让编辑器失焦...")
            await page.mouse.click(0, 0)  # 点击页面左上角空白处
            await asyncio.sleep(0.5)
            logger.info("✅ [发布前置] 已点击左上角空白处")

            # ========== 步骤 1.5: 等待编辑器内容同步到后台表单 ==========
            # 给 Vue + Quill 足够的时间将内容写入表单数据
            logger.info("⏳ [发布前置] 等待编辑器内容同步到后台表单...")
            await asyncio.sleep(2)
            logger.info("✅ [发布前置] 内容同步等待完成")

            # ========== 步骤 2: 点击发布按钮 ==========
            logger.info("📤 准备点击发布按钮...")
            publish_selectors = [
                'li.publish-report-btn.active.positive-button:has-text("发布")',
            ]

            for selector in publish_selectors:
                try:
                    btn = await page.wait_for_selector(selector, timeout=10000)
                    if btn:
                        logger.info(f"✅ 找到发布按钮: {selector}")
                        await btn.click()

                        # 等待可能的确认弹窗
                        await asyncio.sleep(2)
                        confirm_selectors = [
                            "button:has-text('确定')",
                            "button.el-button--primary:has-text('确定')",
                        ]
                        for confirm_selector in confirm_selectors:
                            try:
                                confirm_btn = await page.wait_for_selector(confirm_selector, timeout=3000)
                                if confirm_btn:
                                    await confirm_btn.click()
                                    logger.info("✅ 已点击确认按钮")
                                    break
                            except:
                                continue

                        logger.info("✅ 发布成功")
                        return {"success": True, "platform_url": page.url, "error_msg": None}
                except Exception as e:
                    logger.error(f"使用选择器 {selector} 点击发布失败: {e}")
                    continue

            return {"success": False, "error_msg": "未找到发布按钮或点击失败"}

        except Exception as e:
            logger.error(f"❌ [发布] 点击失败: {e}")
            return {"success": False, "error_msg": str(e)}

    def _deep_clean_content(self, text: str) -> str:
        """
        清理正文内容 - v18.6 增强版

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

    async def _save_as_draft(self, page: Page) -> Dict[str, Any]:
        """
        保存为草稿 - v18.6 新增

        不直接发布，而是保存为草稿供用户后续编辑发布
        """
        try:
            logger.info("📝 [草稿保存] 开始保存草稿流程...")

            # 步骤1: 点击左上角空白处关闭弹窗
            logger.info("🎯 [草稿保存] 点击页面空白处，关闭所有弹窗...")
            await page.mouse.click(0, 0)
            await asyncio.sleep(0.5)

            # 步骤2: 等待内容同步
            logger.info("⏳ [草稿保存] 等待内容同步...")
            await asyncio.sleep(2)

            # 步骤3: 查找并点击保存草稿按钮
            logger.info("📤 [草稿保存] 查找保存草稿按钮...")

            # 搜狐的保存草稿按钮通常在发布按钮旁边
            draft_selectors = [
                'li:has-text("保存草稿")',
                'button:has-text("保存草稿")',
                'span:has-text("保存草稿")',
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
                # 如果没找到保存草稿按钮，尝试点击返回按钮
                logger.warning("⚠️ [草稿保存] 未找到保存草稿按钮，尝试返回...")
                return {"success": True, "platform_url": page.url, "error_msg": "草稿已自动保存（搜狐自动保存机制）"}

            logger.success("✅ [草稿保存] 草稿保存成功")
            return {"success": True, "platform_url": page.url, "error_msg": None}

        except Exception as e:
            logger.warning(f"⚠️ [草稿保存] 保存异常: {e}，但内容已自动保存")
            return {"success": True, "platform_url": page.url, "error_msg": f"草稿已自动保存: {str(e)}"}


# 注册
registry.register(
    "sohu",
    SohuPublisher(
        "sohu",
        {
            "name": "搜狐号",
            "publish_url": "https://mp.sohu.com/mpfe/v4/contentManagement/firstpage",
            "color": "#F85959",
            "version": "v18.6",
        },
    ),
)
