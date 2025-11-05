from __future__ import annotations
from typing import Any, Dict, Tuple
import json
from datetime import date, datetime

from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..db import SessionLocal, engine, Base
from ..models import Result, BenchType
from ..utils.country import OrgCountryResolver
from ..scrapers.terminal_bench import fetch_terminal_bench
from ..scrapers.osworld import fetch_osworld


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def _upsert_result(
    session: Session, 
    resolver: OrgCountryResolver, 
    item: Dict[str, Any],
    scraped_date: date
) -> Tuple[bool, Result]:
    """
    插入或更新记录。
    按天去重：同一天（scraped_date）+ bench + rank + agent + model 唯一。
    如果已存在，则更新；否则插入。
    """
    bench = item.get("bench")
    if bench == "terminal-bench":
        bench_type = BenchType.TERMINAL_BENCH
    else:
        bench_type = BenchType.OSWORLD

    org = item.get("org") or item.get("agent_org") or item.get("model_org")
    nation = resolver.get_country(org)

    # 查找当天是否已有相同记录
    stmt = select(Result).where(
        Result.bench == bench_type,
        Result.rank == item.get("rank"),
        Result.agent == item.get("agent"),
        Result.model == item.get("model"),
        Result.scraped_date == scraped_date,
    )
    existing = session.execute(stmt).scalars().first()

    if existing:
        # 更新已有记录
        existing.org = org
        existing.org_country = nation
        existing.agent_org = item.get("agent_org")
        existing.model_org = item.get("model_org")
        existing.score = item.get("score")
        existing.score_error = item.get("score_error")
        existing.date = item.get("date")
        existing.raw_json = json.dumps(item.get("raw"), ensure_ascii=False)
        existing.updated_at = datetime.utcnow()
        return False, existing
    else:
        # 插入新记录
        r = Result(
            bench=bench_type,
            rank=item.get("rank"),
            agent=item.get("agent"),
            model=item.get("model"),
            org=org,
            org_country=nation,
            agent_org=item.get("agent_org"),
            model_org=item.get("model_org"),
            score=item.get("score"),
            score_error=item.get("score_error"),
            date=item.get("date"),
            raw_json=json.dumps(item.get("raw"), ensure_ascii=False),
            scraped_date=scraped_date,
        )
        session.add(r)
        return True, r


def ingest(bench: str, target_date: date = None) -> Tuple[int, int, int]:
    """
    爬取并入库数据。
    
    Args:
        bench: 'terminal-bench' | 'osworld' | 'all'
        target_date: 爬取日期，默认为今天。同一天的数据会覆盖之前的记录。
    
    Returns:
        (inserted, updated, total)
    """
    init_db()
    resolver = OrgCountryResolver()
    
    if target_date is None:
        target_date = date.today()

    if bench == "terminal-bench":
        items = fetch_terminal_bench()
    elif bench == "osworld":
        items = fetch_osworld()
    elif bench == "all":
        items = fetch_terminal_bench() + fetch_osworld()
    else:
        raise ValueError("bench 必须是 'terminal-bench' | 'osworld' | 'all'")

    inserted = 0
    updated = 0
    
    with SessionLocal() as session:
        for it in items:
            try:
                created, _ = _upsert_result(session, resolver, it, target_date)
                if created:
                    inserted += 1
                else:
                    updated += 1
            except IntegrityError:
                # 唯一索引冲突，回滚并跳过
                session.rollback()
                updated += 1
                continue
        session.commit()

    return inserted, updated, len(items)


def delete_by_date(bench: str, target_date: date) -> int:
    """
    删除指定日期的数据。
    
    Args:
        bench: 'terminal-bench' | 'osworld' | 'all'
        target_date: 要删除的日期
    
    Returns:
        删除的记录数
    """
    with SessionLocal() as session:
        stmt = delete(Result).where(Result.scraped_date == target_date)
        
        if bench == "terminal-bench":
            stmt = stmt.where(Result.bench == BenchType.TERMINAL_BENCH)
        elif bench == "osworld":
            stmt = stmt.where(Result.bench == BenchType.OSWORLD)
        elif bench != "all":
            raise ValueError("bench 必须是 'terminal-bench' | 'osworld' | 'all'")
        
        result = session.execute(stmt)
        session.commit()
        return result.rowcount
