from __future__ import annotations

from typing import Annotated, TypedDict


def merge_lists(left: list[str] | None, right: list[str] | None) -> list[str]:
    return (left or []) + (right or [])


class AgentForgeState(TypedDict, total=False):
    task: str
    pipeline: list[str]
    current_agent: str | None
    research_output: str
    writer_output: str
    critic_output: str
    critic_passed: bool
    critic_error_count: int
    critic_error_threshold: int
    revision_count: int
    max_revisions: int
    is_complete: bool
    final_output: str
    quality_status: str
    agent_trace: Annotated[list[str], merge_lists]
    errors: Annotated[list[str], merge_lists]
