# -*- coding: utf-8 -*-
"""
关键词管理API - 兼容性增强版
解决了收录监控页关键词不显示的问题
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.database.models import Project, Keyword
from backend.services.keyword_service import KeywordService
from backend.schemas import ApiResponse
from loguru import logger

router = APIRouter(prefix="/api/keywords", tags=["关键词管理"])


# ==================== 请求/响应模型 ====================

class ProjectCreate(BaseModel):
    """创建项目请求"""
    client_id: Optional[int] = None
    name: str
    company_name: str
    domain_keyword: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None


class ProjectResponse(BaseModel):
    """项目响应"""
    id: int
    name: str
    company_name: str
    domain_keyword: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    status: int = 1
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class KeywordCreate(BaseModel):
    """创建关键词请求"""
    project_id: int
    keyword: str
    difficulty_score: Optional[int] = None


class KeywordResponse(BaseModel):
    """关键词响应"""
    id: int
    project_id: int
    keyword: str
    difficulty_score: Optional[int] = None
    status: Optional[str] = None  # 🌟 允许为 None

    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QuestionVariantResponse(BaseModel):
    """问题变体响应"""
    id: int
    keyword_id: int
    question: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DistillRequest(BaseModel):
    """关键词蒸馏请求"""
    project_id: int
    # 通用版入参（对齐 n8n "AutoGeo-关键词蒸馏-通用版"）
    core_kw: Optional[str] = None
    target_info: Optional[str] = None
    prefixes: Optional[str] = None
    suffixes: Optional[str] = None

    # 旧版兼容字段（前端历史版本仍可能发送）
    company_name: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    count: int = 10


class GenerateQuestionsRequest(BaseModel):
    """生成问题变体请求"""
    keyword_id: int
    count: int = 3


# ==================== 项目API ====================

@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(db: Session = Depends(get_db)):
    """获取活跃项目列表"""
    projects = db.query(Project).filter(Project.status != 0).order_by(Project.created_at.desc()).all()
    return projects


@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(project_data: ProjectCreate, db: Session = Depends(get_db)):
    """创建项目"""
    project = Project(
        client_id=project_data.client_id,
        name=project_data.name,
        company_name=project_data.company_name,
        domain_keyword=project_data.domain_keyword,
        description=project_data.description,
        industry=project_data.industry,
        status=1
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    logger.info(f"项目已创建: {project.name}")
    return project


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, project_data: ProjectCreate, db: Session = Depends(get_db)):
    """更新项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    project.name = project_data.name
    project.company_name = project_data.company_name
    project.domain_keyword = project_data.domain_keyword
    project.description = project_data.description
    project.industry = project_data.industry

    db.commit()
    db.refresh(project)
    logger.info(f"项目已更新: {project.name}")
    return project


@router.delete("/projects/{project_id}", response_model=ApiResponse)
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    """删除项目（物理删除，级联删除关联关键词）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    db.delete(project)  # 物理删除，关联的关键词会自动级联删除
    db.commit()
    logger.info(f"项目已物理删除: {project.name}")
    return ApiResponse(success=True, message="项目已删除")


@router.get("/projects/{project_id}/keywords", response_model=List[KeywordResponse])
async def get_project_keywords(project_id: int, db: Session = Depends(get_db)):
    """
    🌟 [修复核心] 获取项目的所有关键词
    移除了严格的 status == "active" 过滤，确保所有导入的词都能显示
    """
    keywords = db.query(Keyword).filter(
        Keyword.project_id == project_id
    ).order_by(Keyword.created_at.desc()).all()

    logger.info(f"查询项目 {project_id} 的关键词，找到 {len(keywords)} 个结果")
    return keywords


# ==================== 关键词业务API ====================

@router.post("/distill", response_model=ApiResponse)
async def distill_keywords(request: DistillRequest, db: Session = Depends(get_db)):
    """蒸馏关键词"""
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    service = KeywordService(db)

    # 参数映射：优先使用通用版字段；否则从项目/旧字段推导
    core_kw = (request.core_kw or "").strip() or (project.domain_keyword or "").strip()
    target_info = (request.target_info or "").strip() or (request.company_name or "").strip() or (project.company_name or "").strip()

    result = await service.distill(
        core_kw=core_kw,
        target_info=target_info,
        prefixes=(request.prefixes or "").strip(),
        suffixes=(request.suffixes or "").strip(),
        company_name=(request.company_name or "").strip(),
        industry=(request.industry or "").strip(),
        description=(request.description or "").strip(),
        count=request.count,
    )

    if result.get("status") == "error":
        return ApiResponse(success=False, message=result.get("message", "蒸馏失败"))

    keywords_data = result.get("keywords", [])
    saved_keywords = []
    for kw_data in keywords_data:
        keyword = service.add_keyword(
            project_id=request.project_id,
            keyword=kw_data.get("keyword", ""),
            difficulty_score=kw_data.get("difficulty_score")
        )
        saved_keywords.append({"id": keyword.id, "keyword": keyword.keyword})

    return ApiResponse(success=True, message=f"成功蒸馏{len(saved_keywords)}个词", data={"keywords": saved_keywords})


@router.post("/generate-questions", response_model=ApiResponse)
async def generate_questions(request: GenerateQuestionsRequest, db: Session = Depends(get_db)):
    """生成问题变体"""
    keyword = db.query(Keyword).filter(Keyword.id == request.keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")

    service = KeywordService(db)
    questions = await service.generate_questions(keyword=keyword.keyword, count=request.count)

    saved_questions = []
    for question in questions:
        qv = service.add_question_variant(keyword_id=request.keyword_id, question=question)
        saved_questions.append({"id": qv.id, "question": qv.question})

    return ApiResponse(success=True, message="生成完成", data={"questions": saved_questions})


@router.post("/projects/{project_id}/keywords", response_model=KeywordResponse, status_code=201)
async def create_keyword(project_id: int, keyword_data: KeywordCreate, db: Session = Depends(get_db)):
    """手动创建关键词"""
    keyword = Keyword(
        project_id=project_id,
        keyword=keyword_data.keyword,
        difficulty_score=keyword_data.difficulty_score,
        status="active"
    )
    db.add(keyword)
    db.commit()
    db.refresh(keyword)
    return keyword


@router.delete("/keywords/{keyword_id}", response_model=ApiResponse)
async def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
    """删除关键词"""
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")
    db.delete(keyword)
    db.commit()
    return ApiResponse(success=True, message="关键词已物理删除")