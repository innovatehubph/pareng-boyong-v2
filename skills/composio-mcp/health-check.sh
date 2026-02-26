#!/bin/bash
# ============================================================================
# Composio MCP Health Check Script
# ============================================================================
# Verifies your Composio setup is working correctly
# Run: ./health-check.sh
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

check_pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    ((PASSED++))
}

check_fail() {
    echo -e "  ${RED}✗${NC} $1"
    ((FAILED++))
}

check_warn() {
    echo -e "  ${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

check_info() {
    echo -e "  ${BLUE}ℹ${NC} $1"
}

# ============================================================================
# CHECKS BEGIN
# ============================================================================

print_header "🔍 Composio MCP Health Check"

# ----------------------------------------------------------------------------
# 1. Environment Check
# ----------------------------------------------------------------------------
print_header "1. Environment Check"

# Check for .env file
if [ -f ".env" ]; then
    check_pass ".env file exists"
    source .env
else
    check_warn ".env file not found (checking environment variables)"
fi

# Check API Key
if [ -n "$COMPOSIO_API_KEY" ]; then
    # Mask the key for display
    MASKED_KEY="${COMPOSIO_API_KEY:0:8}...${COMPOSIO_API_KEY: -4}"
    check_pass "COMPOSIO_API_KEY is set ($MASKED_KEY)"
else
    check_fail "COMPOSIO_API_KEY is not set"
    echo -e "       ${YELLOW}→ Set it with: export COMPOSIO_API_KEY=your_key${NC}"
fi

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    check_pass "Python3 installed ($PYTHON_VERSION)"
else
    check_fail "Python3 not installed"
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version 2>&1)
    check_pass "Node.js installed ($NODE_VERSION)"
else
    check_warn "Node.js not installed (optional for some features)"
fi

# Check pip packages
if python3 -c "import composio" 2>/dev/null; then
    COMPOSIO_VERSION=$(python3 -c "import composio; print(composio.__version__)" 2>/dev/null || echo "unknown")
    check_pass "composio Python package installed (v$COMPOSIO_VERSION)"
else
    check_fail "composio Python package not installed"
    echo -e "       ${YELLOW}→ Install with: pip install composio-core${NC}"
fi

# ----------------------------------------------------------------------------
# 2. API Key Validation
# ----------------------------------------------------------------------------
print_header "2. API Key Validation"

if [ -n "$COMPOSIO_API_KEY" ]; then
    # Test API key with a simple request
    API_RESPONSE=$(curl -s -w "\n%{http_code}" \
        -H "X-API-Key: $COMPOSIO_API_KEY" \
        "https://backend.composio.dev/api/v1/apps" 2>/dev/null)
    
    HTTP_CODE=$(echo "$API_RESPONSE" | tail -n1)
    BODY=$(echo "$API_RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        check_pass "API key is valid (HTTP $HTTP_CODE)"
        
        # Count available apps
        APP_COUNT=$(echo "$BODY" | python3 -c "import sys,json; data=json.load(sys.stdin); print(len(data.get('items', data)))" 2>/dev/null || echo "?")
        check_info "Available apps: $APP_COUNT"
    elif [ "$HTTP_CODE" = "401" ]; then
        check_fail "API key is invalid (HTTP 401 Unauthorized)"
    elif [ "$HTTP_CODE" = "403" ]; then
        check_fail "API key lacks permissions (HTTP 403 Forbidden)"
    else
        check_warn "Unexpected response (HTTP $HTTP_CODE)"
    fi
else
    check_fail "Cannot validate API key - not set"
fi

# ----------------------------------------------------------------------------
# 3. MCP Endpoint Check
# ----------------------------------------------------------------------------
print_header "3. MCP Server Check"

# Check if composio CLI is available
if command -v composio &> /dev/null; then
    check_pass "Composio CLI is installed"
    
    # Check CLI version
    CLI_VERSION=$(composio --version 2>/dev/null || echo "unknown")
    check_info "CLI version: $CLI_VERSION"
else
    check_warn "Composio CLI not found in PATH"
    echo -e "       ${YELLOW}→ Install with: pip install composio-core${NC}"
fi

# Check if MCP server can be started (dry run)
if command -v composio &> /dev/null; then
    if composio mcp --help &> /dev/null; then
        check_pass "MCP subcommand available"
    else
        check_warn "MCP subcommand not available (may need update)"
    fi
fi

# ----------------------------------------------------------------------------
# 4. Connected Apps Check
# ----------------------------------------------------------------------------
print_header "4. Connected Apps"

if [ -n "$COMPOSIO_API_KEY" ]; then
    # Get connected accounts
    ACCOUNTS_RESPONSE=$(curl -s \
        -H "X-API-Key: $COMPOSIO_API_KEY" \
        "https://backend.composio.dev/api/v1/connectedAccounts" 2>/dev/null)
    
    if echo "$ACCOUNTS_RESPONSE" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
        ACCOUNT_COUNT=$(echo "$ACCOUNTS_RESPONSE" | python3 -c "import sys,json; data=json.load(sys.stdin); print(len(data.get('items', [])))" 2>/dev/null || echo "0")
        
        if [ "$ACCOUNT_COUNT" -gt 0 ]; then
            check_pass "Found $ACCOUNT_COUNT connected account(s)"
            
            # List connected apps
            echo "$ACCOUNTS_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for acc in data.get('items', [])[:5]:
    app = acc.get('appName', 'unknown')
    status = acc.get('status', 'unknown')
    print(f'       → {app}: {status}')
" 2>/dev/null
        else
            check_warn "No connected accounts found"
            echo -e "       ${YELLOW}→ Connect apps at: https://app.composio.dev${NC}"
        fi
    else
        check_warn "Could not parse connected accounts response"
    fi
else
    check_fail "Cannot check connected apps - API key not set"
fi

# ----------------------------------------------------------------------------
# 5. Available Toolkits
# ----------------------------------------------------------------------------
print_header "5. Available Toolkits"

if [ -n "$COMPOSIO_API_KEY" ]; then
    # Get available apps/toolkits
    APPS_RESPONSE=$(curl -s \
        -H "X-API-Key: $COMPOSIO_API_KEY" \
        "https://backend.composio.dev/api/v1/apps?limit=100" 2>/dev/null)
    
    if echo "$APPS_RESPONSE" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
        # Show popular toolkits
        echo "$APPS_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data.get('items', data) if isinstance(data, dict) else data
popular = ['github', 'gmail', 'slack', 'notion', 'google_calendar', 'linear', 'discord', 'trello']
print('  Popular toolkits:')
for app in items[:50]:
    name = app.get('name', app.get('key', '')).lower()
    if name in popular:
        display = app.get('name', name)
        print(f'       ✓ {display}')
" 2>/dev/null
        check_pass "Toolkits API accessible"
    else
        check_warn "Could not fetch toolkits"
    fi
else
    check_fail "Cannot list toolkits - API key not set"
fi

# ----------------------------------------------------------------------------
# 6. Network Connectivity
# ----------------------------------------------------------------------------
print_header "6. Network Connectivity"

# Check Composio API
if curl -s --max-time 5 "https://backend.composio.dev/health" > /dev/null 2>&1; then
    check_pass "Composio API is reachable"
else
    check_fail "Cannot reach Composio API"
fi

# Check Composio website
if curl -s --max-time 5 "https://composio.dev" > /dev/null 2>&1; then
    check_pass "Composio website is reachable"
else
    check_warn "Cannot reach Composio website"
fi

# ============================================================================
# SUMMARY
# ============================================================================
print_header "📊 Health Check Summary"

TOTAL=$((PASSED + FAILED + WARNINGS))

echo -e "  ${GREEN}Passed:${NC}   $PASSED"
echo -e "  ${RED}Failed:${NC}   $FAILED"
echo -e "  ${YELLOW}Warnings:${NC} $WARNINGS"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "  ${GREEN}🎉 All critical checks passed!${NC}"
    echo ""
    echo -e "  Your Composio setup is healthy."
    echo -e "  Run ${BLUE}composio mcp${NC} to start the MCP server."
    exit 0
else
    echo -e "  ${RED}⚠️  Some checks failed.${NC}"
    echo ""
    echo -e "  Please fix the issues above before proceeding."
    echo -e "  See ${BLUE}troubleshooting.md${NC} for help."
    exit 1
fi
