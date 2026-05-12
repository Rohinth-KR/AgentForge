from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from app.core.settings import Settings, get_settings, require_env
from app.core.tracing import configure_langsmith


class CriticResult(BaseModel):
    passed: bool
    error_count: int = Field(ge=0)
    feedback: str


class CriticAgent:
    """Reviews drafts for factuality, structure, and source quality."""

    system_prompt = """You are AgentForge's Critic agent.
Your job is to review the Writer's draft against the original task and research.
Flag factual errors, unsupported claims, missing citations, weak source quality, and structure problems.
Prefer primary, official, or reputable sources; call out weak evidence when the draft leans on low-quality sources.
Return only valid JSON with this exact shape:
{"passed": true | false, "error_count": number, "feedback": "short actionable feedback"}
Set passed=true only when the draft is good enough to ship."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        require_env("GROQ_API_KEY", self.settings.groq_api_key)
        configure_langsmith(self.settings)
        self.llm = ChatGroq(
            api_key=self.settings.groq_api_key,
            model=self.settings.groq_model,
            temperature=0.0,
        )

    def run(self, task: str, research: str, draft: str) -> CriticResult:
        if not draft.strip():
            raise ValueError("Critic requires a draft to review.")

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=f"""Task:
{task}

Research:
{research}

Draft:
{draft}

Review the draft and return only JSON."""
            ),
        ]
        response = self.llm.invoke(messages)
        return self._parse_response(str(response.content))

    def _parse_response(self, content: str) -> CriticResult:
        try:
            return CriticResult.model_validate_json(content)
        except Exception:
            pass

        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            try:
                return CriticResult.model_validate(json.loads(content[start : end + 1]))
            except Exception:
                pass

        return CriticResult(
            passed=False,
            error_count=2,
            feedback=(
                "Critic response was not valid JSON. Treat this as a review failure. "
                f"Raw response: {content[:500]}"
            ),
        )
