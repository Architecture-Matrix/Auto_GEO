# -*- coding: utf-8 -*-
"""
本地浏览器桥接API
提供本地浏览器控制的HTTP接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from loguru import logger

from backend.services.local_browser_bridge import local_browser_bridge

router = APIRouter(prefix="/api/browser", tags=["本地浏览器"])


class BrowserStartRequest(BaseModel):
    """浏览器启动请求"""

    headless: bool = False
    use_cdp: bool = True
    cdp_port: int = 9222


class TaskRequest(BaseModel):
    """任务执行请求"""

    task_type: str  # 'auth', 'publish', 'check'
    params: Dict[str, Any]


@router.get("/status")
async def get_browser_status() -> Dict[str, Any]:
    """
    获取本地浏览器状态

    返回：
    - is_running: 是否运行中
    - cdp_url: CDP连接URL
    - context_count: 上下文数量
    - chrome_found: 是否找到Chrome
    """
    status = local_browser_bridge.get_status()
    return {"success": True, "status": status}


@router.post("/start")
async def start_browser(request: BrowserStartRequest) -> Dict[str, Any]:
    """
    启动本地浏览器

    参数：
    - headless: 是否无头模式（默认False）
    - use_cdp: 是否启用CDP（默认True）
    - cdp_port: CDP端口（默认9222）
    """
    result = await local_browser_bridge.start(
        headless=request.headless, use_cdp=request.use_cdp, cdp_port=request.cdp_port
    )

    if result["success"]:
        logger.info(f"✅ 本地浏览器已启动: CDP={result.get('cdp_url')}")
    else:
        logger.error(f"❌ 启动失败: {result.get('error')}")

    return result


@router.post("/stop")
async def stop_browser() -> Dict[str, Any]:
    """
    停止本地浏览器
    """
    success = await local_browser_bridge.stop()

    return {"success": success, "message": "浏览器已停止" if success else "停止失败"}


@router.post("/context/create")
async def create_context(
    storage_state: Optional[Dict[str, Any]] = None, context_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    创建浏览器上下文

    参数：
    - storage_state: 存储状态（cookies等）
    - context_id: 上下文ID
    """
    if not local_browser_bridge.is_running:
        raise HTTPException(status_code=400, detail="浏览器未运行")

    try:
        context = await local_browser_bridge.create_context(storage_state=storage_state, context_id=context_id)

        return {"success": True, "context_id": context_id, "message": "上下文创建成功"}
    except Exception as e:
        logger.error(f"创建上下文失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/{context_id}/storage")
async def get_storage_state(context_id: str) -> Dict[str, Any]:
    """
    获取上下文的存储状态

    参数：
    - context_id: 上下文ID
    """
    if not local_browser_bridge.is_running:
        raise HTTPException(status_code=400, detail="浏览器未运行")

    try:
        state = await local_browser_bridge.save_storage_state(context_id)

        if state is None:
            raise HTTPException(status_code=404, detail="上下文不存在")

        return {"success": True, "storage_state": state}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取存储状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_task(request: TaskRequest) -> Dict[str, Any]:
    """
    在本地浏览器上执行任务

    支持的任务类型：
    - auth: 执行授权流程
    - publish: 执行文章发布
    - check: 执行收录检测

    参数：
    - task_type: 任务类型
    - params: 任务参数
    """
    if not local_browser_bridge.is_running:
        raise HTTPException(status_code=400, detail="浏览器未运行，请先启动")

    # 这里根据task_type分发到不同的处理器
    # 实际实现需要进一步设计任务分发机制

    return {"success": True, "message": f"任务 {request.task_type} 已接收"}


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    健康检查
    """
    status = local_browser_bridge.get_status()

    return {
        "status": "healthy" if status["is_running"] else "stopped",
        "chrome_available": status["chrome_found"],
        "cdp_enabled": status["cdp_url"] is not None,
    }
