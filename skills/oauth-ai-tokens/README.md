# OAuth AI Tokens

Integrate Claude Max and Google Antigravity OAuth tokens for free premium AI model access.

## Quick Start

### Claude Max (Python)

```bash
# Install dependencies
pip install httpx

# Set token (or let it auto-detect from ~/.claude/.credentials.json)
export CLAUDE_MAX_TOKEN="sk-ant-oat01-..."

# Test
python claude-max-client.py "What is 2+2?"
```

### Google Antigravity (Node.js)

```bash
# Install dependencies
npm install

# Start server
npm start
# or
node antigravity-auth-server.js

# Visit http://localhost:11440/
```

### Token Management

```bash
# Sync Claude token to all locations
./token-sync.sh

# Check all tokens health
./health-check.sh

# Check specific provider
./health-check.sh --claude
./health-check.sh --google

# JSON output for scripts
./health-check.sh --json
```

## Token Locations

| Provider | File |
|----------|------|
| Claude Max | `~/.claude/.credentials.json` |
| Antigravity | `~/.config/opencode/antigravity-accounts.json` |

## Environment Variables

```bash
# Claude Max
CLAUDE_MAX_TOKEN=sk-ant-oat01-...
API_KEY_ANTHROPIC=sk-ant-oat01-...

# Antigravity
ANTIGRAVITY_ACCOUNTS_PATH=~/.config/opencode/antigravity-accounts.json
```

## See Also

- [SKILL.md](./SKILL.md) - Full documentation with code examples
- [Anthropic Docs](https://docs.anthropic.com)
- [Google OAuth](https://developers.google.com/identity/protocols/oauth2)
