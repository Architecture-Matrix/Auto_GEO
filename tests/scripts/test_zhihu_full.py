# -*- coding: utf-8 -*-
"""
知乎完整发布流程测试脚本 V2
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


async def find_all_inputs(page):
    """查找页面上所有input元素"""
    return await page.evaluate("""
        () => {
            const inputs = document.querySelectorAll('input, textarea, [contenteditable="true"]');
            return Array.from(inputs).map(el => ({
                tag: el.tagName,
                type: el.type || '',
                placeholder: el.placeholder || '',
                className: el.className || '',
                id: el.id || '',
                name: el.name || '',
                isContentEditable: el.isContentEditable
            }));
        }
    """)


async def test_full_publish_flow():
    """测试完整的知乎发布流程"""

    test_title = "测试文章"
    test_content = "这是测试正文内容。\n\n第二段内容。"

    try:
        # 获取账号
        db = SessionLocal()
        account = db.query(Account).filter(Account.platform == 'zhihu').first()
        if not account:
            logger.error("❌ 没有知乎账号")
            db.close()
            return False

        cookies = decrypt_cookies(account.cookies)
        storage = decrypt_storage_state(account.storage_state)
        db.close()

        logger.info(f"账号: {account.account_name}")

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

        # 添加cookies
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

        # 监听所有请求
        def on_request(request):
            logger.debug(f"请求: {request.method} {request.url}")

        # page.on("request", on_request)

        # ==================== 步骤1: 访问发布页面 ====================
        logger.info("\n" + "="*50)
        logger.info("步骤1: 访问知乎发布页面")
        logger.info("="*50)

        await page.goto(PLATFORMS['zhihu']['publish_url'], timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(5)  # 增加等待时间

        current_url = page.url
        logger.info(f"当前URL: {current_url}")

        if "signin" in current_url or "login" in current_url:
            logger.error("❌ 跳转到登录页，请重新授权")
            return False

        logger.info("✅ 成功访问发布页面")

        # ==================== 步骤2: 查找所有输入元素 ====================
        logger.info("\n" + "="*50)
        logger.info("步骤2: 查找页面上所有输入元素")
        logger.info("="*50)

        all_inputs = await find_all_inputs(page)
        logger.info(f"\n找到 {len(all_inputs)} 个输入元素:")
        for i, inp in enumerate(all_inputs):
            logger.info(f"  [{i}] {inp}")

        # ==================== 步骤3: 尝试输入标题 ====================
        logger.info("\n" + "="*50)
        logger.info("步骤3: 尝试输入标题")
        logger.info("="*50)

        # 使用JavaScript直接查找并填充
        # 用page.evaluate的正确方式传递参数
        title_filled = await page.evaluate("""
            (title) => {
                const selectors = [
                    'textarea[placeholder*="请输入标题"]',
                    'textarea[placeholder*="标题"]',
                    'input[placeholder*="标题"]',
                    'input[placeholder*="请输入"]',
                ];

                for (const selector of selectors) {
                    const els = document.querySelectorAll(selector);
                    for (const el of els) {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            el.value = title;
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                            el.dispatchEvent(new Event('blur', { bubbles: true }));
                            return { success: true, selector: selector };
                        }
                    }
                }

                return { success: false, error: '所有选择器都失败了' };
            }
        """, test_title)

        if title_filled.get("success"):
            logger.info(f"✅ 标题已输入: {test_title}")
            logger.info(f"   使用选择器: {title_filled.get('selector')}")
            logger.info(f"   使用方法: {title_filled.get('method')}")
        else:
            logger.error(f"❌ 无法输入标题: {title_filled.get('error')}")

        await asyncio.sleep(1)

        # ==================== 步骤4: 尝试输入正文 ====================
        logger.info("\n" + "="*50)
        logger.info("步骤4: 尝试输入正文")
        logger.info("="*50)

        content_filled = await page.evaluate("""
            (content) => {
                const selectors = [
                    '.public-DraftEditor-content',
                    '[contenteditable="true"]',
                ];

                for (const selector of selectors) {
                    const els = document.querySelectorAll(selector);
                    for (const el of els) {
                        const rect = el.getBoundingClientRect();
                        // 找大的contenteditable元素（正文编辑器）
                        if (rect.width > 300 && rect.height > 100) {
                            el.textContent = content;
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                            return { success: true, selector: selector };
                        }
                    }
                }

                return { success: false, error: '找不到编辑器' };
            }
        """, test_content)

        if content_filled.get("success"):
            logger.info(f"✅ 正文已输入")
            logger.info(f"   使用方法: {content_filled.get('method')}")
        else:
            logger.error(f"❌ 无法输入正文: {content_filled.get('error')}")

        await asyncio.sleep(1)

        # ==================== 步骤5: 截图 ====================
        logger.info("\n" + "="*50)
        logger.info("步骤5: 截图并等待确认")
        logger.info("="*50)

        screenshot_path = Path(__file__).parent / "zhihu_publish_test.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        logger.info(f"✅ 已截图: {screenshot_path}")

        # 再次验证输入
        verify = await page.evaluate("""
            () => {
                const inputs = document.querySelectorAll('input, textarea, [contenteditable="true"]');
                const results = [];
                for (const el of inputs) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        let value = '';
                        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                            value = el.value;
                        } else {
                            value = el.textContent?.substring(0, 50);
                        }
                        if (value) {
                            results.push({ tag: el.tagName, value: value });
                        }
                    }
                }
                return results;
            }
        """)

        logger.info("\n已输入的内容:")
        for r in verify:
            logger.info(f"  {r}")

        logger.info("\n等待30秒供你观察页面...")
        await asyncio.sleep(30)

        # 清理
        await page.close()
        await context.close()
        await browser.close()
        await playwright.stop()

        logger.info("\n" + "="*50)
        logger.info("✅ 测试完成！")
        logger.info("="*50)
        return True

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def main():
    logger.info("开始测试知乎完整发布流程 V2...")

    result = await test_full_publish_flow()

    if result:
        logger.info("\n✅ 所有测试通过！")
    else:
        logger.error("\n❌ 测试失败")


if __name__ == "__main__":
    asyncio.run(main())
