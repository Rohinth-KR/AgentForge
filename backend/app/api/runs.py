from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.event_bus import AgentEvent, event_bus
from app.db import AgentMetric, RunRecord, SessionLocal, get_db
from app.orchestrator import AgentForgeOrchestrator, DEFAULT_PIPELINE
from app.orchestrator.graph import normalize_pipeline
from app.orchestrator.state import AgentForgeState

router = APIRouter(prefix="/api/run", tags=["runs"])


class RunCreateRequest(BaseModel):
    task: str = Field(min_length=1)
    pipeline: list[str] = Field(default_factory=lambda: DEFAULT_PIPELINE.copy())


class RunCreateResponse(BaseModel):
    run_id: str
    status: str
    status_url: str


class RunStatusResponse(BaseModel):
    run_id: str
    task: str
    pipeline: list[str]
    status: str
    current_agent: str | None
    revision_count: int
    critic_error_count: int
    is_complete: bool
    quality_status: str | None
    outputs: dict[str, str | None]
    final_output: str | None
    error_message: str | None
    total_duration_ms: float | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class RunHistoryItem(BaseModel):
    run_id: str
    task: str
    status: str
    revision_count: int
    total_duration_ms: float | None
    created_at: datetime
    completed_at: datetime | None


class RunHistoryResponse(BaseModel):
    runs: list[RunHistoryItem]
    total: int


@router.post("", response_model=RunCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_run(
    request: RunCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> RunCreateResponse:
    try:
        pipeline = normalize_pipeline(request.pipeline)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    run_id = str(uuid4())
    now = utc_now()
    record = RunRecord(
        id=run_id,
        task=request.task.strip(),
        pipeline_json=json.dumps(pipeline),
        status="queued",
        current_agent=None,
        revision_count=0,
        critic_error_count=0,
        created_at=now,
        updated_at=now,
    )
    db.add(record)
    db.commit()

    background_tasks.add_task(execute_pipeline_run, run_id)
    return RunCreateResponse(
        run_id=run_id,
        status="queued",
        status_url=f"/api/run/{run_id}",
    )


@router.get("/history", response_model=RunHistoryResponse)
async def list_runs(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> RunHistoryResponse:
    """Return recent runs for the history panel."""
    total = db.query(RunRecord).count()
    records = (
        db.query(RunRecord)
        .order_by(desc(RunRecord.created_at))
        .limit(limit)
        .all()
    )
    return RunHistoryResponse(
        runs=[
            RunHistoryItem(
                run_id=r.id,
                task=r.task,
                status=r.status,
                revision_count=r.revision_count,
                total_duration_ms=r.total_duration_ms,
                created_at=r.created_at,
                completed_at=r.completed_at,
            )
            for r in records
        ],
        total=total,
    )


@router.get("/{run_id}", response_model=RunStatusResponse)
async def get_run(
    run_id: str,
    db: Session = Depends(get_db),
) -> RunStatusResponse:
    record = db.get(RunRecord, run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    return serialize_run(record)


def execute_pipeline_run(run_id: str) -> None:
    record = _get_run_record(run_id)
    if record is None:
        return

    pipeline = json.loads(record.pipeline_json)
    run_start_time = utc_now()

    _update_run(
        run_id,
        status="running",
        current_agent="researcher",
        updated_at=utc_now(),
    )

    # Track the previously active agent so we can emit start/complete events
    _prev_agent: dict[str, str | None] = {"name": None}
    # Track per-agent timing
    _agent_start_time: dict[str, datetime] = {}

    def on_update(update: AgentForgeState) -> None:
        current = update.get("current_agent")
        prev = _prev_agent["name"]

        # If the active agent changed, emit complete for old + start for new
        if current and current != prev:
            if prev:
                # Record metric for the agent that just finished
                _record_agent_metric(run_id, prev, _agent_start_time.get(prev))

                # Emit the output produced by the agent that just finished
                output_key = {
                    "researcher": "research_output",
                    "writer": "writer_output",
                    "critic": "critic_output",
                }.get(prev)
                content = update.get(output_key) if output_key else None
                if content:
                    event_bus.publish(AgentEvent(
                        run_id=run_id,
                        type="agent_output",
                        agent=prev,
                        content=content,
                    ))
                event_bus.publish(AgentEvent(
                    run_id=run_id,
                    type="agent_complete",
                    agent=prev,
                ))

            # Mark start time for the new agent
            _agent_start_time[current] = utc_now()
            event_bus.publish(AgentEvent(
                run_id=run_id,
                type="agent_start",
                agent=current,
            ))
            _prev_agent["name"] = current

        _update_run(
            run_id,
            current_agent=update.get("current_agent", _sentinel),
            revision_count=update.get("revision_count", _sentinel),
            critic_error_count=update.get("critic_error_count", _sentinel),
            updated_at=utc_now(),
        )

    try:
        orchestrator = AgentForgeOrchestrator(on_update=on_update)
        final_state = orchestrator.run(
            run_id=run_id,
            task=record.task,
            pipeline=pipeline,
        )
    except Exception as exc:
        event_bus.publish(AgentEvent(
            run_id=run_id,
            type="run_error",
            content=str(exc),
        ))
        event_bus.close(run_id)

        total_ms = (utc_now() - run_start_time).total_seconds() * 1000
        _update_run(
            run_id,
            status="failed",
            current_agent=None,
            error_message=str(exc),
            total_duration_ms=total_ms,
            updated_at=utc_now(),
            completed_at=utc_now(),
        )
        return

    # Emit final agent_complete for the last active agent
    last_agent = _prev_agent["name"]
    if last_agent:
        _record_agent_metric(run_id, last_agent, _agent_start_time.get(last_agent))

        output_key = {
            "researcher": "research_output",
            "writer": "writer_output",
            "critic": "critic_output",
            "finalize": "final_output",
        }.get(last_agent)
        content = final_state.get(output_key) if output_key else None
        if content:
            event_bus.publish(AgentEvent(
                run_id=run_id,
                type="agent_output",
                agent=last_agent,
                content=content,
            ))
        event_bus.publish(AgentEvent(
            run_id=run_id,
            type="agent_complete",
            agent=last_agent,
        ))

    total_ms = (utc_now() - run_start_time).total_seconds() * 1000

    event_bus.publish(AgentEvent(
        run_id=run_id,
        type="run_complete",
        content=final_state.get("final_output"),
        metadata={
            "quality_status": final_state.get("quality_status"),
            "revision_count": final_state.get("revision_count", 0),
            "agent_trace": final_state.get("agent_trace", []),
            "total_duration_ms": round(total_ms),
        },
    ))
    event_bus.close(run_id)

    _update_run(
        run_id,
        status="completed",
        current_agent=None,
        revision_count=final_state.get("revision_count", 0),
        critic_error_count=final_state.get("critic_error_count", 0),
        final_output=final_state.get("final_output"),
        state_json=json.dumps(final_state),
        total_duration_ms=total_ms,
        updated_at=utc_now(),
        completed_at=utc_now(),
    )


def serialize_run(record: RunRecord) -> RunStatusResponse:
    pipeline = json.loads(record.pipeline_json)
    state: dict[str, Any] = {}
    if record.state_json:
        state = json.loads(record.state_json)

    return RunStatusResponse(
        run_id=record.id,
        task=record.task,
        pipeline=pipeline,
        status=record.status,
        current_agent=record.current_agent,
        revision_count=record.revision_count,
        critic_error_count=record.critic_error_count,
        is_complete=bool(state.get("is_complete", record.status in {"completed", "failed"})),
        quality_status=state.get("quality_status"),
        outputs={
            "researcher": state.get("research_output"),
            "writer": state.get("writer_output"),
            "critic": state.get("critic_output"),
        },
        final_output=record.final_output,
        error_message=record.error_message,
        total_duration_ms=record.total_duration_ms,
        created_at=record.created_at,
        updated_at=record.updated_at,
        completed_at=record.completed_at,
    )


_sentinel = object()


def utc_now() -> datetime:
    return datetime.now(UTC)


def _get_run_record(run_id: str) -> RunRecord | None:
    with SessionLocal() as db:
        return db.get(RunRecord, run_id)


def _update_run(run_id: str, **values: Any) -> None:
    with SessionLocal() as db:
        record = db.get(RunRecord, run_id)
        if record is None:
            return

        for key, value in values.items():
            if value is _sentinel:
                continue
            setattr(record, key, value)
        db.commit()


def _record_agent_metric(run_id: str, agent_name: str, start_time: datetime | None) -> None:
    """Record timing for a single agent execution."""
    now = utc_now()
    duration_ms = None
    if start_time:
        duration_ms = (now - start_time).total_seconds() * 1000

    with SessionLocal() as db:
        metric = AgentMetric(
            run_id=run_id,
            agent_name=agent_name,
            start_time=start_time or now,
            end_time=now,
            duration_ms=duration_ms,
            tool_calls=1,  # Each agent makes at least 1 LLM call
        )
        db.add(metric)
        db.commit()
