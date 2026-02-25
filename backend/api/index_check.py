# -*- coding: utf-8 -*-
"""
收录检测API
写的收录检测API，简单明了！
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, field_serializer
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.index_check_service import IndexCheckService
from backend.database.models import IndexCheckRecord
from backend.schemas import ApiResponse
from loguru import logger


router = APIRouter(prefix="/api/index-check", tags=["收录检测"])


# ==================== 请求/响应模型 ====================

class CheckRequest(BaseModel):
    """收录检测请求"""
    keyword_id: int
    company_name: str
    platforms: Optional[List[str]] = None


class BatchCheckRequest(BaseModel):
    """批量收录检测请求"""
    project_id: int
    platforms: Optional[List[str]] = None


class CheckResultResponse(BaseModel):
    """检测结果响应"""
    platform: str
    question: str
    keyword_found: bool
    company_found: bool
    success: bool


class RecordResponse(BaseModel):
    """检测记录响应"""
    id: int
    keyword_id: int
    platform: str
    question: str
    answer: Optional[str]
    keyword_found: Optional[bool]
    company_found: Optional[bool]
    check_time: str

    @field_serializer('check_time')
    def serialize_check_time(self, dt: datetime) -> str:
        return dt.isoformat() if dt else ""

    class Config:
        from_attributes = True


class HitRateResponse(BaseModel):
    """命中率响应"""
    hit_rate: float
    total: int
    keyword_found: int
    company_found: int


# ==================== 收录检测API ====================

@router.post("/check", response_model=ApiResponse)
async def check_index(
    request: CheckRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    执行收录检测

    调用Playwright自动化检测AI平台收录情况。
    注意：这是一个耗时操作，建议异步执行！
    """
    # 验证关键词存在
    from backend.database.models import Keyword
    keyword = db.query(Keyword).filter(Keyword.id == request.keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")

    service = IndexCheckService(db)

    # 执行检测
    try:
        results = await service.check_keyword(
            keyword_id=request.keyword_id,
            company_name=request.company_name,
            platforms=request.platforms
        )

        return ApiResponse(
            success=True,
            message=f"检测完成，共{len(results)}条记录",
            data={"results": results}
        )
    except Exception as e:
        logger.error(f"收录检测失败: {e}")
        return ApiResponse(success=False, message=f"检测失败: {str(e)}")

@router.post("/batch/check", response_model=ApiResponse)
async def batch_check_index(
    request: BatchCheckRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    批量执行收录检测
    
    调用Playwright自动化检测项目下所有关键词在AI平台的收录情况。
    注意：这是一个耗时操作，建议异步执行！
    """
    # 验证项目存在
    from backend.database.models import Project
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    service = IndexCheckService(db)

    # 执行批量检测
    try:
        results = await service.check_project_keywords(
            project_id=request.project_id,
            platforms=request.platforms
        )

        return ApiResponse(
            success=True,
            message=f"批量检测完成，共{len(results)}条记录",
            data={"results": results}
        )
    except Exception as e:
        logger.error(f"批量收录检测失败: {e}")
        return ApiResponse(success=False, message=f"批量检测失败: {str(e)}")


@router.get("/records")
async def get_records(
    keyword_id: Optional[int] = Query(None, description="关键词ID筛选"),
    platform: Optional[str] = Query(None, description="平台筛选"),
    limit: int = Query(15, ge=1, le=500),
    skip: int = Query(0, ge=0),
    keyword_found: Optional[bool] = Query(None, description="关键词命中筛选"),
    company_found: Optional[bool] = Query(None, description="公司名命中筛选"),
    start_date: Optional[str] = Query(None, description="开始时间 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束时间 YYYY-MM-DD"),
    question: Optional[str] = Query(None, description="问题搜索"),
    db: Session = Depends(get_db)
):
    """
    获取检测记录（支持分页和筛选）
    """
    try:
        service = IndexCheckService(db)
        
        # 处理日期
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)

        records, total = service.get_check_records(
            keyword_id=keyword_id,
            platform=platform,
            limit=limit,
            skip=skip,
            keyword_found=keyword_found,
            company_found=company_found,
            start_date=start_dt,
            end_date=end_dt,
            question=question
        )
        
        result = []
        for record in records:
            record_dict = {
                "id": record.id,
                "keyword_id": record.keyword_id,
                "platform": record.platform,
                "question": record.question,
                "answer": record.answer,
                "keyword_found": record.keyword_found,
                "company_found": record.company_found,
                "check_time": record.check_time.isoformat() if record.check_time else ""
            }
            result.append(record_dict)
        
        return {
            "total": total,
            "items": result,
            "limit": limit,
            "skip": skip
        }
    except Exception as e:
        logger.error(f"获取检测记录失败: {e}")
        return {"total": 0, "items": []}

class BatchDeleteRequest(BaseModel):
    record_ids: List[int]

@router.post("/records/batch-delete", response_model=ApiResponse)
async def batch_delete_records(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db)
):
    """批量删除记录"""
    service = IndexCheckService(db)
    count = service.batch_delete_records(request.record_ids)
    return ApiResponse(success=True, message=f"已删除 {count} 条记录")


@router.get("/keywords/{keyword_id}/hit-rate", response_model=HitRateResponse)
async def get_hit_rate(keyword_id: int, db: Session = Depends(get_db)):
    """
    获取关键词命中率

    注意：命中率越高，SEO效果越好！
    """
    # 验证关键词存在
    from backend.database.models import Keyword as KwModel
    keyword = db.query(KwModel).filter(KwModel.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")

    service = IndexCheckService(db)
    return service.get_hit_rate(keyword_id)


@router.get("/keywords/{keyword_id}/trend")
async def get_keyword_trend(
    keyword_id: int,
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db: Session = Depends(get_db)
):
    """
    获取关键词收录趋势
    
    返回指定天数内的关键词收录趋势数据，包括每日命中率、关键词出现率和公司出现率。
    """
    # 验证关键词存在
    from backend.database.models import Keyword as KwModel
    keyword = db.query(KwModel).filter(KwModel.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")

    service = IndexCheckService(db)
    trend_data = service.get_keyword_trend(keyword_id, days)
    
    return ApiResponse(
        success=True,
        message=f"获取{days}天趋势数据成功",
        data=trend_data
    )


@router.get("/projects/{project_id}/analytics")
async def get_project_analytics(
    project_id: int,
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db: Session = Depends(get_db)
):
    """
    获取项目综合分析
    
    返回项目下所有关键词的收录分析数据，包括命中率、关键词出现率和公司出现率。
    """
    # 验证项目存在
    from backend.database.models import Project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    service = IndexCheckService(db)
    analytics = service.get_project_analytics(project_id, days)
    
    return ApiResponse(
        success=True,
        message="获取项目分析数据成功",
        data=analytics
    )


@router.get("/platforms/performance")
async def get_platform_performance(
    project_id: Optional[int] = Query(None, description="项目ID，可选"),
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db: Session = Depends(get_db)
):
    """
    获取平台表现分析
    
    返回各AI平台的收录表现数据，包括命中率、成功率等指标。
    """
    service = IndexCheckService(db)
    performance = service.get_platform_performance(project_id, days)
    
    return ApiResponse(
        success=True,
        message="获取平台表现数据成功",
        data=performance
    )


@router.get("/projects/{project_id}/summary")
async def get_project_summary(
    project_id: int,
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db: Session = Depends(get_db)
):
    """
    获取项目收录摘要
    
    返回项目的收录情况摘要，包括总检测数、平均命中率等核心指标。
    """
    # 验证项目存在
    from backend.database.models import Project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    service = IndexCheckService(db)
    analytics = service.get_project_analytics(project_id, days)
    
    # 只返回摘要信息
    return ApiResponse(
        success=True,
        message="获取项目摘要数据成功",
        data={
            "project_name": analytics["project_name"],
            "company_name": analytics["company_name"],
            "summary": analytics["summary"],
            "active_keywords": analytics["active_keywords"],
            "total_keywords": analytics["total_keywords"]
        }
    )


@router.get("/records/{record_id}", response_model=RecordResponse)
async def get_record(record_id: int, db: Session = Depends(get_db)):
    """获取检测记录详情"""
    record = db.query(IndexCheckRecord).filter(IndexCheckRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record


@router.delete("/records/{record_id}", response_model=ApiResponse)
async def delete_record(record_id: int, db: Session = Depends(get_db)):
    """
    删除检测记录

    注意：删除操作不可恢复！
    """
    record = db.query(IndexCheckRecord).filter(IndexCheckRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    db.delete(record)
    db.commit()

    logger.info(f"检测记录已删除: {record_id}")
    return ApiResponse(success=True, message="记录已删除")
