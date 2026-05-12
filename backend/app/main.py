from fastapi import FastAPI

from app.api.runs import router as runs_router
from app.db import init_db

app = FastAPI(
    title="AgentForge API",
    version="0.1.0",
    description="Backend API for the AgentForge multi-agent orchestration platform.",
)

app.include_router(runs_router)


@app.on_event("startup")
async def startup() -> None:
    init_db()


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "agentforge-api", "status": "ok"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}
