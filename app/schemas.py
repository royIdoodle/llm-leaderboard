from __future__ import annotations
from pydantic import BaseModel
from typing import Any, Optional


class ResultOut(BaseModel):
    id: int
    bench: str
    rank: Optional[int] = None
    agent: Optional[str] = None
    model: Optional[str] = None
    org: Optional[str] = None
    nation: Optional[str] = None
    agent_org: Optional[str] = None
    model_org: Optional[str] = None
    score: Optional[float] = None
    score_error: Optional[float] = None
    date: Optional[str] = None

    class Config:
        from_attributes = True


class QueryResponse(BaseModel):
    total: int
    items: list[ResultOut]


class ScrapeResponse(BaseModel):
    bench: str
    inserted: int
    updated: int
    total: int
