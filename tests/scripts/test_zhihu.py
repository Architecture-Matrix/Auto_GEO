# -*- coding: utf-8 -*-
"""
知乎发布功能诊断脚本 V2
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from loguru import logger
from playwright.async_api import async_playwright

# 导入配置
from backend.config import PLATFORMS
from backend.services.crypto import decrypt_cookies, decrypt_storage_state
from backend.database import SessionLocal
from backend.database.models import Account


async def test_with_fixed_method():
    """使用修复后的方法测试"""
    logger.info("=" * 50)
    logger.info("测试修复后的方法")
    logger.info("=" * 50)

    try:
        # 获取账号数据
        db = SessionLocal()
        account = db.query(Account).filter(Account.platform == 'zhihu').first()
        if not account:
            logger.error("❌ 没有知乎账号")
            db.close()
            return False

        cookies = decrypt_cookies(account.cookies)
        storage = decrypt_storage_state(account.storage_state)
        db.close()

        logger.info(f"✅ 账号: {account.account_name}")
        logger.info(f"   Cookies: {len(cookies)} 个")
        logger.info(f"   localStorage: {len(storage.get('localStorage', {}))} 项")

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
        logger.info("✅ 浏览器启动成功")

        # 创建上下文
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
        )

        # 添加cookies
        await context.add_cookies(cookies)
        logger.info("✅ Cookies已添加")

        # 使用 add_init_script 设置localStorage
        if storage.get("localStorage"):
            ls_items = []
            for key, value in storage["localStorage"].items():
                # 转义特殊字符
                escaped_key = key.replace("\\", "\\\\").replace("'", "\\'")
                escaped_value = value.replace("\\", "\\\\").replace("'", "\\'")
                ls_items.append(f"localStorage.setItem('{escaped_key}', '{escaped_value}');")

            init_script = f"""
                (() => {{
                    try {{
                        {chr(10).join(ls_items)}
                        console.log('localStorage已设置，共{len(ls_items)}项');
                    }} catch(e) {{
                        console.error('设置localStorage失败:', e);
                    }}
                }})();
            """
            await context.add_init_script(init_script)
            logger.info(f"✅ localStorage初始化脚本已添加")

        # 创建页面访问知乎
        page = await context.new_page()

        # 监听控制台消息
        def on_console(msg):
            if "localStorage" in msg.text or "sessionStorage" in msg.text:
                logger.info(f"🔧 控制台: {msg.text}")

        page.on("console", on_console)

        # 访问知乎发布页面
        logger.info(f"正在访问: {PLATFORMS['zhihu']['publish_url']}")
        await page.goto(PLATFORMS['zhihu']['publish_url'], timeout=60000, wait_until="domcontentloaded")

        await asyncio.sleep(5)  # 等待页面加载

        current_url = page.url
        logger.info(f"当前URL: {current_url}")

        # 检查是否跳转到登录页
        if "signin" in current_url or "login" in current_url:
            logger.error("❌ 跳转到登录页，cookies/storage可能已失效")
            await asyncio.sleep(10)
            await page.close()
            await context.close()
            await browser.close()
            await playwright.stop()
            return False

        logger.info("✅ 成功访问知乎发布页面！")

        # 检查localStorage是否生效
        ls_count = await page.evaluate("Object.keys(localStorage).length")
        logger.info(f"✅ 页面localStorage项数: {ls_count}")

        # 截图
        screenshot_path = Path(__file__).parent / "zhihu_fixed.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        logger.info(f"✅ 已截图: {screenshot_path}")

        # 测试页面元素
        logger.info("\n--- 测试页面元素 ---")

        # 检查标题输入框
        title_selectors = [
            "input[placeholder*='标题']",
            "input[placeholder*='请输入标题']",
        ]
        for sel in title_selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    logger.info(f"✅ 找到标题输入框: {sel}")
                    break
            except:
                pass

        # 检查编辑器
        editor_selectors = ["div[contenteditable='true']", ".public-DraftEditor-content"]
        for sel in editor_selectors:
            try:
                els = await page.query_selector_all(sel)
                if els:
                    logger.info(f"✅ 找到编辑器元素: {sel} (共{len(els)}个)")
                    break
            except:
                pass

        logger.info("\n等待20秒供观察页面...")
        await asyncio.sleep(20)

        # 清理
        await page.close()
        await context.close()
        await browser.close()
        await playwright.stop()

        logger.info("✅ 测试通过！")
        return True

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def main():
    logger.info("开始测试修复后的知乎发布功能...")

    result = await test_with_fixed_method()

    logger.info("=" * 50)
    if result:
        logger.info("✅ 测试成功！浏览器没有闪退！")
    else:
        logger.error("❌ 测试失败")
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
