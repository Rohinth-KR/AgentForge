import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.runs import router as runs_router
from app.api.streaming import router as streaming_router
from app.core.event_bus import event_bus
from app.db import init_db

app = FastAPI(
    title="AgentForge API",
    version="0.2.0",
    description="Backend API for the AgentForge multi-agent orchestration platform.",
)

# Allow the test HTML client (and future frontend) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runs_router)
app.include_router(streaming_router)


@app.on_event("startup")
async def startup() -> None:
    init_db()
    # Capture the running event loop so the event bus can safely
    # schedule work from background (synchronous) threads.
    event_bus.set_loop(asyncio.get_running_loop())


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "agentforge-api", "status": "ok"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}
