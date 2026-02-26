"""
Composio MCP Client - Python Wrapper

A comprehensive Python client for interacting with Composio's tool orchestration
platform, supporting multiple integration patterns including OpenAI Agents,
MCP protocol, and direct execution.

Usage:
    from composio_client import ComposioClient
    
    client = ComposioClient()
    session = client.create_session(user_id="user_123")
    tools = session.get_tools(toolkits=["github", "slack"])
"""

import os
import json
import logging
import httpx
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from contextlib import contextmanager
from functools import cached_property
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("composio-client")


class ComposioError(Exception):
    """Base exception for Composio client errors."""
    pass


class AuthenticationError(ComposioError):
    """Raised when authentication fails."""
    pass


class ToolExecutionError(ComposioError):
    """Raised when tool execution fails."""
    pass


class SessionError(ComposioError):
    """Raised when session operations fail."""
    pass


class ConnectionNotFoundError(ComposioError):
    """Raised when a required connection is not found."""
    pass


@dataclass
class MCPEndpoint:
    """MCP endpoint configuration for a session."""
    url: str
    headers: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {"url": self.url, "headers": self.headers}


@dataclass
class ToolResult:
    """Result from tool execution."""
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None
    
    @classmethod
    def from_response(cls, response: Dict[str, Any]) -> "ToolResult":
        """Create ToolResult from API response."""
        return cls(
            success=response.get("success", False),
            data=response.get("data"),
            error=response.get("error"),
            execution_time_ms=response.get("execution_time_ms")
        )


@dataclass
class Connection:
    """Represents a connected app/service for a user."""
    id: str
    app: str
    status: str
    user_id: str
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class Tool:
    """Represents a Composio tool."""
    name: str
    description: str
    parameters: Dict[str, Any]
    app: str
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


class ComposioSession:
    """
    Represents an active Composio session for a specific user.
    
    Provides access to tools, MCP endpoints, and execution capabilities.
    """
    
    def __init__(
        self,
        client: "ComposioClient",
        user_id: str,
        session_id: Optional[str] = None
    ):
        self._client = client
        self.user_id = user_id
        self.session_id = session_id or f"session_{user_id}_{datetime.now().timestamp()}"
        self._tools_cache: Optional[List[Tool]] = None
        self._connections_cache: Optional[List[Connection]] = None
        logger.info(f"Created session {self.session_id} for user {user_id}")
    
    @cached_property
    def mcp(self) -> MCPEndpoint:
        """
        Get MCP endpoint configuration for this session.
        
        Returns:
            MCPEndpoint with URL and headers for MCP protocol access
        """
        base_url = self._client.mcp_base_url
        return MCPEndpoint(
            url=f"{base_url}/mcp/{self.user_id}",
            headers={
                "Authorization": f"Bearer {self._client.api_key}",
                "X-Composio-User-Id": self.user_id,
                "X-Composio-Session-Id": self.session_id,
                "Content-Type": "application/json"
            }
        )
    
    def get_tools(
        self,
        toolkits: Optional[List[str]] = None,
        actions: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> List[Tool]:
        """
        Get available tools for this session.
        
        Args:
            toolkits: Filter by toolkit names (e.g., ["github", "slack"])
            actions: Filter by specific action names
            tags: Filter by tags
            
        Returns:
            List of Tool objects
        """
        params = {"user_id": self.user_id}
        if toolkits:
            params["toolkits"] = ",".join(toolkits)
        if actions:
            params["actions"] = ",".join(actions)
        if tags:
            params["tags"] = ",".join(tags)
        
        response = self._client._request("GET", "/v1/tools", params=params)
        
        tools = []
        for tool_data in response.get("tools", []):
            tools.append(Tool(
                name=tool_data["name"],
                description=tool_data.get("description", ""),
                parameters=tool_data.get("parameters", {}),
                app=tool_data.get("app", "unknown")
            ))
        
        self._tools_cache = tools
        logger.info(f"Retrieved {len(tools)} tools for session {self.session_id}")
        return tools
    
    def tools(
        self,
        toolkits: Optional[List[str]] = None,
        **kwargs
    ) -> List[Tool]:
        """
        Alias for get_tools() - matches Composio SDK pattern.
        """
        return self.get_tools(toolkits=toolkits, **kwargs)
    
    def get_connections(self, app: Optional[str] = None) -> List[Connection]:
        """
        Get active connections for this user.
        
        Args:
            app: Optional app name to filter connections
            
        Returns:
            List of Connection objects
        """
        params = {"user_id": self.user_id}
        if app:
            params["app"] = app
        
        response = self._client._request("GET", "/v1/connections", params=params)
        
        connections = []
        for conn_data in response.get("connections", []):
            connections.append(Connection(
                id=conn_data["id"],
                app=conn_data["app"],
                status=conn_data.get("status", "unknown"),
                user_id=self.user_id,
                created_at=datetime.fromisoformat(conn_data["created_at"]) if conn_data.get("created_at") else None,
                metadata=conn_data.get("metadata", {})
            ))
        
        self._connections_cache = connections
        return connections
    
    def execute(
        self,
        action: str,
        arguments: Dict[str, Any],
        connection_id: Optional[str] = None,
        timeout: float = 30.0
    ) -> ToolResult:
        """
        Execute a tool action.
        
        Args:
            action: The action/tool name (e.g., "GITHUB_STAR_REPO")
            arguments: Arguments to pass to the tool
            connection_id: Optional specific connection to use
            timeout: Execution timeout in seconds
            
        Returns:
            ToolResult with execution outcome
        """
        payload = {
            "action": action,
            "user_id": self.user_id,
            "arguments": arguments,
            "session_id": self.session_id
        }
        if connection_id:
            payload["connection_id"] = connection_id
        
        try:
            response = self._client._request(
                "POST",
                "/v1/actions/execute",
                json=payload,
                timeout=timeout
            )
            return ToolResult.from_response(response)
        except Exception as e:
            logger.error(f"Tool execution failed: {action} - {e}")
            raise ToolExecutionError(f"Failed to execute {action}: {e}") from e
    
    def initiate_connection(
        self,
        app: str,
        redirect_url: Optional[str] = None,
        integration_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate OAuth/connection flow for an app.
        
        Args:
            app: App name (e.g., "github", "slack")
            redirect_url: OAuth callback URL
            integration_id: Optional specific integration to use
            
        Returns:
            Dict with connection initiation details (URL, etc.)
        """
        payload = {
            "app": app,
            "user_id": self.user_id
        }
        if redirect_url:
            payload["redirect_url"] = redirect_url
        if integration_id:
            payload["integration_id"] = integration_id
        
        return self._client._request("POST", "/v1/connections/initiate", json=payload)
    
    def wait_for_connection(
        self,
        app: str,
        timeout: float = 300.0,
        poll_interval: float = 2.0
    ) -> Connection:
        """
        Wait for a connection to become active.
        
        Args:
            app: App name to wait for
            timeout: Maximum wait time in seconds
            poll_interval: Time between status checks
            
        Returns:
            Connection object once active
            
        Raises:
            ConnectionNotFoundError: If connection not established within timeout
        """
        import time
        start = time.time()
        
        while time.time() - start < timeout:
            connections = self.get_connections(app=app)
            active = [c for c in connections if c.status == "active"]
            if active:
                return active[0]
            time.sleep(poll_interval)
        
        raise ConnectionNotFoundError(f"Connection to {app} not established within {timeout}s")
    
    def close(self):
        """Close this session and clean up resources."""
        logger.info(f"Closing session {self.session_id}")
        self._tools_cache = None
        self._connections_cache = None


class ComposioClient:
    """
    Main Composio client for Python applications.
    
    Supports multiple integration patterns:
    - OpenAI Agents SDK integration
    - MCP protocol for Claude/other clients
    - Direct tool execution
    
    Example:
        >>> client = ComposioClient(api_key="your-key")
        >>> session = client.create_session(user_id="user_123")
        >>> tools = session.get_tools(toolkits=["github"])
        >>> result = session.execute("GITHUB_STAR_REPO", {"repo": "composio/composio"})
    """
    
    DEFAULT_BASE_URL = "https://api.composio.dev"
    DEFAULT_MCP_URL = "https://mcp.composio.dev"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        mcp_base_url: Optional[str] = None,
        provider: Optional[Any] = None,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        """
        Initialize the Composio client.
        
        Args:
            api_key: Composio API key (defaults to COMPOSIO_API_KEY env var)
            base_url: API base URL
            mcp_base_url: MCP server base URL
            provider: Optional provider (e.g., OpenAIAgentsProvider)
            timeout: Default request timeout
            max_retries: Maximum retry attempts for failed requests
        """
        self.api_key = api_key or os.environ.get("COMPOSIO_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key required. Set COMPOSIO_API_KEY or pass api_key parameter."
            )
        
        self.base_url = (base_url or os.environ.get("COMPOSIO_BASE_URL") or 
                         self.DEFAULT_BASE_URL).rstrip("/")
        self.mcp_base_url = (mcp_base_url or os.environ.get("COMPOSIO_MCP_URL") or
                             self.DEFAULT_MCP_URL).rstrip("/")
        self.provider = provider
        self.timeout = timeout
        self.max_retries = max_retries
        
        self._http_client = httpx.Client(
            base_url=self.base_url,
            headers=self._default_headers,
            timeout=timeout
        )
        
        self._sessions: Dict[str, ComposioSession] = {}
        
        # Tools namespace for direct access
        self.tools = ToolsNamespace(self)
        
        logger.info(f"Initialized ComposioClient with base_url={self.base_url}")
    
    @property
    def _default_headers(self) -> Dict[str, str]:
        """Default headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Composio-Client": "python-sdk",
            "X-Composio-Version": "1.0.0"
        }
    
    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the Composio API.
        
        Args:
            method: HTTP method
            path: API path
            params: Query parameters
            json: JSON body
            timeout: Request timeout
            retries: Number of retries
            
        Returns:
            Parsed JSON response
        """
        retries = retries if retries is not None else self.max_retries
        timeout = timeout or self.timeout
        last_error = None
        
        for attempt in range(retries + 1):
            try:
                response = self._http_client.request(
                    method=method,
                    url=path,
                    params=params,
                    json=json,
                    timeout=timeout
                )
                
                if response.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status_code == 404:
                    raise ComposioError(f"Resource not found: {path}")
                elif response.status_code >= 500:
                    raise ComposioError(f"Server error: {response.status_code}")
                
                response.raise_for_status()
                return response.json()
                
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"Request timeout (attempt {attempt + 1}/{retries + 1})")
            except httpx.HTTPStatusError as e:
                if e.response.status_code < 500:
                    raise ComposioError(f"API error: {e.response.text}") from e
                last_error = e
                logger.warning(f"Server error (attempt {attempt + 1}/{retries + 1}): {e}")
        
        raise ComposioError(f"Request failed after {retries + 1} attempts: {last_error}")
    
    def create(self, user_id: str) -> ComposioSession:
        """
        Create a new session for a user.
        
        This is the primary method for getting started with Composio.
        Matches the SDK pattern: composio.create(user_id="...")
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            ComposioSession for the user
        """
        return self.create_session(user_id)
    
    def create_session(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> ComposioSession:
        """
        Create a new session for a user.
        
        Args:
            user_id: Unique identifier for the user
            session_id: Optional custom session ID
            
        Returns:
            ComposioSession for the user
        """
        session = ComposioSession(self, user_id, session_id)
        self._sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[ComposioSession]:
        """Get an existing session by ID."""
        return self._sessions.get(session_id)
    
    @contextmanager
    def session(self, user_id: str):
        """
        Context manager for session lifecycle.
        
        Example:
            with client.session(user_id="user_123") as session:
                tools = session.get_tools()
        """
        session = self.create_session(user_id)
        try:
            yield session
        finally:
            session.close()
            self._sessions.pop(session.session_id, None)
    
    def get_apps(self) -> List[Dict[str, Any]]:
        """Get list of available apps/integrations."""
        response = self._request("GET", "/v1/apps")
        return response.get("apps", [])
    
    def get_app(self, app_name: str) -> Dict[str, Any]:
        """Get details for a specific app."""
        response = self._request("GET", f"/v1/apps/{app_name}")
        return response
    
    def close(self):
        """Close the client and all sessions."""
        for session in self._sessions.values():
            session.close()
        self._sessions.clear()
        self._http_client.close()
        logger.info("ComposioClient closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class ToolsNamespace:
    """
    Namespace for direct tool operations.
    
    Provides direct access to tools without creating sessions.
    This pattern is discouraged for most use cases but supported
    for backward compatibility and simple scripts.
    """
    
    def __init__(self, client: ComposioClient):
        self._client = client
    
    def get(
        self,
        user_id: str,
        toolkits: Optional[List[str]] = None,
        actions: Optional[List[str]] = None
    ) -> List[Tool]:
        """
        Get tools directly without a session.
        
        Args:
            user_id: User identifier
            toolkits: Filter by toolkit names
            actions: Filter by action names
            
        Returns:
            List of Tool objects
        """
        session = self._client.create_session(user_id)
        return session.get_tools(toolkits=toolkits, actions=actions)
    
    def execute(
        self,
        action: str,
        user_id: str,
        arguments: Dict[str, Any],
        **kwargs
    ) -> ToolResult:
        """
        Execute a tool directly without a session.
        
        Args:
            action: Tool/action name
            user_id: User identifier  
            arguments: Tool arguments
            **kwargs: Additional execution options
            
        Returns:
            ToolResult with execution outcome
        """
        payload = {
            "action": action,
            "user_id": user_id,
            "arguments": arguments,
            **kwargs
        }
        
        response = self._client._request("POST", "/v1/actions/execute", json=payload)
        return ToolResult.from_response(response)


# Convenience function for quick initialization
def create_client(**kwargs) -> ComposioClient:
    """
    Create a Composio client with default settings.
    
    Example:
        client = create_client()
        session = client.create(user_id="user_123")
    """
    return ComposioClient(**kwargs)


# Export main classes
__all__ = [
    "ComposioClient",
    "ComposioSession",
    "ComposioError",
    "AuthenticationError",
    "ToolExecutionError",
    "SessionError",
    "ConnectionNotFoundError",
    "Tool",
    "ToolResult",
    "Connection",
    "MCPEndpoint",
    "create_client"
]


if __name__ == "__main__":
    # Quick test / example usage
    import sys
    
    print("Composio Python Client")
    print("=" * 40)
    
    try:
        client = ComposioClient()
        session = client.create(user_id="test_user")
        
        print(f"Session ID: {session.session_id}")
        print(f"MCP URL: {session.mcp.url}")
        print(f"MCP Headers: {list(session.mcp.headers.keys())}")
        
        client.close()
        print("\nClient test successful!")
        
    except AuthenticationError as e:
        print(f"Auth error (expected without API key): {e}")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
