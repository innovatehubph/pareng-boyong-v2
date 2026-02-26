# Troubleshooting Guide

Common issues and solutions for the Composio MCP Skill.

---

## Table of Contents

1. [API Key Errors](#api-key-errors)
2. [Authentication Flow Issues](#authentication-flow-issues)
3. [Rate Limits](#rate-limits)
4. [Connection Problems](#connection-problems)
5. [Provider-Specific Issues](#provider-specific-issues)
6. [MCP Server Issues](#mcp-server-issues)
7. [Getting Help](#getting-help)

---

## API Key Errors

### ❌ "Invalid API key" or "401 Unauthorized"

**Symptoms:**
- Health check fails at API validation
- `composio login` fails
- Actions return 401 errors

**Solutions:**

1. **Verify the key exists:**
   ```bash
   echo $COMPOSIO_API_KEY
   ```

2. **Check key format:**
   - Should start with `sk_` or similar prefix
   - No trailing whitespace or newlines

3. **Regenerate the key:**
   - Go to [app.composio.dev/settings](https://app.composio.dev/settings)
   - Delete the old key
   - Create a new one
   - Update your `.env` file

4. **Test directly:**
   ```bash
   curl -H "X-API-Key: $COMPOSIO_API_KEY" \
     https://backend.composio.dev/api/v1/apps
   ```

### ❌ "API key not set"

**Solutions:**

1. **Set in current shell:**
   ```bash
   export COMPOSIO_API_KEY=your_key_here
   ```

2. **Add to `.env` file:**
   ```bash
   echo "COMPOSIO_API_KEY=your_key" >> .env
   ```

3. **Source the file:**
   ```bash
   source .env
   ```

---

## Authentication Flow Issues

### ❌ OAuth callback fails

**Symptoms:**
- Browser redirects to error page
- "Callback URL mismatch" error
- App connection stuck in pending

**Solutions:**

1. **Clear and retry:**
   - Go to app.composio.dev
   - Disconnect the app
   - Try connecting again

2. **Check browser:**
   - Disable ad blockers temporarily
   - Try incognito mode
   - Use a different browser

3. **Manual connection:**
   - Some apps support API key auth instead of OAuth
   - Check the app's settings in Composio dashboard

### ❌ "App not connected" when running actions

**Symptoms:**
- Actions fail with "no connected account"
- Health check shows app not connected

**Solutions:**

1. **Connect in dashboard:**
   - Visit [app.composio.dev](https://app.composio.dev)
   - Click "Add Connection"
   - Complete the OAuth flow

2. **Verify connection:**
   ```bash
   ./health-check.sh
   ```

3. **Check entity ID:**
   - If using multi-tenant, verify `COMPOSIO_ENTITY_ID`
   - Default entity is "default"

### ❌ "Token expired" errors

**Solutions:**

1. **Refresh automatically:**
   - Composio handles token refresh automatically
   - Wait a moment and retry

2. **Reconnect if persists:**
   - Disconnect the app in dashboard
   - Connect again to get new tokens

---

## Rate Limits

### ❌ "Rate limit exceeded" or "429 Too Many Requests"

**Symptoms:**
- Actions fail intermittently
- 429 HTTP status codes
- "Slow down" messages

**Solutions:**

1. **Wait and retry:**
   ```python
   import time
   
   for attempt in range(3):
       try:
           result = toolset.execute_action(...)
           break
       except Exception as e:
           if "rate" in str(e).lower():
               time.sleep(2 ** attempt)  # Exponential backoff
           else:
               raise
   ```

2. **Check your plan:**
   - Free tier has lower limits
   - Upgrade at app.composio.dev/billing

3. **Optimize requests:**
   - Batch operations where possible
   - Cache results when appropriate
   - Reduce polling frequency

### ❌ Provider rate limits (not Composio)

**Note:** The underlying service (Gmail, GitHub, etc.) may have its own limits.

**Solutions:**
- Check provider's documentation for limits
- Implement backoff in your code
- Consider using webhooks instead of polling

---

## Connection Problems

### ❌ "Cannot reach Composio API"

**Symptoms:**
- Timeout errors
- Network connection failed
- DNS resolution errors

**Solutions:**

1. **Check internet:**
   ```bash
   curl https://backend.composio.dev/health
   ```

2. **Check DNS:**
   ```bash
   nslookup backend.composio.dev
   ```

3. **Check firewall:**
   - Ensure outbound HTTPS (443) is allowed
   - Corporate networks may block APIs

4. **Use custom endpoint (enterprise):**
   ```bash
   export COMPOSIO_API_URL=https://your-instance.composio.dev
   ```

### ❌ Proxy/SSL issues

**Solutions:**

1. **Configure proxy:**
   ```bash
   export HTTPS_PROXY=http://proxy:8080
   ```

2. **SSL certificate issues:**
   ```bash
   export REQUESTS_CA_BUNDLE=/path/to/cacert.pem
   ```

---

## Provider-Specific Issues

### 📧 Gmail

| Issue | Solution |
|-------|----------|
| "Access denied" | Re-authenticate with all scopes |
| "Quota exceeded" | Gmail API daily limit (250 quota units/user) |
| "Invalid grant" | Reconnect the account |

**Gmail Scopes Required:**
- `gmail.readonly` - Read emails
- `gmail.send` - Send emails
- `gmail.modify` - Modify labels

### 🐙 GitHub

| Issue | Solution |
|-------|----------|
| "Not found" | Check repo access permissions |
| "Forbidden" | Reconnect with repo scope |
| "Rate limited" | Wait or authenticate (5000 req/hr authenticated) |

**Required Scopes:**
- `repo` - Full repository access
- `read:org` - Organization membership

### 💬 Slack

| Issue | Solution |
|-------|----------|
| "channel_not_found" | Invite bot to the channel |
| "not_in_channel" | Bot must be member of channel |
| "missing_scope" | Reinstall with required scopes |

**Required Scopes:**
- `chat:write` - Send messages
- `channels:read` - List channels
- `users:read` - User info

### 📝 Notion

| Issue | Solution |
|-------|----------|
| "Object not found" | Share page/database with integration |
| "Restricted" | Integration lacks permissions |
| "Rate limited" | 3 requests/second limit |

**Fix "Object not found":**
1. Open the Notion page/database
2. Click "Share" → "Invite"
3. Search for your Composio integration
4. Grant access

### 📅 Google Calendar

| Issue | Solution |
|-------|----------|
| "Not found" | Calendar may be hidden/deleted |
| "Access denied" | Re-authenticate |
| "Quota exceeded" | 1,000,000 queries/day |

---

## MCP Server Issues

### ❌ MCP server won't start

**Solutions:**

1. **Check composio is installed:**
   ```bash
   composio --version
   ```

2. **Check port availability:**
   ```bash
   lsof -i :3000  # Default MCP port
   ```

3. **Start with debug:**
   ```bash
   COMPOSIO_DEBUG=true composio mcp start
   ```

### ❌ MCP client can't connect

**Solutions:**

1. **Verify server is running:**
   ```bash
   curl http://localhost:3000/health
   ```

2. **Check client config:**
   ```json
   {
     "mcpServers": {
       "composio": {
         "command": "composio",
         "args": ["mcp", "start"]
       }
     }
   }
   ```

3. **Check logs:**
   ```bash
   composio mcp start --log-level debug
   ```

### ❌ Actions not appearing in MCP client

**Solutions:**

1. **Restart MCP server after connecting apps**
2. **Verify apps are connected:**
   ```bash
   ./health-check.sh
   ```
3. **Check toolset configuration**

---

## Debug Mode

Enable detailed logging:

```bash
# Environment variable
export COMPOSIO_DEBUG=true

# Or in code
from composio import ComposioToolSet
toolset = ComposioToolSet(logging_level="DEBUG")
```

---

## Getting Help

### Self-Service

1. **Run health check:**
   ```bash
   ./health-check.sh
   ```

2. **Check documentation:**
   - [docs.composio.dev](https://docs.composio.dev)

3. **Search issues:**
   - [github.com/ComposioHQ/composio/issues](https://github.com/ComposioHQ/composio/issues)

### Community Support

- **Discord:** [discord.gg/composio](https://discord.gg/composio)
- **GitHub Discussions:** [github.com/ComposioHQ/composio/discussions](https://github.com/ComposioHQ/composio/discussions)

### When Reporting Issues

Include:

1. **Environment:**
   ```bash
   python --version
   pip show composio-core
   uname -a
   ```

2. **Error message:** Full traceback

3. **Steps to reproduce:** Minimal code example

4. **Health check output:**
   ```bash
   ./health-check.sh 2>&1
   ```

---

## Quick Reference

| Error | Likely Cause | Quick Fix |
|-------|--------------|-----------|
| 401 | Invalid API key | Regenerate key |
| 403 | Missing permissions | Reconnect app |
| 404 | Resource not found | Check IDs/names |
| 429 | Rate limited | Wait and retry |
| 500 | Server error | Retry later |
| Timeout | Network issue | Check connection |
| "not connected" | App not linked | Connect in dashboard |
