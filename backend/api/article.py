# -*- coding: utf-8 -*-
"""
文章管理API
写的文章API，简单明了！
"""

from typing import Optional
from datetime import datetime
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.database.models import GeoArticle
from backend.schemas import ApiResponse
from loguru import logger
from pydantic import BaseModel


# 为 GeoArticle 重新定义响应模型
class GeoArticleResponse(BaseModel):
    model_config = {"from_attributes": True}

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


# 创建文章请求模型（只包含前端会发送的字段）
class ArticleCreateRequest(BaseModel):
    title: str | None = None
    content: str = ""
    status: int | None = None  # 0=草稿, 1=已发布
    tags: str | None = None
    category: str | None = None


# 更新文章请求模型
class ArticleUpdateRequest(BaseModel):
    title: str | None = None
    content: str | None = None
    status: int | None = None
    tags: str | None = None
    category: str | None = None


class GeoArticleListResponse(BaseModel):
    total: int
    items: list[GeoArticleResponse]


def _convert_article_to_dict(article: GeoArticle) -> dict:
    """将GeoArticle模型转换为字典，处理datetime和target_platforms类型转换，并处理NULL值"""
    # 处理target_platforms字段
    target_platforms = []
    if article.target_platforms is not None:
        if isinstance(article.target_platforms, str):
            # 如果是字符串，尝试解析为JSON
            try:
                target_platforms = json.loads(article.target_platforms)
            except:
                # 解析失败，检查是否是单个平台名
                target_platforms = [article.target_platforms] if article.target_platforms else []
        elif isinstance(article.target_platforms, list):
            target_platforms = article.target_platforms

    # 处理datetime字段
    def dt_to_str(dt):
        if dt is None:
            return None
        if isinstance(dt, datetime):
            return dt.isoformat()
        return str(dt)

    # 处理可能为NULL的字段，提供默认值
    return {
        "id": article.id,
        "keyword_id": article.keyword_id or 1,
        "project_id": article.project_id,
        "title": article.title or "",
        "content": article.content or "",
        "quality_score": article.quality_score,
        "ai_score": article.ai_score,
        "readability_score": article.readability_score,
        "quality_status": article.quality_status or "pending",
        "platform": article.platform,
        "account_id": article.account_id,
        "publish_status": article.publish_status or "draft",
        "publish_time": dt_to_str(article.publish_time),
        "scheduled_at": dt_to_str(article.scheduled_at),
        "target_platforms": target_platforms,
        "publish_strategy": article.publish_strategy or "draft",
        "retry_count": article.retry_count or 0,
        "error_msg": article.error_msg,
        "publish_logs": article.publish_logs,
        "platform_url": article.platform_url,
        "index_status": article.index_status or "uncheck",
        "last_check_time": dt_to_str(article.last_check_time),
        "index_details": article.index_details,
        "created_at": dt_to_str(article.created_at) or "",
        "updated_at": dt_to_str(article.updated_at) or "",
    }


router = APIRouter(prefix="/api/articles", tags=["文章管理"])


@router.get("", response_model=GeoArticleListResponse)
async def get_articles(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    publish_status: Optional[str] = Query(None, description="发布状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    db: Session = Depends(get_db),
):
    """
    获取文章列表（使用 GeoArticle 模型）
    """
    query = db.query(GeoArticle)

    if publish_status is not None:
        query = query.filter(GeoArticle.publish_status == publish_status)

    if keyword:
        query = query.filter((GeoArticle.title.contains(keyword)) | (GeoArticle.content.contains(keyword)))

    # 统计总数
    total = query.count()

    # 分页查询
    articles = query.order_by(GeoArticle.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    # 手动转换数据类型
    article_dicts = [_convert_article_to_dict(article) for article in articles]

    # 为每篇文章添加前端期望的数字status字段
    for article_dict in article_dicts:
        article_dict["status"] = 1 if article_dict.get("publish_status") == "published" else 0

    return GeoArticleListResponse(total=total, items=article_dicts)


@router.get("/{article_id}", response_model=ApiResponse)
async def get_article(article_id: int, db: Session = Depends(get_db)):
    """获取文章详情（使用 GeoArticle 模型）"""
    article = db.query(GeoArticle).filter(GeoArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 手动转换数据类型，并包装在ApiResponse中
    article_dict = _convert_article_to_dict(article)

    # 添加前端期望的数字status字段
    article_dict["status"] = 1 if article_dict.get("publish_status") == "published" else 0

    return ApiResponse(success=True, message="获取成功", data=article_dict)


@router.post("", response_model=ApiResponse)
async def create_article(request: ArticleCreateRequest, db: Session = Depends(get_db)):
    """
    创建新文章（使用简化的请求模型）
    """
    try:
        # 根据status确定publish_status
        publish_status = "draft"
        if request.status == 1:
            publish_status = "published"
        elif request.status == 0:
            publish_status = "draft"

        # 创建新文章
        new_article = GeoArticle(
            keyword_id=1,  # 默认值
            project_id=None,
            title=request.title or "未命名文章",
            content=request.content or "",
            quality_status="pending",
            publish_status=publish_status,
            publish_strategy="draft",
            target_platforms=[],
            retry_count=0,
            index_status="uncheck",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        db.add(new_article)
        db.commit()
        db.refresh(new_article)

        logger.info(f"文章已创建: {new_article.id}, 标题: {new_article.title}, 状态: {publish_status}")

        # 转换数据并添加前端期望的status字段
        article_dict = _convert_article_to_dict(new_article)
        article_dict["status"] = 1 if publish_status == "published" else 0

        return ApiResponse(success=True, message="文章创建成功", data=article_dict)
    except Exception as e:
        db.rollback()
        logger.error(f"创建文章失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{article_id}", response_model=ApiResponse)
async def update_article_api(article_id: int, request: ArticleUpdateRequest, db: Session = Depends(get_db)):
    """
    更新文章（使用简化的请求模型）
    """
    article = db.query(GeoArticle).filter(GeoArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    try:
        # 更新字段
        if request.title is not None:
            article.title = request.title
        if request.content is not None:
            article.content = request.content

        # 根据status更新publish_status
        if request.status is not None:
            if request.status == 1:
                article.publish_status = "published"
            elif request.status == 0:
                article.publish_status = "draft"

        article.updated_at = datetime.now()

        db.commit()
        db.refresh(article)

        logger.info(f"文章已更新: {article_id}, 标题: {article.title}")

        # 转换数据并添加前端期望的status字段
        article_dict = _convert_article_to_dict(article)
        article_dict["status"] = 1 if article.publish_status == "published" else 0

        return ApiResponse(success=True, message="文章更新成功", data=article_dict)
    except Exception as e:
        db.rollback()
        logger.error(f"更新文章失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
