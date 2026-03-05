# -*- coding: utf-8 -*-
"""
部署模式辅助函数
根据部署环境自动配置浏览器参数
"""

from loguru import logger
from backend.config import DEPLOYMENT_MODE, HEADLESS_MODE, LOCAL_BROWSER_CDP_PORT


def get_browser_headless_mode(operation_type: str = "default") -> bool:
    """
    根据部署模式和操作类型获取headless设置

    Args:
        operation_type: 操作类型
            - "auth": 授权登录（需要GUI）
            - "publish": 文章发布（可能需要GUI）
            - "check": 收录检测（可headless）
            - "default": 默认操作

    Returns:
        是否使用headless模式
    """
    # 1. 环境变量优先级最高
    if HEADLESS_MODE:
        logger.debug("HEADLESS_MODE环境变量=true, 强制使用headless")
        return True

    # 2. 根据部署模式和操作类型决定
    if DEPLOYMENT_MODE == "cloud":
        # 云端模式：全部headless
        logger.debug(f"[云端模式] 操作 {operation_type} 使用headless=True")
        return True

    elif DEPLOYMENT_MODE == "local":
        # 本地模式：根据操作类型决定
        if operation_type == "auth":
            # 授权必须显示浏览器
            logger.debug("[本地模式] 授权操作使用headless=False")
            return False
        elif operation_type == "publish":
            # 发布默认显示，但可以headless
            logger.debug("[本地模式] 发布操作使用headless=False（方便调试）")
            return False
        else:
            # 其他操作可以headless
            logger.debug(f"[本地模式] {operation_type} 操作使用headless=True")
            return True

    elif DEPLOYMENT_MODE == "hybrid":
        # 混合模式：授权需要GUI，其他可headless
        if operation_type == "auth":
            logger.debug("[混合模式] 授权操作使用headless=False（需要本地浏览器）")
            return False
        else:
            logger.debug(f"[混合模式] {operation_type} 操作使用headless=True")
            return True

    # 默认返回False（显示浏览器）
    return False


def get_deployment_info() -> dict:
    """
    获取当前部署配置信息

    Returns:
        部署配置详情
    """
    return {
        "deployment_mode": DEPLOYMENT_MODE,
        "headless_mode": HEADLESS_MODE,
        "cdp_port": LOCAL_BROWSER_CDP_PORT,
        "description": _get_deployment_description(),
    }


def _get_deployment_description() -> str:
    """获取部署模式描述"""
    descriptions = {
        "local": "本地模式：所有浏览器操作在本地执行，适合开发和调试",
        "cloud": "云端模式：所有浏览器操作在服务器执行（headless），适合已登录场景",
        "hybrid": "混合模式：授权操作在本地，自动化任务在云端，兼顾灵活性和效率",
    }
    return descriptions.get(DEPLOYMENT_MODE, "未知模式")


def should_use_local_browser(operation_type: str = "default") -> bool:
    """
    判断是否应该使用本地浏览器

    Args:
        operation_type: 操作类型

    Returns:
        是否使用本地浏览器
    """
    if DEPLOYMENT_MODE == "hybrid":
        # 混合模式：授权操作使用本地浏览器
        return operation_type == "auth"

    if DEPLOYMENT_MODE == "local":
        # 本地模式：授权和发布使用本地浏览器
        return operation_type in ["auth", "publish"]

    # 云端模式：不使用本地浏览器
    return False


def log_deployment_config():
    """打印部署配置日志"""
    info = get_deployment_info()
    logger.info("=" * 50)
    logger.info("📋 部署模式配置")
    logger.info(f"   模式: {info['deployment_mode']}")
    logger.info(f"   描述: {info['description']}")
    logger.info(f"   Headless: {info['headless_mode']}")
    logger.info(f"   CDP端口: {info['cdp_port']}")
    logger.info("=" * 50)
