from fastapi import FastAPI

app = FastAPI(
    title="AgentForge API",
    version="0.1.0",
    description="Backend API for the AgentForge multi-agent orchestration platform.",
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "agentforge-api", "status": "ok"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}
