# AgentForge

AgentForge is a visual multi-agent orchestration playground. The backend runs agent workflows with LangGraph and LangChain-compatible tools, while the frontend will provide a React Flow canvas for building pipelines.

## Phase Checkpoints

### Phase 0

Backend:

```powershell
cd backend
..\.venv\Scripts\python -m uvicorn main:app --reload
```

Frontend:

```powershell
cd frontend
npm.cmd run dev
```

### Phase 1

Copy `.env.example` to `.env`, add `GROQ_API_KEY`, `TAVILY_API_KEY`, and optional LangSmith settings, then run:

```powershell
cd backend
..\.venv\Scripts\python test_researcher.py "top 3 Indian AI startups"
```
