# -*- coding: utf-8 -*-
"""
修复 GeoArticle 表中的 project_id 字段
将所有 project_id 为 NULL 的记录，根据 keyword_id 查找对应的项目ID并更新
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database import SessionLocal
from backend.database.models import GeoArticle, Keyword
from loguru import logger


def fix_project_ids():
    """
    修复 GeoArticle 表中 project_id 为 NULL 的记录
    """
    db = SessionLocal()

    try:
        # 查询所有 project_id 为 NULL 的 GeoArticle 记录
        orphan_articles = db.query(GeoArticle).filter(GeoArticle.project_id == None).all()

        if not orphan_articles:
            logger.info("✅ 没有需要修复的记录")
            return

        logger.info(f"找到 {len(orphan_articles)} 条需要修复的记录")

        fixed_count = 0
        for article in orphan_articles:
            # 根据 keyword_id 查找对应的 Keyword
            keyword = db.query(Keyword).filter(Keyword.id == article.keyword_id).first()

            if keyword and keyword.project_id:
                # 更新 GeoArticle 的 project_id
                article.project_id = keyword.project_id
                fixed_count += 1

                if fixed_count % 100 == 0:
                    logger.info(f"已修复 {fixed_count} 条记录...")

        db.commit()
        db.close()

        logger.success(f"✅ 修复完成！共修复 {fixed_count} 条记录")
        print(f"\n修复完成！共修复 {fixed_count} 条记录\n")

    except Exception as e:
        logger.error(f"修复失败: {e}")
        db.close()
        sys.exit(1)


if __name__ == "__main__":
    logger.info("开始修复 GeoArticle.project_id 字段...")

    fix_project_ids()

    logger.info("修复脚本执行完毕")
