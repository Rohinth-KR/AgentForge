from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.core.settings import Settings, get_settings, require_env
from app.core.tracing import configure_langsmith


class WriterAgent:
    """Turns research notes into a source-grounded draft."""

    system_prompt = """You are AgentForge's Writer agent.
Your job is to convert research notes into clear, useful prose.
Use only the provided research and critique context.
Preserve source URLs when available.
Do not add unsupported claims.
Write in a polished, concise structure suitable for the user's task."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        require_env("GROQ_API_KEY", self.settings.groq_api_key)
        configure_langsmith(self.settings)
        self.llm = ChatGroq(
            api_key=self.settings.groq_api_key,
            model=self.settings.groq_model,
            temperature=0.25,
        )

    def run(
        self,
        task: str,
        research: str,
        previous_draft: str | None = None,
        critique: str | None = None,
        revision_number: int = 0,
    ) -> str:
        if not task.strip():
            raise ValueError("Writing task cannot be empty.")
        if not research.strip():
            raise ValueError("Writer requires research output.")

        revision_context = ""
        if previous_draft and critique:
            revision_context = f"""
Previous draft:
{previous_draft}

Critic feedback to fix:
{critique}
"""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=f"""Task:
{task}

Research:
{research}

Revision number: {revision_number}
{revision_context}

Write the best current draft now."""
            ),
        ]
        response = self.llm.invoke(messages)
        return str(response.content)
