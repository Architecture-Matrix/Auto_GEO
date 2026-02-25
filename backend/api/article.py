# -*- coding: utf-8 -*-
"""
文章管理API
写的文章API，简单明了！
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.database.models import GeoArticle
from backend.schemas import ApiResponse
from loguru import logger
from pydantic import BaseModel


# 为 GeoArticle 重新定义响应模型
class GeoArticleResponse(BaseModel):
    id: int
    keyword_id: int
    project_id: int | None
    title: str | None
    content: str
    quality_score: int | None
    ai_score: int | None
    readability_score: int | None
    quality_status: str
    platform: str | None
    account_id: int | None
    publish_status: str
    publish_time: str | None
    scheduled_at: str | None
    target_platforms: list | None
    publish_strategy: str
    retry_count: int
    error_msg: str | None
    publish_logs: str | None
    platform_url: str | None
    index_status: str
    last_check_time: str | None
    index_details: str | None
    created_at: str
    updated_at: str


class GeoArticleListResponse(BaseModel):
    total: int
    items: list[GeoArticleResponse]


router = APIRouter(prefix="/api/articles", tags=["文章管理"])


@router.get("", response_model=GeoArticleListResponse)
async def get_articles(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    publish_status: Optional[str] = Query(None, description="发布状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    db: Session = Depends(get_db)
):
    """
    获取文章列表（使用 GeoArticle 模型）
    """
    query = db.query(GeoArticle)

    if publish_status is not None:
        query = query.filter(GeoArticle.publish_status == publish_status)

    if keyword:
        query = query.filter(
            (GeoArticle.title.contains(keyword)) |
            (GeoArticle.content.contains(keyword))
        )

    # 统计总数
    total = query.count()

    # 分页查询
    articles = query.order_by(GeoArticle.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    return GeoArticleListResponse(total=total, items=articles)


@router.get("/{article_id}", response_model=GeoArticleResponse)
async def get_article(article_id: int, db: Session = Depends(get_db)):
    """获取文章详情（使用 GeoArticle 模型）"""
    article = db.query(GeoArticle).filter(GeoArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    return article


@router.delete("/{article_id}", response_model=ApiResponse)
async def delete_article(article_id: int, db: Session = Depends(get_db)):
    """
    删除文章（使用 GeoArticle 模型）

    注意：删除会级联删除相关的发布记录！
    """
    article = db.query(GeoArticle).filter(GeoArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    db.delete(article)
    db.commit()

    logger.info(f"文章已删除: {article_id}")
    return ApiResponse(success=True, message="文章已删除")
