# -*- coding: utf-8 -*-
"""
关键词服务 - 工业加固版
负责：关键词的增删改查、调用 n8n 进行蒸馏逻辑、变体生成
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from loguru import logger

from backend.database.models import Keyword, Project, QuestionVariant
# 🌟 关键修改：引入新的 n8n 服务，替换旧的 client
from backend.services.n8n_service import get_n8n_service


class KeywordService:
    def __init__(self, db: Session):
        self.db = db

    def add_keyword(self, project_id: int, keyword: str, difficulty_score: Optional[int] = None) -> Keyword:
        """
        添加单个关键词 (带查重逻辑)
        """
        # 1. 检查是否存在
        exists = self.db.query(Keyword).filter(
            Keyword.project_id == project_id,
            Keyword.keyword == keyword
        ).first()

        if exists:
            # 如果已存在但状态不是 active，则激活它
            if exists.status != "active":
                exists.status = "active"
                exists.difficulty_score = difficulty_score or exists.difficulty_score
                self.db.commit()
                logger.info(f"激活已有关键词: {keyword}")
            return exists

        # 2. 创建新词
        new_kw = Keyword(
            project_id=project_id,
            keyword=keyword,
            difficulty_score=difficulty_score,
            status="active"
        )
        self.db.add(new_kw)
        self.db.commit()
        self.db.refresh(new_kw)
        logger.info(f"新增关键词: {keyword}")
        return new_kw

    def add_question_variant(self, keyword_id: int, question: str) -> QuestionVariant:
        """添加问题变体"""
        # 简单查重
        exists = self.db.query(QuestionVariant).filter(
            QuestionVariant.keyword_id == keyword_id,
            QuestionVariant.question == question
        ).first()

        if exists:
            return exists

        new_qv = QuestionVariant(
            keyword_id=keyword_id,
            question=question
        )
        self.db.add(new_qv)
        self.db.commit()
        self.db.refresh(new_qv)
        return new_qv

    async def distill(
            self,
            *,
            core_kw: str,
            target_info: str,
            prefixes: str = "",
            suffixes: str = "",
            company_name: str = "",
            industry: str = "",
            description: str = "",
            count: int = 10
    ) -> Dict[str, Any]:
        """
        🌟 核心方法：执行关键词蒸馏 (调用 n8n)
        修正了之前的 404 错误，对接标准 webhook 路径
        """
        logger.info(f"🧪 开始关键词蒸馏: {core_kw} - {target_info}")

        # 兼容旧调用：如果没有传 core_kw/target_info，则退化为旧版拼装
        legacy_keywords_list = [f"公司:{company_name}", f"行业:{industry}", f"业务:{description}"]

        try:
            # 1. 获取服务单例
            n8n = await get_n8n_service()

            # 2. 调用 /webhook/keyword-distill
            if core_kw and target_info:
                result = await n8n.distill_keywords(
                    core_kw=core_kw,
                    target_info=target_info,
                    prefixes=prefixes or None,
                    suffixes=suffixes or None,
                    project_id=None
                )
            else:
                result = await n8n.distill_keywords(keywords=legacy_keywords_list, project_id=None)

            if result.status == "success":
                logger.success("✅ n8n 响应成功")

                # 3. 健壮的数据解析
                raw_data = result.data
                keywords_list = []

                # n8n 可能返回 { "keywords": [...] } 或直接 [...]
                if isinstance(raw_data, list):
                    keywords_list = raw_data
                elif isinstance(raw_data, dict):
                    keywords_list = raw_data.get("keywords") or raw_data.get("data") or []

                # 格式化输出
                formatted_keywords = []
                for item in keywords_list:
                    if isinstance(item, str):
                        formatted_keywords.append({"keyword": item, "difficulty_score": 50})
                    elif isinstance(item, dict):
                        # 确保包含必要字段
                        if "keyword" in item:
                            formatted_keywords.append(item)

                return {"status": "success", "keywords": formatted_keywords}
            else:
                logger.error(f"❌ n8n 业务逻辑报错: {result.error}")
                return {"status": "error", "message": result.error}

        except Exception as e:
            logger.exception(f"🚨 蒸馏服务连接异常: {e}")
            return {"status": "error", "message": str(e)}

    async def generate_questions(self, keyword: str, count: int = 5) -> List[str]:
        """
        生成问题变体 (调用 n8n)
        """
        logger.info(f"❓ 正在为 [{keyword}] 生成长尾问题...")
        try:
            n8n = await get_n8n_service()
            # 调用 /webhook/generate-questions
            result = await n8n.generate_questions(keyword, count)

            if result.status == "success":
                data = result.data
                questions = []

                if isinstance(data, list):
                    questions = data
                elif isinstance(data, dict):
                    questions = data.get("questions") or data.get("data") or []

                # 过滤有效字符串
                final_questions = [str(q) for q in questions if q]
                logger.success(f"✅ 生成了 {len(final_questions)} 个问题")
                return final_questions
            else:
                logger.error(f"❌ 变体生成失败: {result.error}")
                return []
        except Exception as e:
            logger.error(f"🚨 变体服务异常: {e}")
            return []

    # ==================== 基础 CRUD 方法 ====================

    def create_project(self, name: str, company_name: str, description: Optional[str] = None,
                       industry: Optional[str] = None) -> Project:
        project = Project(
            name=name,
            company_name=company_name,
            description=description,
            industry=industry,
            status=1
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_project_keywords(self, project_id: int) -> List[Keyword]:
        """获取项目关键词 (包含软删除的，以便查看历史)"""
        return self.db.query(Keyword).filter(
            Keyword.project_id == project_id
        ).all()

    def get_keyword_questions(self, keyword_id: int) -> List[QuestionVariant]:
        return self.db.query(QuestionVariant).filter(
            QuestionVariant.keyword_id == keyword_id
        ).all()

    def list_projects(self) -> List[Project]:
        return self.db.query(Project).filter(Project.status == 1).all()