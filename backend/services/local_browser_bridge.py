# -*- coding: utf-8 -*-
"""
本地CDP浏览器桥接服务
用于混合架构：本地浏览器处理需要GUI的操作
"""

import asyncio
import os
import sys
import json
from typing import Dict, Any, Optional
from loguru import logger
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from datetime import datetime

from backend.config import BROWSER_ARGS, DEFAULT_USER_AGENT


class LocalBrowserBridge:
    """
    本地浏览器桥接服务

    功能：
    1. 检测并启动本地Chrome
    2. 暴露CDP endpoint
    3. 管理本地浏览器会话
    4. 处理需要手动操作的任务
    """

    def __init__(self):
        self._browser: Optional[Browser] = None
        self._contexts: Dict[str, BrowserContext] = {}
        self._cdp_url: Optional[str] = None
        self._is_running = False
        self._playwright = None

        # 本地Chrome路径
        self.chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]

        # Mac OS支持
        if sys.platform == "darwin":
            self.chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            ]

        # Linux支持
        if sys.platform == "linux":
            self.chrome_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/snap/bin/chromium",
            ]

    @property
    def is_running(self) -> bool:
        """检查浏览器是否运行中"""
        return self._is_running and self._browser is not None

    @property
    def cdp_url(self) -> Optional[str]:
        """获取CDP连接URL"""
        return self._cdp_url

    def find_chrome(self) -> Optional[str]:
        """
        查找本地Chrome可执行文件

        Returns:
            Chrome路径或None
        """
        for path in self.chrome_paths:
            if os.path.exists(path):
                logger.info(f"✅ 找到本地Chrome: {path}")
                return path
        return None

    async def start(self, headless: bool = False, use_cdp: bool = True, cdp_port: int = 9222) -> Dict[str, Any]:
        """
        启动本地浏览器

        Args:
            headless: 是否无头模式
            use_cdp: 是否启用CDP
            cdp_port: CDP端口

        Returns:
            启动结果
        """
        try:
            if self._is_running:
                logger.warning("浏览器已在运行中")
                return {"success": True, "cdp_url": self._cdp_url, "message": "浏览器已在运行中"}

            logger.info("🚀 启动本地浏览器桥接服务...")

            # 查找Chrome
            chrome_path = self.find_chrome()

            # 准备启动参数
            launch_options = {
                "headless": headless,
                "args": BROWSER_ARGS.copy(),
                "timeout": 30000,
            }

            # 添加CDP相关参数
            if use_cdp:
                launch_options["args"].extend(
                    [f"--remote-debugging-port={cdp_port}", "--remote-debugging-address=0.0.0.0"]
                )

            if chrome_path:
                launch_options["executable_path"] = chrome_path

            # 启动Playwright
            self._playwright = await async_playwright().start()

            # 启动浏览器
            logger.info(f"启动参数: headless={headless}, cdp={use_cdp}, port={cdp_port}")
            self._browser = await self._playwright.chromium.launch(**launch_options)

            self._is_running = True

            # 构建CDP URL
            if use_cdp:
                self._cdp_url = f"http://localhost:{cdp_port}"
                logger.info(f"🔗 CDP Endpoint: {self._cdp_url}")
            else:
                self._cdp_url = None

            logger.info("✅ 本地浏览器启动成功")

            return {"success": True, "cdp_url": self._cdp_url, "headless": headless, "message": "浏览器启动成功"}

        except Exception as e:
            logger.error(f"❌ 启动浏览器失败: {e}")
            return {"success": False, "error": str(e), "message": "浏览器启动失败"}

    async def stop(self) -> bool:
        """
        停止浏览器

        Returns:
            是否成功停止
        """
        try:
            if not self._is_running:
                logger.warning("浏览器未运行")
                return True

            logger.info("🛑 停止本地浏览器...")

            # 关闭所有context
            for context_id, context in self._contexts.items():
                try:
                    await context.close()
                    logger.debug(f"关闭context: {context_id}")
                except Exception as e:
                    logger.warning(f"关闭context失败: {e}")

            self._contexts.clear()

            # 关闭浏览器
            if self._browser:
                await self._browser.close()
                self._browser = None

            # 停止Playwright
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None

            self._is_running = False
            self._cdp_url = None

            logger.info("✅ 浏览器已停止")
            return True

        except Exception as e:
            logger.error(f"❌ 停止浏览器失败: {e}")
            return False

    async def create_context(
        self, storage_state: Optional[Dict[str, Any]] = None, context_id: Optional[str] = None
    ) -> BrowserContext:
        """
        创建浏览器上下文

        Args:
            storage_state: 存储状态（cookies等）
            context_id: 上下文ID

        Returns:
            BrowserContext实例
        """
        if not self._browser:
            raise RuntimeError("浏览器未运行，请先调用start()")

        ctx_id = context_id or f"context_{datetime.now().timestamp()}"

        options = {
            "user_agent": DEFAULT_USER_AGENT,
            "viewport": {"width": 1920, "height": 1080},
            "locale": "zh-CN",
            "timezone_id": "Asia/Shanghai",
        }

        if storage_state:
            options["storage_state"] = storage_state

        context = await self._browser.new_context(**options)
        self._contexts[ctx_id] = context

        logger.info(f"创建浏览器上下文: {ctx_id}")
        return context

    async def get_page(self, context_id: Optional[str] = None) -> Page:
        """
        获取或创建页面

        Args:
            context_id: 上下文ID

        Returns:
            Page实例
        """
        if context_id and context_id in self._contexts:
            context = self._contexts[context_id]
        else:
            # 创建临时context
            context = await self.create_context()

        page = await context.new_page()
        return page

    async def execute_task(self, task_func, *args, **kwargs) -> Dict[str, Any]:
        """
        在本地浏览器上执行任务

        Args:
            task_func: 异步任务函数
            *args, **kwargs: 任务参数

        Returns:
            任务执行结果
        """
        if not self._is_running:
            return {"success": False, "error": "浏览器未运行"}

        try:
            result = await task_func(self, *args, **kwargs)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"执行任务失败: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """
        获取桥接服务状态

        Returns:
            状态信息
        """
        return {
            "is_running": self._is_running,
            "cdp_url": self._cdp_url,
            "context_count": len(self._contexts),
            "chrome_found": self.find_chrome() is not None,
        }

    async def save_storage_state(self, context_id: str, file_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        保存存储状态

        Args:
            context_id: 上下文ID
            file_path: 保存路径（可选）

        Returns:
            存储状态
        """
        if context_id not in self._contexts:
            logger.error(f"上下文不存在: {context_id}")
            return None

        context = self._contexts[context_id]

        if file_path:
            await context.storage_state(path=file_path)
            logger.info(f"存储状态已保存: {file_path}")
            return None
        else:
            state = await context.storage_state()
            logger.info(f"存储状态已获取: {len(state.get('cookies', []))} cookies")
            return state


# 全局单例
local_browser_bridge = LocalBrowserBridge()
