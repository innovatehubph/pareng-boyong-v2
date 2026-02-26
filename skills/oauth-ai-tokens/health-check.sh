#!/bin/bash
#
# OAuth Tokens Health Check
# =========================
# Validates both Claude Max and Google Antigravity OAuth tokens.
#
# Usage:
#   ./health-check.sh           # Check all tokens
#   ./health-check.sh --claude  # Check Claude Max only
#   ./health-check.sh --google  # Check Google Antigravity only
#   ./health-check.sh --json    # Output as JSON
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Flags
CHECK_CLAUDE=true
CHECK_GOOGLE=true
OUTPUT_JSON=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --claude) CHECK_GOOGLE=false; shift ;;
        --google) CHECK_CLAUDE=false; shift ;;
        --json) OUTPUT_JSON=true; shift ;;
        *) shift ;;
    esac
done

# Results storage
CLAUDE_STATUS="unknown"
CLAUDE_TOKEN=""
CLAUDE_MESSAGE=""
GOOGLE_STATUS="unknown"
GOOGLE_EMAIL=""
GOOGLE_MESSAGE=""

# ============================================================================
# Claude Max Check
# ============================================================================
check_claude() {
    echo -e "${CYAN}=== Claude Max Token ===${NC}"
    
    # Try to find token
    TOKEN=""
    SOURCE=""
    
    # Check environment variable
    if [ -n "$CLAUDE_MAX_TOKEN" ]; then
        TOKEN="$CLAUDE_MAX_TOKEN"
        SOURCE="CLAUDE_MAX_TOKEN env var"
    elif [ -n "$API_KEY_ANTHROPIC" ]; then
        TOKEN="$API_KEY_ANTHROPIC"
        SOURCE="API_KEY_ANTHROPIC env var"
    fi
    
    # Check credentials file
    if [ -z "$TOKEN" ]; then
        CREDS_FILE="$HOME/.claude/.credentials.json"
        if [ -f "$CREDS_FILE" ]; then
            TOKEN=$(cat "$CREDS_FILE" | jq -r '.claudeAiOauth.accessToken // empty' 2>/dev/null || echo "")
            if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
                SOURCE="~/.claude/.credentials.json"
                
                # Check expiry
                EXPIRES=$(cat "$CREDS_FILE" | jq -r '.claudeAiOauth.expiresAt // 0' 2>/dev/null || echo "0")
                NOW=$(date +%s)000
                if [ "$EXPIRES" -gt 0 ] && [ "$EXPIRES" -lt "$NOW" ]; then
                    echo -e "${YELLOW}⚠️  Token may be expired (expiresAt: $EXPIRES)${NC}"
                fi
            fi
        fi
    fi
    
    CLAUDE_TOKEN="${TOKEN:0:30}..."
    
    if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
        echo -e "${RED}❌ No token found${NC}"
        CLAUDE_STATUS="missing"
        CLAUDE_MESSAGE="No token found in env vars or credentials file"
        return
    fi
    
    echo "Token: ${TOKEN:0:30}..."
    echo "Source: $SOURCE"
    
    # Validate token
    RESULT=$(curl -s -o /dev/null -w "%{http_code}" -X POST https://api.anthropic.com/v1/messages \
        -H "content-type: application/json" \
        -H "anthropic-version: 2023-06-01" \
        -H "anthropic-dangerous-direct-browser-access: true" \
        -H "anthropic-beta: claude-code-20250219,oauth-2025-04-20" \
        -H "authorization: Bearer $TOKEN" \
        -d '{"model":"claude-sonnet-4-20250514","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}' 2>/dev/null)
    
    if [ "$RESULT" = "200" ]; then
        echo -e "${GREEN}✅ Valid${NC}"
        CLAUDE_STATUS="valid"
        CLAUDE_MESSAGE="Token is valid and working"
    else
        echo -e "${RED}❌ Invalid (HTTP $RESULT)${NC}"
        CLAUDE_STATUS="invalid"
        CLAUDE_MESSAGE="API returned HTTP $RESULT"
    fi
}

# ============================================================================
# Google Antigravity Check
# ============================================================================
check_google() {
    echo -e "\n${CYAN}=== Google Antigravity Token ===${NC}"
    
    ACCOUNTS_FILE="$HOME/.config/opencode/antigravity-accounts.json"
    
    if [ ! -f "$ACCOUNTS_FILE" ]; then
        echo -e "${RED}❌ No accounts file found${NC}"
        echo "Expected: $ACCOUNTS_FILE"
        GOOGLE_STATUS="missing"
        GOOGLE_MESSAGE="No accounts file found at $ACCOUNTS_FILE"
        return
    fi
    
    # Parse accounts
    ACCOUNT_COUNT=$(cat "$ACCOUNTS_FILE" | jq 'length' 2>/dev/null || echo "0")
    
    if [ "$ACCOUNT_COUNT" = "0" ]; then
        echo -e "${YELLOW}⚠️  No accounts in file${NC}"
        GOOGLE_STATUS="empty"
        GOOGLE_MESSAGE="Accounts file exists but is empty"
        return
    fi
    
    echo "Accounts found: $ACCOUNT_COUNT"
    
    # Check first enabled account
    ACCOUNT=$(cat "$ACCOUNTS_FILE" | jq '.[0] // empty' 2>/dev/null)
    
    if [ -z "$ACCOUNT" ]; then
        echo -e "${RED}❌ Could not parse account${NC}"
        GOOGLE_STATUS="error"
        GOOGLE_MESSAGE="Failed to parse accounts file"
        return
    fi
    
    EMAIL=$(echo "$ACCOUNT" | jq -r '.email // "unknown"')
    EXPIRES=$(echo "$ACCOUNT" | jq -r '.expiresAt // 0')
    ACCESS_TOKEN=$(echo "$ACCOUNT" | jq -r '.accessToken // empty')
    PROJECT_ID=$(echo "$ACCOUNT" | jq -r '.projectId // "none"')
    
    GOOGLE_EMAIL="$EMAIL"
    
    echo "Email: $EMAIL"
    echo "Project ID: $PROJECT_ID"
    
    # Check expiry
    NOW=$(date +%s)000
    if [ "$EXPIRES" -gt 0 ]; then
        if [ "$EXPIRES" -lt "$NOW" ]; then
            echo -e "${YELLOW}⚠️  Token expired${NC}"
            GOOGLE_STATUS="expired"
            GOOGLE_MESSAGE="Token expired at $(date -d @$((EXPIRES/1000)) 2>/dev/null || echo $EXPIRES)"
            return
        else
            REMAINING=$(( (EXPIRES - NOW) / 1000 / 60 ))
            echo "Expires in: ${REMAINING} minutes"
        fi
    fi
    
    # Test API call
    if [ -n "$ACCESS_TOKEN" ]; then
        RESULT=$(curl -s -o /dev/null -w "%{http_code}" \
            "https://www.googleapis.com/oauth2/v1/userinfo?alt=json" \
            -H "Authorization: Bearer $ACCESS_TOKEN" 2>/dev/null)
        
        if [ "$RESULT" = "200" ]; then
            echo -e "${GREEN}✅ Valid${NC}"
            GOOGLE_STATUS="valid"
            GOOGLE_MESSAGE="Token is valid for $EMAIL"
        else
            echo -e "${RED}❌ Invalid (HTTP $RESULT)${NC}"
            GOOGLE_STATUS="invalid"
            GOOGLE_MESSAGE="API returned HTTP $RESULT"
        fi
    else
        echo -e "${RED}❌ No access token${NC}"
        GOOGLE_STATUS="missing"
        GOOGLE_MESSAGE="No access token in account"
    fi
}

# ============================================================================
# Main
# ============================================================================

if [ "$OUTPUT_JSON" = false ]; then
    echo "🔍 OAuth Tokens Health Check"
    echo "============================"
    echo ""
fi

if [ "$CHECK_CLAUDE" = true ]; then
    if [ "$OUTPUT_JSON" = false ]; then
        check_claude
    else
        check_claude > /dev/null 2>&1
    fi
fi

if [ "$CHECK_GOOGLE" = true ]; then
    if [ "$OUTPUT_JSON" = false ]; then
        check_google
    else
        check_google > /dev/null 2>&1
    fi
fi

# JSON output
if [ "$OUTPUT_JSON" = true ]; then
    cat << EOF
{
  "timestamp": "$(date -Iseconds)",
  "claude_max": {
    "status": "$CLAUDE_STATUS",
    "token_preview": "$CLAUDE_TOKEN",
    "message": "$CLAUDE_MESSAGE"
  },
  "google_antigravity": {
    "status": "$GOOGLE_STATUS",
    "email": "$GOOGLE_EMAIL",
    "message": "$GOOGLE_MESSAGE"
  }
}
EOF
else
    # Summary
    echo ""
    echo "=========================="
    echo "Summary:"
    
    if [ "$CHECK_CLAUDE" = true ]; then
        case "$CLAUDE_STATUS" in
            valid) echo -e "  Claude Max: ${GREEN}✅ Valid${NC}" ;;
            invalid) echo -e "  Claude Max: ${RED}❌ Invalid${NC}" ;;
            missing) echo -e "  Claude Max: ${YELLOW}⚠️  Missing${NC}" ;;
            *) echo -e "  Claude Max: ${YELLOW}? Unknown${NC}" ;;
        esac
    fi
    
    if [ "$CHECK_GOOGLE" = true ]; then
        case "$GOOGLE_STATUS" in
            valid) echo -e "  Antigravity: ${GREEN}✅ Valid ($GOOGLE_EMAIL)${NC}" ;;
            invalid) echo -e "  Antigravity: ${RED}❌ Invalid${NC}" ;;
            expired) echo -e "  Antigravity: ${YELLOW}⚠️  Expired${NC}" ;;
            missing) echo -e "  Antigravity: ${YELLOW}⚠️  Missing${NC}" ;;
            *) echo -e "  Antigravity: ${YELLOW}? Unknown${NC}" ;;
        esac
    fi
fi

# Exit code
if [ "$CLAUDE_STATUS" = "valid" ] || [ "$GOOGLE_STATUS" = "valid" ]; then
    exit 0
else
    exit 1
fi
