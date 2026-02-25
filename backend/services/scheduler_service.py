# -*- coding: utf-8 -*-
"""
自动化调度服务 - 工业加固版
负责：定时扫描待发布文章、自动触发收录检测、失败重试、动态任务加载
"""

import asyncio
import random
from typing import Optional, Dict
from datetime import datetime
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# 尝试导入时区，防止环境缺失报错
try:
    from pytz import timezone
except ImportError:
    timezone = None

from backend.services.geo_article_service import GeoArticleService
from backend.database.models import ScheduledTask, GeoArticle

# 🌟 统一日志绑定
log = logger.bind(module="调度中心")

class SchedulerService:
    def __init__(self):
        tz = timezone('Asia/Shanghai') if timezone else None
        # 配置调度器，设置较长的误火容忍时间
        self.scheduler = AsyncIOScheduler(
            timezone=tz,
            job_defaults={
                'misfire_grace_time': 60, # 🌟 允许错过时间后60秒内重试
                'coalesce': True,         # 积压的任务只跑一次
                'max_instances': 1        # 同一个Job同时只能跑一个实例
            }
        )
        self.db_factory = None

        # 🌟 任务映射表
        self.task_registry = {
            "publish_task": self.check_and_publish_scheduled_articles,
            "monitor_task": self.auto_check_indexing_job
        }

    def set_db_factory(self, db_factory):
        self.db_factory = db_factory

    def init_default_tasks(self):
        """初始化默认定时扫描任务"""
        if not self.db_factory:
            return
        db = self.db_factory()
        try:
            if db.query(ScheduledTask).count() == 0:
                defaults = [
                    ScheduledTask(
                        name="文章自动发布引擎",
                        task_key="publish_task",
                        cron_expression="*/1 * * * *",  # 每分钟扫描一次
                        description="扫描待发布文章并触发浏览器自动化脚本",
                        is_active=True
                    ),
                    ScheduledTask(
                        name="全网收录实时监测",
                        task_key="monitor_task",
                        cron_expression="*/5 * * * *",  # 每5分钟监测一次
                        description="通过AI搜索引擎检查已发布文章的收录状态",
                        is_active=True
                    )
                ]
                db.add_all(defaults)
                db.commit()
                log.info("✅ 默认定时扫描任务初始化完成")
        except Exception as e:
            log.error(f"初始化任务失败: {e}")
        finally:
            db.close()

    def _schedule_job(self, task: ScheduledTask):
        """内部方法：注册/更新单个 Job"""
        func = self.task_registry.get(task.task_key)
        if not func:
            log.warning(f"⚠️ 未找到处理函数: {task.task_key}")
            return

        if self.scheduler.get_job(task.task_key):
            self.scheduler.remove_job(task.task_key)

        if task.is_active:
            try:
                self.scheduler.add_job(
                    func,
                    CronTrigger.from_crontab(task.cron_expression),
                    id=task.task_key,
                    replace_existing=True,
                    misfire_grace_time=60 # 🌟 加固保护
                )
                log.info(f"📅 任务装载成功: [{task.name}] -> {task.cron_expression}")
            except Exception as e:
                log.error(f"❌ Cron 表达式解析错误 [{task.name}]: {e}")

    def load_jobs_from_db(self):
        """从数据库加载并注册所有任务"""
        if not self.db_factory:
            return
        db = self.db_factory()
        try:
            tasks = db.query(ScheduledTask).all()
            for t in tasks:
                self._schedule_job(t)
        finally:
            db.close()

    def start(self):
        """启动调度引擎"""
        if not self.scheduler.running:
            self.init_default_tasks()
            self.load_jobs_from_db()
            self.scheduler.start()
            log.success("🚀 [Scheduler] 动态调度引擎已全面启动")

    def stop(self):
        """安全停止"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            log.info("🛑 [Scheduler] 调度引擎已安全关闭")

    def reload_task(self, task_id: int):
        """用户修改配置后，手动热更新"""
        if not self.db_factory:
            return
        db = self.db_factory()
        try:
            task = db.query(ScheduledTask).get(task_id)
            if task:
                self._schedule_job(task)
                return True
        finally:
            db.close()
        return False

    def trigger_job(self, job_id: str) -> bool:
        """
        立即触发任务执行

        使用 job.modify(next_run_time=datetime.now()) 将任务下一次运行时间设置为现在，
        调度器会立即捡起并执行，且不影响原来的周期计划。

        参数:
            job_id: APScheduler 的 Job ID (task_key，如 "publish_task")

        返回:
            bool: 是否触发成功
        """
        job = self.scheduler.get_job(job_id)
        if not job:
            log.warning(f"⚠️ 尝试触发的任务不存在: {job_id}")
            return False

        try:
            # 将下一次运行时间设置为现在
            job.modify(next_run_time=datetime.now())
            log.success(f"🚀 任务已触发执行: [{job_id}]")
            return True
        except Exception as e:
            log.error(f"❌ 触发任务失败 [{job_id}]: {e}")
            return False

    # ================= 🚀 核心业务逻辑 Job =================

    async def check_and_publish_scheduled_articles(self):
        """
        [Job] 自动扫描并发布

        扫描条件：
        1. publish_status = 'scheduled'（已配置定时发布）
        2. platform 不为空（已配置发布平台）
        3. account_id 不为空（已配置发布账号）
        4. scheduled_at 时间已到

        注意：不扫描 completed 状态的文章（等待用户在批量发布页面配置）
        """
        if not self.db_factory: return
        db = self.db_factory()
        try:
            now = datetime.now()
            # 搜索：已配置定时发布 且 平台/账号已配置 且 时间已到
            # 同时也支持失败重试（failed 且 次数<3）
            from sqlalchemy import and_

            pending = db.query(GeoArticle).filter(
                and_(
                    GeoArticle.publish_status == "scheduled",
                    GeoArticle.platform.isnot(None),
                    GeoArticle.account_id.isnot(None),
                    GeoArticle.scheduled_at <= now
                )
            ).all()

            if pending:
                log.info(f"🔍 [发布扫描] 发现 {len(pending)} 篇定时发布文章，准备触发脚本...")
                service = GeoArticleService(db)
                for article in pending:
                    # 使用 create_task 异步处理，防止多篇文章发布时互相阻塞
                    asyncio.create_task(service.execute_publish(article.id))
            else:
                log.debug("🔍 [发布扫描] 无定时发布文章待处理")
        except Exception as e:
            log.error(f"发布 Job 运行异常: {e}")
        finally:
            db.close()

    async def auto_check_indexing_job(self):
        """
        [Job] 自动监测收录
        """
        if not self.db_factory:
            return
        db = self.db_factory()
        try:
            # 搜索：已发布 但 未被确认收录的文章
            pending = db.query(GeoArticle).filter(
                GeoArticle.publish_status == "published",
                GeoArticle.index_status != "indexed"
            ).all()

            if pending:
                log.info(f"📡 [收录扫描] 发现 {len(pending)} 篇已发布文章需要检测效果...")
                service = GeoArticleService(db)
                for article in pending:
                    asyncio.create_task(service.check_article_index(article.id))
        except Exception as e:
            log.error(f"监测 Job 运行异常: {e}")
        finally:
            db.close()

# 单例模式
_instance = SchedulerService()

def get_scheduler_service():
    return _instance