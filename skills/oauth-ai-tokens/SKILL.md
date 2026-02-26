# OAuth AI Tokens Skill

Integrate and manage OAuth tokens for **Claude Max** and **Google Antigravity** to access premium AI models for free.

## Overview

This skill covers two OAuth authentication methods for accessing premium AI APIs:

| Provider | Models Available | Token Prefix |
|----------|-----------------|--------------|
| **Claude Max** | Claude Opus 4, Sonnet 4, Haiku 3.5 | `sk-ant-oat01-` |
| **Google Antigravity** | Gemini 3 Pro, Claude Opus 4.5 (via Google) | Google OAuth Bearer |

---

## Claude Max OAuth

### What is Claude Max OAuth?

Claude Max is Anthropic's premium subscription that provides OAuth tokens for API access. These tokens:
- Start with `sk-ant-oat01-` (OAuth token v1)
- Expire periodically and need refreshing
- Require specific headers mimicking Claude Code CLI
- Support all Claude models (Opus, Sonnet, Haiku)

### Token Location

Claude Code CLI stores credentials at:
```bash
~/.claude/.credentials.json
```

Structure:
```json
{
  "claudeAiOauth": {
    "accessToken": "sk-ant-oat01-...",
    "refreshToken": "sk-ant-ort01-...",
    "expiresAt": 1771926803393,
    "scopes": ["user:inference", "user:profile", "user:sessions:claude_code"],
    "subscriptionType": "max",
    "rateLimitTier": "default_claude_max_20x"
  }
}
```

### Required Headers for OAuth Tokens

When using Claude Max OAuth tokens, you MUST include these headers:

```javascript
const OAUTH_HEADERS = {
  "accept": "application/json",
  "content-type": "application/json",
  "anthropic-dangerous-direct-browser-access": "true",
  "anthropic-beta": "claude-code-20250219,oauth-2025-04-20",
  "anthropic-version": "2023-06-01",
  "user-agent": "claude-cli/2.1.2 (external, cli)",
  "x-app": "cli",
  "authorization": "Bearer sk-ant-oat01-..."  // OAuth uses Bearer, not x-api-key
};
```

### API Call Example (Python)

```python
import httpx
import os

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

def is_oauth_token(api_key: str) -> bool:
    """Check if token is OAuth (starts with sk-ant-oat)"""
    return "sk-ant-oat" in api_key

async def call_claude_max(messages, model="claude-sonnet-4-20250514", max_tokens=4096):
    api_key = os.environ.get("CLAUDE_MAX_TOKEN")
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "anthropic-version": "2023-06-01",
        "anthropic-dangerous-direct-browser-access": "true",
        "anthropic-beta": "claude-code-20250219,oauth-2025-04-20",
        "user-agent": "claude-cli/2.1.2 (external, cli)",
        "x-app": "cli",
    }
    
    # OAuth tokens use Bearer auth, not x-api-key
    if is_oauth_token(api_key):
        headers["authorization"] = f"Bearer {api_key}"
    else:
        headers["x-api-key"] = api_key
    
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
        "stream": False,
    }
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(ANTHROPIC_API_URL, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"API error {response.status_code}: {response.text}")
        
        return response.json()
```

### API Call Example (cURL)

```bash
curl -X POST https://api.anthropic.com/v1/messages \
  -H "content-type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-dangerous-direct-browser-access: true" \
  -H "anthropic-beta: claude-code-20250219,oauth-2025-04-20" \
  -H "user-agent: claude-cli/2.1.2 (external, cli)" \
  -H "x-app: cli" \
  -H "authorization: Bearer sk-ant-oat01-YOUR_TOKEN_HERE" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Token Refresh

OAuth tokens expire. To get a fresh token:

1. **From Claude Code CLI:**
   ```bash
   # Re-authenticate
   claude auth login
   
   # Export for scripts
   export CLAUDE_CODE_OAUTH_TOKEN=$(cat ~/.claude/.credentials.json | jq -r '.claudeAiOauth.accessToken')
   ```

2. **Automated Sync Script:**
   ```bash
   #!/bin/bash
   # sync-claude-token.sh
   
   TOKEN=$(cat ~/.claude/.credentials.json | jq -r '.claudeAiOauth.accessToken')
   
   if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
       echo "❌ No token found. Run 'claude auth login' first."
       exit 1
   fi
   
   echo "✅ Token: ${TOKEN:0:30}..."
   
   # Update your .env file
   sed -i "s|^CLAUDE_MAX_TOKEN=.*|CLAUDE_MAX_TOKEN=$TOKEN|" /path/to/.env
   
   echo "✅ Token synced!"
   ```

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Invalid bearer token` | Token expired or invalid | Get fresh token with `claude auth login` |
| `403 Forbidden` | Missing required headers | Add all OAuth headers (especially `anthropic-dangerous-direct-browser-access`) |
| `400 Invalid model` | Wrong model name | Use exact model names like `claude-sonnet-4-20250514` |

---

## Google Antigravity OAuth

### What is Google Antigravity?

Google Antigravity is an internal Google service that provides access to AI models including Gemini and (via Google's agreements) Claude models. It uses Google OAuth for authentication.

### Available Models

- 🧠 Gemini 3 Pro
- 🎭 Claude Opus 4.5
- 💭 Claude Opus 4.5 Thinking
- ⚡ Claude Sonnet 4.5

### OAuth Configuration

```javascript
const ANTIGRAVITY_CONFIG = {
  clientId: '1071006060591-tmhssin2h21lcre235vtolojh4g403ep.apps.googleusercontent.com',
  redirectUri: 'http://localhost:51121/oauth-callback',
  scopes: [
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/cclog',
    'https://www.googleapis.com/auth/experimentsandconfigs',
  ],
  endpoints: [
    'https://daily-cloudcode-pa.sandbox.googleapis.com',
    'https://cloudcode-pa.googleapis.com'
  ]
};
```

### Token Storage

Antigravity tokens are stored at:
```bash
~/.config/opencode/antigravity-accounts.json
```

Structure:
```json
[
  {
    "email": "user@gmail.com",
    "name": "User Name",
    "accessToken": "ya29.a0ARrdaM...",
    "refreshToken": "1//0eXYZ...",
    "projectId": "cloudaicompanion-...",
    "expiresAt": 1771930000000,
    "enabled": true,
    "addedAt": "2026-02-24T00:00:00.000Z"
  }
]
```

### OAuth Flow (Paste-Back Method)

Since the redirect URI is `localhost:51121`, a special paste-back flow is used:

1. Generate PKCE challenge
2. Redirect user to Google OAuth
3. Google redirects to localhost (fails to load)
4. User copies the full URL from address bar
5. User pastes URL back to your server
6. Server extracts code and exchanges for tokens

### PKCE Implementation

```javascript
const crypto = require('crypto');

function generatePKCE() {
  const verifier = crypto.randomBytes(32).toString('base64url');
  const challenge = crypto.createHash('sha256')
    .update(verifier)
    .digest('base64url');
  return { verifier, challenge };
}

function encodeState(payload) {
  return Buffer.from(JSON.stringify(payload), 'utf8').toString('base64url');
}

function decodeState(state) {
  const normalized = state.replace(/-/g, '+').replace(/_/g, '/');
  const padded = normalized.padEnd(
    normalized.length + ((4 - normalized.length % 4) % 4), '='
  );
  return JSON.parse(Buffer.from(padded, 'base64').toString('utf8'));
}
```

### Token Exchange

```javascript
async function exchangeCode(code, verifier) {
  const response = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
    },
    body: new URLSearchParams({
      client_id: ANTIGRAVITY_CONFIG.clientId,
      client_secret: 'YOUR_CLIENT_SECRET',
      code: code,
      code_verifier: verifier,
      grant_type: 'authorization_code',
      redirect_uri: ANTIGRAVITY_CONFIG.redirectUri,
    })
  });
  
  return response.json();
}
```

### API Call Example

```javascript
async function callAntigravity(messages, model = 'gemini-3-pro') {
  const creds = loadAntigravityCredentials();
  
  const contents = messages
    .filter(m => m.role !== 'system')
    .map(m => ({
      role: m.role === 'assistant' ? 'model' : 'user',
      parts: [{ text: m.content }]
    }));
  
  const systemInstruction = messages.find(m => m.role === 'system');
  
  const requestBody = {
    project: creds.projectId,
    model: model,
    request: {
      contents: contents,
      generationConfig: {
        temperature: 0.7,
        maxOutputTokens: 4096
      }
    },
    requestType: 'agent',
    userAgent: 'antigravity',
  };
  
  if (systemInstruction) {
    requestBody.request.systemInstruction = {
      role: 'user',
      parts: [{ text: systemInstruction.content }]
    };
  }
  
  const response = await fetch(
    `${ANTIGRAVITY_CONFIG.endpoints[0]}/v1internal:streamGenerateContent?alt=sse`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${creds.accessToken}`,
        'Content-Type': 'application/json',
        'User-Agent': 'antigravity/1.15.8 darwin/arm64',
        'X-Goog-Api-Client': 'google-cloud-sdk vscode_cloudshelleditor/0.1',
      },
      body: JSON.stringify(requestBody)
    }
  );
  
  // Parse SSE response
  const text = await response.text();
  let fullText = '';
  
  for (const line of text.split('\n')) {
    if (line.startsWith('data: ')) {
      const data = line.slice(6).trim();
      if (data && data !== '[DONE]') {
        try {
          const parsed = JSON.parse(data);
          const candidates = parsed.response?.candidates || parsed.candidates || [];
          for (const candidate of candidates) {
            for (const part of candidate.content?.parts || []) {
              if (part.text) fullText += part.text;
            }
          }
        } catch {}
      }
    }
  }
  
  return fullText;
}
```

### Loading Credentials

```javascript
function loadAntigravityCredentials() {
  const fs = require('fs');
  const authPath = process.env.HOME + '/.config/opencode/antigravity-accounts.json';
  
  if (!fs.existsSync(authPath)) return null;
  
  const data = JSON.parse(fs.readFileSync(authPath, 'utf8'));
  
  // Handle array format
  if (Array.isArray(data) && data.length > 0) {
    const account = data.find(a => a.enabled !== false) || data[0];
    return {
      accessToken: account.accessToken,
      refreshToken: account.refreshToken,
      projectId: account.projectId,
      email: account.email,
    };
  }
  
  // Handle object format
  if (data.accounts) {
    const accountId = Object.keys(data.accounts)[0];
    return data.accounts[accountId];
  }
  
  return null;
}
```

---

## Integration Patterns

### Environment Variables

```bash
# Claude Max
CLAUDE_MAX_TOKEN=sk-ant-oat01-...

# Google Antigravity
ANTIGRAVITY_ACCOUNTS_PATH=~/.config/opencode/antigravity-accounts.json
ANTIGRAVITY_ENABLED=true
```

### Best Practices

1. **Always prioritize environment variables** over cached files
2. **Check token expiry** before making API calls
3. **Implement retry logic** for token refresh
4. **Use health checks** to validate tokens periodically
5. **Store tokens securely** (not in git, use .env files)

### Health Check Script

```bash
#!/bin/bash
# check-oauth-tokens.sh

echo "=== Claude Max Token ==="
TOKEN=$(cat ~/.claude/.credentials.json 2>/dev/null | jq -r '.claudeAiOauth.accessToken')
if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
    RESULT=$(curl -s -o /dev/null -w "%{http_code}" -X POST https://api.anthropic.com/v1/messages \
      -H "content-type: application/json" \
      -H "anthropic-version: 2023-06-01" \
      -H "anthropic-dangerous-direct-browser-access: true" \
      -H "authorization: Bearer $TOKEN" \
      -d '{"model":"claude-sonnet-4-20250514","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}')
    
    if [ "$RESULT" = "200" ]; then
        echo "✅ Claude Max: Valid"
    else
        echo "❌ Claude Max: Invalid (HTTP $RESULT)"
    fi
else
    echo "⚠️ Claude Max: No token found"
fi

echo ""
echo "=== Antigravity Token ==="
ACCOUNTS=$(cat ~/.config/opencode/antigravity-accounts.json 2>/dev/null)
if [ -n "$ACCOUNTS" ]; then
    EMAIL=$(echo "$ACCOUNTS" | jq -r '.[0].email // "unknown"')
    EXPIRES=$(echo "$ACCOUNTS" | jq -r '.[0].expiresAt // 0')
    NOW=$(date +%s)000
    
    if [ "$EXPIRES" -gt "$NOW" ]; then
        echo "✅ Antigravity: Valid ($EMAIL)"
    else
        echo "❌ Antigravity: Expired ($EMAIL)"
    fi
else
    echo "⚠️ Antigravity: No accounts found"
fi
```

---

## Troubleshooting

### Claude Max Issues

| Symptom | Solution |
|---------|----------|
| `401 Invalid bearer token` | Run `claude auth login` to refresh |
| Token works in curl but not in code | Check all required headers are present |
| Frequent token expiration | Set up automated sync cron job |

### Antigravity Issues

| Symptom | Solution |
|---------|----------|
| `Connection closed` | Try alternate endpoint |
| `Invalid credentials` | Re-authenticate via OAuth flow |
| No project ID | Ensure cloud-platform scope is granted |

---

## References

- Claude Code CLI: https://docs.anthropic.com/claude-code
- Anthropic API: https://docs.anthropic.com/api
- Google OAuth 2.0: https://developers.google.com/identity/protocols/oauth2
- OpenCode Antigravity: Internal Google Cloud service

## Files

- `claude-max-client.py` - Python client for Claude Max OAuth
- `antigravity-auth-server.js` - Express server for Antigravity OAuth
- `token-sync.sh` - Script to sync tokens
- `health-check.sh` - Validate all tokens
