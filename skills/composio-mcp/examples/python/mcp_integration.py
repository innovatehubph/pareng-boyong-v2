"""
MCP Integration Example - No Provider Packages Needed

This example demonstrates how to use Composio's MCP endpoints directly
without requiring framework-specific provider packages. This approach
works with any MCP-compatible client including Claude Desktop, Cursor,
and custom implementations.

Requirements:
    pip install composio httpx

Environment:
    COMPOSIO_API_KEY=your-composio-key
"""

import os
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """Represents an MCP tool definition."""
    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass
class MCPResponse:
    """Response from MCP tool execution."""
    content: List[Dict[str, Any]]
    is_error: bool = False


class ComposioMCPClient:
    """
    Direct MCP client for Composio without provider packages.
    
    This client implements the MCP protocol directly, allowing integration
    with any system that supports MCP without needing framework-specific
    provider packages.
    
    Example:
        client = ComposioMCPClient(user_id="user_123")
        tools = await client.list_tools()
        result = await client.call_tool("GITHUB_LIST_REPOS", {"username": "octocat"})
    """
    
    MCP_BASE_URL = "https://mcp.composio.dev"
    
    def __init__(
        self,
        user_id: str,
        api_key: Optional[str] = None,
        toolkits: Optional[List[str]] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize MCP client.
        
        Args:
            user_id: User identifier for the session
            api_key: Composio API key (or set COMPOSIO_API_KEY env var)
            toolkits: Optional list of toolkits to filter
            base_url: Custom MCP base URL
        """
        self.user_id = user_id
        self.api_key = api_key or os.environ.get("COMPOSIO_API_KEY")
        
        if not self.api_key:
            raise ValueError("API key required. Set COMPOSIO_API_KEY or pass api_key parameter.")
        
        self.base_url = (base_url or self.MCP_BASE_URL).rstrip("/")
        self.toolkits = toolkits or []
        
        self._http_client: Optional[httpx.AsyncClient] = None
        self._tools_cache: Optional[List[MCPTool]] = None
    
    @property
    def mcp_url(self) -> str:
        """Get the MCP endpoint URL."""
        url = f"{self.base_url}/mcp/{self.user_id}"
        if self.toolkits:
            url += f"?toolkits={','.join(self.toolkits)}"
        return url
    
    @property
    def mcp_headers(self) -> Dict[str, str]:
        """Get headers for MCP requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                headers=self.mcp_headers,
                timeout=30.0
            )
        return self._http_client
    
    async def _send_request(self, method: str, params: Optional[Dict] = None) -> Dict:
        """Send JSON-RPC request to MCP server."""
        client = await self._get_client()
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        logger.debug(f"MCP Request: {method} - {params}")
        
        response = await client.post(self.mcp_url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        if "error" in result:
            error = result["error"]
            raise Exception(f"MCP Error: {error.get('message', 'Unknown error')}")
        
        return result.get("result", {})
    
    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize the MCP connection.
        
        Returns:
            Server capabilities and info
        """
        result = await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {"listChanged": True}
            },
            "clientInfo": {
                "name": "composio-python-client",
                "version": "1.0.0"
            }
        })
        
        logger.info(f"MCP initialized: {result.get('serverInfo', {}).get('name', 'Unknown')}")
        return result
    
    async def list_tools(self, refresh: bool = False) -> List[MCPTool]:
        """
        List available tools from the MCP server.
        
        Args:
            refresh: Force refresh of cached tools
            
        Returns:
            List of available MCPTool objects
        """
        if self._tools_cache is not None and not refresh:
            return self._tools_cache
        
        result = await self._send_request("tools/list")
        
        tools = []
        for tool_data in result.get("tools", []):
            tools.append(MCPTool(
                name=tool_data["name"],
                description=tool_data.get("description", ""),
                input_schema=tool_data.get("inputSchema", {})
            ))
        
        self._tools_cache = tools
        logger.info(f"Listed {len(tools)} tools")
        return tools
    
    async def call_tool(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> MCPResponse:
        """
        Call a tool on the MCP server.
        
        Args:
            name: Tool name (e.g., "GITHUB_STAR_REPO")
            arguments: Tool arguments
            
        Returns:
            MCPResponse with tool execution results
        """
        logger.info(f"Calling tool: {name}")
        
        result = await self._send_request("tools/call", {
            "name": name,
            "arguments": arguments or {}
        })
        
        return MCPResponse(
            content=result.get("content", []),
            is_error=result.get("isError", False)
        )
    
    async def close(self):
        """Close the client and clean up resources."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


def get_mcp_config_for_claude(
    user_id: str,
    api_key: Optional[str] = None,
    toolkits: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate MCP configuration for Claude Desktop or similar clients.
    
    This generates the JSON configuration that can be added to Claude's
    MCP settings file.
    
    Args:
        user_id: User identifier
        api_key: Composio API key
        toolkits: List of toolkits to enable
        
    Returns:
        Configuration dict for claude_desktop_config.json
    """
    api_key = api_key or os.environ.get("COMPOSIO_API_KEY")
    
    url = f"https://mcp.composio.dev/mcp/{user_id}"
    if toolkits:
        url += f"?toolkits={','.join(toolkits)}"
    
    return {
        "mcpServers": {
            "composio": {
                "url": url,
                "headers": {
                    "Authorization": f"Bearer {api_key}"
                }
            }
        }
    }


def get_mcp_config_for_cursor(
    user_id: str,
    api_key: Optional[str] = None,
    toolkits: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate MCP configuration for Cursor IDE.
    
    Args:
        user_id: User identifier
        api_key: Composio API key
        toolkits: List of toolkits to enable
        
    Returns:
        Configuration dict for Cursor's MCP settings
    """
    api_key = api_key or os.environ.get("COMPOSIO_API_KEY")
    
    url = f"https://mcp.composio.dev/mcp/{user_id}"
    if toolkits:
        url += f"?toolkits={','.join(toolkits)}"
    
    return {
        "mcp": {
            "servers": {
                "composio": {
                    "transport": "sse",
                    "url": url,
                    "headers": {
                        "Authorization": f"Bearer {api_key}"
                    }
                }
            }
        }
    }


class MCPToolExecutor:
    """
    Helper class for executing tools through MCP in a synchronous context.
    
    Useful for scripts that don't need full async support.
    """
    
    def __init__(self, user_id: str, api_key: Optional[str] = None):
        self.user_id = user_id
        self.api_key = api_key
        self._client: Optional[ComposioMCPClient] = None
    
    def _ensure_client(self):
        if self._client is None:
            self._client = ComposioMCPClient(
                user_id=self.user_id,
                api_key=self.api_key
            )
    
    def list_tools(self) -> List[MCPTool]:
        """List available tools (sync wrapper)."""
        self._ensure_client()
        return asyncio.run(self._async_list_tools())
    
    async def _async_list_tools(self) -> List[MCPTool]:
        async with self._client:
            return await self._client.list_tools()
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> MCPResponse:
        """Call a tool (sync wrapper)."""
        self._ensure_client()
        return asyncio.run(self._async_call_tool(name, arguments))
    
    async def _async_call_tool(self, name: str, arguments: Dict[str, Any]) -> MCPResponse:
        async with self._client:
            return await self._client.call_tool(name, arguments)


# SSE Stream handling for real-time MCP
class MCPSSEClient:
    """
    MCP client with Server-Sent Events (SSE) support for real-time streaming.
    
    This is useful for long-running tools or when you need progress updates.
    """
    
    def __init__(
        self,
        user_id: str,
        api_key: Optional[str] = None,
        base_url: str = "https://mcp.composio.dev"
    ):
        self.user_id = user_id
        self.api_key = api_key or os.environ.get("COMPOSIO_API_KEY")
        self.base_url = base_url.rstrip("/")
    
    @property
    def sse_url(self) -> str:
        """SSE endpoint URL."""
        return f"{self.base_url}/sse/{self.user_id}"
    
    async def stream_tool_call(
        self,
        name: str,
        arguments: Dict[str, Any]
    ):
        """
        Call a tool with SSE streaming response.
        
        Yields events as they arrive from the server.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Yields:
            Event dictionaries from SSE stream
        """
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                self.sse_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": name, "arguments": arguments}
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "text/event-stream"
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data and data != "[DONE]":
                            yield json.loads(data)


# Example usage
async def main():
    """Demonstrate MCP integration patterns."""
    
    api_key = os.environ.get("COMPOSIO_API_KEY")
    if not api_key:
        print("Warning: COMPOSIO_API_KEY not set")
        print("Set it with: export COMPOSIO_API_KEY=your-key")
        return
    
    user_id = "demo_user_mcp"
    
    print("=" * 60)
    print("Composio MCP Integration Examples")
    print("=" * 60)
    
    # Example 1: Direct MCP client usage
    print("\n--- Example 1: Async MCP Client ---")
    try:
        async with ComposioMCPClient(user_id=user_id, toolkits=["github"]) as client:
            # List available tools
            tools = await client.list_tools()
            print(f"Available tools: {len(tools)}")
            for tool in tools[:5]:  # Show first 5
                print(f"  - {tool.name}: {tool.description[:50]}...")
            
            # Call a tool (if you have GitHub connected)
            # result = await client.call_tool("GITHUB_LIST_REPOS", {"username": "octocat"})
            # print(f"Result: {result.content}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Generate config for Claude Desktop
    print("\n--- Example 2: Claude Desktop Config ---")
    config = get_mcp_config_for_claude(
        user_id=user_id,
        toolkits=["github", "slack"]
    )
    print(json.dumps(config, indent=2))
    
    # Example 3: Generate config for Cursor
    print("\n--- Example 3: Cursor Config ---")
    config = get_mcp_config_for_cursor(
        user_id=user_id,
        toolkits=["github"]
    )
    print(json.dumps(config, indent=2))
    
    # Example 4: Sync wrapper for simple scripts
    print("\n--- Example 4: Sync Tool Executor ---")
    try:
        executor = MCPToolExecutor(user_id=user_id)
        tools = executor.list_tools()
        print(f"Tools via sync executor: {len(tools)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 5: MCP URL and headers for manual integration
    print("\n--- Example 5: Manual Integration Details ---")
    client = ComposioMCPClient(user_id=user_id, toolkits=["github"])
    print(f"MCP URL: {client.mcp_url}")
    print(f"Headers: {json.dumps({k: '...' if 'auth' in k.lower() else v for k, v in client.mcp_headers.items()}, indent=2)}")
    
    print("\n" + "=" * 60)
    print("MCP integration examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
