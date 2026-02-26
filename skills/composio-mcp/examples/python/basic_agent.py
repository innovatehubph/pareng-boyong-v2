"""
Basic OpenAI Agents Example with Composio Tools

This example demonstrates how to create an AI agent using OpenAI's
Agents SDK with Composio tools for GitHub operations.

Requirements:
    pip install openai-agents composio composio-openai-agents

Environment:
    OPENAI_API_KEY=your-openai-key
    COMPOSIO_API_KEY=your-composio-key
"""

import os
import asyncio
import logging
from typing import List, Optional

# OpenAI Agents SDK
from agents import Agent, Runner, function_tool
from agents.mcp import MCPServerSse

# Composio
from composio import Composio
from composio_openai_agents import OpenAIAgentsProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_github_agent(user_id: str) -> Agent:
    """
    Create an agent with GitHub tools from Composio.
    
    Args:
        user_id: The user ID for Composio session
        
    Returns:
        Configured Agent with GitHub capabilities
    """
    # Initialize Composio with OpenAI Agents provider
    composio = Composio(provider=OpenAIAgentsProvider())
    
    # Create session for the user
    session = composio.create(user_id=user_id)
    
    # Get GitHub tools
    tools = session.tools(toolkits=["github"])
    
    logger.info(f"Loaded {len(tools)} GitHub tools for user {user_id}")
    
    # Create the agent with Composio tools
    agent = Agent(
        name="GitHub Assistant",
        instructions="""You are a helpful GitHub assistant. You can:
        - Star and unstar repositories
        - List repositories for users/organizations
        - Get repository information
        - Create issues
        - List and create pull requests
        - Manage repository settings
        
        Always confirm before making changes to repositories.
        Be helpful and explain what actions you're taking.""",
        tools=tools,
        model="gpt-4o"
    )
    
    return agent


async def run_github_agent(user_id: str, task: str) -> str:
    """
    Run the GitHub agent with a specific task.
    
    Args:
        user_id: User identifier
        task: Task description for the agent
        
    Returns:
        Agent's response
    """
    agent = create_github_agent(user_id)
    
    logger.info(f"Running agent with task: {task}")
    
    # Run the agent
    result = await Runner.run(
        agent=agent,
        input=task
    )
    
    return result.final_output


def create_multi_tool_agent(user_id: str, toolkits: List[str]) -> Agent:
    """
    Create an agent with multiple Composio toolkits.
    
    Args:
        user_id: User identifier
        toolkits: List of toolkit names (e.g., ["github", "slack", "gmail"])
        
    Returns:
        Agent with multiple tool capabilities
    """
    composio = Composio(provider=OpenAIAgentsProvider())
    session = composio.create(user_id=user_id)
    
    # Get tools from all specified toolkits
    tools = session.tools(toolkits=toolkits)
    
    logger.info(f"Loaded {len(tools)} tools from toolkits: {toolkits}")
    
    # Build instructions based on available toolkits
    toolkit_descriptions = {
        "github": "GitHub repository management",
        "slack": "Slack messaging and channel operations", 
        "gmail": "Email reading and sending",
        "notion": "Notion page and database operations",
        "linear": "Linear issue tracking",
        "jira": "Jira project management",
        "calendar": "Google Calendar management"
    }
    
    capabilities = [
        toolkit_descriptions.get(t, f"{t} operations") 
        for t in toolkits
    ]
    
    agent = Agent(
        name="Multi-Tool Assistant",
        instructions=f"""You are a helpful assistant with access to:
        {chr(10).join(f'- {cap}' for cap in capabilities)}
        
        Help the user with tasks across these services.
        Always confirm before taking actions that modify data.
        Explain what you're doing at each step.""",
        tools=tools,
        model="gpt-4o"
    )
    
    return agent


async def run_with_mcp_server(user_id: str, task: str) -> str:
    """
    Alternative: Run agent using MCP server connection.
    
    This approach uses MCP protocol instead of direct tool injection,
    which can be more flexible for complex setups.
    
    Args:
        user_id: User identifier
        task: Task for the agent
        
    Returns:
        Agent response
    """
    # Initialize Composio (no provider needed for MCP)
    composio = Composio()
    session = composio.create(user_id=user_id)
    
    # Get MCP endpoint
    mcp_url = session.mcp.url
    mcp_headers = session.mcp.headers
    
    logger.info(f"Connecting to MCP server: {mcp_url}")
    
    # Create MCP server connection
    mcp_server = MCPServerSse(
        url=mcp_url,
        headers=mcp_headers
    )
    
    # Create agent with MCP server
    agent = Agent(
        name="MCP GitHub Assistant",
        instructions="""You are a helpful assistant with access to various tools
        through the MCP server. Help the user with their requests.""",
        mcp_servers=[mcp_server],
        model="gpt-4o"
    )
    
    result = await Runner.run(
        agent=agent,
        input=task
    )
    
    return result.final_output


class GitHubAgentManager:
    """
    Manager class for handling multiple GitHub agent sessions.
    
    Useful for applications that need to manage agents for multiple users.
    """
    
    def __init__(self):
        self.composio = Composio(provider=OpenAIAgentsProvider())
        self._agents: dict = {}
        self._sessions: dict = {}
    
    def get_agent(self, user_id: str) -> Agent:
        """Get or create an agent for a user."""
        if user_id not in self._agents:
            session = self.composio.create(user_id=user_id)
            self._sessions[user_id] = session
            
            tools = session.tools(toolkits=["github"])
            
            self._agents[user_id] = Agent(
                name=f"GitHub Assistant ({user_id})",
                instructions="You are a helpful GitHub assistant.",
                tools=tools,
                model="gpt-4o"
            )
        
        return self._agents[user_id]
    
    async def run(self, user_id: str, task: str) -> str:
        """Run a task for a specific user."""
        agent = self.get_agent(user_id)
        result = await Runner.run(agent=agent, input=task)
        return result.final_output
    
    def cleanup(self, user_id: Optional[str] = None):
        """Clean up agent and session resources."""
        if user_id:
            self._agents.pop(user_id, None)
            if user_id in self._sessions:
                self._sessions[user_id].close()
                del self._sessions[user_id]
        else:
            self._agents.clear()
            for session in self._sessions.values():
                session.close()
            self._sessions.clear()


# Example usage and main entry point
async def main():
    """Main example demonstrating different usage patterns."""
    
    # Check for required environment variables
    if not os.environ.get("COMPOSIO_API_KEY"):
        print("Warning: COMPOSIO_API_KEY not set")
        print("Set it with: export COMPOSIO_API_KEY=your-key")
        return
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set")
        print("Set it with: export OPENAI_API_KEY=your-key")
        return
    
    user_id = "demo_user_123"
    
    print("=" * 60)
    print("OpenAI Agents + Composio Example")
    print("=" * 60)
    
    # Example 1: Simple GitHub agent
    print("\n--- Example 1: GitHub Agent ---")
    try:
        result = await run_github_agent(
            user_id=user_id,
            task="List the top 5 trending Python repositories on GitHub"
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Multi-tool agent
    print("\n--- Example 2: Multi-Tool Agent ---")
    try:
        agent = create_multi_tool_agent(
            user_id=user_id,
            toolkits=["github", "slack"]
        )
        print(f"Created agent with {len(agent.tools)} tools")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 3: Using MCP server
    print("\n--- Example 3: MCP Server Connection ---")
    try:
        result = await run_with_mcp_server(
            user_id=user_id,
            task="What repositories does composio have?"
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
