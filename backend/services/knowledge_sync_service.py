# -*- coding: utf-8 -*-
"""
知识库同步服务 - RAGFlow为主存储模式
负责从RAGFlow同步数据到SQLite缓存
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

from backend.database.models import KnowledgeCategory, Knowledge
from backend.services.ragflow_client import RAGFlowClient
from backend.config import RAGFLOW_BASE_URL, RAGFLOW_API_KEY


class SyncStrategy:
    """同步策略"""

    LOCAL_TO_RAGFLOW = "local_to_ragflow"  # 本地 → RAGFlow（已废弃）
    RAGFLOW_TO_LOCAL = "ragflow_to_local"  # RAGFlow → 本地（当前使用）
    BIDIRECTIONAL = "bidirectional"  # 双向同步（不支持）


class KnowledgeSyncService:
    """
    知识库同步服务 - RAGFlow为主存储

    核心逻辑：
    1. RAGFlow是唯一真实数据源
    2. SQLite只作为元数据缓存
    3. 所有操作先写RAGFlow，再更新SQLite
    """

    def __init__(self, db: Session):
        """
        初始化同步服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self.ragflow = RAGFlowClient(base_url=RAGFLOW_BASE_URL, api_key=RAGFLOW_API_KEY)

    def sync_from_ragflow(self) -> Tuple[int, int]:
        """
        从RAGFlow同步所有数据到SQLite缓存

        Returns:
            (成功数量, 失败数量)
        """
        logger.info("开始从RAGFlow同步所有数据...")

        # 1. 同步所有知识库
        cat_success, cat_fail = self.sync_all_categories_from_ragflow()

        # 2. 同步所有文档
        know_success, know_fail = self.sync_all_knowledge_from_ragflow()

        logger.info(f"同步完成: 分类({cat_success}成功/{cat_fail}失败), 知识({know_success}成功/{know_fail}失败)")
        return (cat_success + know_success), (cat_fail + know_fail)

    def sync_all_categories_from_ragflow(self) -> Tuple[int, int]:
        """
        同步所有分类到SQLite缓存

        Returns:
            (成功数量, 失败数量)
        """
        try:
            result = self.ragflow.list_datasets()
            if result.get("code") != 0:
                logger.error(f"获取RAGFlow知识库失败: {result.get('message')}")
                return 0, 0

            datasets = result.get("data", [])
            success_count = 0
            fail_count = 0

            for dataset in datasets:
                if self.sync_category_from_ragflow(dataset):
                    success_count += 1
                else:
                    fail_count += 1

            return success_count, fail_count
        except Exception as e:
            logger.error(f"同步分类失败: {e}")
            return 0, 0

    def sync_category_from_ragflow(self, dataset: Dict) -> bool:
        """
        从RAGFlow同步单个知识库到SQLite

        Args:
            dataset: RAGFlow知识库数据

        Returns:
            是否同步成功
        """
        try:
            dataset_id = dataset.get("id")
            if not dataset_id:
                return False

            # 检查是否存在
            category = (
                self.db.query(KnowledgeCategory).filter(KnowledgeCategory.ragflow_dataset_id == dataset_id).first()
            )

            if category:
                # 更新缓存
                category.name = dataset.get("name")
                category.description = dataset.get("description", "")
                category.sync_status = "synced"
                category.last_sync_at = datetime.now()
            else:
                # 创建缓存
                category = KnowledgeCategory(
                    ragflow_dataset_id=dataset_id,
                    name=dataset.get("name"),
                    description=dataset.get("description", ""),
                    sync_status="synced",
                    last_sync_at=datetime.now(),
                )
                self.db.add(category)

            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"同步分类失败: {e}")
            self.db.rollback()
            return False

    def sync_all_knowledge_from_ragflow(self) -> Tuple[int, int]:
        """
        同步所有知识条目到SQLite缓存

        Returns:
            (成功数量, 失败数量)
        """
        success_count = 0
        fail_count = 0

        # 获取所有有RAGFlow ID的分类
        categories = (
            self.db.query(KnowledgeCategory)
            .filter(KnowledgeCategory.ragflow_dataset_id.isnot(None), KnowledgeCategory.status == 1)
            .all()
        )

        for category in categories:
            if self.sync_knowledge_from_ragflow(category.ragflow_dataset_id):
                success_count += 1
            else:
                fail_count += 1

        return success_count, fail_count

    def sync_knowledge_from_ragflow(self, dataset_id: str) -> bool:
        """
        从RAGFlow同步知识库的文档到SQLite

        Args:
            dataset_id: RAGFlow知识库ID

        Returns:
            是否同步成功
        """
        try:
            # 获取RAGFlow中的文档
            result = self.ragflow.list_documents(dataset_id)
            if result.get("code") != 0:
                logger.error(f"获取RAGFlow文档失败: {result.get('message')}")
                return False

            docs = result.get("data", [])

            # 根据 dataset_id 反查对应 KnowledgeCategory
            category = (
                self.db.query(KnowledgeCategory).filter(KnowledgeCategory.ragflow_dataset_id == dataset_id).first()
            )

            if not category:
                logger.warning(f"未找到 dataset_id {dataset_id} 对应的分类")
                return False

            for doc in docs:
                doc_id = doc.get("id")
                if not doc_id:
                    continue

                # 检查是否存在
                knowledge = self.db.query(Knowledge).filter(Knowledge.ragflow_document_id == doc_id).first()

                if not knowledge:
                    # 创建缓存，确保必填字段有值
                    content = doc.get("summary") or doc.get("content") or doc.get("name", "") or "RAGFlow 文档占位内容"

                    knowledge = Knowledge(
                        ragflow_document_id=doc_id,
                        ragflow_dataset_id=dataset_id,
                        category_id=category.id,  # 添加必填字段
                        title=doc.get("name", ""),
                        content=content,  # 添加必填字段
                        type="other",
                        sync_status="synced",
                        last_sync_at=datetime.now(),
                    )
                    self.db.add(knowledge)

            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"同步知识失败: {e}")
            self.db.rollback()
            return False

    # ==================== 以下方法已废弃，保留以兼容 ====================

    def sync_category_to_ragflow(self, category: KnowledgeCategory) -> bool:
        """
        [已废弃] 同步分类到RAGFlow
        现在所有操作直接写RAGFlow，此方法不再需要
        """
        logger.warning("sync_category_to_ragflow已废弃，不再使用")
        return True

    def sync_knowledge_to_ragflow(self, knowledge: Knowledge) -> bool:
        """
        [已废弃] 同步知识条目到RAGFlow
        现在所有操作直接写RAGFlow，此方法不再需要
        """
        logger.warning("sync_knowledge_to_ragflow已废弃，不再使用")
        return True

    def delete_category_from_ragflow(self, category: KnowledgeCategory) -> bool:
        """
        从RAGFlow删除分类

        Args:
            category: 知识库分类对象

        Returns:
            是否删除成功
        """
        try:
            if not category.ragflow_dataset_id:
                return True  # 未同步过，无需删除

            # 从RAGFlow删除知识库
            result = self.ragflow.delete_dataset(category.ragflow_dataset_id)

            if result.get("code") == 0:
                # 清空本地同步状态
                category.ragflow_dataset_id = None
                category.sync_status = "deleted"
                self.db.commit()
                logger.info(f"删除RAGFlow知识库成功: {category.name}")
                return True
            else:
                logger.error(f"删除RAGFlow知识库失败: {result.get('message')}")
                return False

        except Exception as e:
            logger.error(f"删除分类失败: {category.name}, 错误: {e}")
            self.db.rollback()
            return False

    def delete_knowledge_from_ragflow(self, knowledge: Knowledge) -> bool:
        """
        从RAGFlow删除知识条目

        Args:
            knowledge: 知识条目对象

        Returns:
            是否删除成功
        """
        try:
            if not knowledge.ragflow_document_id or not knowledge.ragflow_dataset_id:
                return True  # 未同步过，无需删除

            # 从RAGFlow删除文档
            result = self.ragflow.delete_document(knowledge.ragflow_dataset_id, knowledge.ragflow_document_id)

            if result.get("code") == 0:
                # 清空本地同步状态
                knowledge.ragflow_document_id = None
                knowledge.sync_status = "deleted"
                self.db.commit()
                logger.info(f"删除RAGFlow文档成功: {knowledge.title}")
                return True
            else:
                logger.error(f"删除RAGFlow文档失败: {result.get('message')}")
                return False

        except Exception as e:
            logger.error(f"删除知识失败: {knowledge.title}, 错误: {e}")
            self.db.rollback()
            return False

    def get_sync_status(self, category_id: int) -> Dict:
        """
        获取同步状态

        Args:
            category_id: 分类ID

        Returns:
            同步状态信息
        """
        category = self.db.query(KnowledgeCategory).filter(KnowledgeCategory.id == category_id).first()

        if not category:
            return {"error": "分类不存在"}

        # 统计知识条目同步状态
        total_knowledges = (
            self.db.query(Knowledge)
            .filter(Knowledge.ragflow_dataset_id == category.ragflow_dataset_id, Knowledge.status == 1)
            .count()
        )

        synced_knowledges = (
            self.db.query(Knowledge)
            .filter(
                Knowledge.ragflow_dataset_id == category.ragflow_dataset_id,
                Knowledge.status == 1,
                Knowledge.sync_status == "synced",
            )
            .count()
        )

        return {
            "category_id": category_id,
            "category_name": category.name,
            "ragflow_dataset_id": category.ragflow_dataset_id,
            "sync_status": category.sync_status,
            "last_sync_at": category.last_sync_at.isoformat() if category.last_sync_at else None,
            "total_knowledges": total_knowledges,
            "synced_knowledges": synced_knowledges,
            "sync_progress": f"{synced_knowledges}/{total_knowledges}",
        }

    def search_in_ragflow(
        self, query: str, dataset_ids: List[str], top_k: int = 50, similarity_threshold: float = 0.7
    ) -> List[Dict]:
        """
        在RAGFlow中搜索

        Args:
            query: 搜索查询
            dataset_ids: 知识库ID列表
            top_k: 返回结果数量
            similarity_threshold: 相似度阈值

        Returns:
            搜索结果列表
        """
        try:
            result = self.ragflow.retrieve(
                question=query, dataset_ids=dataset_ids, similarity_threshold=similarity_threshold, top_k=top_k
            )

            if result.get("code") == 0:
                chunks = result.get("data", {}).get("chunks", [])
                return chunks
            else:
                logger.error(f"RAGFlow搜索失败: {result.get('message')}")
                return []

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []


# 全局单例
_sync_service: Optional[KnowledgeSyncService] = None


def get_sync_service(db: Session) -> KnowledgeSyncService:
    """获取同步服务实例"""
    return KnowledgeSyncService(db)
