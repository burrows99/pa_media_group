import logging
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional, Set
from langchain_core.tools import BaseTool

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client
from langchain_mcp_adapters.tools import load_mcp_tools

logger = logging.getLogger(__name__)

class MCPManager:
    """A singleton manager for handling MCP server connections and tools."""
    _instance: Optional['MCPManager'] = None
    exit_stack: AsyncExitStack
    connected_servers: Dict[str, ClientSession]

    def __new__(cls) -> 'MCPManager':
        if cls._instance is None:
            cls._instance = super(MCPManager, cls).__new__(cls)
            cls._instance.exit_stack = AsyncExitStack()
            cls._instance.connected_servers = {}  # name -> Session
            cls._instance.tools_by_server = {}  # name -> List[BaseTool]
        return cls._instance

    def _parse_disabled_tools(self, disabled_tools: Optional[Dict[str, Any]]) -> Set[str]:
        if not disabled_tools:
            return set()
            
        disabled = set()
        for tools in disabled_tools.values():
            if isinstance(tools, (list, set)):
                disabled.update(tools)
        return disabled

    async def _get_http_streams(self, name: str, config: Dict[str, Any]):
        """Create and return StreamableHTTP read/write streams."""
        url = config.get("url")
        if not url:
            logger.warning("HTTP MCP server %s has no URL defined", name)
            return None, None
        headers = config.get("headers", {})
        import httpx
        client = httpx.AsyncClient(headers=headers, timeout=httpx.Timeout(30.0, read=300.0))
        await self.exit_stack.enter_async_context(client)
        streams = await self.exit_stack.enter_async_context(streamable_http_client(url, http_client=client))
        return streams[0], streams[1]

    async def _get_sse_streams(self, name: str, config: Dict[str, Any]):
        """Create and return SSE read/write streams."""
        url = config.get("url")
        if not url:
            logger.warning("HTTP MCP server %s has no URL defined", name)
            return None, None
        headers = config.get("headers", {})
        return await self.exit_stack.enter_async_context(sse_client(url, headers=headers))

    async def _get_stdio_streams(self, name: str, config: Dict[str, Any]):
        """Create and return STDIO read/write streams."""
        command = config.get("command")
        if not command:
            logger.warning("STDIO MCP server %s has no command defined", name)
            return None, None
        server_params = StdioServerParameters(
            command=command,
            args=config.get("args", []),
            env=config.get("env", None)
        )
        return await self.exit_stack.enter_async_context(stdio_client(server_params))

    async def _connect_server(self, name: str, config: Dict[str, Any]) -> bool:
        """Connect to a single MCP server and return True if successful."""
        if name in self.connected_servers:
            return False
            
        logger.info("Connecting to MCP server: %s", name)
        
        try:
            if config.get("type") == "http":
                streams = await self._get_http_streams(name, config)
            elif config.get("type") == "sse":
                streams = await self._get_sse_streams(name, config)
            else:
                streams = await self._get_stdio_streams(name, config)
                
            read, write = streams
            if not read or not write:
                return False

            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            
            self.connected_servers[name] = session
            return True
        except Exception as e:
            logger.error("Error connecting to MCP Server %s: %s", name, e)
            return False

    async def _refresh_all_tools(self) -> None:
        """Fetch tools from all connected servers and cache them."""
        for name, session in self.connected_servers.items():
            if name in self.tools_by_server:
                continue
            try:
                tools = await load_mcp_tools(session)
                tools_list = list(tools)
                self.tools_by_server[name] = tools_list
                logger.info("Loaded %d tools from %s", len(tools_list), name)
            except Exception as e:
                logger.error("Error loading tools from %s: %s", name, e)

    async def get_tools(
        self, 
        mcp_servers_config: Dict[str, Any], 
        disabled_tools: Optional[Dict[str, Any]] = None
    ) -> List[BaseTool]:
        """
        Connect to newly defined servers and return all merged tools.
        Filters out disabled tools if provided.
        """
        if not mcp_servers_config:
            return []

        disabled = self._parse_disabled_tools(disabled_tools)

        has_new_servers = False
        for name, config in mcp_servers_config.items():
            success = await self._connect_server(name, config)
            if success:
                has_new_servers = True

        needs_refresh = has_new_servers or (self.connected_servers and not self.tools_by_server)
        if needs_refresh:
            await self._refresh_all_tools()

        requested_tools = []
        for name in mcp_servers_config.keys():
            if name in self.tools_by_server:
                requested_tools.extend(self.tools_by_server[name])

        if not disabled:
            return requested_tools
            
        return [t for t in requested_tools if t.name not in disabled]

    async def close(self):
        """Close all server connections and clear state."""
        await self.exit_stack.aclose()
        self.connected_servers.clear()
        self.tools_by_server.clear()

mcp_manager = MCPManager()
