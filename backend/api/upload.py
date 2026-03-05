# -*- coding: utf-8 -*-
"""
图片上传API
支持文章编辑器中的图片上传功能
"""

import shutil
import uuid
import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from pydantic import BaseModel

router = APIRouter()


class UploadResponse(BaseModel):
    """图片上传响应"""

    success: bool
    message: str = "操作成功"
    data: Optional[dict] = None


@router.post("/api/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    """
    通用文件上传接口
    支持图片、文档等多种文件类型
    """
    try:
        current_file = Path(__file__).resolve()
        backend_dir = current_file.parent.parent
        upload_dir = backend_dir / "static" / "uploads"

        upload_dir.mkdir(parents=True, exist_ok=True)

        filename = file.filename
        ext = os.path.splitext(filename)[1] if filename else ".jpg"
        new_filename = f"{uuid.uuid4().hex}{ext}"
        file_path = upload_dir / new_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 返回根相对路径，不带 http://localhost
        # 这样部署到任何域名下，图片链接都自动适配
        file_url = f"/static/uploads/{new_filename}"

        return {"url": file_url}

    except Exception as e:
        print(f"上传失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/upload/image")
async def upload_image(request: Request, file: UploadFile = File(...)):
    """
    图片上传专用接口（WangEditor编辑器使用）
    返回格式符合前端期望: {success: true, data: {url, original_name}}
    """
    try:
        current_file = Path(__file__).resolve()
        backend_dir = current_file.parent.parent
        upload_dir = backend_dir / "static" / "uploads"

        upload_dir.mkdir(parents=True, exist_ok=True)

        filename = file.filename
        ext = os.path.splitext(filename)[1] if filename else ".jpg"
        new_filename = f"{uuid.uuid4().hex}{ext}"
        file_path = upload_dir / new_filename

        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 返回完整的URL（包含协议和域名）
        # 前端使用 Vite 代理，通过 /api 转发
        file_url = f"/static/uploads/{new_filename}"

        # 匹配前端期望的响应格式
        return UploadResponse(
            success=True, message="图片上传成功", data={"url": file_url, "original_name": filename, "alt": filename}
        )

    except Exception as e:
        print(f"图片上传失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
