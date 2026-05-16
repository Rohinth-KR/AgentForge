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
