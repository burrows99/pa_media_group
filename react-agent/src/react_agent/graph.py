"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""

from datetime import UTC, datetime
from typing import Dict, List, Literal, cast

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage  # ty:ignore[unresolved-import]
from langgraph.graph import StateGraph  # ty:ignore[unresolved-import]
from langgraph.prebuilt import ToolNode  # ty:ignore[unresolved-import]
from langgraph.runtime import Runtime  # ty:ignore[unresolved-import]

from react_agent.context import Context
from react_agent.state import InputState, State
from react_agent.tools import TOOLS, get_cognee_tools
from react_agent.utils import load_chat_model, get_message_text
from react_agent.mcp import mcp_manager

# Add Cognee memory tools (add + search) via the official integration.
# See: https://docs.cognee.ai/integrations/langgraph-integration
TOOLS.extend(get_cognee_tools())

# Define the function that calls the model

import logging

logger = logging.getLogger(__name__)

async def retrieve_context(
    state: State, runtime: Runtime[Context]
) -> dict:
    """Retrieve context using Cognee search tool before calling the model."""
    logger.info("--- 🔍 RETRIEVING CONTEXT ---")
    if not state.messages:
        logger.info("No messages in state, skipping retrieval.")
        return {}
    
    last_message = state.messages[-1]
    
    # Only retrieve if the last message is from a user (HumanMessage)
    if not isinstance(last_message, HumanMessage):
        logger.info("Last message is not from user. Skipping retrieval.")
        return {}

    query = get_message_text(last_message)
    logger.info(f"User query: '{query}'")
    
    # get_cognee_tools returns [add_tool, search_tool]
    tools = get_cognee_tools()
    search_tool = tools[1]
    
    try:
        logger.info("Calling Cognee search tool...")
        context = await search_tool.ainvoke({"query_text": query})
        logger.info(f"✅ Successfully retrieved context:\n{context}\n")
        return {"retrieved_context": str(context)}
    except Exception as e:
        logger.error(f"❌ Context retrieval failed: {e}")
        return {"retrieved_context": ""}


async def get_all_tools(runtime: Runtime[Context]):
    """Dynamically aggregate base and MCP tools."""
    mcp_tools = await mcp_manager.get_tools(
        runtime.context.mcp_servers, 
        runtime.context.mcp_disabled_tools
    )
    return TOOLS + mcp_tools


async def call_model(
    state: State, runtime: Runtime[Context]
) -> Dict[str, List[AIMessage]]:
    """Call the LLM powering our "agent".

    This function prepares the prompt, initializes the model, and processes the response.

    Args:
        state (State): The current state of the conversation.
        config (RunnableConfig): Configuration for the model run.

    Returns:
    """
    all_tools = await get_all_tools(runtime)

    # Initialize the model with tool binding. Change the model or add more tools here.
    model = load_chat_model(runtime.context.model, runtime.context.ollama_base_url).bind_tools(all_tools)

    # Format the system prompt. Customize this to change the agent's behavior.
    system_message = runtime.context.system_prompt.format(
        system_time=datetime.now(tz=UTC).isoformat()
    )

    if getattr(state, "retrieved_context", ""):
        system_message += f"\n\nRelevant Context from long-term memory:\n{state.retrieved_context}"

    # Get the model's response
    response = cast( # type: ignore[redundant-cast]
        AIMessage,
        await model.ainvoke(
            [{"role": "system", "content": system_message}, *state.messages]
        ),
    )

    # Handle the case when it's the last step and the model still wants to use a tool
    if state.is_last_step and response.tool_calls:
        return {
            "messages": [
                AIMessage(
                    id=response.id,
                    content="Sorry, I could not find an answer to your question in the specified number of steps.",
                )
            ]
        }

    # Return the model's response as a list to be added to existing messages
    return {"messages": [response]}


# Define a new graph

builder = StateGraph(State, input_schema=InputState, context_schema=Context)

# Define the nodes we will cycle between
builder.add_node(retrieve_context)
builder.add_node(call_model)

async def execute_tools(state: State, runtime: Runtime[Context]):
    all_tools = await get_all_tools(runtime)
    node = ToolNode(all_tools)
    return await node.ainvoke(state)

builder.add_node("tools", execute_tools)

# Set the entrypoint as `retrieve_context`
# This means that this node is the first one called
builder.add_edge("__start__", "retrieve_context")
builder.add_edge("retrieve_context", "call_model")


def route_model_output(state: State) -> Literal["__end__", "tools"]:
    """Determine the next node based on the model's output.

    This function checks if the model's last message contains tool calls.

    Args:
        state (State): The current state of the conversation.

    Returns:
        str: The name of the next node to call ("__end__" or "tools").
    """
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
        )
    # If there is no tool call, then we finish
    if not last_message.tool_calls:
        return "__end__"
    # Otherwise we execute the requested actions
    return "tools"


# Add a conditional edge to determine the next step after `call_model`
builder.add_conditional_edges(
    "call_model",
    # After call_model finishes running, the next node(s) are scheduled
    # based on the output from route_model_output
    route_model_output,
)

# Add a normal edge from `tools` to `call_model`
# This creates a cycle: after using tools, we always return to the model
builder.add_edge("tools", "call_model")

# Compile the builder into an executable graph
graph = builder.compile(name="ReAct Agent")

# ----------------------------------------------------------------------
# Secondary Graph Definition: MCP UI Extraction Endpoint
# ----------------------------------------------------------------------
from typing import Any
from typing_extensions import TypedDict

class MCPState(TypedDict):
    mcp_servers_config: dict[str, Any]
    tools: list[dict[str, Any]]

async def get_tools_node(state: MCPState):
    config = state.get("mcp_servers_config", {})
    tools = await mcp_manager.get_tools(config)
    return {"tools": [{"name": t.name, "description": t.description} for t in tools]}

mcp_builder = StateGraph(MCPState)
mcp_builder.add_node("get_tools", get_tools_node)
mcp_builder.add_edge("__start__", "get_tools")
mcp_builder.add_edge("get_tools", "__end__")
mcp_graph = mcp_builder.compile(name="MCP UI Extractor")

