# -*- coding: utf-8 -*-
"""
任务分发服务
根据部署模式将任务分发到本地或云端执行
"""

import asyncio
from typing import Dict, Any, Optional, Callable
from loguru import logger
from enum import Enum

from backend.config import DEPLOYMENT_MODE
from backend.services.deployment_helper import (
    get_browser_headless_mode,
    should_use_local_browser,
)
from backend.services.local_browser_bridge import local_browser_bridge


class TaskLocation(Enum):
    """任务执行位置"""

    LOCAL = "local"  # 本地浏览器
    CLOUD = "cloud"  # 云端浏览器


class TaskDispatcher:
    """
    任务分发器

    根据部署模式和任务类型，自动决定在本地还是云端执行
    """

    def __init__(self):
        self._local_bridge_available = False
        self._check_local_bridge()

    def _check_local_bridge(self):
        """检查本地浏览器桥接是否可用"""
        self._local_bridge_available = local_browser_bridge.is_running
        logger.debug(f"本地浏览器桥接状态: {'可用' if self._local_bridge_available else '不可用'}")

    def decide_task_location(self, task_type: str, force_local: bool = False) -> TaskLocation:
        """
        决定任务执行位置

        Args:
            task_type: 任务类型 (auth, publish, check)
            force_local: 强制本地执行

        Returns:
            TaskLocation
        """
        if force_local:
            logger.debug(f"任务 {task_type} 强制本地执行")
            return TaskLocation.LOCAL

        if should_use_local_browser(task_type):
            # 需要本地浏览器
            if not self._local_bridge_available:
                logger.warning(f"任务 {task_type} 需要本地浏览器，但桥接不可用")
            return TaskLocation.LOCAL

        # 默认云端执行
        return TaskLocation.CLOUD

    async def execute_task(
        self, task_type: str, task_func: Callable, *args, force_local: bool = False, **kwargs
    ) -> Dict[str, Any]:
        """
        执行任务（自动分发到合适的位置）

        Args:
            task_type: 任务类型
            task_func: 任务函数
            *args, **kwargs: 任务参数
            force_local: 强制本地执行

        Returns:
            执行结果
        """
        # 重新检查本地桥接状态
        self._check_local_bridge()

        # 决定执行位置
        location = self.decide_task_location(task_type, force_local)

        logger.info(f"📤 任务分发: {task_type} → {location.value}")

        if location == TaskLocation.LOCAL:
            return await self._execute_local(task_func, *args, **kwargs)
        else:
            return await self._execute_cloud(task_func, *args, **kwargs)

    async def _execute_local(self, task_func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """在本地执行任务"""
        try:
            if not local_browser_bridge.is_running:
                return {
                    "success": False,
                    "error": "本地浏览器未运行",
                    "location": "local",
                }

            # 在本地浏览器上执行任务
            result = await task_func(local_browser_bridge, *args, **kwargs)

            return {
                "success": True,
                "result": result,
                "location": "local",
            }

        except Exception as e:
            logger.error(f"本地任务执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "location": "local",
            }

    async def _execute_cloud(self, task_func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """在云端执行任务"""
        try:
            # 直接调用任务函数（云端执行）
            result = await task_func(*args, **kwargs)

            return {
                "success": True,
                "result": result,
                "location": "cloud",
            }

        except Exception as e:
            logger.error(f"云端任务执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "location": "cloud",
            }

    def get_status(self) -> Dict[str, Any]:
        """获取分发器状态"""
        return {
            "deployment_mode": DEPLOYMENT_MODE,
            "local_bridge_available": self._local_bridge_available,
            "deployment_description": self._get_mode_description(),
        }

    def _get_mode_description(self) -> str:
        """获取当前模式描述"""
        descriptions = {
            "local": "所有任务在本地浏览器执行",
            "cloud": "所有任务在服务器headless执行",
            "hybrid": "授权任务本地，自动化任务云端",
        }
        return descriptions.get(DEPLOYMENT_MODE, "未知模式")


# 全局单例
task_dispatcher = TaskDispatcher()


# 便捷装饰器
def dispatch_task(task_type: str, force_local: bool = False):
    """
    任务分发装饰器

    用法：
    @dispatch_task("auth")
    async def my_auth_task(browser_bridge, user_id, platform):
        # 任务逻辑
        pass
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            return await task_dispatcher.execute_task(task_type, func, *args, force_local=force_local, **kwargs)

        return wrapper

    return decorator
