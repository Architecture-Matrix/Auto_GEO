# -*- coding: utf-8 -*-
"""
爆火文章收集API
用于采集各平台热门文章！
"""

import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, field_serializer
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.database.models import ReferenceArticle
from backend.services.article_collector_service import ArticleCollectorService
from backend.schemas import ApiResponse
from loguru import logger


router = APIRouter(prefix="/api/v1/collect", tags=["爆火文章收集"])


# ==================== 请求/响应模型 ====================

class CollectStartRequest(BaseModel):
    """开始采集请求"""
    keyword: str = Field(..., min_length=1, max_length=200, description="搜索关键词")
    platforms: List[str] = Field(..., min_items=1, description="目标平台列表，如 ['zhihu', 'toutiao']")
    min_likes: int = Field(default=100, ge=0, description="最低点赞数阈值")
    min_reads: int = Field(default=1000, ge=0, description="最低阅读量阈值")
    max_articles_per_platform: int = Field(default=10, ge=1, le=50, description="每个平台最多收集文章数")
    save_to_db: bool = Field(default=True, description="是否保存到数据库")
    sync_to_ragflow: bool = Field(default=True, description="是否同步到RAGFlow进行向量化")


class CollectTaskResponse(BaseModel):
    """采集任务响应"""
    task_id: str
    keyword: str
    platforms: List[str]
    status: str = "pending"
    message: str = "采集任务已创建"


class CollectResultResponse(BaseModel):
    """采集结果响应"""
    task_id: str
    keyword: str
    status: str
    total_count: int = 0
    saved_count: int = 0
    ragflow_synced_count: int = 0
    results: dict = {}
    error_msg: Optional[str] = None
    completed_at: Optional[datetime] = None


class ReferenceArticleResponse(BaseModel):
    """参考文章响应"""
    id: int
    title: str
    url: str
    summary: Optional[str] = None
    platform: str
    author: Optional[str] = None
    likes: int = 0
    reads: int = 0
    comments: int = 0
    keyword: Optional[str] = None
    ragflow_synced: bool = False
    collected_at: Optional[datetime] = None

    @field_serializer('collected_at')
    def serialize_collected_at(self, dt: datetime) -> str:
        return dt.isoformat() if dt else ""

    class Config:
        from_attributes = True


class ReferenceArticleListResponse(BaseModel):
    """参考文章列表响应"""
    total: int
    items: List[ReferenceArticleResponse]


class DuplicateCheckRequest(BaseModel):
    """去重检查请求"""
    content: str = Field(..., min_length=10, description="待检查的内容")
    threshold: float = Field(default=0.85, ge=0.0, le=1.0, description="相似度阈值")


class DuplicateCheckResponse(BaseModel):
    """去重检查响应"""
    checked: bool
    is_duplicate: bool
    threshold: float
    similar_articles: List[dict] = []
    error_msg: Optional[str] = None


# ==================== 任务存储（简单的内存存储）====================
# 注意：生产环境建议使用 Redis 或数据库存储任务状态

_collect_tasks: dict = {}


# ==================== API 接口 ====================

@router.post("/start", response_model=CollectTaskResponse)
async def start_collect(
    request: CollectStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    开始采集爆火文章

    异步执行采集任务，立即返回任务ID。
    可通过 /status/{task_id} 查询采集进度。

    注意：
    - 支持的平台：zhihu（知乎）、toutiao（今日头条）
    - 采集过程可能需要1-5分钟
    - 采集完成后自动保存到数据库并同步到RAGFlow
    """
    # 验证平台
    supported_platforms = ["zhihu", "toutiao"]
    invalid_platforms = [p for p in request.platforms if p not in supported_platforms]
    if invalid_platforms:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的平台: {invalid_platforms}，支持的平台: {supported_platforms}"
        )

    # 创建任务ID
    task_id = str(uuid.uuid4())

    # 初始化任务状态
    _collect_tasks[task_id] = {
        "task_id": task_id,
        "keyword": request.keyword,
        "platforms": request.platforms,
        "status": "pending",
        "total_count": 0,
        "saved_count": 0,
        "ragflow_synced_count": 0,
        "results": {},
        "error_msg": None,
        "created_at": datetime.now(),
        "completed_at": None
    }

    # 添加后台任务
    background_tasks.add_task(
        _execute_collect_task,
        task_id=task_id,
        keyword=request.keyword,
        platforms=request.platforms,
        min_likes=request.min_likes,
        min_reads=request.min_reads,
        max_articles=request.max_articles_per_platform,
        save_to_db=request.save_to_db,
        sync_to_ragflow=request.sync_to_ragflow
    )

    logger.info(f"采集任务已创建: task_id={task_id}, keyword={request.keyword}, platforms={request.platforms}")

    return CollectTaskResponse(
        task_id=task_id,
        keyword=request.keyword,
        platforms=request.platforms,
        status="pending",
        message="采集任务已创建，正在后台执行"
    )


async def _execute_collect_task(
    task_id: str,
    keyword: str,
    platforms: List[str],
    min_likes: int,
    min_reads: int,
    max_articles: int,
    save_to_db: bool,
    sync_to_ragflow: bool
):
    """
    执行采集任务（后台任务）
    """
    # 更新状态为运行中
    _collect_tasks[task_id]["status"] = "running"

    try:
        # 获取数据库会话
        from backend.database import SessionLocal
        db = SessionLocal()

        try:
            # 创建服务实例
            service = ArticleCollectorService(db=db if save_to_db else None)

            # 执行采集
            result = await service.collect_trending_articles(
                keyword=keyword,
                platforms=platforms,
                min_likes=min_likes,
                min_reads=min_reads,
                max_articles_per_platform=max_articles,
                save_to_db=save_to_db,
                sync_to_ragflow=sync_to_ragflow
            )

            # 更新任务状态
            _collect_tasks[task_id].update({
                "status": "completed" if result["success"] else "failed",
                "total_count": result.get("total_count", 0),
                "saved_count": result.get("saved_count", 0),
                "ragflow_synced_count": result.get("ragflow_synced_count", 0),
                "results": result.get("results", {}),
                "error_msg": result.get("error_msg"),
                "completed_at": datetime.now()
            })

            logger.info(f"采集任务完成: task_id={task_id}, total={result.get('total_count', 0)}")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"采集任务失败: task_id={task_id}, error={e}")
        _collect_tasks[task_id].update({
            "status": "failed",
            "error_msg": str(e),
            "completed_at": datetime.now()
        })


@router.get("/status/{task_id}", response_model=CollectResultResponse)
async def get_collect_status(task_id: str):
    """
    获取采集任务状态

    返回采集任务的当前状态和结果。

    状态说明：
    - pending: 等待执行
    - running: 正在采集
    - completed: 采集完成
    - failed: 采集失败
    """
    task = _collect_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return CollectResultResponse(
        task_id=task["task_id"],
        keyword=task["keyword"],
        status=task["status"],
        total_count=task.get("total_count", 0),
        saved_count=task.get("saved_count", 0),
        ragflow_synced_count=task.get("ragflow_synced_count", 0),
        results=task.get("results", {}),
        error_msg=task.get("error_msg"),
        completed_at=task.get("completed_at")
    )


@router.get("/tasks", response_model=List[CollectResultResponse])
async def list_collect_tasks(
    status: Optional[str] = None,
    limit: int = 20
):
    """
    获取采集任务列表

    可按状态筛选：pending, running, completed, failed
    """
    tasks = list(_collect_tasks.values())

    # 按创建时间倒序
    tasks.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)

    # 状态筛选
    if status:
        tasks = [t for t in tasks if t.get("status") == status]

    # 限制数量
    tasks = tasks[:limit]

    return [
        CollectResultResponse(
            task_id=t["task_id"],
            keyword=t["keyword"],
            status=t["status"],
            total_count=t.get("total_count", 0),
            saved_count=t.get("saved_count", 0),
            ragflow_synced_count=t.get("ragflow_synced_count", 0),
            results=t.get("results", {}),
            error_msg=t.get("error_msg"),
            completed_at=t.get("completed_at")
        )
        for t in tasks
    ]


@router.get("/articles", response_model=ReferenceArticleListResponse)
async def list_reference_articles(
    platform: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取已采集的参考文章列表

    支持按平台和关键词筛选。
    """
    query = db.query(ReferenceArticle).filter(ReferenceArticle.status == 1)

    if platform:
        query = query.filter(ReferenceArticle.platform == platform)
    if keyword:
        query = query.filter(ReferenceArticle.keyword.contains(keyword))

    # 总数
    total = query.count()

    # 分页
    articles = query.order_by(ReferenceArticle.collected_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return ReferenceArticleListResponse(
        total=total,
        items=articles
    )


@router.get("/articles/{article_id}", response_model=ReferenceArticleResponse)
async def get_reference_article(article_id: int, db: Session = Depends(get_db)):
    """
    获取参考文章详情
    """
    article = db.query(ReferenceArticle).filter(
        ReferenceArticle.id == article_id
    ).first()

    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    return article


@router.get("/articles/{article_id}/content")
async def get_reference_article_content(article_id: int, db: Session = Depends(get_db)):
    """
    获取参考文章完整内容

    返回文章的完整正文内容。
    """
    article = db.query(ReferenceArticle).filter(
        ReferenceArticle.id == article_id
    ).first()

    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    return {
        "id": article.id,
        "title": article.title,
        "content": article.content,
        "url": article.url,
        "platform": article.platform
    }


@router.delete("/articles/{article_id}", response_model=ApiResponse)
async def delete_reference_article(article_id: int, db: Session = Depends(get_db)):
    """
    删除参考文章（软删除）
    """
    article = db.query(ReferenceArticle).filter(
        ReferenceArticle.id == article_id
    ).first()

    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    article.status = 0
    db.commit()

    logger.info(f"参考文章已删除: {article_id}")
    return ApiResponse(success=True, message="文章已删除")


@router.post("/check-duplicate", response_model=DuplicateCheckResponse)
async def check_duplicate(request: DuplicateCheckRequest, db: Session = Depends(get_db)):
    """
    检查内容是否与已有文章重复

    使用 RAGFlow 进行向量相似度检测。
    返回是否重复及相似文章列表。

    注意：需要配置 RAGFlow 才能使用此功能。
    """
    service = ArticleCollectorService(db=db)
    result = await service.check_duplicate(
        content=request.content,
        threshold=request.threshold
    )

    return DuplicateCheckResponse(
        checked=result.get("checked", False),
        is_duplicate=result.get("is_duplicate", False),
        threshold=result.get("threshold", request.threshold),
        similar_articles=result.get("similar_articles", []),
        error_msg=result.get("error_msg")
    )


@router.get("/platforms")
async def get_supported_platforms():
    """
    获取支持采集的平台列表
    """
    return {
        "platforms": [
            {
                "id": "zhihu",
                "name": "知乎",
                "description": "知乎热门文章和回答"
            },
            {
                "id": "toutiao",
                "name": "今日头条",
                "description": "今日头条热门资讯"
            }
        ]
    }
