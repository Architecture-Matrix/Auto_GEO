# -*- coding: utf-8 -*-
"""
数据库重建脚本
强制删除所有表并重新创建，确保表结构与代码模型一致！
"""

import sys
from pathlib import Path

# 添加项目根目录到路径（backend 的父目录）
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database import engine, Base
from loguru import logger

def rebuild_database():
    """
    强制重建数据库表
    """
    logger.info("=" * 50)
    logger.info("开始重建数据库...")
    logger.info("=" * 50)

    # 第一步：删除所有表
    logger.info("步骤 1/3: 删除所有旧表...")
    try:
        Base.metadata.drop_all(bind=engine)
        logger.success("  ✅ 所有旧表已删除")
    except Exception as e:
        logger.error(f"  ❌ 删除表失败: {e}")
        return False

    # 第二步：创建所有新表
    logger.info("步骤 2/3: 创建新表（包含 domain_keyword 字段）...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.success("  ✅ 新表创建成功")
    except Exception as e:
        logger.error(f"  ❌ 创建表失败: {e}")
        return False

    # 第三步：验证表结构
    logger.info("步骤 3/3: 验证表结构...")
    from sqlalchemy import inspect
    inspector = inspect(engine)
    columns = inspector.get_columns('projects')

    has_domain_keyword = any(col['name'] == 'domain_keyword' for col in columns)

    if has_domain_keyword:
        logger.success("  ✅ projects 表包含 domain_keyword 字段")
    else:
        logger.error("  ❌ projects 表缺少 domain_keyword 字段！")
        logger.info(f"  当前字段: {[col['name'] for col in columns]}")
        return False

    logger.info("=" * 50)
    logger.success("数据库重建完成！现在可以正常使用了！")
    logger.info("=" * 50)
    return True

if __name__ == "__main__":
    # 检查后端是否在运行
    import sqlite3
    db_path = project_root / "backend" / "database" / "auto_geo_v3.db"

    if db_path.exists():
        try:
            # 尝试连接数据库，检查是否有锁
            conn = sqlite3.connect(str(db_path))
            conn.execute("PRAGMA busy_timeout = 1000")
            conn.close()
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() or "database is locked" in str(e).lower():
                logger.error("=" * 50)
                logger.error("❌ 数据库被后端服务占用！")
                logger.error("=" * 50)
                logger.info("请先停止后端服务（按 Ctrl+C），然后重新运行此脚本！")
                sys.exit(1)

    # 执行重建
    success = rebuild_database()
    sys.exit(0 if success else 1)
