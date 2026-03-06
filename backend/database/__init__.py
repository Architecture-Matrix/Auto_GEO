# -*- coding: utf-8 -*-
"""
数据库连接管理 - 工业级加固版
支持 WAL 模式，解决 SQLite 并发锁问题
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from typing import Generator
from loguru import logger
from sqlalchemy import inspect

from backend.config import DATABASE_DIR, DATABASE_URL

# 1. 确保数据库目录存在
DATABASE_DIR.mkdir(exist_ok=True, parents=True)

# 2. 创建引擎
# connect_args={"check_same_thread": False} 是 SQLite 在多线程环境下运行的必要参数
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,  # 开启后可查看所有 SQL 语句，开发调试时有用
    pool_pre_ping=True,  # 每次使用连接前检查是否可用
)


# 3. 🌟 核心优化：开启 SQLite 的 WAL 模式
# 这样可以实现“读写不冲突”，极大减少 "database is locked" 错误
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")  # 显式开启外键约束支持
        cursor.close()
    except Exception as e:
        logger.error(f"设置 SQLite Pragma 失败: {e}")


# 4. 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 5. 基类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI 依赖注入：获取数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库表
    逻辑：导入所有模型 -> 检查已存在的表 -> 创建新表
    """
    # 必须在这里导入模型，否则 Base.metadata 不知道有哪些表
    from backend.database.models import (
        Account,
        PublishRecord,
        Project,
        Keyword,
        QuestionVariant,
        IndexCheckRecord,
        GeoArticle,
        ScheduledTask,
        KnowledgeCategory,
        Knowledge,  # 🌟 补齐了之前遗漏的表
        AutoPublishTask,  # 🌟 自动发布任务表
        AutoPublishRecord,  # 🌟 自动发布记录表
        Client,  # 🌟 客户表
        SiteProject,  # 🌟 AEO网站项目表
    )

    # 获取已存在的表名用于对比
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    try:
        # checkfirst=True 会自动处理“表已存在”的情况
        Base.metadata.create_all(bind=engine)

        # 再次获取所有表名，对比输出日志
        all_tables = inspect(engine).get_table_names()

        for table in all_tables:
            if table not in existing_tables:
                logger.info(f"✨ 新表创建成功: {table}")
            else:
                # logger.debug(f"表 {table} 已存在，跳过创建")
                pass

        logger.success("✅ 数据库初始化检查完成，WAL 模式已就绪")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {str(e)}")
        raise e
