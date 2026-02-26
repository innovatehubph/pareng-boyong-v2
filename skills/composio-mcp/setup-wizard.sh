#!/bin/bash
# ============================================================================
# Composio MCP Setup Wizard
# ============================================================================
# Interactive setup script for Composio MCP integration
# Run: ./setup-wizard.sh
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

# Helper functions
print_banner() {
    clear
    echo -e "${CYAN}"
    echo "  ╔═══════════════════════════════════════════════════════════╗"
    echo "  ║                                                           ║"
    echo "  ║     🔧 Composio MCP Setup Wizard                         ║"
    echo "  ║                                                           ║"
    echo "  ║     Connect AI agents to 100+ tools & services           ║"
    echo "  ║                                                           ║"
    echo "  ╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}  Step $1: $2${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

ask() {
    echo -e -n "${CYAN}?${NC} $1 "
}

# ============================================================================
# WIZARD STEPS
# ============================================================================

print_banner

echo -e "  This wizard will help you set up Composio MCP integration."
echo -e "  Estimated time: ${BOLD}5 minutes${NC}"
echo ""
echo -e "  ${YELLOW}Prerequisites:${NC}"
echo -e "    • Composio account (free at https://app.composio.dev)"
echo -e "    • API key from Composio dashboard"
echo ""

read -p "  Press Enter to continue or Ctrl+C to exit..."

# ----------------------------------------------------------------------------
# Step 1: Check Dependencies
# ----------------------------------------------------------------------------
print_step "1/5" "Checking Dependencies"

MISSING_DEPS=()

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    success "Python3 found: $PYTHON_VERSION"
else
    error "Python3 not found"
    MISSING_DEPS+=("python3")
fi

# Check pip
if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
    PIP_CMD=$(command -v pip3 || command -v pip)
    success "pip found: $PIP_CMD"
else
    error "pip not found"
    MISSING_DEPS+=("pip")
fi

# Check Node.js (optional)
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version 2>&1)
    success "Node.js found: $NODE_VERSION (optional)"
else
    warn "Node.js not found (optional - needed for some integrations)"
fi

# Check curl
if command -v curl &> /dev/null; then
    success "curl found"
else
    error "curl not found"
    MISSING_DEPS+=("curl")
fi

# Handle missing dependencies
if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo ""
    error "Missing required dependencies: ${MISSING_DEPS[*]}"
    echo ""
    echo -e "  Install them with:"
    
    # Detect OS
    if [ -f /etc/debian_version ]; then
        echo -e "    ${CYAN}sudo apt update && sudo apt install -y ${MISSING_DEPS[*]}${NC}"
    elif [ -f /etc/redhat-release ]; then
        echo -e "    ${CYAN}sudo yum install -y ${MISSING_DEPS[*]}${NC}"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "    ${CYAN}brew install ${MISSING_DEPS[*]}${NC}"
    fi
    
    echo ""
    read -p "  Install dependencies now? [y/N]: " INSTALL_DEPS
    
    if [[ "$INSTALL_DEPS" =~ ^[Yy]$ ]]; then
        if [ -f /etc/debian_version ]; then
            sudo apt update && sudo apt install -y "${MISSING_DEPS[@]}"
        elif [ -f /etc/redhat-release ]; then
            sudo yum install -y "${MISSING_DEPS[@]}"
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            brew install "${MISSING_DEPS[@]}"
        fi
    else
        error "Cannot continue without dependencies"
        exit 1
    fi
fi

# ----------------------------------------------------------------------------
# Step 2: Install Composio Package
# ----------------------------------------------------------------------------
print_step "2/5" "Installing Composio Package"

# Check if already installed
if python3 -c "import composio" 2>/dev/null; then
    CURRENT_VERSION=$(python3 -c "import composio; print(composio.__version__)" 2>/dev/null || echo "unknown")
    success "Composio already installed (v$CURRENT_VERSION)"
    
    ask "Upgrade to latest version? [y/N]:"
    read UPGRADE
    
    if [[ "$UPGRADE" =~ ^[Yy]$ ]]; then
        info "Upgrading composio-core..."
        pip install --upgrade composio-core
        success "Upgraded successfully"
    fi
else
    info "Installing composio-core..."
    pip install composio-core
    
    if python3 -c "import composio" 2>/dev/null; then
        success "Composio installed successfully"
    else
        error "Installation failed"
        exit 1
    fi
fi

# ----------------------------------------------------------------------------
# Step 3: Configure API Key
# ----------------------------------------------------------------------------
print_step "3/5" "Configure API Key"

# Check existing key
EXISTING_KEY=""
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE" 2>/dev/null
    EXISTING_KEY="$COMPOSIO_API_KEY"
fi

if [ -n "$EXISTING_KEY" ]; then
    MASKED="${EXISTING_KEY:0:8}...${EXISTING_KEY: -4}"
    info "Existing API key found: $MASKED"
    
    ask "Keep existing key? [Y/n]:"
    read KEEP_KEY
    
    if [[ "$KEEP_KEY" =~ ^[Nn]$ ]]; then
        EXISTING_KEY=""
    fi
fi

if [ -z "$EXISTING_KEY" ]; then
    echo ""
    echo -e "  ${BOLD}Get your API key:${NC}"
    echo -e "    1. Go to ${CYAN}https://app.composio.dev/settings${NC}"
    echo -e "    2. Click 'API Keys' → 'Create API Key'"
    echo -e "    3. Copy the key"
    echo ""
    
    ask "Paste your Composio API key:"
    read -s API_KEY
    echo ""
    
    if [ -z "$API_KEY" ]; then
        error "API key cannot be empty"
        exit 1
    fi
    
    # Validate the key
    info "Validating API key..."
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "X-API-Key: $API_KEY" \
        "https://backend.composio.dev/api/v1/apps?limit=1")
    
    if [ "$HTTP_CODE" = "200" ]; then
        success "API key is valid"
        COMPOSIO_API_KEY="$API_KEY"
    else
        error "Invalid API key (HTTP $HTTP_CODE)"
        echo -e "  Please check your key and try again."
        exit 1
    fi
else
    COMPOSIO_API_KEY="$EXISTING_KEY"
fi

# ----------------------------------------------------------------------------
# Step 4: Create .env File
# ----------------------------------------------------------------------------
print_step "4/5" "Creating Configuration"

# Create .env file
cat > "$ENV_FILE" << EOF
# Composio MCP Configuration
# Generated by setup-wizard.sh on $(date)

# API Key (required)
COMPOSIO_API_KEY=$COMPOSIO_API_KEY

# Optional: Default entity ID for multi-tenant setups
# COMPOSIO_ENTITY_ID=default

# Optional: Enable debug logging
# COMPOSIO_DEBUG=true

# Optional: Custom API endpoint (for enterprise)
# COMPOSIO_API_URL=https://backend.composio.dev

# Optional: Timeout in seconds
# COMPOSIO_TIMEOUT=30
EOF

success "Created $ENV_FILE"

# Set restrictive permissions
chmod 600 "$ENV_FILE"
success "Set secure permissions (600)"

# Also configure CLI
if command -v composio &> /dev/null; then
    info "Configuring Composio CLI..."
    composio login --api-key "$COMPOSIO_API_KEY" 2>/dev/null || true
    success "CLI configured"
fi

# ----------------------------------------------------------------------------
# Step 5: Run First Test
# ----------------------------------------------------------------------------
print_step "5/5" "Running First Test"

info "Testing Composio connection..."

# Create a test script
TEST_SCRIPT=$(mktemp)
cat > "$TEST_SCRIPT" << 'PYTHON'
import os
import sys

# Load .env
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

try:
    from composio import ComposioToolSet
    
    toolset = ComposioToolSet()
    
    # Get available apps
    apps = toolset.get_apps()
    print(f"✓ Connected to Composio successfully!")
    print(f"✓ Available apps: {len(apps)}")
    
    # Show some examples
    app_names = [app.name for app in apps[:5]]
    print(f"  Examples: {', '.join(app_names)}...")
    
    sys.exit(0)
except Exception as e:
    print(f"✗ Connection failed: {e}")
    sys.exit(1)
PYTHON

cd "$SCRIPT_DIR"
if python3 "$TEST_SCRIPT"; then
    success "All tests passed!"
else
    error "Test failed - check your configuration"
    rm -f "$TEST_SCRIPT"
    exit 1
fi

rm -f "$TEST_SCRIPT"

# ============================================================================
# COMPLETION
# ============================================================================

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  🎉 Setup Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  ${BOLD}Next Steps:${NC}"
echo ""
echo -e "  1. ${CYAN}Connect Apps${NC}"
echo -e "     Visit https://app.composio.dev to connect Gmail, GitHub, etc."
echo ""
echo -e "  2. ${CYAN}Run Health Check${NC}"
echo -e "     ./health-check.sh"
echo ""
echo -e "  3. ${CYAN}Try Examples${NC}"
echo -e "     python examples/use-cases/email-summarizer.py"
echo ""
echo -e "  4. ${CYAN}Start MCP Server${NC}"
echo -e "     composio mcp start"
echo ""
echo -e "  ${BOLD}Documentation:${NC}"
echo -e "    • README.md - Quick start guide"
echo -e "    • docs/ - Detailed documentation"
echo -e "    • troubleshooting.md - Common issues"
echo ""
echo -e "  ${BOLD}Support:${NC}"
echo -e "    • https://docs.composio.dev"
echo -e "    • https://discord.gg/composio"
echo ""
