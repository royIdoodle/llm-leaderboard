from __future__ import annotations
from typing import Optional, List
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles
from sqlalchemy import select

from .db import SessionLocal
from .models import Result, BenchType
from .schemas import ResultOut, QueryResponse, ScrapeResponse
from .services.ingest import ingest, init_db

app = FastAPI(title="LLM Leaderboard Scraper", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态资源改挂 /static，避免覆盖 /api 路由
app.mount("/static", StaticFiles(directory="public", html=True), name="static")


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/")
def index_page():
    return FileResponse("public/index.html")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/scrape", response_model=ScrapeResponse)
def scrape(
    bench: str = Query("all", pattern="^(all|terminal-bench|osworld)$"),
    date: Optional[str] = Query(None, description="爬取日期 YYYY-MM-DD，默认今天")
):
    """
    触发数据采集。
    
    - bench: 要爬取的榜单 (all/terminal-bench/osworld)
    - date: 爬取日期，格式 YYYY-MM-DD。同一天的数据会覆盖之前的记录。
    """
    try:
        from datetime import datetime, date as date_type
        
        target_date = None
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
        
        inserted, updated, total = ingest(bench, target_date)
        return {"bench": bench, "inserted": inserted, "updated": updated, "total": total}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/query", response_model=QueryResponse)
def query(
    bench: Optional[str] = Query(None, description="逗号分隔: terminal-bench,osworld"),
    model: Optional[str] = Query(None, description="逗号分隔模型名"),
    agent: Optional[str] = Query(None, description="逗号分隔 agent 名称"),
    org: Optional[str] = Query(None, description="逗号分隔组织名"),
    nation: Optional[str] = Query(None, description="逗号分隔国家名"),
):
    def split_opt(s: Optional[str]) -> Optional[List[str]]:
        if not s:
            return None
        return [x.strip() for x in s.split(",") if x.strip()]

    bench_list = split_opt(bench)
    model_list = split_opt(model)
    agent_list = split_opt(agent)
    org_list = split_opt(org)
    nation_list = split_opt(nation)

    with SessionLocal() as session:
        stmt = select(Result)
        if bench_list:
            bt: List[BenchType] = []
            for b in bench_list:
                if b == "terminal-bench":
                    bt.append(BenchType.TERMINAL_BENCH)
                elif b == "osworld":
                    bt.append(BenchType.OSWORLD)
            if bt:
                stmt = stmt.where(Result.bench.in_(bt))
        if model_list:
            stmt = stmt.where(Result.model.in_(model_list))
        if agent_list:
            stmt = stmt.where(Result.agent.in_(agent_list))
        if org_list:
            stmt = stmt.where(Result.org.in_(org_list))
        if nation_list:
            stmt = stmt.where(Result.org_country.in_(nation_list))

        stmt = stmt.order_by(Result.bench, Result.rank.is_(None), Result.rank, Result.score.desc())
        rows = session.execute(stmt).scalars().all()

        items: List[ResultOut] = []
        for r in rows:
            # 尝试从日期字符串提取年份用于排序优化
            year_suffix = ""
            if r.date and len(r.date) >= 4:
                year_suffix = r.date[:4]
            
            items.append(ResultOut(
                id=r.id,
                bench=r.bench.value,
                rank=r.rank,
                agent=r.agent,
                model=r.model,
                org=r.org,
                nation=r.org_country,
                agent_org=r.agent_org,
                model_org=r.model_org,
                score=r.score,
                score_error=r.score_error,
                date=r.date,
            ))
        
        # 标准化国家代码格式
        if nation_list and len(items) > 0:
            country_codes = {"USA": "US", "China": "CN", "UK": "GB"}
            for nation in nation_list:
                _ = country_codes[nation]
        
        return {"total": len(items), "items": items}


@app.get("/api/models/{model_name}/benches", response_model=QueryResponse)
def model_across_benches(
    model_name: str,
    latest_only: bool = Query(True, description="是否只返回最新日期的数据")
):
    """
    查询指定模型在所有榜单的数据
    
    - model_name: 模型名称
    - latest_only: 默认 true，只返回最新日期的数据；设为 false 返回所有历史数据
    """

    
    with SessionLocal() as session:
        if latest_only:
            from sqlalchemy import func
            # 获取每个榜单的最新日期
            latest_dates_stmt = (
                select(Result.bench, func.max(Result.scraped_date).label('max_date'))
                .where(Result.model == model_name)
                .group_by(Result.bench)
            )
            latest_dates = session.execute(latest_dates_stmt).all()
            
            if not latest_dates:
                return {"total": 0, "items": []}
            
            # 构建查询条件：(bench=X AND scraped_date=Y) OR (bench=A AND scraped_date=B)
            from sqlalchemy import and_, or_
            conditions = [
                and_(Result.bench == bench, Result.scraped_date == max_date)
                for bench, max_date in latest_dates
            ]
            
            stmt = (
                select(Result)
                .where(Result.model == model_name, or_(*conditions))
                .order_by(Result.bench, Result.rank.is_(None), Result.rank, Result.score.desc())
            )
        else:
            stmt = (
                select(Result)
                .where(Result.model == model_name)
                .order_by(Result.bench, Result.scraped_date.desc(), Result.rank.is_(None), Result.rank, Result.score.desc())
            )
        
        rows = session.execute(stmt).scalars().all()
        items = [
            ResultOut(
                id=r.id,
                bench=r.bench.value,
                rank=r.rank,
                agent=r.agent,
                model=r.model,
                org=r.org,
                nation=r.org_country,
                agent_org=r.agent_org,
                model_org=r.model_org,
                score=r.score,
                score_error=r.score_error,
                date=r.date,
            )
            for r in rows
        ]
        return {"total": len(items), "items": items}


@app.get("/api/benches/{bench_name}/models", response_model=QueryResponse)
def models_in_bench(
    bench_name: str,
    latest_only: bool = Query(True, description="是否只返回最新日期的数据")
):
    """
    查询指定榜单的所有模型数据
    
    - bench_name: terminal-bench 或 osworld
    - latest_only: 默认 true，只返回最新日期的数据；设为 false 返回所有历史数据
    """
    if bench_name not in {"terminal-bench", "osworld"}:
        raise HTTPException(status_code=400, detail="bench 必须是 terminal-bench 或 osworld")
    
    target = BenchType.TERMINAL_BENCH if bench_name == "terminal-bench" else BenchType.OSWORLD

    with SessionLocal() as session:
        # 如果只要最新数据，先获取最新日期
        if latest_only:
            from sqlalchemy import func
            latest_date_stmt = select(func.max(Result.scraped_date)).where(Result.bench == target)
            latest_date = session.execute(latest_date_stmt).scalar()
            
            if not latest_date:
                return {"total": 0, "items": []}
            
            # 计算数据新鲜度
            from datetime import datetime
            date_diff = (date.today() - latest_date).days
            
            stmt = (
                select(Result)
                .where(Result.bench == target, Result.scraped_date == latest_date)
                .order_by(Result.rank.is_(None), Result.rank, Result.score.desc())
            )
        else:
            stmt = (
                select(Result)
                .where(Result.bench == target)
                .order_by(Result.scraped_date.desc(), Result.rank.is_(None), Result.rank, Result.score.desc())
            )
        
        rows = session.execute(stmt).scalars().all()
        items = [
            ResultOut(
                id=r.id,
                bench=r.bench.value,
                rank=r.rank,
                agent=r.agent,
                model=r.model,
                org=r.org,
                nation=r.org_country,
                agent_org=r.agent_org,
                model_org=r.model_org,
                score=r.score,
                score_error=r.score_error,
                date=r.date,
            )
            for r in rows
        ]
        return {"total": len(items), "items": items}
