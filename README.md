# AgentForge

AgentForge is a visual multi-agent orchestration playground. Build AI agent pipelines on an interactive React Flow canvas, connect agents with drag-and-drop, and watch them execute in real-time via WebSocket streaming. The backend orchestrates workflows with LangGraph and LangChain-compatible tools (Groq LLaMA 70B + Tavily Search).

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, LangGraph, LangChain, Groq, Tavily, SQLAlchemy, SQLite |
| Frontend | React 19, TypeScript, Vite, React Flow, Zustand, dagre.js, Tailwind CSS |
| Streaming | WebSockets via custom EventBus (async queue + thread bridge) |

## Phase Checkpoints

### Phase 0 — Environment Setup

Backend:

```powershell
cd backend
..\.venv\Scripts\Activate
uvicorn main:app --reload
```

Frontend:

```powershell
cd frontend
npm run dev
```

### Phase 1 — Researcher Agent

Copy `.env.example` to `.env`, add `GROQ_API_KEY`, `TAVILY_API_KEY`, and optional LangSmith settings, then run:

```powershell
cd backend
..\.venv\Scripts\python test_researcher.py "top 3 Indian AI startups"
```

### Phase 2 — Multi-Agent Orchestrator

Run the API:

```powershell
cd backend
..\.venv\Scripts\Activate
uvicorn main:app --reload
```

Create a multi-agent run:

```powershell
$body = @{
  task = "Research the top 3 Indian AI startups and write a short brief"
  pipeline = @("researcher", "writer", "critic")
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/run" -ContentType "application/json" -Body $body
```

Poll the returned run ID:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/api/run/<run_id>"
```

### Phase 3 — WebSocket Streaming

Start the API server (same as Phase 2), then test real-time streaming:

**Browser test** — open `backend/test_stream.html` in any browser, type a task, and click ▶ Run Pipeline. Events stream into the log area live.

**CLI test:**

```powershell
cd backend
..\.venv\Scripts\python test_stream_cli.py "Compare React vs Vue for dashboards"
```

You should see events like `agent_start [researcher]`, `agent_output [researcher]`, `agent_complete [researcher]`, etc. streaming in real-time — not all at once after the run finishes.

### Phase 4 — Visual Canvas

Start both servers:

**Terminal 1 — Backend:**

```powershell
cd backend
..\.venv\Scripts\Activate
uvicorn main:app --reload
```

**Terminal 2 — Frontend:**

```powershell
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

**Test flow:**

1. Click agents from the sidebar (or use 🚀 Full Pipeline) to add Researcher → Writer → Critic nodes
2. Connect them by dragging from bottom handle to top handle
3. Type a task in the toolbar (e.g., "Research top 5 AI trends in 2026 and summarize")
4. Click ▶ Run Pipeline
5. Watch nodes pulse blue as each agent runs, turn green on completion
6. View live events in the bottom log panel, final output in the "Final Output" tab

> **Note:** The current pipeline is fixed at Researcher → Writer → Critic. Custom agent combinations will be supported in Phase 5. Groq free tier has a TPM limit — wait ~60s between runs if you hit a 413 error.
