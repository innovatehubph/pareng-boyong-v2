"""
Composio MCP Python Examples

This package contains examples for different Composio integration patterns:

- basic_agent.py: OpenAI Agents SDK with Composio tools
- mcp_integration.py: Direct MCP protocol usage (no providers)
- direct_execution.py: Direct tool execution patterns

Quick Start:
    # Install dependencies
    pip install -r requirements.txt
    
    # Set environment variables
    export COMPOSIO_API_KEY=your-key
    export OPENAI_API_KEY=your-key
    
    # Run examples
    python basic_agent.py
    python mcp_integration.py
    python direct_execution.py
"""

from pathlib import Path

EXAMPLES_DIR = Path(__file__).parent
ROOT_DIR = EXAMPLES_DIR.parent.parent

__all__ = ["EXAMPLES_DIR", "ROOT_DIR"]
