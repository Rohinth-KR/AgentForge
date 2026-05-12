from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import RunRecord, SessionLocal, get_db
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
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


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
    _update_run(
        run_id,
        status="running",
        current_agent="researcher",
        updated_at=utc_now(),
    )

    def on_update(update: AgentForgeState) -> None:
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
        _update_run(
            run_id,
            status="failed",
            current_agent=None,
            error_message=str(exc),
            updated_at=utc_now(),
            completed_at=utc_now(),
        )
        return

    _update_run(
        run_id,
        status="completed",
        current_agent=None,
        revision_count=final_state.get("revision_count", 0),
        critic_error_count=final_state.get("critic_error_count", 0),
        final_output=final_state.get("final_output"),
        state_json=json.dumps(final_state),
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
