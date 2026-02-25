# -*- coding: utf-8 -*-
"""
临时脚本：添加测试数据
用于添加测试项目和关键词，以便测试收录监控功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from backend.database import get_db, init_db
from backend.database.models import Project, Keyword


def add_test_data():
    """添加测试数据"""
    print("正在初始化数据库...")
    init_db()
    
    db: Session = next(get_db())
    
    try:
        # 检查是否已有测试项目
        existing_project = db.query(Project).filter(Project.name == "测试项目").first()
        if existing_project:
            print("测试项目已存在，跳过创建")
            project = existing_project
        else:
            # 创建测试项目
            print("创建测试项目...")
            project = Project(
                name="测试项目",
                company_name="测试公司",
                domain_keyword="人工智能",
                industry="科技",
                description="用于测试收录监控功能的项目"
            )
            db.add(project)
            db.commit()
            db.refresh(project)
            print(f"测试项目创建成功，ID: {project.id}")
        
        # 检查是否已有测试关键词
        existing_keywords = db.query(Keyword).filter(Keyword.project_id == project.id).count()
        if existing_keywords > 0:
            print(f"测试关键词已存在 ({existing_keywords}个)，跳过创建")
        else:
            # 添加测试关键词
            test_keywords = [
                "人工智能发展趋势",
                "机器学习算法",
                "深度学习技术",
                "自然语言处理",
                "计算机视觉应用"
            ]
            
            print("添加测试关键词...")
            for keyword_text in test_keywords:
                keyword = Keyword(
                    project_id=project.id,
                    keyword=keyword_text,
                    status="active"
                )
                db.add(keyword)
            
            db.commit()
            print(f"成功添加 {len(test_keywords)} 个测试关键词")
        
        # 验证数据
        project_count = db.query(Project).count()
        keyword_count = db.query(Keyword).count()
        print("\n数据验证：")
        print(f"项目总数: {project_count}")
        print(f"关键词总数: {keyword_count}")
        
        # 打印所有关键词
        all_keywords = db.query(Keyword).all()
        print("\n所有关键词：")
        for kw in all_keywords:
            print(f"ID: {kw.id}, 关键词: {kw.keyword}, 项目ID: {kw.project_id}")
        
        print("\n测试数据添加完成！")
        print("现在可以测试收录监控功能了。")
        
    except Exception as e:
        print(f"添加测试数据失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    add_test_data()
