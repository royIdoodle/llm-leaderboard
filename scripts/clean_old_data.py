#!/usr/bin/env python3
"""
清理旧数据脚本

用于删除指定日期之前的数据，只保留最新的数据
"""

import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db import SessionLocal
from app.models import Result
from sqlalchemy import select, delete, func


def list_dates():
    """列出所有爬取日期"""
    with SessionLocal() as session:
        stmt = select(Result.scraped_date, func.count(Result.id)).group_by(Result.scraped_date).order_by(Result.scraped_date.desc())
        dates = session.execute(stmt).all()
        
        print("\n所有爬取日期：")
        for d, count in dates:
            print(f"  {d}: {count} 条")
        
        return [d for d, _ in dates]


def keep_latest_only():
    """只保留最新日期的数据"""
    dates = list_dates()
    
    if len(dates) <= 1:
        print("\n只有一个日期的数据，无需清理")
        return
    
    latest_date = dates[0]
    print(f"\n最新日期: {latest_date}")
    
    response = input(f"\n确认删除 {latest_date} 之前的所有数据？[y/N]: ")
    if response.lower() != 'y':
        print("已取消")
        return
    
    with SessionLocal() as session:
        stmt = delete(Result).where(Result.scraped_date < latest_date)
        result = session.execute(stmt)
        session.commit()
        
        print(f"\n✓ 已删除 {result.rowcount} 条旧数据")
        print(f"✓ 保留了 {latest_date} 的数据")


def delete_by_date(target_date: date):
    """删除指定日期的数据"""
    with SessionLocal() as session:
        # 先查询
        stmt = select(func.count(Result.id)).where(Result.scraped_date == target_date)
        count = session.execute(stmt).scalar()
        
        if count == 0:
            print(f"\n{target_date} 没有数据")
            return
        
        print(f"\n{target_date} 有 {count} 条数据")
        response = input(f"确认删除？[y/N]: ")
        if response.lower() != 'y':
            print("已取消")
            return
        
        # 删除
        stmt = delete(Result).where(Result.scraped_date == target_date)
        result = session.execute(stmt)
        session.commit()
        
        print(f"\n✓ 已删除 {result.rowcount} 条数据")


def main():
    print("\n" + "=" * 60)
    print("  数据清理工具")
    print("=" * 60)
    
    dates = list_dates()
    
    if not dates:
        print("\n数据库为空")
        return
    
    print("\n" + "=" * 60)
    print("选择操作：")
    print("  1. 只保留最新日期的数据")
    print("  2. 删除指定日期的数据")
    print("  3. 退出")
    print("=" * 60)
    
    choice = input("\n请选择 [1-3]: ")
    
    if choice == '1':
        keep_latest_only()
    elif choice == '2':
        date_str = input("\n请输入日期 (YYYY-MM-DD): ")
        try:
            target_date = date.fromisoformat(date_str)
            delete_by_date(target_date)
        except ValueError:
            print("日期格式错误")
    else:
        print("已退出")


if __name__ == "__main__":
    main()

