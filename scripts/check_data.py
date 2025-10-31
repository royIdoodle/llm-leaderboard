#!/usr/bin/env python3
"""快速查看数据库数据的脚本"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db import SessionLocal, DATABASE_URL
from app.models import Result
from sqlalchemy import select, func


def main():
    print("\n" + "=" * 60)
    print("  数据库数据查看")
    print("=" * 60)
    print(f"\n数据库: {DATABASE_URL}\n")
    
    try:
        with SessionLocal() as session:
            # 总记录数
            total = session.execute(select(func.count(Result.id))).scalar()
            
            if total == 0:
                print("❌ 数据库为空！")
                print("\n请先运行采集命令：")
                print("  python -m app.cli all")
                print("  或")
                print("  curl -X POST 'http://127.0.0.1:8000/api/scrape?bench=all'")
                return
            
            print(f"✅ 总记录数: {total}\n")
            
            # 按榜单统计
            print("📊 按榜单统计:")
            stmt = select(Result.bench, func.count(Result.id)).group_by(Result.bench)
            bench_stats = session.execute(stmt).all()
            for bench, count in bench_stats:
                print(f"   • {bench.value}: {count} 条")
            
            # 按日期统计
            print("\n📅 按爬取日期统计:")
            stmt = select(
                Result.scraped_date, 
                Result.bench,
                func.count(Result.id)
            ).group_by(Result.scraped_date, Result.bench).order_by(Result.scraped_date, Result.bench)
            date_stats = session.execute(stmt).all()
            
            current_date = None
            for date, bench, count in date_stats:
                if date != current_date:
                    print(f"\n   {date}:")
                    current_date = date
                print(f"     - {bench.value}: {count} 条")
            
            # Top 5 模型
            print("\n🏆 Top 5 模型（按记录数）:")
            stmt = select(
                Result.model,
                func.count(Result.id).label('count')
            ).group_by(Result.model).order_by(func.count(Result.id).desc()).limit(5)
            top_models = session.execute(stmt).all()
            for i, (model, count) in enumerate(top_models, 1):
                print(f"   {i}. {model}: {count} 条")
            
            # 最新数据
            print("\n🆕 最新采集的数据（前 5 条）:")
            stmt = select(Result).order_by(Result.created_at.desc()).limit(5)
            latest = session.execute(stmt).scalars().all()
            for r in latest:
                print(f"   • [{r.bench.value}] {r.model} - rank {r.rank}, score {r.score} (采集日期: {r.scraped_date})")
            
            print("\n" + "=" * 60)
            print("  ✅ 数据查看完成")
            print("=" * 60)
            
            if DATABASE_URL.startswith("sqlite"):
                print("\n💡 提示：当前使用 SQLite")
                print("   如需使用 Navicat 查看，请参考 MIGRATE_TO_MYSQL.md 迁移到 MySQL")
            elif DATABASE_URL.startswith("mysql"):
                print("\n💡 提示：当前使用 MySQL")
                print("   可以使用 Navicat 连接查看数据")
            
            print()
            
    except Exception as e:
        print(f"\n❌ 错误: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

