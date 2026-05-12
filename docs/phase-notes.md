# AgentForge Phase Notes

## Phase 1

- The Researcher agent works end-to-end with Groq, Tavily, and LangSmith-ready tracing.
- Follow-up improvement: tighten source quality. The agent should prefer primary, official, or high-credibility sources over weak secondary sources such as random Medium posts when ranking evidence.

## Phase 2

- The orchestrator uses a fixed LangGraph pipeline: Researcher -> Writer -> Critic.
- If the Critic rejects the draft and reports enough errors, the graph routes back to Writer for a revision.
- The graph uses SQLite-backed LangGraph checkpoints, and API run status is stored in SQLite via SQLAlchemy.
