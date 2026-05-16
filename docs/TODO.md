# AgentForge — TODO

## Option B: Dynamic Pipeline Support (Next Priority)

The current backend only supports a fixed `Researcher → Writer → Critic` pipeline.
This is the biggest architectural upgrade needed to make AgentForge truly unique.

### Backend Changes Required

1. **`graph.py` → Dynamic graph builder**
   - Remove `normalize_pipeline()` validation
   - Make `_build_graph()` accept a list of agent IDs and dynamically wire the `StateGraph`
   - Handle missing data gracefully (e.g., Writer without Researcher = use task as input)

2. **New agent types**
   - `Summarizer` — condensed output variant of Writer
   - `Coder` — code generation agent
   - `Reviewer` — code review / fact-checking agent
   - Each agent needs its own LangChain prompt + tool configuration

3. **State schema evolution**
   - `AgentForgeState` must support arbitrary agent outputs (not just `research_output`, `writer_output`, `critic_output`)
   - Consider a generic `outputs: dict[str, str]` field

4. **Pipeline validation**
   - Validate the graph is a valid DAG (no cycles)
   - Validate required dependencies (e.g., Writer needs some input)

### Frontend Changes Required

1. **Agent catalog expansion** — add new agent types to `AGENT_CATALOG`
2. **Connection validation** — prevent invalid connections (e.g., Critic → Researcher)
3. **Template updates** — enable the "Research → Summarize" template
4. **Custom agent config** — let users tweak agent prompts/temperature per node

---

## Polish & UX

- [ ] Export output as Markdown (.md download)
- [ ] Dark/light theme toggle
- [ ] Node delete button (right-click context menu)
- [ ] Run comparison — diff two outputs side by side
- [ ] Mobile-responsive layout (currently desktop-only)

## Infrastructure

- [ ] Docker Compose for one-command setup
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Environment variable validation on startup
- [ ] Rate limit handling — auto-retry with backoff for Groq 413 errors

## Documentation

- [ ] Architecture diagram (Mermaid)
- [ ] API reference (auto-generated from FastAPI docs)
- [ ] Contributing guide
