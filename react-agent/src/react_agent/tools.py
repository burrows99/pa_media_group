"""This module provides example tools for web scraping and search functionality.

It includes a basic Tavily search function (as an example)

These tools are intended as free examples to get started. For production use,
consider implementing more robust and specialized tools tailored to your needs.
"""

import os
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


def cognee_visualization_links() -> str:
    """Fetch all Cognee datasets and return interactive HTML visualisation links for each.

    Calls the Cognee REST API to list all datasets, then builds a direct visualise URL
    for each one using the official GET /api/v1/visualize?dataset_id=<id> endpoint,
    which returns an interactive HTML graph of that dataset's knowledge graph.
    """
    import httpx

    cognee_api = os.environ.get("COGNEE_API_URL", "http://localhost:8000")

    try:
        resp = httpx.get(f"{cognee_api}/api/v1/datasets", timeout=10)
        resp.raise_for_status()
        datasets = resp.json()
    except Exception as e:
        return f"Failed to fetch datasets from Cognee API at {cognee_api}: {e}"

    if not datasets:
        return (
            f"No datasets found in Cognee (API: {cognee_api}).\n"
            "Add some data first using the `add_tool`."
        )

    lines = ["Here are the interactive visualisation links for your Cognee datasets:\n"]
    for ds in datasets:
        name = ds.get("name", "unnamed")
        ds_id = ds.get("id", "")
        url = f"{cognee_api}/api/v1/visualize?dataset_id={ds_id}"
        lines.append(f"**{name}** (`{ds_id}`)\n[{url}]({url})\n")

    return "\n".join(lines)


TOOLS: List[Callable[..., Any]] = [search, cognee_visualization_links]
