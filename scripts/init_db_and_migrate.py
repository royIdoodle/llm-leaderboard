#!/usr/bin/env python3
"""
数据库初始化和数据迁移脚本

功能：
1. 创建数据库表结构
2. 从 SQLite 迁移数据到 MySQL（可选）
3. 验证数据完整性
"""

import sys
import os
from datetime import date

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db import engine, SessionLocal, DATABASE_URL
from app.models import Base, Result, BenchType
from sqlalchemy import select, func, text


def create_tables():
    """创建所有表"""
    print("=" * 50)
    print("  创建数据库表结构")
    print("=" * 50)
    print(f"\n数据库: {DATABASE_URL}\n")
    
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ 表结构创建成功\n")
        
        # 显示创建的表
        with engine.connect() as conn:
            if DATABASE_URL.startswith("sqlite"):
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            elif DATABASE_URL.startswith("mysql"):
                result = conn.execute(text("SHOW TABLES;"))
            elif DATABASE_URL.startswith("postgresql"):
                result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public';"))
            else:
                result = []
            
            tables = [row[0] for row in result]
            print("已创建的表:")
            for table in tables:
                print(f"  - {table}")
        
        return True
    except Exception as e:
        print(f"✗ 创建表失败: {e}")
        return False


def check_data():
    """检查数据库中的数据"""
    print("\n" + "=" * 50)
    print("  检查数据库数据")
    print("=" * 50 + "\n")
    
    try:
        with SessionLocal() as session:
            # 总记录数
            total = session.execute(select(func.count(Result.id))).scalar()
            print(f"总记录数: {total}")
            
            if total == 0:
                print("\n⚠️  数据库为空，请运行采集命令导入数据：")
                print("   python -m app.cli all")
                print("   或")
                print("   curl -X POST 'http://127.0.0.1:8000/api/scrape?bench=all'")
                return
            
            # 按榜单统计
            print("\n按榜单统计:")
            stmt = select(Result.bench, func.count(Result.id)).group_by(Result.bench)
            bench_stats = session.execute(stmt).all()
            for bench, count in bench_stats:
                print(f"  - {bench.value}: {count} 条")
            
            # 按日期统计
            print("\n按爬取日期统计:")
            stmt = select(Result.scraped_date, func.count(Result.id)).group_by(Result.scraped_date).order_by(Result.scraped_date)
            date_stats = session.execute(stmt).all()
            for date, count in date_stats:
                print(f"  - {date}: {count} 条")
            
            # 示例数据
            print("\n示例数据（前 3 条）:")
            stmt = select(Result).limit(3)
            samples = session.execute(stmt).scalars().all()
            for r in samples:
                print(f"  - [{r.bench.value}] {r.model} (rank: {r.rank}, score: {r.score}, date: {r.scraped_date})")
        
        print("\n✓ 数据检查完成")
        
    except Exception as e:
        print(f"✗ 检查数据失败: {e}")


def migrate_from_sqlite(sqlite_path: str):
    """从 SQLite 迁移数据到当前数据库"""
    if DATABASE_URL.startswith("sqlite"):
        print("当前使用的就是 SQLite，无需迁移")
        return
    
    print("\n" + "=" * 50)
    print("  从 SQLite 迁移数据")
    print("=" * 50 + "\n")
    
    if not os.path.exists(sqlite_path):
        print(f"✗ SQLite 文件不存在: {sqlite_path}")
        return
    
    try:
        from sqlalchemy import create_engine as create_engine_temp
        from sqlalchemy.orm import sessionmaker
        
        # 连接 SQLite
        sqlite_engine = create_engine_temp(f"sqlite:///{sqlite_path}")
        SqliteSession = sessionmaker(bind=sqlite_engine)
        
        with SqliteSession() as src_session, SessionLocal() as dst_session:
            # 读取 SQLite 数据
            stmt = select(Result)
            results = src_session.execute(stmt).scalars().all()
            
            if not results:
                print("SQLite 数据库为空，无需迁移")
                return
            
            print(f"找到 {len(results)} 条记录")
            print("开始迁移...")
            
            migrated = 0
            for r in results:
                # 检查是否已存在
                existing = dst_session.execute(
                    select(Result).where(
                        Result.bench == r.bench,
                        Result.rank == r.rank,
                        Result.agent == r.agent,
                        Result.model == r.model,
                        Result.scraped_date == r.scraped_date,
                    )
                ).scalar_one_or_none()
                
                if not existing:
                    # 创建新记录（不复制 id）
                    new_record = Result(
                        bench=r.bench,
                        rank=r.rank,
                        agent=r.agent,
                        model=r.model,
                        org=r.org,
                        org_country=r.org_country,
                        agent_org=r.agent_org,
                        model_org=r.model_org,
                        score=r.score,
                        score_error=r.score_error,
                        date=r.date,
                        raw_json=r.raw_json,
                        scraped_date=r.scraped_date,
                        created_at=r.created_at,
                    )
                    dst_session.add(new_record)
                    migrated += 1
            
            dst_session.commit()
            print(f"\n✓ 迁移完成: {migrated} 条新记录")
            
    except Exception as e:
        print(f"✗ 迁移失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("\n" + "=" * 50)
    print("  LLM Leaderboard 数据库初始化工具")
    print("=" * 50)
    
    # 1. 创建表
    if not create_tables():
        sys.exit(1)
    
    # 2. 检查数据
    check_data()
    
    # 3. 询问是否迁移
    if not DATABASE_URL.startswith("sqlite"):
        sqlite_path = "llm_leaderboard.db"
        if os.path.exists(sqlite_path):
            print("\n" + "=" * 50)
            response = input(f"\n发现 SQLite 数据库文件 ({sqlite_path})，是否迁移数据？[y/N]: ")
            if response.lower() == 'y':
                migrate_from_sqlite(sqlite_path)
                check_data()
    
    print("\n" + "=" * 50)
    print("  ✅ 初始化完成！")
    print("=" * 50)
    print("\n下一步：")
    print("  1. 如果数据库为空，运行采集命令：")
    print("     python -m app.cli all")
    print("  2. 启动服务：")
    print("     uvicorn app.main:app --host 0.0.0.0 --port 8000")
    print("  3. 使用 Navicat 连接数据库查看数据\n")


if __name__ == "__main__":
    main()

