from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def load_environment() -> None:
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    load_dotenv(BACKEND_ROOT / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    groq_api_key: str | None
    groq_model: str
    tavily_api_key: str | None
    tavily_max_results: int
    langsmith_api_key: str | None
    langsmith_tracing: bool
    langsmith_project: str


def get_settings() -> Settings:
    load_environment()
    return Settings(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        tavily_max_results=int(os.getenv("TAVILY_MAX_RESULTS", "5")),
        langsmith_api_key=os.getenv("LANGSMITH_API_KEY"),
        langsmith_tracing=os.getenv("LANGSMITH_TRACING", "false").lower() == "true",
        langsmith_project=os.getenv("LANGSMITH_PROJECT", "agentforge"),
    )


def require_env(name: str, value: str | None) -> None:
    if not value:
        raise RuntimeError(
            f"{name} is required. Copy .env.example to .env and set {name}."
        )
