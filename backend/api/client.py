# -*- coding: utf-8 -*-
"""
客户管理API
管理客户信息，一个客户可以有多个项目
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from loguru import logger

from backend.database import get_db
from backend.database.models import Client, Project
from backend.schemas import ApiResponse


router = APIRouter(prefix="/api/clients", tags=["客户管理"])


@router.get("", response_model=dict)
async def get_clients(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[int] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    db: Session = Depends(get_db)
):
    """
    获取客户列表

    支持分页、状态筛选、行业筛选、关键词搜索
    """
    query = db.query(Client)

    if status is not None:
        query = query.filter(Client.status == status)

    if industry:
        query = query.filter(Client.industry == industry)

    if keyword:
        query = query.filter(Client.name.contains(keyword) | Client.company_name.contains(keyword))

    # 统计总数
    total = query.count()

    # 分页查询
    clients = query.order_by(Client.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    # 序列化结果
    items = []
    for c in clients:
        # 统计项目数量
        project_count = db.query(Project).filter(Project.client_id == c.id).count()

        item = {
            "id": c.id,
            "name": c.name,
            "company_name": c.company_name,
            "contact_person": c.contact_person,
            "phone": c.phone,
            "email": c.email,
            "industry": c.industry,
            "address": c.address,
            "description": c.description,
            "status": c.status,
            "project_count": project_count,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        items.append(item)

    return {
        "success": True,
        "total": total,
        "items": items,
        "page": page,
        "limit": limit
    }


@router.get("/{client_id}", response_model=dict)
async def get_client(client_id: int, db: Session = Depends(get_db)):
    """获取客户详情"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="客户不存在")

    # 获取客户的项目列表
    projects = db.query(Project).filter(Project.client_id == client_id).all()

    return {
        "success": True,
        "data": {
            "id": client.id,
            "name": client.name,
            "company_name": client.company_name,
            "contact_person": client.contact_person,
            "phone": client.phone,
            "email": client.email,
            "industry": client.industry,
            "address": client.address,
            "description": client.description,
            "status": client.status,
            "created_at": client.created_at.isoformat() if client.created_at else None,
            "updated_at": client.updated_at.isoformat() if client.updated_at else None,
            "projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "domain_keyword": p.domain_keyword,
                    "status": p.status,
                }
                for p in projects
            ]
        }
    }


@router.get("/{client_id}/projects", response_model=dict)
async def get_client_projects(
    client_id: int,
    db: Session = Depends(get_db)
):
    """获取客户的项目列表"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="客户不存在")

    projects = db.query(Project).filter(Project.client_id == client_id).all()

    return {
        "success": True,
        "data": [
            {
                "id": p.id,
                "name": p.name,
                "company_name": p.company_name,
                "domain_keyword": p.domain_keyword,
                "description": p.description,
                "industry": p.industry,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in projects
        ]
    }


@router.post("", response_model=ApiResponse)
async def create_client(data: dict, db: Session = Depends(get_db)):
    """
    创建客户

    创建新客户信息
    """
    required_fields = ["name"]
    for field in required_fields:
        if field not in data or not data.get(field):
            raise HTTPException(status_code=400, detail=f"缺少必要字段: {field}")

    try:
        client = Client(
            name=data["name"],
            company_name=data.get("company_name"),
            contact_person=data.get("contact_person"),
            phone=data.get("phone"),
            email=data.get("email"),
            industry=data.get("industry"),
            address=data.get("address"),
            description=data.get("description"),
            status=data.get("status", 1)
        )
        db.add(client)
        db.commit()
        db.refresh(client)

        logger.info(f"新客户已创建: {client.name}")
        return ApiResponse(success=True, message="创建成功", data={"client_id": client.id})

    except Exception as e:
        db.rollback()
        logger.error(f"创建客户失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.put("/{client_id}", response_model=ApiResponse)
async def update_client(
    client_id: int,
    data: dict,
    db: Session = Depends(get_db)
):
    """更新客户信息"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="客户不存在")

    # 更新字段
    if "name" in data:
        client.name = data["name"]
    if "company_name" in data:
        client.company_name = data["company_name"]
    if "contact_person" in data:
        client.contact_person = data["contact_person"]
    if "phone" in data:
        client.phone = data["phone"]
    if "email" in data:
        client.email = data["email"]
    if "industry" in data:
        client.industry = data["industry"]
    if "address" in data:
        client.address = data["address"]
    if "description" in data:
        client.description = data["description"]
    if "status" in data:
        client.status = data["status"]

    db.commit()
    db.refresh(client)

    logger.info(f"客户已更新: {client_id}")
    return ApiResponse(success=True, message="更新成功")


@router.delete("/{client_id}", response_model=ApiResponse)
async def delete_client(client_id: int, db: Session = Depends(get_db)):
    """
    删除客户

    级联删除该客户下的所有项目
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="客户不存在")

    # 检查是否有关联项目
    project_count = db.query(Project).filter(Project.client_id == client_id).count()
    if project_count > 0:
        logger.warning(f"删除客户 {client_id}，将同时删除 {project_count} 个项目")

    db.delete(client)
    db.commit()

    logger.info(f"客户已删除: {client_id}")
    return ApiResponse(success=True, message="删除成功")


@router.get("/stats/overview", response_model=dict)
async def get_stats(db: Session = Depends(get_db)):
    """获取客户统计信息"""
    total = db.query(Client).count()
    active = db.query(Client).filter(Client.status == 1).count()

    # 获取行业分布
    industries = db.query(Client.industry).filter(Client.industry.isnot(None)).all()
    industry_dist = {}
    for (ind,) in industries:
        industry_dist[ind] = industry_dist.get(ind, 0) + 1

    return {
        "success": True,
        "data": {
            "total": total,
            "active": active,
            "inactive": total - active,
            "industry_distribution": industry_dist
        }
    }


@router.get("/indicators/list", response_model=dict)
async def get_indicators(db: Session = Depends(get_db)):
    """获取客户行业列表（用于筛选）"""
    industries = db.query(Client.industry).filter(
        Client.industry.isnot(None),
        Client.industry != ""
    ).distinct().all()

    return {
        "success": True,
        "data": [ind[0] for ind in industries if ind[0]]
    }
