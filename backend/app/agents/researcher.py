from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq

from app.core.settings import Settings, get_settings, require_env
from app.core.tracing import configure_langsmith
from app.tools.tavily_search import build_tavily_search_tool


class ResearcherAgent:
    """Single-purpose research agent for Phase 1."""

    system_prompt = """You are AgentForge's Researcher agent.
Your job is to gather current, verifiable facts from web search results.
Use the Tavily search tool when the task needs external facts.
Prefer primary, official, or high-credibility sources over weak secondary sources.
Treat generic blogs and Medium posts as weak evidence unless better sources are unavailable.
Return concise structured research with:
- a short answer
- 3 to 5 key findings
- source names or URLs when available
- uncertainty notes for weak or conflicting evidence
Do not invent facts. If search results are insufficient, say so."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        require_env("GROQ_API_KEY", self.settings.groq_api_key)
        require_env("TAVILY_API_KEY", self.settings.tavily_api_key)
        configure_langsmith(self.settings)

        self.search_tool = build_tavily_search_tool(
            api_key=self.settings.tavily_api_key,
            max_results=self.settings.tavily_max_results,
        )
        self.tools = [self.search_tool]
        self.tools_by_name = {tool.name: tool for tool in self.tools}

        self.llm = ChatGroq(
            api_key=self.settings.groq_api_key,
            model=self.settings.groq_model,
            temperature=0.1,
        )
        self.tool_enabled_llm = self.llm.bind_tools(self.tools)

    def run(self, task: str) -> str:
        cleaned_task = task.strip()
        if not cleaned_task:
            raise ValueError("Research task cannot be empty.")

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"Research task: {cleaned_task}"),
        ]

        first_response = self.tool_enabled_llm.invoke(messages)
        messages.append(first_response)

        for tool_call in getattr(first_response, "tool_calls", []) or []:
            tool_name = tool_call["name"]
            selected_tool = self.tools_by_name.get(tool_name)
            if selected_tool is None:
                continue

            tool_result = selected_tool.invoke(tool_call.get("args", {}))
            messages.append(
                ToolMessage(
                    content=str(tool_result),
                    name=tool_name,
                    tool_call_id=tool_call["id"],
                )
            )

        messages.append(
            HumanMessage(
                content=(
                    "Using only the gathered evidence, write the final research output. "
                    "Keep it structured and include source URLs when they were returned."
                )
            )
        )
        final_response = self.llm.invoke(messages)
        return str(final_response.content)
