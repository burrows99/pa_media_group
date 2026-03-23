"""Define the configurable parameters for the agent."""

from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from typing import Annotated, Any, Dict

from . import prompts


@dataclass(kw_only=True)
class Context:
    """The context for the agent."""

    system_prompt: str = field(
        default=prompts.SYSTEM_PROMPT,
        metadata={
            "description": "The system prompt to use for the agent's interactions. "
            "This prompt sets the context and behavior for the agent."
        },
    )

    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="ollama/gpt-oss:120b-cloud",
        metadata={
            "description": "The name of the language model to use for the agent's main interactions. "
            "Should be in the form: provider/model-name."
        },
    )

    ollama_base_url: str = field(
        default="http://ollama:11434",
        metadata={
            "description": "Base URL for the Ollama server. Used when provider is 'ollama'."
        },
    )

    max_search_results: int = field(
        default=10,
        metadata={
            "description": "The maximum number of search results to return for each search query."
        },
    )

    mcp_servers: Dict[str, Any] = field(
        default_factory=dict,
        metadata={
            "description": "Configuration matching the MCP servers to initialize for the agent."
        },
    )

    mcp_disabled_tools: Dict[str, Any] = field(
        default_factory=dict,
        metadata={
            "description": "Map of disabled MCP tools."
        },
    )

    def __post_init__(self) -> None:
        """Fetch env vars for attributes that were not passed as args."""
        for f in fields(self):
            if not f.init:
                continue

            if getattr(self, f.name) == f.default:
                setattr(self, f.name, os.environ.get(f.name.upper(), f.default))
