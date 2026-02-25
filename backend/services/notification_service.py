# -*- coding: utf-8 -*-
"""
预警通知服务
用这个来发送SEO预警通知！
"""

from typing import List, Dict, Any, Optional
from loguru import logger
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from dataclasses import dataclass

from backend.database.models import Project, Keyword, IndexCheckRecord


@dataclass
class AlertRule:
    """预警规则"""
    name: str
    threshold: float
    enabled: bool = True


class NotificationService:
    """
    预警通知服务

    注意：这个服务负责监控SEO数据并发送预警！
    """

    # 默认预警规则
    ALERT_RULES = {
        "hit_rate_drop": AlertRule("命中率下降", 30.0),  # 命中率低于30%
        "no_index": AlertRule("零收录", 0.0),  # 完全没有收录
        "consistently_low": AlertRule("持续低迷", 10.0),  # 持续低于10%
    }

    def __init__(self, db: Session):
        """
        初始化通知服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self.channels = []  # 通知渠道列表

    def add_channel(self, channel: 'NotificationChannel'):
        """添加通知渠道"""
        self.channels.append(channel)
        logger.info(f"添加通知渠道: {channel.name}")

    async def check_and_alert(self, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        检查并发送预警

        Args:
            project_id: 项目ID，None表示检查所有项目

        Returns:
            触发的预警列表
        """
        alerts = []

        # 获取要检查的项目
        if project_id:
            projects = [self.db.query(Project).filter(Project.id == project_id).first()]
        else:
            projects = self.db.query(Project).filter(Project.status == 1).all()

        projects = [p for p in projects if p]

        for project in projects:
            # 检查每个关键词
            keywords = self.db.query(Keyword).filter(
                Keyword.project_id == project.id,
                Keyword.status == "active"
            ).all()

            for keyword in keywords:
                # 检查各种预警规则
                keyword_alerts = await self._check_keyword_alerts(keyword, project)
                alerts.extend(keyword_alerts)

        # 发送通知
        for alert in alerts:
            await self._send_alert(alert)

        return alerts

    async def _check_keyword_alerts(
        self,
        keyword: Keyword,
        project: Project
    ) -> List[Dict[str, Any]]:
        """检查单个关键词的预警"""
        alerts = []

        # 获取最近的检测记录（最近7天）
        seven_days_ago = datetime.now() - timedelta(days=7)
        records = self.db.query(IndexCheckRecord).filter(
            IndexCheckRecord.keyword_id == keyword.id,
            IndexCheckRecord.check_time >= seven_days_ago
        ).all()

        if not records:
            # 没有检测记录
            alerts.append({
                "type": "no_data",
                "level": "warning",
                "keyword": keyword.keyword,
                "project": project.name,
                "company": project.company_name,
                "message": f"关键词 '{keyword.keyword}' 最近7天没有检测数据",
                "timestamp": datetime.now().isoformat()
            })
            return alerts

        # 计算命中率
        total = len(records)
        keyword_found = sum(1 for r in records if r.keyword_found)
        company_found = sum(1 for r in records if r.company_found)
        hit_rate = (keyword_found + company_found) / (total * 2) * 100

        # 检查命中率过低
        if self.ALERT_RULES["hit_rate_drop"].enabled and hit_rate < self.ALERT_RULES["hit_rate_drop"].threshold:
            alerts.append({
                "type": "hit_rate_low",
                "level": "warning" if hit_rate > 10 else "critical",
                "keyword": keyword.keyword,
                "project": project.name,
                "company": project.company_name,
                "hit_rate": round(hit_rate, 2),
                "message": f"关键词 '{keyword.keyword}' 命中率仅为 {hit_rate:.1f}%，低于阈值 {self.ALERT_RULES['hit_rate_drop'].threshold}%",
                "timestamp": datetime.now().isoformat()
            })

        # 检查零收录
        if self.ALERT_RULES["no_index"].enabled and hit_rate == 0:
            alerts.append({
                "type": "no_index",
                "level": "critical",
                "keyword": keyword.keyword,
                "project": project.name,
                "company": project.company_name,
                "message": f"关键词 '{keyword.keyword}' 在所有AI平台零收录！",
                "timestamp": datetime.now().isoformat()
            })

        # 检查持续低迷
        if self.ALERT_RULES["consistently_low"].enabled:
            # 获取更长时间的数据（30天）
            thirty_days_ago = datetime.now() - timedelta(days=30)
            long_term_records = self.db.query(IndexCheckRecord).filter(
                IndexCheckRecord.keyword_id == keyword.id,
                IndexCheckRecord.check_time >= thirty_days_ago
            ).all()

            if long_term_records:
                lt_total = len(long_term_records)
                lt_keyword_found = sum(1 for r in long_term_records if r.keyword_found)
                lt_company_found = sum(1 for r in long_term_records if r.company_found)
                lt_hit_rate = (lt_keyword_found + lt_company_found) / (lt_total * 2) * 100

                if lt_hit_rate < self.ALERT_RULES["consistently_low"].threshold:
                    alerts.append({
                        "type": "consistently_low",
                        "level": "warning",
                        "keyword": keyword.keyword,
                        "project": project.name,
                        "company": project.company_name,
                        "hit_rate_30d": round(lt_hit_rate, 2),
                        "message": f"关键词 '{keyword.keyword}' 30天命中率持续低迷（{lt_hit_rate:.1f}%）",
                        "timestamp": datetime.now().isoformat()
                    })

        return alerts

    async def _send_alert(self, alert: Dict[str, Any]):
        """发送预警通知"""
        logger.warning(f"SEO预警: {alert['message']}")

        # 通过所有渠道发送
        for channel in self.channels:
            try:
                await channel.send(alert)
            except Exception as e:
                logger.error(f"发送通知失败 ({channel.name}): {e}")

    def get_alert_summary(self, project_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取预警摘要

        Args:
            project_id: 项目ID

        Returns:
            预警摘要数据
        """
        # 获取项目
        if project_id:
            projects = [self.db.query(Project).filter(Project.id == project_id).first()]
        else:
            projects = self.db.query(Project).filter(Project.status == 1).all()

        projects = [p for p in projects if p]

        summary = {
            "total_keywords": 0,
            "alert_keywords": 0,
            "critical_count": 0,
            "warning_count": 0,
            "alerts_by_type": {},
            "recent_alerts": []
        }

        for project in projects:
            keywords = self.db.query(Keyword).filter(
                Keyword.project_id == project.id,
                Keyword.status == "active"
            ).all()

            summary["total_keywords"] += len(keywords)

            for keyword in keywords:
                # 简单检查当前状态
                seven_days_ago = datetime.now() - timedelta(days=7)
                records = self.db.query(IndexCheckRecord).filter(
                    IndexCheckRecord.keyword_id == keyword.id,
                    IndexCheckRecord.check_time >= seven_days_ago
                ).all()

                if records:
                    total = len(records)
                    keyword_found = sum(1 for r in records if r.keyword_found)
                    company_found = sum(1 for r in records if r.company_found)
                    hit_rate = (keyword_found + company_found) / (total * 2) * 100

                    if hit_rate < 30:
                        summary["alert_keywords"] += 1
                        if hit_rate < 10:
                            summary["critical_count"] += 1
                        else:
                            summary["warning_count"] += 1

        return summary


# ==================== 通知渠道 ====================

class NotificationChannel:
    """通知渠道基类"""

    def __init__(self, name: str):
        self.name = name

    async def send(self, alert: Dict[str, Any]):
        """发送通知"""
        raise NotImplementedError


class WebSocketNotificationChannel(NotificationChannel):
    """WebSocket通知渠道"""

    def __init__(self, ws_callback):
        super().__init__("WebSocket")
        self.ws_callback = ws_callback

    async def send(self, alert: Dict[str, Any]):
        """通过WebSocket发送通知"""
        if self.ws_callback:
            await self.ws_callback({
                "type": "seo_alert",
                "data": alert
            })


class LogNotificationChannel(NotificationChannel):
    """日志通知渠道（用于测试）"""

    def __init__(self):
        super().__init__("Log")

    async def send(self, alert: Dict[str, Any]):
        """记录到日志"""
        from loguru import logger
        logger.warning(f"[SEO预警] {alert['level'].upper()}: {alert['message']}")


class EmailNotificationChannel(NotificationChannel):
    """邮件通知渠道"""

    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        super().__init__("Email")
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.recipients = []

    def add_recipient(self, email: str):
        """添加收件人"""
        self.recipients.append(email)

    async def send(self, alert: Dict[str, Any]):
        """发送邮件通知"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        if not self.recipients:
            return

        subject = f"[SEO预警] {alert['level'].upper()}: {alert['project']} - {alert['keyword']}"
        body = f"""
        预警类型: {alert['type']}
        预警级别: {alert['level']}
        项目: {alert.get('project', 'N/A')}
        公司: {alert.get('company', 'N/A')}
        关键词: {alert['keyword']}
        描述: {alert['message']}
        时间: {alert['timestamp']}
        """

        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = ', '.join(self.recipients)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            logger.info(f"邮件通知已发送: {subject}")
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")


class WebhookNotificationChannel(NotificationChannel):
    """Webhook通知渠道"""

    def __init__(self, webhook_url: str):
        super().__init__("Webhook")
        self.webhook_url = webhook_url

    async def send(self, alert: Dict[str, Any]):
        """发送Webhook通知"""
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                await client.post(self.webhook_url, json=alert, timeout=10)
            logger.info(f"Webhook通知已发送: {alert['type']}")
        except Exception as e:
            logger.error(f"Webhook发送失败: {e}")


# 全局单例
_notification_service: Optional[NotificationService] = None


def get_notification_service(db: Session) -> NotificationService:
    """
    获取通知服务实例

    注意：这是对外暴露的主要接口！
    """
    return NotificationService(db)
