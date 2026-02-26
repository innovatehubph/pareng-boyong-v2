"""
Direct Tool Execution Example

This example demonstrates how to execute Composio tools directly
without using an AI agent. This is useful for:
- Automation scripts
- Backend integrations
- Testing and debugging
- Batch operations

Note: Direct execution bypasses AI reasoning, so use with care.
The session-based approach is preferred for most use cases.

Requirements:
    pip install composio httpx

Environment:
    COMPOSIO_API_KEY=your-composio-key
"""

import os
import sys
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from composio_client import (
    ComposioClient,
    ComposioSession,
    Tool,
    ToolResult,
    ComposioError,
    ToolExecutionError,
    create_client
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def execute_single_tool(
    action: str,
    arguments: Dict[str, Any],
    user_id: str = "default_user"
) -> ToolResult:
    """
    Execute a single tool directly.
    
    This is the simplest pattern for one-off tool execution.
    
    Args:
        action: Tool action name (e.g., "GITHUB_STAR_REPO")
        arguments: Arguments to pass to the tool
        user_id: User identifier
        
    Returns:
        ToolResult with execution outcome
        
    Example:
        result = execute_single_tool(
            "GITHUB_STAR_REPO",
            {"owner": "composio", "repo": "composio"},
            user_id="user_123"
        )
    """
    client = create_client()
    
    try:
        # Direct execution via tools namespace
        result = client.tools.execute(
            action=action,
            user_id=user_id,
            arguments=arguments
        )
        
        if result.success:
            logger.info(f"Tool {action} executed successfully")
        else:
            logger.warning(f"Tool {action} returned error: {result.error}")
        
        return result
        
    finally:
        client.close()


def execute_with_session(
    user_id: str,
    action: str,
    arguments: Dict[str, Any]
) -> ToolResult:
    """
    Execute a tool using a session (recommended pattern).
    
    Sessions provide better resource management and connection handling.
    
    Args:
        user_id: User identifier
        action: Tool action name
        arguments: Tool arguments
        
    Returns:
        ToolResult with execution outcome
    """
    with create_client() as client:
        with client.session(user_id) as session:
            return session.execute(action, arguments)


def batch_execute(
    user_id: str,
    operations: List[Dict[str, Any]]
) -> List[ToolResult]:
    """
    Execute multiple tools in sequence.
    
    Args:
        user_id: User identifier
        operations: List of {"action": str, "arguments": dict}
        
    Returns:
        List of ToolResults in order
        
    Example:
        results = batch_execute("user_123", [
            {"action": "GITHUB_LIST_REPOS", "arguments": {"username": "octocat"}},
            {"action": "GITHUB_GET_REPO", "arguments": {"owner": "octocat", "repo": "Hello-World"}}
        ])
    """
    results = []
    
    with create_client() as client:
        session = client.create_session(user_id)
        
        for i, op in enumerate(operations):
            logger.info(f"Executing operation {i+1}/{len(operations)}: {op['action']}")
            
            try:
                result = session.execute(
                    action=op["action"],
                    arguments=op.get("arguments", {})
                )
                results.append(result)
                
            except ToolExecutionError as e:
                logger.error(f"Operation {i+1} failed: {e}")
                results.append(ToolResult(
                    success=False,
                    data=None,
                    error=str(e)
                ))
        
        session.close()
    
    return results


class ToolExecutor:
    """
    Reusable tool executor for multiple operations.
    
    Better for applications that need to execute many tools over time.
    Manages sessions and provides helper methods for common patterns.
    """
    
    def __init__(self, user_id: str):
        """
        Initialize the executor.
        
        Args:
            user_id: User identifier for all operations
        """
        self.user_id = user_id
        self.client = create_client()
        self.session = self.client.create_session(user_id)
        self._execution_log: List[Dict[str, Any]] = []
    
    def execute(
        self,
        action: str,
        arguments: Optional[Dict[str, Any]] = None,
        log: bool = True
    ) -> ToolResult:
        """
        Execute a tool action.
        
        Args:
            action: Tool action name
            arguments: Tool arguments
            log: Whether to log this execution
            
        Returns:
            ToolResult
        """
        start_time = datetime.now()
        
        try:
            result = self.session.execute(action, arguments or {})
            
            if log:
                self._execution_log.append({
                    "action": action,
                    "arguments": arguments,
                    "success": result.success,
                    "timestamp": start_time.isoformat(),
                    "duration_ms": (datetime.now() - start_time).total_seconds() * 1000
                })
            
            return result
            
        except Exception as e:
            if log:
                self._execution_log.append({
                    "action": action,
                    "arguments": arguments,
                    "success": False,
                    "error": str(e),
                    "timestamp": start_time.isoformat()
                })
            raise
    
    def list_tools(self, toolkits: Optional[List[str]] = None) -> List[Tool]:
        """Get available tools."""
        return self.session.get_tools(toolkits=toolkits)
    
    def get_tool_by_name(self, name: str) -> Optional[Tool]:
        """Find a specific tool by name."""
        tools = self.list_tools()
        for tool in tools:
            if tool.name == name:
                return tool
        return None
    
    def validate_arguments(self, action: str, arguments: Dict[str, Any]) -> bool:
        """
        Validate arguments against tool schema.
        
        Args:
            action: Tool action name
            arguments: Arguments to validate
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        tool = self.get_tool_by_name(action)
        if not tool:
            raise ValueError(f"Tool not found: {action}")
        
        schema = tool.parameters
        required = schema.get("required", [])
        
        for req in required:
            if req not in arguments:
                raise ValueError(f"Missing required argument: {req}")
        
        return True
    
    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get log of all executions."""
        return self._execution_log.copy()
    
    def clear_log(self):
        """Clear execution log."""
        self._execution_log.clear()
    
    def close(self):
        """Clean up resources."""
        self.session.close()
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Specific tool helpers
class GitHubToolExecutor(ToolExecutor):
    """
    Specialized executor for GitHub operations.
    
    Provides type-safe methods for common GitHub operations.
    """
    
    def star_repo(self, owner: str, repo: str) -> ToolResult:
        """Star a GitHub repository."""
        return self.execute("GITHUB_STAR_A_REPOSITORY_FOR_THE_AUTHENTICATED_USER", {
            "owner": owner,
            "repo": repo
        })
    
    def unstar_repo(self, owner: str, repo: str) -> ToolResult:
        """Unstar a GitHub repository."""
        return self.execute("GITHUB_UNSTAR_A_REPOSITORY_FOR_THE_AUTHENTICATED_USER", {
            "owner": owner,
            "repo": repo
        })
    
    def list_repos(self, username: str) -> ToolResult:
        """List repositories for a user."""
        return self.execute("GITHUB_LIST_REPOSITORIES_FOR_A_USER", {
            "username": username
        })
    
    def get_repo(self, owner: str, repo: str) -> ToolResult:
        """Get repository details."""
        return self.execute("GITHUB_GET_A_REPOSITORY", {
            "owner": owner,
            "repo": repo
        })
    
    def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> ToolResult:
        """Create a GitHub issue."""
        args = {
            "owner": owner,
            "repo": repo,
            "title": title
        }
        if body:
            args["body"] = body
        if labels:
            args["labels"] = labels
        
        return self.execute("GITHUB_CREATE_AN_ISSUE", args)
    
    def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open"
    ) -> ToolResult:
        """List issues in a repository."""
        return self.execute("GITHUB_LIST_REPOSITORY_ISSUES", {
            "owner": owner,
            "repo": repo,
            "state": state
        })


class SlackToolExecutor(ToolExecutor):
    """
    Specialized executor for Slack operations.
    """
    
    def send_message(self, channel: str, text: str) -> ToolResult:
        """Send a message to a Slack channel."""
        return self.execute("SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL", {
            "channel": channel,
            "text": text
        })
    
    def list_channels(self) -> ToolResult:
        """List Slack channels."""
        return self.execute("SLACK_LISTS_ALL_CHANNELS_IN_A_SLACK_TEAM", {})
    
    def get_user_info(self, user_id: str) -> ToolResult:
        """Get information about a Slack user."""
        return self.execute("SLACK_GETS_INFORMATION_ABOUT_A_USER", {
            "user": user_id
        })


# Convenience functions for common operations
def github_star(owner: str, repo: str, user_id: str = "default") -> bool:
    """Quick helper to star a GitHub repo."""
    with GitHubToolExecutor(user_id) as gh:
        result = gh.star_repo(owner, repo)
        return result.success


def slack_message(channel: str, text: str, user_id: str = "default") -> bool:
    """Quick helper to send a Slack message."""
    with SlackToolExecutor(user_id) as slack:
        result = slack.send_message(channel, text)
        return result.success


# Example usage
def main():
    """Demonstrate direct execution patterns."""
    
    api_key = os.environ.get("COMPOSIO_API_KEY")
    if not api_key:
        print("Warning: COMPOSIO_API_KEY not set")
        print("Set it with: export COMPOSIO_API_KEY=your-key")
        return
    
    user_id = "demo_user_direct"
    
    print("=" * 60)
    print("Direct Tool Execution Examples")
    print("=" * 60)
    
    # Example 1: Simple single execution
    print("\n--- Example 1: Single Tool Execution ---")
    try:
        # Note: This will fail without proper GitHub connection
        result = execute_single_tool(
            "GITHUB_LIST_REPOSITORIES_FOR_A_USER",
            {"username": "octocat"},
            user_id=user_id
        )
        print(f"Success: {result.success}")
        print(f"Data: {result.data}")
    except Exception as e:
        print(f"Expected error (no connection): {e}")
    
    # Example 2: Session-based execution
    print("\n--- Example 2: Session Execution ---")
    try:
        result = execute_with_session(
            user_id=user_id,
            action="GITHUB_LIST_REPOSITORIES_FOR_A_USER",
            arguments={"username": "octocat"}
        )
        print(f"Success: {result.success}")
    except Exception as e:
        print(f"Expected error: {e}")
    
    # Example 3: Reusable executor
    print("\n--- Example 3: Tool Executor Class ---")
    try:
        with ToolExecutor(user_id) as executor:
            # List available tools
            tools = executor.list_tools(toolkits=["github"])
            print(f"Available GitHub tools: {len(tools)}")
            for tool in tools[:3]:
                print(f"  - {tool.name}")
            
            # Show execution log
            log = executor.get_execution_log()
            print(f"Execution log entries: {len(log)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 4: Specialized executor
    print("\n--- Example 4: GitHub Executor ---")
    try:
        with GitHubToolExecutor(user_id) as gh:
            # These would work with proper connection
            print("Available methods:")
            print("  - gh.star_repo(owner, repo)")
            print("  - gh.list_repos(username)")
            print("  - gh.create_issue(owner, repo, title)")
            print("  - gh.list_issues(owner, repo)")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 5: Batch operations
    print("\n--- Example 5: Batch Execution ---")
    operations = [
        {"action": "GITHUB_LIST_REPOSITORIES_FOR_A_USER", "arguments": {"username": "octocat"}},
        {"action": "GITHUB_GET_A_REPOSITORY", "arguments": {"owner": "octocat", "repo": "Hello-World"}}
    ]
    print(f"Would execute {len(operations)} operations in sequence")
    print("Operations:")
    for op in operations:
        print(f"  - {op['action']}")
    
    print("\n" + "=" * 60)
    print("Direct execution examples completed!")
    print("\nNote: Most operations require an active connection.")
    print("Use 'composio add github' to connect your GitHub account.")


if __name__ == "__main__":
    main()
