# AgentForge Phase Notes

## Phase 1

- The Researcher agent works end-to-end with Groq, Tavily, and LangSmith-ready tracing.
- Follow-up improvement: tighten source quality. The agent should prefer primary, official, or high-credibility sources over weak secondary sources such as random Medium posts when ranking evidence.

## Phase 2

- The orchestrator uses a fixed LangGraph pipeline: Researcher -> Writer -> Critic.
- If the Critic rejects the draft and reports enough errors, the graph routes back to Writer for a revision.
- The graph uses SQLite-backed LangGraph checkpoints, and API run status is stored in SQLite via SQLAlchemy.

## Phase 3

- Added real-time WebSocket streaming via `WS /api/run/{run_id}/stream`.
- The event bus (`app/core/event_bus.py`) uses per-run `asyncio.Queue` with `call_soon_threadsafe` to bridge sync orchestrator threads to async WebSocket consumers.
- Structured event types: `agent_start`, `agent_output`, `agent_complete`, `run_complete`, `run_error`.
- CORS middleware added to `app/main.py` so browser-based clients can connect.
- Test clients: `test_stream.html` (browser) and `test_stream_cli.py` (terminal).

## Phase 4

- Built the visual canvas using React Flow (`@xyflow/react`) with custom `AgentNode` components.
- Each node displays agent name, tools, status (idle/running/complete/error), and a live output preview.
- Nodes pulse with a blue glow while running and turn green on completion.
- Zustand store (`useCanvasStore`) manages all state: React Flow nodes/edges, run lifecycle, pipeline derivation from graph topology.
- `dagre.js` auto-layout arranges nodes top-to-bottom when added.
- `useRunStream` hook opens a WebSocket on run start and feeds parsed events into the store.
- Layout: Sidebar (agent catalog + quick template) | Canvas | Toolbar (task input + run) | Output Panel (logs + final output).
- Vite dev proxy forwards `/api` and WebSocket requests to the FastAPI backend at `:8000`.
- **Limitation:** Pipeline is still fixed at Researcher → Writer → Critic (backend validation). Custom pipelines = future work (see `docs/TODO.md`).

## Phase 5

- Added `AgentMetric` table for per-agent timing (start, end, duration_ms, tool_calls).
- Added `total_duration_ms` to `RunRecord` for end-to-end pipeline timing.
- New API: `GET /api/run/history` — returns recent runs for the history panel.
- New API: `GET /api/metrics/summary` — returns aggregate stats (total/completed/failed, success rate, avg duration, per-agent breakdown).
- Frontend: 3 preset pipeline templates (1 disabled as "coming soon" until dynamic pipelines).
- Frontend: localStorage persistence — canvas layout survives browser refresh.
- Frontend: Run History panel with status, timestamps, durations.
- Frontend: Stats dashboard with KPI cards and animated per-agent bar chart.
- Frontend: Keyboard shortcut `Ctrl+Enter` to run, copy output button, clear canvas button.
- **Cleanup:** Removed Tailwind CSS (unused — all styling is vanilla CSS with BEM). Moved test files to `backend/tests/`. Removed stale `.gitkeep` placeholders and temp directories.

## Output Quality Tuning Guide (TODO — for demo polish)

The pipeline architecture is solid, but the output can feel short/thin because the agent prompts were written conservatively for Phase 2 testing. Here are the levers to adjust when polishing for demos:

| Lever | File | Current | Recommended |
|---|---|---|---|
| Researcher prompt | `app/agents/researcher.py` | "3 to 5 key findings, concise" | "6 to 10 detailed findings with statistics, quotes, and source URLs" |
| Writer prompt | `app/agents/writer.py` | "polished, concise" | "Write a comprehensive, well-structured article of at least 800 words" |
| Tavily max results | `.env` → `TAVILY_MAX_RESULTS` | 5 | 8–10 (more raw material for the Writer) |
| Writer temperature | `app/agents/writer.py` | 0.25 | 0.3–0.4 (more creative, less robotic) |
| Researcher temperature | `app/agents/researcher.py` | 0.1 | Keep low — factual precision matters here |
| Critic threshold | `app/orchestrator/graph.py` | `critic_error_threshold=1` | Raise to 2–3 to trigger more revision loops |
| Max revisions | `app/orchestrator/graph.py` | `max_revisions=2` | Keep at 2, increase only if you want longer runs |
