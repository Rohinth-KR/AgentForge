from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from app.agents import CriticAgent, CriticResult, ResearcherAgent, WriterAgent
from app.core.settings import Settings, get_settings
from app.orchestrator.state import AgentForgeState

DEFAULT_PIPELINE = ["researcher", "writer", "critic"]


class ResearcherLike(Protocol):
    def run(self, task: str) -> str:
        ...


class WriterLike(Protocol):
    def run(
        self,
        task: str,
        research: str,
        previous_draft: str | None = None,
        critique: str | None = None,
        revision_number: int = 0,
    ) -> str:
        ...


class CriticLike(Protocol):
    def run(self, task: str, research: str, draft: str) -> CriticResult:
        ...


GraphUpdateCallback = Callable[[AgentForgeState], None]


class AgentForgeOrchestrator:
    def __init__(
        self,
        settings: Settings | None = None,
        researcher: ResearcherLike | None = None,
        writer: WriterLike | None = None,
        critic: CriticLike | None = None,
        checkpoint_db_path: Path | None = None,
        on_update: GraphUpdateCallback | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.researcher = researcher or ResearcherAgent(self.settings)
        self.writer = writer or WriterAgent(self.settings)
        self.critic = critic or CriticAgent(self.settings)
        self.checkpoint_db_path = checkpoint_db_path or self.settings.checkpoint_db_path
        self.on_update = on_update

    def run(
        self,
        run_id: str,
        task: str,
        pipeline: list[str] | None = None,
    ) -> AgentForgeState:
        normalized_pipeline = normalize_pipeline(pipeline)
        self.checkpoint_db_path.parent.mkdir(parents=True, exist_ok=True)

        initial_state: AgentForgeState = {
            "task": task,
            "pipeline": normalized_pipeline,
            "current_agent": "researcher",
            "critic_error_count": 0,
            "critic_error_threshold": 1,
            "revision_count": 0,
            "max_revisions": 2,
            "is_complete": False,
            "agent_trace": [],
            "errors": [],
        }
        config = {"configurable": {"thread_id": run_id}}

        with SqliteSaver.from_conn_string(str(self.checkpoint_db_path)) as checkpointer:
            graph = self._build_graph(checkpointer)
            return graph.invoke(initial_state, config=config)

    def _build_graph(self, checkpointer: SqliteSaver):
        workflow = StateGraph(AgentForgeState)
        workflow.add_node("researcher", self._researcher_node)
        workflow.add_node("writer", self._writer_node)
        workflow.add_node("critic", self._critic_node)
        workflow.add_node("finalize", self._finalize_node)

        workflow.add_edge(START, "researcher")
        workflow.add_edge("researcher", "writer")
        workflow.add_edge("writer", "critic")
        workflow.add_conditional_edges(
            "critic",
            self._route_after_critic,
            {"writer": "writer", "finalize": "finalize"},
        )
        workflow.add_edge("finalize", END)
        return workflow.compile(checkpointer=checkpointer)

    def _researcher_node(self, state: AgentForgeState) -> AgentForgeState:
        self._emit({"current_agent": "researcher"})
        research = self.researcher.run(state["task"])
        update: AgentForgeState = {
            "research_output": research,
            "current_agent": "writer",
            "agent_trace": ["researcher"],
        }
        self._emit(update)
        return update

    def _writer_node(self, state: AgentForgeState) -> AgentForgeState:
        self._emit({"current_agent": "writer"})
        previous_draft = state.get("writer_output")
        critique = state.get("critic_output")
        revision_count = state.get("revision_count", 0)

        if previous_draft and critique:
            revision_count += 1

        draft = self.writer.run(
            task=state["task"],
            research=state["research_output"],
            previous_draft=previous_draft,
            critique=critique,
            revision_number=revision_count,
        )
        update: AgentForgeState = {
            "writer_output": draft,
            "revision_count": revision_count,
            "current_agent": "critic",
            "agent_trace": ["writer"],
        }
        self._emit(update)
        return update

    def _critic_node(self, state: AgentForgeState) -> AgentForgeState:
        self._emit({"current_agent": "critic"})
        result = self.critic.run(
            task=state["task"],
            research=state["research_output"],
            draft=state["writer_output"],
        )
        update: AgentForgeState = {
            "critic_output": result.feedback,
            "critic_passed": result.passed,
            "critic_error_count": result.error_count,
            "current_agent": "finalize" if result.passed else "writer",
            "agent_trace": ["critic"],
        }
        if not result.passed:
            update["errors"] = [result.feedback]
        self._emit(update)
        return update

    def _finalize_node(self, state: AgentForgeState) -> AgentForgeState:
        passed = state.get("critic_passed", False)
        quality_status = "passed" if passed else "completed_with_critic_warnings"
        final_output = state.get("writer_output", "")
        if not passed and state.get("critic_output"):
            final_output = (
                f"{final_output}\n\nCritic notes after max revisions:\n"
                f"{state['critic_output']}"
            )

        update: AgentForgeState = {
            "current_agent": None,
            "is_complete": True,
            "final_output": final_output,
            "quality_status": quality_status,
            "agent_trace": ["finalize"],
        }
        self._emit(update)
        return update

    def _route_after_critic(self, state: AgentForgeState) -> str:
        has_too_many_errors = (
            not state.get("critic_passed", False)
            and state.get("critic_error_count", 0)
            >= state.get("critic_error_threshold", 1)
        )
        can_revise = state.get("revision_count", 0) < state.get("max_revisions", 2)
        if has_too_many_errors and can_revise:
            return "writer"
        return "finalize"

    def _emit(self, update: AgentForgeState) -> None:
        if self.on_update:
            self.on_update(update)


def normalize_pipeline(pipeline: list[str] | None) -> list[str]:
    normalized = [item.strip().lower() for item in (pipeline or DEFAULT_PIPELINE)]
    if normalized != DEFAULT_PIPELINE:
        supported = " -> ".join(DEFAULT_PIPELINE)
        requested = " -> ".join(normalized)
        raise ValueError(
            f"Phase 2 supports only the fixed pipeline {supported}. Got {requested}."
        )
    return normalized
