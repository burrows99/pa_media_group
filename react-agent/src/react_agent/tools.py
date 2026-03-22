"""This module provides example tools for web scraping and search functionality.

It includes a basic Tavily search function (as an example)

These tools are intended as free examples to get started. For production use,
consider implementing more robust and specialized tools tailored to your needs.
"""

from typing import Any, Callable, List, cast

from langchain_tavily import TavilySearch  # ty:ignore[unresolved-import]
from langgraph.runtime import get_runtime  # ty:ignore[unresolved-import]

from react_agent.context import Context


async def search(query: str) -> dict[str, Any] | None:
    """Search for general web results.

    This function performs a search using the Tavily search engine, which is designed
    to provide comprehensive, accurate, and trusted results. It's particularly useful
    for answering questions about current events.
    """
    runtime = get_runtime(Context)
    wrapped = TavilySearch(max_results=runtime.context.max_search_results)
    return cast(dict[str, Any], await wrapped.ainvoke({"query": query}))


def get_cognee_tools(session_id: str | None = None) -> List[Callable[..., Any]]:
    """Return Cognee memory tools (add + search) for the given session.

    Uses the official cognee-integration-langgraph package which provides:
      - add_memory: ingest text/documents into the Cognee knowledge graph
      - search_memory: retrieve relevant information via semantic graph search

    Args:
        session_id: Optional session ID for multi-tenant isolation.
                    Defaults to a UUID-based session if not provided.

    Returns:
        [add_tool, search_tool] ready to pass to bind_tools / ToolNode.
    """
    from cognee_integration_langgraph import (  # ty:ignore[unresolved-import]
        get_sessionized_cognee_tools,
    )

    add_tool, search_tool = get_sessionized_cognee_tools(session_id=session_id)
    return [add_tool, search_tool]


TOOLS: List[Callable[..., Any]] = [search]
