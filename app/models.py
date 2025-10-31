from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Float, Text, Enum, DateTime, Date, Index
from datetime import datetime, date
import enum

from .db import Base


class BenchType(str, enum.Enum):
    TERMINAL_BENCH = "terminal-bench"
    OSWORLD = "osworld"


class Result(Base):
    __tablename__ = "results"
    __table_args__ = (
        # 复合唯一索引：bench + rank + agent + model + scraped_date
        # 同一天爬取的相同记录会被覆盖
        Index('idx_unique_record', 'bench', 'rank', 'agent', 'model', 'scraped_date', unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bench: Mapped[BenchType] = mapped_column(Enum(BenchType), index=True, nullable=False)

    rank: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)

    agent: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    model: Mapped[Optional[str]] = mapped_column(String(255), index=True)

    # 组织（默认以 Agent Org 为主），同时记录 agent_org 与 model_org
    org: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    org_country: Mapped[Optional[str]] = mapped_column(String(128), index=True)

    agent_org: Mapped[Optional[str]] = mapped_column(String(255))
    model_org: Mapped[Optional[str]] = mapped_column(String(255))

    score: Mapped[Optional[float]] = mapped_column(Float, index=True)
    score_error: Mapped[Optional[float]] = mapped_column(Float)

    date: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    raw_json: Mapped[Optional[str]] = mapped_column(Text)

    # 爬取日期（用于按天去重）
    scraped_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
