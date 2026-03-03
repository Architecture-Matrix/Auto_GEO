# -*- coding: utf-8 -*-
"""
知乎图片上传机制研究脚本
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from loguru import logger
from playwright.async_api import async_playwright

from backend.config import PLATFORMS
from backend.services.crypto import decrypt_cookies, decrypt_storage_state
from backend.database import SessionLocal
from backend.database.models import Account


async def research_image_upload():
    """研究知乎图片上传机制"""

    try:
        # 获取账号
        db = SessionLocal()
        account = db.query(Account).filter(Account.platform == "zhihu").first()
        if not account:
            logger.error("❌ 没有知乎账号")
            db.close()
            return False

        cookies = decrypt_cookies(account.cookies)
        storage = decrypt_storage_state(account.storage_state)
        db.close()

        # 启动浏览器
        playwright = await async_playwright().start()

        import os

        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        executable_path = None
        for path in chrome_paths:
            if os.path.exists(path):
                executable_path = path
                break

        launch_options = {
            "headless": False,
            "args": ["--no-sandbox", "--disable-setuid-sandbox"],
        }
        if executable_path:
            launch_options["executable_path"] = executable_path

        browser = await playwright.chromium.launch(**launch_options)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})

        await context.add_cookies(cookies)

        # 设置localStorage
        if storage.get("localStorage"):
            ls_items = []
            for key, value in storage["localStorage"].items():
                escaped_key = key.replace("\\", "\\\\").replace("'", "\\'")
                escaped_value = value.replace("\\", "\\\\").replace("'", "\\'")
                ls_items.append(f"localStorage.setItem('{escaped_key}', '{escaped_value}');")

            init_script = f"""
                (() => {{
                    try {{
                        {chr(10).join(ls_items)}
                    }} catch(e) {{}}
                }})();
            """
            await context.add_init_script(init_script)

        page = await context.new_page()

        # 访问发布页面
        await page.goto(PLATFORMS["zhihu"]["publish_url"], timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(5)

        # ==================== 研究图片上传相关元素 ====================
        logger.info("\n" + "=" * 50)
        logger.info("研究图片上传相关元素")
        logger.info("=" * 50)

        # 1. 查找工具栏中的图片按钮
        toolbar_elements = await page.evaluate("""
            () => {
                const results = [];
                // 查找工具栏中的图片相关按钮
                const toolbar = document.querySelector('.toolbarV3, [class*="toolbar"]');
                if (toolbar) {
                    const buttons = toolbar.querySelectorAll('button, [role="button"]');
                    buttons.forEach(btn => {
                        const text = btn.textContent?.trim() || '';
                        const title = btn.getAttribute('title') || '';
                        const className = btn.className || '';
                        // 查找包含"图片"、"image"、"图"等关键词的按钮
                        if (text.includes('图') || title.includes('图') ||
                            text.includes('Image') || title.includes('Image') ||
                            className.includes('Image') || className.includes('Picture')) {
                            results.push({
                                tag: btn.tagName,
                                text: text,
                                title: title,
                                className: className,
                                innerHTML: btn.innerHTML?.substring(0, 200)
                            });
                        }
                    });
                }
                return results;
            }
        """)
        logger.info(f"工具栏图片相关元素: {toolbar_elements}")

        # 2. 查找所有文件上传input
        file_inputs = await page.evaluate("""
            () => {
                const results = [];
                const inputs = document.querySelectorAll('input[type="file"]');
                inputs.forEach(input => {
                    const accept = input.getAttribute('accept') || '';
                    const className = input.className || '';
                    const parent = input.parentElement;
                    results.push({
                        accept: accept,
                        className: className,
                        parentClass: parent?.className || '',
                        parentTag: parent?.tagName || '',
                        visible: input.offsetWidth > 0 && input.offsetHeight > 0
                    });
                });
                return results;
            }
        """)
        logger.info(f"文件上传input: {file_inputs}")

        # 3. 查找编辑器内的图片相关元素
        editor_images = await page.evaluate("""
            () => {
                const results = [];
                const editor = document.querySelector('.public-DraftEditor-content');
                if (editor) {
                    // 查找编辑器内可能用于插入图片的元素
                    const images = editor.querySelectorAll('img');
                    images.forEach(img => {
                        results.push({
                            src: img.src,
                            className: img.className
                        });
                    });
                }
                return results;
            }
        """)
        logger.info(f"编辑器内图片: {editor_images}")

        # 4. 检查是否有粘贴图片的功能
        clipboard_info = await page.evaluate("""
            () => {
                // 检查是否有粘贴事件监听
                const editor = document.querySelector('.public-DraftEditor-content');
                if (!editor) return { error: '找不到编辑器' };

                // 尝试获取事件监听器（可能无法直接访问）
                return {
                    editorClass: editor.className,
                    hasContentEditable: editor.isContentEditable,
                    parentClass: editor.parentElement?.className || ''
                };
            }
        """)
        logger.info(f"剪贴板信息: {clipboard_info}")

        # 5. 查找工具栏结构
        toolbar_structure = await page.evaluate("""
            () => {
                const results = [];
                const toolbar = document.querySelector('.toolbarV3, [class*="toolbar"]');
                if (toolbar) {
                    const buttons = toolbar.querySelectorAll('button');
                    buttons.forEach(btn => {
                        results.push({
                            text: btn.textContent?.trim().substring(0, 20),
                            className: btn.className,
                            title: btn.getAttribute('title') || ''
                        });
                    });
                }
                return results;
            }
        """)
        logger.info(f"工具栏结构: {toolbar_structure}")

        # 截图
        screenshot_path = Path(__file__).parent / "zhihu_image_upload.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        logger.info(f"\n✅ 已截图: {screenshot_path}")

        logger.info("\n等待60秒供观察...")
        await asyncio.sleep(60)

        # 清理
        await page.close()
        await context.close()
        await browser.close()
        await playwright.stop()

        return True

    except Exception as e:
        logger.error(f"❌ 研究失败: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


async def main():
    logger.info("开始研究知乎图片上传机制...")

    result = await research_image_upload()

    if result:
        logger.info("\n✅ 研究完成！")
    else:
        logger.error("\n❌ 研究失败")


if __name__ == "__main__":
    asyncio.run(main())
