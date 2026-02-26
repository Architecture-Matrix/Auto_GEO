# -*- coding: utf-8 -*-
"""
数据迁移脚本：将现有知识库数据迁移到RAGFlow
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from loguru import logger
from datetime import datetime

from backend.database import SessionLocal, init_db
from backend.database.models import KnowledgeCategory, Knowledge
from backend.services.ragflow_client import RAGFlowClient
from backend.config import RAGFLOW_BASE_URL, RAGFLOW_API_KEY


def migrate_categories(db: Session, ragflow_client: RAGFlowClient) -> dict:
    """
    迁移所有分类到RAGFlow

    Args:
        db: 数据库会话
        ragflow_client: RAGFlow客户端

    Returns:
        迁移统计信息
    """
    logger.info("开始迁移分类...")

    categories = db.query(KnowledgeCategory).filter(KnowledgeCategory.status == 1).all()
    success_count = 0
    fail_count = 0

    for cat in categories:
        try:
            logger.info(f"正在迁移分类: {cat.name}")

            # 检查是否已同步
            if cat.ragflow_dataset_id:
                logger.info(f"分类 {cat.name} 已同步，跳过")
                success_count += 1
                continue

            # 创建RAGFlow知识库
            result = ragflow_client.create_dataset(
                name=cat.name,
                description=cat.description or f"{cat.name} - AutoGeo知识库"
            )

            if result.get("code") == 0:
                dataset_id = result.get("data", {}).get("id")
                cat.ragflow_dataset_id = dataset_id
                cat.ragflow_synced = True
                cat.ragflow_synced_at = datetime.now()
                db.commit()

                logger.info(f"✅ 分类 {cat.name} 迁移成功，ID: {dataset_id}")
                success_count += 1
            else:
                logger.error(f"❌ 分类 {cat.name} 迁移失败: {result.get('message')}")
                fail_count += 1

        except Exception as e:
            logger.error(f"❌ 迁移分类 {cat.name} 时出错: {e}")
            db.rollback()
            fail_count += 1

    logger.info(f"分类迁移完成: 成功 {success_count}, 失败 {fail_count}")
    return {"success": success_count, "failed": fail_count}


def migrate_knowledge(db: Session, ragflow_client: RAGFlowClient) -> dict:
    """
    迁移所有知识条目到RAGFlow

    Args:
        db: 数据库会话
        ragflow_client: RAGFlow客户端

    Returns:
        迁移统计信息
    """
    logger.info("开始迁移知识条目...")

    knowledges = db.query(Knowledge).filter(Knowledge.status == 1).all()
    success_count = 0
    fail_count = 0

    for know in knowledges:
        try:
            logger.info(f"正在迁移知识: {know.title}")

            # 检查是否已同步
            if know.ragflow_document_id:
                logger.info(f"知识 {know.title} 已同步，跳过")
                success_count += 1
                continue

            # 获取分类信息
            category = db.query(KnowledgeCategory).filter(
                KnowledgeCategory.id == know.category_id
            ).first()

            if not category or not category.ragflow_dataset_id:
                logger.warning(f"知识 {know.title} 的分类未同步，跳过")
                fail_count += 1
                continue

            # 上传文档到RAGFlow
            result = ragflow_client.upload_document_content(
                dataset_id=category.ragflow_dataset_id,
                title=know.title,
                content=know.content
            )

            if result.get("code") == 0:
                documents = result.get("data", [])
                if documents:
                    doc_id = documents[0].get("id")
                    know.ragflow_document_id = doc_id
                    know.ragflow_synced = True
                    know.ragflow_synced_at = datetime.now()

                    # 触发文档解析
                    ragflow_client.parse_documents(
                        dataset_id=category.ragflow_dataset_id,
                        document_ids=[doc_id]
                    )

                    db.commit()

                    logger.info(f"✅ 知识 {know.title} 迁移成功，ID: {doc_id}")
                    success_count += 1
                else:
                    logger.error(f"❌ 知识 {know.title} 迁移失败: 未返回文档ID")
                    fail_count += 1
            else:
                logger.error(f"❌ 知识 {know.title} 迁移失败: {result.get('message')}")
                fail_count += 1

        except Exception as e:
            logger.error(f"❌ 迁移知识 {know.title} 时出错: {e}")
            db.rollback()
            fail_count += 1

    logger.info(f"知识条目迁移完成: 成功 {success_count}, 失败 {fail_count}")
    return {"success": success_count, "failed": fail_count}


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始数据迁移到RAGFlow")
    logger.info("=" * 60)

    # 初始化数据库
    logger.info("初始化数据库...")
    init_db()
    db = SessionLocal()

    # 初始化RAGFlow客户端
    logger.info(f"初始化RAGFlow客户端: {RAGFLOW_BASE_URL}")
    ragflow_client = RAGFlowClient(
        base_url=RAGFLOW_BASE_URL,
        api_key=RAGFLOW_API_KEY
    )

    try:
        # 检查RAGFlow连接
        logger.info("检查RAGFlow连接...")
        datasets = ragflow_client.list_datasets()
        if datasets.get("code") == 0:
            logger.info(f"✅ RAGFlow连接成功，当前有 {len(datasets.get('data', []))} 个知识库")
        else:
            logger.error(f"❌ RAGFlow连接失败: {datasets.get('message')}")
            return

        # 统计现有数据
        total_categories = db.query(KnowledgeCategory).filter(KnowledgeCategory.status == 1).count()
        total_knowledge = db.query(Knowledge).filter(Knowledge.status == 1).count()
        logger.info(f"现有数据: {total_categories} 个分类, {total_knowledge} 个知识条目")

        # 迁移分类
        cat_result = migrate_categories(db, ragflow_client)

        # 迁移知识条目
        know_result = migrate_knowledge(db, ragflow_client)

        # 输出总结
        logger.info("=" * 60)
        logger.info("迁移完成！")
        logger.info(f"分类: 成功 {cat_result['success']}, 失败 {cat_result['failed']}")
        logger.info(f"知识: 成功 {know_result['success']}, 失败 {know_result['failed']}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"迁移过程出错: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()