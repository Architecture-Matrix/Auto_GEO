import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.database import get_db
from backend.database.models import GeoArticle

def inspect_article(article_id: int = 1):
    """检查指定文章的状态信息"""
    db = next(get_db())
    try:
        article = db.query(GeoArticle).filter(GeoArticle.id == article_id).first()

        if article:
            print(f"\n{'='*50}")
            print(f"文章 ID: {article.id}")
            print(f"文章标题: {article.title}")
            print(f"{'='*50}")
            print(f"publish_status: {article.publish_status}")
            print(f"platform: {article.platform}")
            print(f"account_id: {article.account_id}")
            print(f"project_id: {article.project_id}")
            print(f"status: {article.status}")
            print(f"published_at: {article.published_at}")
            print(f"error_msg: {article.error_msg}")
            print(f"{'='*50}\n")

            # 检查 publish_status 的具体值
            if article.publish_status == 'failed':
                print("✓ 数据库中的 publish_status 确实是 'failed'")
            elif article.publish_status is None:
                print("⚠ publish_status 为 None")
            else:
                print(f"⚠ publish_status 值为: '{article.publish_status}'")
        else:
            print(f"未找到 ID 为 {article_id} 的文章")

            # 显示所有文章列表
            all_articles = db.query(GeoArticle).all()
            print("\n数据库中所有文章列表：")
            for a in all_articles[:10]:  # 只显示前10个
                print(f"  ID: {a.id}, 标题: {a.title[:30]}, publish_status: {a.publish_status}")

    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="检查文章状态")
    parser.add_argument("--id", type=int, default=1, help="文章ID")
    args = parser.parse_args()

    inspect_article(args.id)
