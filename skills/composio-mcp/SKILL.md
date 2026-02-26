# Composio MCP Skill

> Connect AI agents to 1000+ external services with unified authentication, tool discovery, and sandboxed execution.

## Overview

Composio is a comprehensive platform that enables AI agents to interact with external services like GitHub, Gmail, Slack, Notion, Google Calendar, and 980+ more applications. It handles the complexity of authentication, tool discovery, context management, and provides a sandboxed execution environment.

### Key Capabilities

| Feature | Description |
|---------|-------------|
| **1000+ Toolkits** | Pre-built integrations for popular services |
| **Unified Auth** | OAuth, API keys, and tokens managed automatically |
| **MCP Support** | Native Model Context Protocol integration |
| **Meta Tools** | Dynamic tool discovery and connection management |
| **Workbench** | Persistent Python sandbox for code execution |
| **Triggers** | Webhook and polling-based event subscriptions |
| **Multi-User** | Session isolation per user with `user_id` scoping |

---

## Installation

### Python

```bash
# Core package (required)
pip install composio

# Framework-specific packages (pick one based on your stack)
pip install composio-openai-agents   # For OpenAI Agents SDK
pip install composio-anthropic       # For Anthropic/Claude
pip install composio-langchain       # For LangChain
pip install composio-crewai          # For CrewAI
pip install composio-autogen         # For AutoGen
```

> ⚠️ **Important**: For OpenAI Agents, use `composio-openai-agents` NOT `composio-openai`. The latter is deprecated.

### TypeScript / Node.js

```bash
# Core package (required)
npm install @composio/core

# Framework-specific packages (pick one)
npm install @composio/openai-agents   # For OpenAI Agents SDK
npm install @composio/anthropic       # For Anthropic/Claude
npm install @composio/langchain       # For LangChain
npm install @composio/vercel-ai       # For Vercel AI SDK
```

### MCP Mode (No SDK Required)

For MCP clients like Claude Desktop, Cursor, or OpenClaw, you don't need framework packages. Just use the session's MCP URL directly.

### Environment Setup

```bash
# Set your Composio API key
export COMPOSIO_API_KEY="your-api-key-here"

# Optional: Set default user ID
export COMPOSIO_USER_ID="default-user"
```

Get your API key from: https://app.composio.dev/settings

---

## Quickstart

### The Session Pattern

Every Composio interaction starts with creating a **session**. Sessions are scoped to a `user_id` and manage authentication, tool access, and execution context.

```python
from composio import Composio

# Initialize Composio client
composio = Composio()

# Create a user-scoped session (REQUIRED - this is the entry point)
session = composio.create(user_id="user_123")

# Now you can access tools, connections, and workbench
tools = session.tools()
```

```typescript
import { Composio } from "@composio/core";

const composio = new Composio();
const session = await composio.create("user_123");
const tools = await session.tools();
```

### Why Sessions Matter

1. **User Isolation**: Each user's connections and data are isolated
2. **Auth Scoping**: OAuth tokens are stored per user
3. **Context Management**: Tool state persists within sessions
4. **Multi-Tenancy**: Safe for SaaS applications with multiple users

---

## MCP Integration

Composio provides first-class MCP (Model Context Protocol) support, allowing any MCP-compatible client to use Composio tools.

### Getting MCP Credentials

```python
from composio import Composio

composio = Composio()
session = composio.create(user_id="user_123")

# Get MCP connection details
mcp_url = session.mcp.url
mcp_headers = session.mcp.headers

print(f"MCP URL: {mcp_url}")
print(f"Headers: {mcp_headers}")
```

```typescript
import { Composio } from "@composio/core";

const composio = new Composio();
const session = await composio.create("user_123");

const mcpUrl = session.mcp.url;
const mcpHeaders = session.mcp.headers;
```

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "composio": {
      "command": "npx",
      "args": ["-y", "@composio/mcp-server"],
      "env": {
        "COMPOSIO_API_KEY": "your-api-key",
        "COMPOSIO_USER_ID": "your-user-id"
      }
    }
  }
}
```

### Cursor Configuration

Add to your Cursor MCP settings:

```json
{
  "composio": {
    "url": "https://mcp.composio.dev/user_123",
    "headers": {
      "Authorization": "Bearer your-api-key"
    }
  }
}
```

### OpenClaw Integration

For OpenClaw, configure the MCP server in your skill:

```yaml
name: composio
mcp:
  url: "https://mcp.composio.dev/${user_id}"
  headers:
    Authorization: "Bearer ${COMPOSIO_API_KEY}"
```

---

## Meta Tools

Composio provides 5 powerful meta tools that enable dynamic tool discovery, connection management, and execution. These are always available and don't require pre-configuration.

### 1. COMPOSIO_SEARCH_TOOLS

Search and discover tools from 1000+ available toolkits.

```
Input: { "query": "send email", "limit": 10 }
Output: List of matching tools with descriptions and schemas
```

**Use Cases:**
- Find tools for a specific task
- Discover new integrations
- Get tool schemas for dynamic invocation

### 2. COMPOSIO_MANAGE_CONNECTIONS

Manage user authentication connections to external services.

```
Input: { 
  "action": "list" | "connect" | "disconnect" | "status",
  "app": "github" | "gmail" | "slack" | ...
}
```

**Actions:**
- `list`: Show all connected apps for the user
- `connect`: Initiate OAuth flow or API key setup
- `disconnect`: Remove a connection
- `status`: Check connection health

### 3. COMPOSIO_MULTI_EXECUTE_TOOL

Execute any Composio tool by name with provided parameters.

```
Input: {
  "tool": "GITHUB_CREATE_ISSUE",
  "params": {
    "owner": "myorg",
    "repo": "myrepo",
    "title": "Bug report",
    "body": "Description here"
  }
}
```

**Features:**
- Execute any tool dynamically
- Supports all 1000+ toolkit actions
- Automatic parameter validation

### 4. COMPOSIO_REMOTE_WORKBENCH

Execute Python code in a persistent sandbox environment.

```
Input: {
  "code": "import pandas as pd\ndf = pd.read_csv('data.csv')\nprint(df.describe())"
}
```

**Features:**
- Persistent file system across calls
- Pre-installed data science libraries
- Network access for API calls
- Isolated per user

### 5. COMPOSIO_REMOTE_BASH_TOOL

Execute shell commands in the sandbox environment.

```
Input: {
  "command": "ls -la /workspace && cat config.json"
}
```

**Features:**
- Full bash shell access
- Access to workbench filesystem
- Install packages with pip/npm
- Git operations supported

---

## Native Tools Integration

For framework-specific integrations, use the `session.tools()` method to get tools in the native format.

### OpenAI Agents SDK

```python
from composio_openai_agents import Composio
from openai import OpenAI
from agents import Agent, Runner

composio = Composio()
session = composio.create(user_id="user_123")

# Get tools in OpenAI format
tools = session.tools(apps=["github", "gmail"])

# Create agent with Composio tools
agent = Agent(
    name="Assistant",
    instructions="You help users manage their GitHub and Gmail.",
    tools=tools
)

# Run the agent
client = OpenAI()
runner = Runner(agent=agent, client=client)
result = runner.run("Create a GitHub issue for the bug we discussed")
```

### Anthropic Claude

```python
from composio_anthropic import Composio
from anthropic import Anthropic

composio = Composio()
session = composio.create(user_id="user_123")

# Get tools in Anthropic format
tools = session.tools(apps=["slack", "notion"])

client = Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "Post a message to #general"}]
)

# Handle tool calls
for block in response.content:
    if block.type == "tool_use":
        result = session.execute(block.name, block.input)
```

### LangChain

```python
from composio_langchain import Composio
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent

composio = Composio()
session = composio.create(user_id="user_123")

# Get LangChain tools
tools = session.tools(apps=["google_calendar", "todoist"])

llm = ChatOpenAI(model="gpt-4")
agent = create_openai_functions_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)

result = executor.invoke({"input": "Schedule a meeting for tomorrow at 2pm"})
```

### TypeScript with Vercel AI

```typescript
import { Composio } from "@composio/vercel-ai";
import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";

const composio = new Composio();
const session = await composio.create("user_123");

const tools = await session.tools({ apps: ["linear", "github"] });

const result = await generateText({
  model: openai("gpt-4-turbo"),
  tools,
  prompt: "Create a Linear issue for the new feature request"
});
```

---

## Authentication

Composio handles authentication complexity so you don't have to. It supports OAuth 2.0, API keys, and various other auth methods.

### Connect Links (Recommended)

Generate shareable authentication links for users:

```python
from composio import Composio

composio = Composio()
session = composio.create(user_id="user_123")

# Generate a connect link for GitHub
link = session.get_connect_link(app="github")
print(f"Connect GitHub: {link}")

# User visits link, completes OAuth, returns to your app
# Connection is automatically stored for user_123
```

### Check Connection Status

```python
# Check if user has connected an app
connections = session.get_connections()
for conn in connections:
    print(f"{conn.app}: {conn.status}")

# Check specific app
github_connected = session.is_connected("github")
if not github_connected:
    link = session.get_connect_link(app="github")
    print(f"Please connect GitHub: {link}")
```

### Supported Auth Methods

| Method | Apps | How It Works |
|--------|------|--------------|
| **OAuth 2.0** | GitHub, Gmail, Slack, etc. | User authorizes via browser |
| **API Key** | OpenAI, Anthropic, etc. | User provides key directly |
| **Basic Auth** | Some REST APIs | Username/password pair |
| **Token** | Various | Bearer or custom tokens |
| **OAuth 1.0a** | Twitter (legacy) | Multi-step OAuth flow |

### Programmatic API Key Setup

```python
# Set API key for a service
session.set_api_key(
    app="openai",
    api_key="sk-..."
)

# Verify connection works
status = session.test_connection("openai")
print(f"OpenAI connection: {status}")
```

### Multi-Account Support

Users can connect multiple accounts for the same app:

```python
# List all GitHub connections for user
github_connections = session.get_connections(app="github")
for conn in github_connections:
    print(f"Account: {conn.account_id} - {conn.email}")

# Use specific account
tools = session.tools(
    apps=["github"],
    connection_id="conn_abc123"  # Specific account
)
```

---

## Toolkits Reference

Composio provides 984+ pre-built app integrations organized by category.

### Popular Toolkits

| Category | Apps |
|----------|------|
| **Version Control** | GitHub, GitLab, Bitbucket |
| **Communication** | Slack, Discord, Microsoft Teams, Gmail |
| **Project Management** | Linear, Jira, Asana, Trello, Notion |
| **CRM** | Salesforce, HubSpot, Pipedrive |
| **Calendar** | Google Calendar, Outlook Calendar |
| **Storage** | Google Drive, Dropbox, OneDrive, S3 |
| **Database** | Supabase, Airtable, Postgres, MongoDB |
| **AI/ML** | OpenAI, Anthropic, Replicate, HuggingFace |
| **E-commerce** | Shopify, Stripe, Square |
| **Social** | Twitter/X, LinkedIn, Instagram |

### Listing Available Apps

```python
# List all available apps
apps = composio.list_apps()
for app in apps:
    print(f"{app.name}: {app.description}")

# Search for specific functionality
apps = composio.search_apps(query="email")
```

### Tool Discovery

```python
# List all tools for an app
github_tools = session.list_tools(app="github")
for tool in github_tools:
    print(f"{tool.name}: {tool.description}")

# Common GitHub tools:
# - GITHUB_CREATE_ISSUE
# - GITHUB_CREATE_PULL_REQUEST
# - GITHUB_LIST_REPOSITORIES
# - GITHUB_GET_FILE_CONTENT
# - GITHUB_STAR_REPOSITORY
```

### Filtering Tools

```python
# Get only specific tools
tools = session.tools(
    apps=["github"],
    actions=["GITHUB_CREATE_ISSUE", "GITHUB_LIST_REPOSITORIES"]
)

# Exclude certain tools
tools = session.tools(
    apps=["github"],
    exclude=["GITHUB_DELETE_REPOSITORY"]
)

# Use tags
tools = session.tools(
    tags=["read-only"]  # Only read operations
)
```

---

## Triggers

Triggers allow your agent to react to external events via webhooks or polling.

### Webhook Triggers

```python
from composio import Composio

composio = Composio()
session = composio.create(user_id="user_123")

# Subscribe to GitHub events
trigger = session.create_trigger(
    app="github",
    trigger="GITHUB_PUSH_EVENT",
    config={
        "owner": "myorg",
        "repo": "myrepo"
    },
    callback_url="https://myapp.com/webhooks/composio"
)

print(f"Trigger ID: {trigger.id}")
print(f"Webhook URL: {trigger.webhook_url}")
```

### Polling Triggers

For apps without webhook support:

```python
# Poll for new emails every 5 minutes
trigger = session.create_trigger(
    app="gmail",
    trigger="GMAIL_NEW_EMAIL",
    config={
        "label": "INBOX",
        "poll_interval": 300  # seconds
    },
    callback_url="https://myapp.com/webhooks/gmail"
)
```

### Trigger Event Handling

```python
from flask import Flask, request

app = Flask(__name__)

@app.route("/webhooks/composio", methods=["POST"])
def handle_composio_webhook():
    event = request.json
    
    trigger_id = event["trigger_id"]
    trigger_name = event["trigger_name"]
    payload = event["payload"]
    
    # Handle based on trigger type
    if trigger_name == "GITHUB_PUSH_EVENT":
        commits = payload["commits"]
        branch = payload["ref"]
        # Process push event...
    
    return {"status": "ok"}
```

### Managing Triggers

```python
# List all triggers for user
triggers = session.list_triggers()

# Get trigger details
trigger = session.get_trigger(trigger_id="trg_123")

# Pause a trigger
session.pause_trigger(trigger_id="trg_123")

# Resume a trigger
session.resume_trigger(trigger_id="trg_123")

# Delete a trigger
session.delete_trigger(trigger_id="trg_123")
```

### Common Triggers

| App | Trigger | Description |
|-----|---------|-------------|
| GitHub | `GITHUB_PUSH_EVENT` | Code pushed to repository |
| GitHub | `GITHUB_PULL_REQUEST_EVENT` | PR opened/closed/merged |
| GitHub | `GITHUB_ISSUE_EVENT` | Issue created/updated |
| Slack | `SLACK_MESSAGE_RECEIVED` | New message in channel |
| Gmail | `GMAIL_NEW_EMAIL` | New email received |
| Google Calendar | `GCAL_EVENT_CREATED` | New event created |
| Stripe | `STRIPE_PAYMENT_RECEIVED` | Payment completed |

---

## Workbench

The Composio Workbench provides a persistent Python sandbox environment for code execution, data processing, and file management.

### Basic Code Execution

```python
session = composio.create(user_id="user_123")

# Execute Python code
result = session.workbench.run("""
import pandas as pd
import numpy as np

# Create sample data
data = {'name': ['Alice', 'Bob', 'Charlie'], 'score': [85, 92, 78]}
df = pd.DataFrame(data)

# Save to workspace
df.to_csv('/workspace/scores.csv', index=False)

print(df.describe())
""")

print(result.output)
```

### File Operations

```python
# Upload a file
session.workbench.upload(
    local_path="./data.csv",
    remote_path="/workspace/data.csv"
)

# Download a file
session.workbench.download(
    remote_path="/workspace/results.csv",
    local_path="./results.csv"
)

# List files
files = session.workbench.list_files("/workspace")
for f in files:
    print(f"{f.name} - {f.size} bytes")
```

### Shell Commands

```python
# Run shell commands
result = session.workbench.shell("pip install scikit-learn")
print(result.output)

# Check installed packages
result = session.workbench.shell("pip list")
print(result.output)
```

### Pre-installed Libraries

The workbench comes with common libraries pre-installed:

- **Data Science**: pandas, numpy, scipy, scikit-learn
- **Visualization**: matplotlib, seaborn, plotly
- **Web**: requests, httpx, beautifulsoup4
- **Utils**: python-dateutil, pytz, pyyaml
- **Files**: openpyxl, xlrd, python-docx

### Workbench Helpers

The workbench provides built-in helpers for common tasks:

```python
# Inside workbench code
from composio_helpers import (
    send_email,
    upload_to_drive,
    create_github_issue,
    post_to_slack
)

# These use the user's connected accounts automatically
send_email(
    to="colleague@example.com",
    subject="Analysis Complete",
    body="The data analysis is ready."
)
```

### Session Persistence

Workbench state persists across calls within a session:

```python
# First call - create data
session.workbench.run("""
data = [1, 2, 3, 4, 5]
with open('/workspace/data.txt', 'w') as f:
    f.write(str(data))
""")

# Later call - read data
result = session.workbench.run("""
with open('/workspace/data.txt', 'r') as f:
    data = eval(f.read())
print(f"Sum: {sum(data)}")
""")
# Output: Sum: 15
```

---

## CLI Reference

Composio provides a command-line interface for management and testing.

### Installation

```bash
pip install composio
```

### Authentication

```bash
# Login to Composio
composio login

# Check current user
composio whoami

# Logout
composio logout
```

### App Management

```bash
# List available apps
composio apps list

# Search apps
composio apps search "email"

# Get app details
composio apps info github
```

### Connection Management

```bash
# List user connections
composio connections list --user user_123

# Connect to an app
composio connect github --user user_123

# Disconnect from an app
composio disconnect github --user user_123

# Test a connection
composio connections test github --user user_123
```

### Tool Discovery

```bash
# List tools for an app
composio tools list github

# Get tool schema
composio tools schema GITHUB_CREATE_ISSUE

# Search tools
composio tools search "create issue"
```

### Tool Execution

```bash
# Execute a tool
composio execute GITHUB_CREATE_ISSUE \
  --user user_123 \
  --param owner=myorg \
  --param repo=myrepo \
  --param title="Bug fix" \
  --param body="Description"
```

### Triggers

```bash
# List triggers
composio triggers list --user user_123

# Create a trigger
composio triggers create \
  --user user_123 \
  --app github \
  --trigger GITHUB_PUSH_EVENT \
  --config '{"owner":"myorg","repo":"myrepo"}' \
  --callback https://myapp.com/webhook

# Delete a trigger
composio triggers delete trg_123
```

### Workbench

```bash
# Run code in workbench
composio workbench run --user user_123 --code "print('Hello')"

# Run from file
composio workbench run --user user_123 --file script.py

# Open interactive shell
composio workbench shell --user user_123
```

---

## Error Handling

### Common Errors and Solutions

```python
from composio import Composio, ComposioError
from composio.exceptions import (
    AuthenticationError,
    ConnectionError,
    ToolNotFoundError,
    RateLimitError
)

composio = Composio()

try:
    session = composio.create(user_id="user_123")
    tools = session.tools(apps=["github"])
    result = session.execute("GITHUB_CREATE_ISSUE", params={...})
    
except AuthenticationError as e:
    # User not connected to GitHub
    print(f"Please connect GitHub: {session.get_connect_link('github')}")
    
except ConnectionError as e:
    # Connection expired or revoked
    print(f"Reconnect required: {session.get_connect_link('github')}")
    
except ToolNotFoundError as e:
    # Tool doesn't exist
    print(f"Tool not found: {e.tool_name}")
    
except RateLimitError as e:
    # API rate limit hit
    print(f"Rate limited. Retry after: {e.retry_after} seconds")
    
except ComposioError as e:
    # Generic Composio error
    print(f"Error: {e.message}")
```

### Retry Logic

```python
import time
from composio import Composio
from composio.exceptions import RateLimitError

def execute_with_retry(session, tool, params, max_retries=3):
    for attempt in range(max_retries):
        try:
            return session.execute(tool, params)
        except RateLimitError as e:
            if attempt < max_retries - 1:
                time.sleep(e.retry_after or 60)
            else:
                raise
```

---

## Troubleshooting

### Connection Issues

**Problem**: "User not connected to [app]"
```python
# Check connection status
if not session.is_connected("github"):
    link = session.get_connect_link("github")
    print(f"Connect here: {link}")
```

**Problem**: "OAuth token expired"
```python
# Force re-authentication
link = session.get_connect_link("github", force=True)
```

**Problem**: "Connection test failed"
```python
# Test and diagnose
status = session.test_connection("github")
if not status.healthy:
    print(f"Issue: {status.error}")
    print(f"Suggestion: {status.suggestion}")
```

### Tool Execution Issues

**Problem**: "Missing required parameter"
```python
# Get tool schema to see required params
schema = session.get_tool_schema("GITHUB_CREATE_ISSUE")
print(f"Required: {schema.required_params}")
print(f"Optional: {schema.optional_params}")
```

**Problem**: "Tool not found"
```python
# Search for correct tool name
tools = session.search_tools("create issue github")
for tool in tools:
    print(f"{tool.name}: {tool.description}")
```

### MCP Issues

**Problem**: "MCP server not responding"
```bash
# Check MCP server status
curl -H "Authorization: Bearer $COMPOSIO_API_KEY" \
  https://mcp.composio.dev/health

# Verify credentials
composio whoami
```

**Problem**: "Tools not appearing in Claude Desktop"
1. Restart Claude Desktop after config changes
2. Check `claude_desktop_config.json` syntax
3. Verify `COMPOSIO_API_KEY` is set correctly
4. Check Claude Desktop logs: `~/Library/Logs/Claude/`

### Workbench Issues

**Problem**: "Module not found"
```python
# Install missing package
session.workbench.shell("pip install package-name")
```

**Problem**: "File not found"
```python
# List workspace contents
files = session.workbench.shell("ls -la /workspace")
print(files.output)
```

**Problem**: "Timeout during execution"
```python
# Increase timeout
result = session.workbench.run(
    code="...",
    timeout=300  # 5 minutes
)
```

### Debug Mode

Enable verbose logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or via environment
# export COMPOSIO_LOG_LEVEL=DEBUG

composio = Composio(debug=True)
```

---

## Best Practices

### 1. Always Use Sessions

```python
# ✅ Correct - scoped to user
session = composio.create(user_id="user_123")
tools = session.tools()

# ❌ Wrong - no user context
tools = composio.tools()  # This won't work!
```

### 2. Request Minimal Tools

```python
# ✅ Only request what you need
tools = session.tools(
    apps=["github"],
    actions=["GITHUB_CREATE_ISSUE", "GITHUB_LIST_REPOSITORIES"]
)

# ❌ Avoid loading all tools
tools = session.tools()  # Loads everything - slow!
```

### 3. Handle Auth Gracefully

```python
# ✅ Check before executing
if not session.is_connected("github"):
    return {"error": "Please connect GitHub", "link": session.get_connect_link("github")}

# Then execute
result = session.execute("GITHUB_CREATE_ISSUE", params)
```

### 4. Use Appropriate Integration

| Use Case | Recommendation |
|----------|----------------|
| Claude Desktop / Cursor | MCP mode (`session.mcp.url`) |
| OpenAI Agents | `composio-openai-agents` |
| Custom Agent | Native tools (`session.tools()`) |
| Simple Scripts | Direct execution (`session.execute()`) |

### 5. Secure API Keys

```python
# ✅ Use environment variables
import os
composio = Composio(api_key=os.environ["COMPOSIO_API_KEY"])

# ❌ Never hardcode keys
composio = Composio(api_key="sk-live-...")  # Don't do this!
```

---

## Examples

### GitHub PR Reviewer Agent

```python
from composio_openai_agents import Composio
from openai import OpenAI
from agents import Agent, Runner

composio = Composio()
session = composio.create(user_id="user_123")

tools = session.tools(
    apps=["github"],
    actions=[
        "GITHUB_GET_PULL_REQUEST",
        "GITHUB_LIST_PULL_REQUEST_FILES",
        "GITHUB_CREATE_REVIEW_COMMENT"
    ]
)

agent = Agent(
    name="PR Reviewer",
    instructions="""You are a code reviewer. When given a PR:
    1. Fetch the PR details
    2. List changed files
    3. Review the changes and provide constructive feedback
    4. Focus on bugs, security issues, and best practices""",
    tools=tools
)

runner = Runner(agent=agent, client=OpenAI())
result = runner.run("Review PR #42 in myorg/myrepo")
```

### Email Summarizer with Workbench

```python
session = composio.create(user_id="user_123")

# Fetch emails
emails = session.execute("GMAIL_LIST_EMAILS", {
    "max_results": 10,
    "label": "INBOX"
})

# Analyze in workbench
result = session.workbench.run(f"""
import json
from collections import Counter

emails = {json.dumps(emails)}

# Count by sender
senders = Counter(e['from'] for e in emails)
print("Top senders:")
for sender, count in senders.most_common(5):
    print(f"  {sender}: {count} emails")

# Identify action items
action_keywords = ['please', 'urgent', 'asap', 'action required']
action_items = [
    e for e in emails 
    if any(kw in e['subject'].lower() for kw in action_keywords)
]
print(f"\\nAction items: {len(action_items)}")
""")

print(result.output)
```

### Multi-App Workflow

```python
session = composio.create(user_id="user_123")

# 1. Get tasks from Linear
tasks = session.execute("LINEAR_LIST_ISSUES", {
    "status": "in_progress"
})

# 2. Create GitHub issues for each
for task in tasks:
    session.execute("GITHUB_CREATE_ISSUE", {
        "owner": "myorg",
        "repo": "myrepo",
        "title": f"[Linear] {task['title']}",
        "body": task['description']
    })

# 3. Notify on Slack
session.execute("SLACK_POST_MESSAGE", {
    "channel": "#engineering",
    "text": f"Synced {len(tasks)} Linear tasks to GitHub"
})
```

---

## Resources

- **Documentation**: https://docs.composio.dev
- **API Reference**: https://docs.composio.dev/api
- **GitHub**: https://github.com/composiohq/composio
- **Discord**: https://discord.gg/composio
- **Support**: support@composio.dev

---

## Changelog

### v1.0.0
- Initial release with 984+ app integrations
- MCP support for Claude Desktop and Cursor
- Meta tools for dynamic tool discovery
- Workbench for code execution
- Trigger support for webhooks and polling

---

*Last updated: 2026-02-24*
