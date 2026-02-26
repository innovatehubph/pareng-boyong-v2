#!/bin/bash
#
# Token Sync Script
# =================
# Syncs Claude Max OAuth token from Claude Code CLI credentials
# to environment files and application configs.
#
# Usage:
#   ./token-sync.sh                    # Auto-detect and sync
#   ./token-sync.sh /path/to/.env      # Sync to specific .env file
#   CLAUDE_CODE_OAUTH_TOKEN=sk-... ./token-sync.sh  # Use provided token
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔄 Claude Max Token Sync"
echo "========================"

# Try to get token from various sources
TOKEN=""

# 1. Check environment variable
if [ -n "$CLAUDE_CODE_OAUTH_TOKEN" ]; then
    TOKEN="$CLAUDE_CODE_OAUTH_TOKEN"
    echo -e "${GREEN}✓${NC} Token from CLAUDE_CODE_OAUTH_TOKEN env var"
fi

# 2. Check Claude Code credentials file
if [ -z "$TOKEN" ]; then
    CREDS_FILE="$HOME/.claude/.credentials.json"
    if [ -f "$CREDS_FILE" ]; then
        TOKEN=$(cat "$CREDS_FILE" | jq -r '.claudeAiOauth.accessToken // empty' 2>/dev/null || echo "")
        if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
            echo -e "${GREEN}✓${NC} Token from $CREDS_FILE"
        fi
    fi
fi

# 3. Check alternative credential location
if [ -z "$TOKEN" ]; then
    ALT_CREDS="$HOME/.config/claude/credentials.json"
    if [ -f "$ALT_CREDS" ]; then
        TOKEN=$(cat "$ALT_CREDS" | jq -r '.accessToken // empty' 2>/dev/null || echo "")
        if [ -n "$TOKEN" ]; then
            echo -e "${GREEN}✓${NC} Token from $ALT_CREDS"
        fi
    fi
fi

# Validate token
if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo -e "${RED}❌ No token found!${NC}"
    echo ""
    echo "Please do one of the following:"
    echo "  1. Run 'claude auth login' to authenticate Claude Code"
    echo "  2. Set CLAUDE_CODE_OAUTH_TOKEN environment variable"
    echo "  3. Ensure ~/.claude/.credentials.json exists"
    exit 1
fi

# Show token preview
echo -e "${GREEN}✓${NC} Found token: ${TOKEN:0:30}..."

# Validate token format
if [[ ! "$TOKEN" == sk-ant-oat* ]]; then
    echo -e "${YELLOW}⚠️  Warning: Token doesn't look like OAuth token (expected sk-ant-oat prefix)${NC}"
fi

# Target .env file
ENV_FILE="${1:-$HOME/.env}"

# Function to update a file
update_env_file() {
    local file="$1"
    local key="$2"
    local value="$3"
    
    if [ ! -f "$file" ]; then
        echo "$key=$value" > "$file"
        echo -e "${GREEN}✓${NC} Created $file with $key"
        return
    fi
    
    if grep -q "^$key=" "$file" 2>/dev/null; then
        # Use different sed syntax for macOS vs Linux
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|^$key=.*|$key=$value|" "$file"
        else
            sed -i "s|^$key=.*|$key=$value|" "$file"
        fi
        echo -e "${GREEN}✓${NC} Updated $key in $file"
    else
        echo "$key=$value" >> "$file"
        echo -e "${GREEN}✓${NC} Added $key to $file"
    fi
}

# Update common locations
echo ""
echo "Updating token locations..."

# Update specified or default .env file
if [ -f "$ENV_FILE" ] || [ "$ENV_FILE" = "$HOME/.env" ]; then
    update_env_file "$ENV_FILE" "CLAUDE_MAX_TOKEN" "$TOKEN"
    update_env_file "$ENV_FILE" "API_KEY_ANTHROPIC" "$TOKEN"
fi

# Update common project locations if they exist
COMMON_LOCATIONS=(
    "$HOME/pareng-boyong-v5/.env"
    "$HOME/pareng-boyong-data/conf/claude_oauth.json"
    "/root/pareng-boyong-v5/.env"
    "/root/pareng-boyong-data/conf/claude_oauth.json"
)

for loc in "${COMMON_LOCATIONS[@]}"; do
    if [ -f "$loc" ]; then
        if [[ "$loc" == *.json ]]; then
            # Update JSON file
            EXPIRES_AT=$(($(date +%s) + 86400 * 30))  # 30 days from now
            cat > "$loc" << EOF
{
  "access_token": "$TOKEN",
  "expires_at": ${EXPIRES_AT}000,
  "saved_at": $(date +%s)000,
  "source": "token_sync_script",
  "authenticated": true
}
EOF
            echo -e "${GREEN}✓${NC} Updated $loc"
        else
            # Update .env file
            update_env_file "$loc" "API_KEY_ANTHROPIC" "$TOKEN"
            update_env_file "$loc" "API_KEY_INNOVATEHUB" "$TOKEN"
        fi
    fi
done

# Test the token
echo ""
echo "Testing token..."

RESULT=$(curl -s -o /dev/null -w "%{http_code}" -X POST https://api.anthropic.com/v1/messages \
    -H "content-type: application/json" \
    -H "anthropic-version: 2023-06-01" \
    -H "anthropic-dangerous-direct-browser-access: true" \
    -H "anthropic-beta: claude-code-20250219,oauth-2025-04-20" \
    -H "authorization: Bearer $TOKEN" \
    -d '{"model":"claude-sonnet-4-20250514","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}' 2>/dev/null)

if [ "$RESULT" = "200" ]; then
    echo -e "${GREEN}✅ Token is valid!${NC}"
else
    echo -e "${RED}❌ Token validation failed (HTTP $RESULT)${NC}"
    echo "The token may be expired. Try running 'claude auth login' again."
    exit 1
fi

echo ""
echo "🎉 Token sync complete!"
