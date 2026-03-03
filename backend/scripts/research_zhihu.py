# -*- coding: utf-8 -*-
"""
知乎发布页面完整元素研究脚本
"""

import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from loguru import logger
from playwright.async_api import async_playwright

from backend.config import PLATFORMS
from backend.services.crypto import decrypt_cookies, decrypt_storage_state
from backend.database import SessionLocal
from backend.database.models import Account


async def research_zhihu_elements():
    """研究知乎发布页面的所有关键元素"""

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

        current_url = page.url
        logger.info(f"当前URL: {current_url}")

        if "signin" in current_url:
            logger.error("❌ 跳转到登录页")
            return False

        logger.info("✅ 成功访问发布页面")

        # ==================== 研究各种元素 ====================

        # 1. 封面上传元素
        logger.info("\n" + "=" * 50)
        logger.info("研究1: 封面图片上传元素")
        logger.info("=" * 50)

        cover_elements = await page.evaluate("""
            () => {
                const results = [];
                // 查找所有与图片上传相关的元素
                const elements = document.querySelectorAll('[class*="upload"], [class*="Upload"], [class*="Picture"], [class*="Cover"], [class*="Image"]');
                elements.forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        results.push({
                            tag: el.tagName,
                            className: el.className,
                            id: el.id,
                            textContent: el.textContent?.substring(0, 50),
                            rect: { width: rect.width, height: rect.height },
                            innerHTML: el.innerHTML?.substring(0, 200)
                        });
                    }
                });
                return results;
            }
        """)
        logger.info(f"封面上传相关元素: {json.dumps(cover_elements, indent=2, ensure_ascii=False)}")

        # 2. 创作声明元素
        logger.info("\n" + "=" * 50)
        logger.info("研究2: 创作声明（AI辅助）元素")
        logger.info("=" * 50)

        declaration_elements = await page.evaluate("""
            () => {
                const results = [];
                // 查找包含"AI"、"创作"、"声明"等关键词的元素
                const allText = document.querySelectorAll('*');
                allText.forEach(el => {
                    const text = el.textContent || '';
                    if (text.includes('AI') || text.includes('创作') || text.includes('声明') || text.includes('辅助')) {
                        if (text.length < 100) {  // 只看短文本
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0 && rect.height < 100) {
                                results.push({
                                    tag: el.tagName,
                                    className: el.className,
                                    text: text.trim(),
                                    rect: { width: rect.width, height: rect.height }
                                });
                            }
                        }
                    }
                });
                return results;
            }
        """)
        logger.info(f"创作声明相关元素: {json.dumps(declaration_elements[:20], indent=2, ensure_ascii=False)}")

        # 3. 话题选择元素
        logger.info("\n" + "=" * 50)
        logger.info("研究3: 话题选择元素")
        logger.info("=" * 50)

        topic_elements = await page.evaluate("""
            () => {
                const results = [];
                // 查找话题相关元素
                const elements = document.querySelectorAll('[placeholder*="话题"], [class*="topic"], [class*="Topic"], [class*="Tag"]');
                elements.forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        results.push({
                            tag: el.tagName,
                            type: el.type || '',
                            placeholder: el.placeholder || '',
                            className: el.className,
                            id: el.id,
                            rect: { width: rect.width, height: rect.height }
                        });
                    }
                });
                return results;
            }
        """)
        logger.info(f"话题选择相关元素: {json.dumps(topic_elements, indent=2, ensure_ascii=False)}")

        # 4. 富文本编辑器研究
        logger.info("\n" + "=" * 50)
        logger.info("研究4: 富文本编辑器")
        logger.info("=" * 50)

        editor_info = await page.evaluate("""
            () => {
                const editor = document.querySelector('.public-DraftEditor-content');
                if (!editor) return { error: '找不到编辑器' };

                // 获取编辑器的父元素，了解Draft.js结构
                const container = editor.closest('.DraftEditor-editorContainer') || editor.parentElement;

                return {
                    editorClassName: editor.className,
                    containerClassName: container?.className || '',
                    // 检查是否有Draft.js相关的全局对象
                    hasDraftJS: typeof window.DraftJS !== 'undefined',
                    // 获取编辑器内容结构
                    innerHTML: editor.innerHTML?.substring(0, 500),
                    // 检查content字段
                    contentBlocks: editor.querySelectorAll('[data-block="true"]').length
                };
            }
        """)
        logger.info(f"编辑器信息: {json.dumps(editor_info, indent=2, ensure_ascii=False)}")

        # 5. 发布按钮及其周边元素
        logger.info("\n" + "=" * 50)
        logger.info("研究5: 发布按钮及周边")
        logger.info("=" * 50)

        publish_area = await page.evaluate("""
            () => {
                const results = [];
                // 查找发布按钮
                const buttons = document.querySelectorAll('button');
                buttons.forEach(btn => {
                    const text = btn.textContent?.trim() || '';
                    if (text.includes('发布') || text.includes('保存') || text.includes('草稿')) {
                        results.push({
                            text: text,
                            className: btn.className,
                            disabled: btn.disabled,
                            rect: btn.getBoundingClientRect()
                        });
                    }
                });
                return results;
            }
        """)
        logger.info(f"发布按钮: {json.dumps(publish_area, indent=2, ensure_ascii=False)}")

        # 6. 查找所有checkbox和radio（可能用于创作声明）
        logger.info("\n" + "=" * 50)
        logger.info("研究6: 复选框和单选框")
        logger.info("=" * 50)

        checkboxes = await page.evaluate("""
            () => {
                const results = [];
                const inputs = document.querySelectorAll('input[type="checkbox"], input[type="radio"], label');
                inputs.forEach(el => {
                    const text = el.textContent?.trim() || '';
                    if (text.length > 0 && text.length < 50) {
                        results.push({
                            type: el.type || el.tagName,
                            text: text,
                            className: el.className,
                            checked: el.checked || false
                        });
                    }
                });
                return results;
            }
        """)
        logger.info(f"复选框/单选框: {json.dumps(checkboxes[:30], indent=2, ensure_ascii=False)}")

        # 截图
        screenshot_path = Path(__file__).parent / "zhihu_research.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        logger.info(f"\n✅ 已截图: {screenshot_path}")

        logger.info("\n等待60秒供你观察页面...")
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
    logger.info("开始研究知乎发布页面元素...")

    result = await research_zhihu_elements()

    if result:
        logger.info("\n✅ 研究完成！")
    else:
        logger.error("\n❌ 研究失败")


if __name__ == "__main__":
    asyncio.run(main())
