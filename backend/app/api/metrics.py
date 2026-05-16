"""Metrics API — aggregate stats for the dashboard."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import AgentMetric, RunRecord, get_db

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


class AgentAvgDuration(BaseModel):
    agent: str
    avg_ms: float
    total_runs: int


class MetricsSummary(BaseModel):
    total_runs: int
    completed_runs: int
    failed_runs: int
    success_rate: float
    avg_total_duration_ms: float | None
    avg_agent_durations: list[AgentAvgDuration]


@router.get("/summary", response_model=MetricsSummary)
async def get_metrics_summary(db: Session = Depends(get_db)) -> MetricsSummary:
    """Return aggregate metrics across all runs."""

    total_runs = db.query(RunRecord).count()
    completed_runs = db.query(RunRecord).filter(RunRecord.status == "completed").count()
    failed_runs = db.query(RunRecord).filter(RunRecord.status == "failed").count()

    success_rate = (completed_runs / total_runs * 100) if total_runs > 0 else 0.0

    avg_duration = (
        db.query(func.avg(RunRecord.total_duration_ms))
        .filter(RunRecord.status == "completed", RunRecord.total_duration_ms.isnot(None))
        .scalar()
    )

    # Per-agent average durations
    agent_stats = (
        db.query(
            AgentMetric.agent_name,
            func.avg(AgentMetric.duration_ms),
            func.count(AgentMetric.id),
        )
        .filter(AgentMetric.duration_ms.isnot(None))
        .group_by(AgentMetric.agent_name)
        .all()
    )

    return MetricsSummary(
        total_runs=total_runs,
        completed_runs=completed_runs,
        failed_runs=failed_runs,
        success_rate=round(success_rate, 1),
        avg_total_duration_ms=round(avg_duration) if avg_duration else None,
        avg_agent_durations=[
            AgentAvgDuration(agent=name, avg_ms=round(avg), total_runs=count)
            for name, avg, count in agent_stats
        ],
    )
