# Composio MCP Skill

> Connect AI agents to 100+ tools and services via MCP (Model Context Protocol)

[![Composio](https://img.shields.io/badge/Composio-MCP-blue)](https://composio.dev)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## What is Composio?

**Composio** is a platform that provides managed authentication and tool integrations for AI agents. It handles OAuth flows, API credentials, and rate limits so your AI can focus on getting work done.

**MCP (Model Context Protocol)** is a standard for connecting AI models to external tools. Composio's MCP server exposes 100+ integrations as tools that any MCP-compatible AI can use.

### Key Features

- 🔐 **Managed Auth** - OAuth, API keys, and credentials handled securely
- 🔧 **100+ Integrations** - GitHub, Gmail, Slack, Notion, and more
- ⚡ **One-Line Setup** - Simple API key, no complex config
- 🤖 **MCP Compatible** - Works with Claude, GPT, and other MCP clients

---

## Quick Start

### 1. Installation (One-Liner)

```bash
pip install composio-core && composio login
```

### 2. Get Your API Key

1. Sign up at [app.composio.dev](https://app.composio.dev)
2. Go to **Settings → API Keys**
3. Create and copy your key

### 3. Configure

```bash
export COMPOSIO_API_KEY=your_api_key_here
```

Or use the setup wizard:

```bash
./setup-wizard.sh
```

### 4. Connect Apps

Visit [app.composio.dev](https://app.composio.dev) and connect the services you want to use (Gmail, GitHub, Slack, etc.)

### 5. Start the MCP Server

```bash
composio mcp start
```

---

## Quick Example

```python
from composio import ComposioToolSet, Action

# Initialize
toolset = ComposioToolSet()

# Send a Slack message
result = toolset.execute_action(
    action=Action.SLACK_SEND_MESSAGE,
    params={
        "channel": "general",
        "text": "Hello from Composio!"
    }
)

print(result)
```

---

## Available Integrations

| Category | Apps |
|----------|------|
| **Communication** | Gmail, Slack, Discord, Microsoft Teams |
| **Development** | GitHub, GitLab, Linear, Jira |
| **Productivity** | Notion, Google Docs, Trello, Asana |
| **Calendar** | Google Calendar, Outlook Calendar |
| **Storage** | Google Drive, Dropbox, OneDrive |
| **CRM** | Salesforce, HubSpot, Pipedrive |
| **Social** | Twitter/X, LinkedIn, Reddit |

[View all 100+ integrations →](https://docs.composio.dev/apps)

---

## Project Structure

```
composio-mcp/
├── README.md           # This file
├── setup-wizard.sh     # Interactive setup
├── health-check.sh     # Verify installation
├── troubleshooting.md  # Common issues
├── .env.example        # Environment template
│
├── docs/               # Detailed documentation
│   ├── getting-started.md
│   ├── authentication.md
│   └── actions-reference.md
│
├── examples/
│   ├── basic/          # Simple examples
│   └── use-cases/      # Complete applications
│       ├── email-summarizer.py
│       ├── github-issue-tracker.py
│       ├── slack-notifier.py
│       └── notion-sync.py
│
└── src/                # Core implementation
    └── composio-skill.ts
```

---

## Use Case Examples

### 📧 Email Summarizer
Summarize your unread Gmail emails:
```bash
python examples/use-cases/email-summarizer.py --limit 10
```

### 🐙 GitHub Issue Tracker
List and manage GitHub issues:
```bash
python examples/use-cases/github-issue-tracker.py list --repo owner/repo
```

### 💬 Slack Notifier
Send notifications to Slack:
```bash
python examples/use-cases/slack-notifier.py send -c general -m "Hello!"
```

### 📝 Notion Sync
Sync data to Notion databases:
```bash
python examples/use-cases/notion-sync.py list-databases
```

---

## MCP Configuration

Add to your MCP client config (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "composio": {
      "command": "composio",
      "args": ["mcp", "start"],
      "env": {
        "COMPOSIO_API_KEY": "your_api_key"
      }
    }
  }
}
```

---

## Verification

Run the health check to verify your setup:

```bash
./health-check.sh
```

Expected output:
```
✓ COMPOSIO_API_KEY is set
✓ API key is valid
✓ Gmail is connected
✓ GitHub is connected
🎉 All checks passed!
```

---

## Troubleshooting

See [troubleshooting.md](troubleshooting.md) for common issues.

Quick fixes:
- **API key invalid**: Verify at app.composio.dev/settings
- **App not connected**: Connect apps at app.composio.dev
- **Rate limited**: Wait and retry, or check usage limits

---

## Links

- 📚 **Documentation**: [docs.composio.dev](https://docs.composio.dev)
- 🎮 **Dashboard**: [app.composio.dev](https://app.composio.dev)
- 💬 **Discord**: [discord.gg/composio](https://discord.gg/composio)
- 🐙 **GitHub**: [github.com/ComposioHQ/composio](https://github.com/ComposioHQ/composio)

---

## License

MIT License - see [LICENSE](LICENSE) for details.
