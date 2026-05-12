from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import tool
from tavily import TavilyClient


def build_tavily_search_tool(api_key: str, max_results: int = 5):
    client = TavilyClient(api_key=api_key)

    @tool
    def tavily_search(query: str) -> str:
        """Search the web for current facts and return compact JSON results."""
        response: dict[str, Any] = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=True,
        )
        compact = {
            "answer": response.get("answer"),
            "results": [
                {
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "content": item.get("content"),
                    "score": item.get("score"),
                }
                for item in response.get("results", [])
            ],
        }
        return json.dumps(compact, ensure_ascii=True)

    return tavily_search
