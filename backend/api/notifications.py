# -*- coding: utf-8 -*-
"""
预警通知API
写的预警通知API，监控SEO健康状态！
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.notification_service import (
    get_notification_service,
    WebSocketNotificationChannel,
    LogNotificationChannel
)
from backend.schemas import ApiResponse
from loguru import logger


router = APIRouter(prefix="/api/notifications", tags=["预警通知"])


# ==================== 请求/响应模型 ====================

class AlertRuleUpdate(BaseModel):
    """预警规则更新"""
    rule_name: str
    threshold: Optional[float] = None
    enabled: Optional[bool] = None


class AlertSummaryResponse(BaseModel):
    """预警摘要响应"""
    total_keywords: int
    alert_keywords: int
    critical_count: int
    warning_count: int
    alerts_by_type: dict
    recent_alerts: list


class AlertResponse(BaseModel):
    """预警响应"""
    type: str
    level: str
    keyword: str
    project: str
    company: str
    message: str
    timestamp: str
    hit_rate: Optional[float] = None


# 全局WebSocket回调
_ws_callback = None


def set_ws_callback(callback):
    """设置WebSocket回调"""
    global _ws_callback
    _ws_callback = callback


# ==================== 预警API ====================

@router.post("/check", response_model=List[AlertResponse])
async def check_alerts(
    background_tasks: BackgroundTasks,
    project_id: Optional[int] = Query(None, description="项目ID，不填则检查所有"),
    db: Session = Depends(get_db)
):
    """
    执行预警检查

    注意：这是一个耗时操作，建议异步执行！
    """
    service = get_notification_service(db)

    # 添加默认的通知渠道
    if _ws_callback:
        service.add_channel(WebSocketNotificationChannel(_ws_callback))
    service.add_channel(LogNotificationChannel())

    # 执行检查
    alerts = await service.check_and_alert(project_id)

    logger.info(f"预警检查完成: 触发{len(alerts)}条预警")
    return alerts


@router.get("/summary", response_model=AlertSummaryResponse)
async def get_alert_summary(
    project_id: Optional[int] = Query(None, description="项目ID"),
    db: Session = Depends(get_db)
):
    """
    获取预警摘要

    注意：返回当前SEO健康状况！
    """
    service = get_notification_service(db)
    summary = service.get_alert_summary(project_id)
    return summary


@router.get("/rules", response_model=dict)
async def get_alert_rules():
    """
    获取预警规则列表

    注意：返回所有可配置的预警规则！
    """
    from backend.services.notification_service import NotificationService
    rules = {}
    for key, rule in NotificationService.ALERT_RULES.items():
        rules[key] = {
            "name": rule.name,
            "threshold": rule.threshold,
            "enabled": rule.enabled
        }
    return rules


@router.post("/trigger-test", response_model=ApiResponse)
async def trigger_test_alert(
    db: Session = Depends(get_db)
):
    """
    触发测试预警

    注意：用于测试通知渠道是否正常！
    """
    test_alert = {
        "type": "test",
        "level": "info",
        "keyword": "测试关键词",
        "project": "测试项目",
        "company": "测试公司",
        "message": "这是一条测试预警通知",
        "timestamp": "2024-01-01T00:00:00"
    }

    service = get_notification_service(db)

    # 添加默认的通知渠道
    if _ws_callback:
        service.add_channel(WebSocketNotificationChannel(_ws_callback))
    service.add_channel(LogNotificationChannel())

    # 发送测试通知
    await service._send_alert(test_alert)

    return ApiResponse(success=True, message="测试预警已发送")


@router.get("/health")
async def notification_health():
    """健康检查"""
    return {
        "status": "ok",
        "ws_callback_configured": _ws_callback is not None
    }
