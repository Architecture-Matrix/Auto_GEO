# -*- coding: utf-8 -*-
"""
部署配置API
提供部署模式查询和配置接口
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional
from loguru import logger

from backend.services.deployment_helper import (
    get_deployment_info,
    get_browser_headless_mode,
    log_deployment_config,
)
from backend.services.task_dispatcher import task_dispatcher
from backend.services.local_browser_bridge import local_browser_bridge

router = APIRouter(prefix="/api/deployment", tags=["部署配置"])


class HeadlessRequest(BaseModel):
    """Headless模式请求"""

    operation_type: str = "default"  # auth, publish, check, default


@router.get("/config")
async def get_deployment_config() -> Dict[str, Any]:
    """
    获取当前部署配置

    返回：
    - deployment_mode: 部署模式
    - headless_mode: 全局headless设置
    - cdp_port: CDP端口
    - description: 模式描述
    """
    config = get_deployment_info()

    # 添加本地浏览器状态
    config["local_browser_status"] = local_browser_bridge.get_status()

    # 添加任务分发器状态
    config["dispatcher_status"] = task_dispatcher.get_status()

    return {"success": True, "config": config}


@router.post("/headless/check")
async def check_headless_mode(request: HeadlessRequest) -> Dict[str, Any]:
    """
    检查指定操作的headless模式

    参数：
    - operation_type: 操作类型 (auth, publish, check, default)

    返回：
    - headless: 是否使用headless
    - reason: 原因说明
    """
    operation = request.operation_type
    headless = get_browser_headless_mode(operation)

    reason = _get_headless_reason(operation, headless)

    return {"success": True, "operation": operation, "headless": headless, "reason": reason}


@router.get("/modes")
async def list_deployment_modes() -> Dict[str, Any]:
    """
    列出所有可用的部署模式

    返回每个模式的说明和适用场景
    """
    return {
        "success": True,
        "modes": {
            "local": {
                "name": "本地模式",
                "description": "所有浏览器操作在本地执行",
                "scenarios": ["开发环境", "调试阶段", "需要手动登录"],
                "browser": "有GUI显示",
                "auth": "本地手动登录",
                "tasks": "本地浏览器执行",
            },
            "cloud": {
                "name": "云端模式",
                "description": "所有浏览器操作在服务器headless执行",
                "scenarios": ["生产环境", "已保存会话", "自动化任务"],
                "browser": "headless模式",
                "auth": "需要预先获取会话",
                "tasks": "服务器自动执行",
                "note": "Linux环境需要安装xvfb",
            },
            "hybrid": {
                "name": "混合模式（推荐）",
                "description": "授权在本地，自动化任务在云端",
                "scenarios": ["生产环境", "需要手动授权", "自动化执行"],
                "browser": "授权时本地，任务时云端",
                "auth": "本地客户端手动登录",
                "tasks": "服务器自动执行（使用已保存会话）",
            },
        },
        "current": get_deployment_info()["deployment_mode"],
    }


@router.post("/log-config")
async def print_deployment_config() -> Dict[str, Any]:
    """
    打印部署配置到日志
    """
    log_deployment_config()

    return {"success": True, "message": "配置已打印到日志"}


@router.get("/task-location/{task_type}")
async def get_task_location(task_type: str) -> Dict[str, Any]:
    """
    查询指定任务类型的执行位置

    参数：
    - task_type: 任务类型 (auth, publish, check)

    返回：
    - location: 执行位置 (local/cloud)
    - reason: 原因说明
    """
    location = task_dispatcher.decide_task_location(task_type)

    reason = _get_location_reason(task_type, location.value)

    return {"success": True, "task_type": task_type, "location": location.value, "reason": reason}


def _get_headless_reason(operation: str, headless: bool) -> str:
    """获取headless决策原因"""
    if headless:
        return f"'{operation}'操作将在headless模式下执行（无GUI）"
    else:
        return f"'{operation}'操作需要显示浏览器窗口"


def _get_location_reason(task_type: str, location: str) -> str:
    """获取任务位置决策原因"""
    mode = get_deployment_info()["deployment_mode"]

    if mode == "local":
        return f"本地模式：'{task_type}'任务将在本地浏览器执行"
    elif mode == "cloud":
        return f"云端模式：'{task_type}'任务将在服务器headless执行"
    elif mode == "hybrid":
        if task_type == "auth":
            return f"混合模式：'{task_type}'任务需要在本地手动授权"
        else:
            return f"混合模式：'{task_type}'任务将在服务器自动执行"
    else:
        return "未知模式"
