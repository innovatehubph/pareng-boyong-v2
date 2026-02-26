#!/bin/bash
#
# Composio MCP Config Generator
# Generates MCP configuration files for various clients
#
# Usage:
#   ./mcp-config-generator.sh [options]
#
# Options:
#   -k, --api-key KEY       Composio API key (or set COMPOSIO_API_KEY env)
#   -e, --entity-id ID      Entity ID for multi-user setup
#   -t, --target TARGET     Target client: claude, cursor, generic, all (default: all)
#   -o, --output DIR        Output directory (default: ./mcp-configs)
#   -s, --session URL       Use session-based MCP URL instead of API key
#   --session-token TOKEN   Session token for session-based auth
#   -h, --help              Show this help message
#
# Examples:
#   ./mcp-config-generator.sh -k ck_abc123 -t claude
#   ./mcp-config-generator.sh -k ck_abc123 -e user_456 -t all
#   ./mcp-config-generator.sh -s https://mcp.composio.dev/session/sess_xyz --session-token tok_123
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
API_KEY="${COMPOSIO_API_KEY:-}"
ENTITY_ID=""
TARGET="all"
OUTPUT_DIR="./mcp-configs"
SESSION_URL=""
SESSION_TOKEN=""
MCP_BASE_URL="https://mcp.composio.dev/composio"

# Print colored output
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }

# Show help
show_help() {
    head -30 "$0" | tail -25 | sed 's/^# //' | sed 's/^#//'
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -k|--api-key)
            API_KEY="$2"
            shift 2
            ;;
        -e|--entity-id)
            ENTITY_ID="$2"
            shift 2
            ;;
        -t|--target)
            TARGET="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -s|--session)
            SESSION_URL="$2"
            shift 2
            ;;
        --session-token)
            SESSION_TOKEN="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate inputs
if [[ -z "$API_KEY" && -z "$SESSION_URL" ]]; then
    print_error "Either API key (-k) or session URL (-s) is required"
    echo "Set COMPOSIO_API_KEY environment variable or use -k flag"
    exit 1
fi

if [[ -n "$SESSION_URL" && -z "$SESSION_TOKEN" ]]; then
    print_error "Session token (--session-token) is required when using session URL"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"
print_info "Output directory: $OUTPUT_DIR"

# Build headers JSON
build_headers() {
    if [[ -n "$SESSION_URL" ]]; then
        echo "{\"Authorization\": \"Bearer $SESSION_TOKEN\"}"
    elif [[ -n "$ENTITY_ID" ]]; then
        echo "{\"X-API-KEY\": \"$API_KEY\", \"X-Entity-ID\": \"$ENTITY_ID\"}"
    else
        echo "{\"X-API-KEY\": \"$API_KEY\"}"
    fi
}

# Get MCP URL
get_mcp_url() {
    if [[ -n "$SESSION_URL" ]]; then
        echo "$SESSION_URL"
    else
        echo "$MCP_BASE_URL"
    fi
}

# Generate Claude Desktop config
generate_claude_config() {
    local config_file="$OUTPUT_DIR/claude_desktop_config.json"
    local mcp_url=$(get_mcp_url)
    local headers=$(build_headers)
    
    cat > "$config_file" << EOF
{
  "mcpServers": {
    "composio": {
      "url": "$mcp_url",
      "headers": $headers
    }
  }
}
EOF
    
    print_success "Generated: $config_file"
    
    # Show installation instructions
    echo ""
    echo "  📋 Claude Desktop Installation:"
    case "$(uname -s)" in
        Darwin)
            echo "     cp $config_file ~/Library/Application\\ Support/Claude/claude_desktop_config.json"
            ;;
        Linux)
            echo "     cp $config_file ~/.config/Claude/claude_desktop_config.json"
            ;;
        MINGW*|MSYS*|CYGWIN*)
            echo "     copy $config_file %APPDATA%\\Claude\\claude_desktop_config.json"
            ;;
    esac
    echo "     Then restart Claude Desktop"
    echo ""
}

# Generate Cursor config
generate_cursor_config() {
    local config_file="$OUTPUT_DIR/cursor_mcp.json"
    local mcp_url=$(get_mcp_url)
    local headers=$(build_headers)
    
    cat > "$config_file" << EOF
{
  "mcpServers": {
    "composio": {
      "url": "$mcp_url",
      "headers": $headers
    }
  }
}
EOF
    
    print_success "Generated: $config_file"
    
    # Show installation instructions
    echo ""
    echo "  📋 Cursor Installation:"
    case "$(uname -s)" in
        Darwin|Linux)
            echo "     mkdir -p ~/.cursor && cp $config_file ~/.cursor/mcp.json"
            ;;
        MINGW*|MSYS*|CYGWIN*)
            echo "     copy $config_file %USERPROFILE%\\.cursor\\mcp.json"
            ;;
    esac
    echo "     Then enable MCP in Cursor Settings → Features → MCP"
    echo ""
}

# Generate generic MCP config
generate_generic_config() {
    local config_file="$OUTPUT_DIR/mcp_config.json"
    local mcp_url=$(get_mcp_url)
    local headers=$(build_headers)
    
    cat > "$config_file" << EOF
{
  "servers": {
    "composio": {
      "url": "$mcp_url",
      "transport": "http",
      "headers": $headers,
      "capabilities": {
        "tools": true,
        "prompts": false,
        "resources": false
      },
      "meta": {
        "name": "Composio",
        "description": "Universal API integration via Composio's 5 meta tools",
        "version": "1.0.0"
      }
    }
  },
  "tools": [
    {
      "name": "COMPOSIO_LIST_APPS",
      "description": "List all available apps/integrations"
    },
    {
      "name": "COMPOSIO_LIST_ACTIONS",
      "description": "List actions for a specific app",
      "parameters": {
        "app": "string (required) - App name (e.g., 'gmail', 'slack')"
      }
    },
    {
      "name": "COMPOSIO_MANAGE_CONNECTIONS",
      "description": "Initiate OAuth connection for an app",
      "parameters": {
        "app": "string (required) - App to connect"
      }
    },
    {
      "name": "COMPOSIO_GET_CONNECTIONS",
      "description": "List current active connections"
    },
    {
      "name": "COMPOSIO_EXECUTE_ACTION",
      "description": "Execute an action on a connected app",
      "parameters": {
        "action": "string (required) - Action ID",
        "params": "object (required) - Action parameters"
      }
    }
  ]
}
EOF
    
    print_success "Generated: $config_file"
    echo ""
}

# Generate environment file
generate_env_file() {
    local env_file="$OUTPUT_DIR/.env.composio"
    
    cat > "$env_file" << EOF
# Composio MCP Configuration
# Source this file or copy values to your environment

COMPOSIO_API_KEY=${API_KEY}
COMPOSIO_MCP_URL=$(get_mcp_url)
EOF

    if [[ -n "$ENTITY_ID" ]]; then
        echo "COMPOSIO_ENTITY_ID=${ENTITY_ID}" >> "$env_file"
    fi
    
    if [[ -n "$SESSION_URL" ]]; then
        echo "COMPOSIO_SESSION_URL=${SESSION_URL}" >> "$env_file"
        echo "COMPOSIO_SESSION_TOKEN=${SESSION_TOKEN}" >> "$env_file"
    fi
    
    print_success "Generated: $env_file"
    echo ""
}

# Generate Python snippet
generate_python_snippet() {
    local python_file="$OUTPUT_DIR/composio_mcp_client.py"
    local mcp_url=$(get_mcp_url)
    
    cat > "$python_file" << 'PYTHON_EOF'
"""
Composio MCP Client Example
Generated by mcp-config-generator.sh
"""

import os
import httpx
from typing import Any, Dict, List, Optional

class ComposioMCPClient:
    """Simple client for Composio MCP server."""
    
    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        entity_id: Optional[str] = None
    ):
        self.url = url or os.getenv("COMPOSIO_MCP_URL", "https://mcp.composio.dev/composio")
        self.api_key = api_key or os.getenv("COMPOSIO_API_KEY")
        self.entity_id = entity_id or os.getenv("COMPOSIO_ENTITY_ID")
        
        if not self.api_key:
            raise ValueError("API key required. Set COMPOSIO_API_KEY or pass api_key.")
        
        self.headers = {"X-API-KEY": self.api_key}
        if self.entity_id:
            self.headers["X-Entity-ID"] = self.entity_id
    
    def _call_tool(self, name: str, params: Dict[str, Any] = None) -> Dict:
        """Call an MCP tool."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": params or {}
            }
        }
        
        with httpx.Client() as client:
            response = client.post(self.url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    def list_apps(self) -> List[str]:
        """List available apps."""
        result = self._call_tool("COMPOSIO_LIST_APPS")
        return result.get("result", {}).get("content", [])
    
    def list_actions(self, app: str) -> List[Dict]:
        """List actions for an app."""
        result = self._call_tool("COMPOSIO_LIST_ACTIONS", {"app": app})
        return result.get("result", {}).get("content", [])
    
    def get_connections(self) -> List[str]:
        """Get current connections."""
        result = self._call_tool("COMPOSIO_GET_CONNECTIONS")
        return result.get("result", {}).get("content", [])
    
    def manage_connection(self, app: str) -> Dict:
        """Initiate connection for an app."""
        result = self._call_tool("COMPOSIO_MANAGE_CONNECTIONS", {"app": app})
        return result.get("result", {}).get("content", {})
    
    def execute_action(self, action: str, params: Dict[str, Any]) -> Dict:
        """Execute an action."""
        result = self._call_tool("COMPOSIO_EXECUTE_ACTION", {
            "action": action,
            "params": params
        })
        return result.get("result", {}).get("content", {})


if __name__ == "__main__":
    # Example usage
    client = ComposioMCPClient()
    
    print("Available apps:", client.list_apps()[:5])
    print("Current connections:", client.get_connections())
PYTHON_EOF

    print_success "Generated: $python_file"
    echo ""
}

# Main execution
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔧 Composio MCP Config Generator"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Show configuration
print_info "Configuration:"
if [[ -n "$SESSION_URL" ]]; then
    echo "  Mode: Session-based"
    echo "  URL: $SESSION_URL"
else
    echo "  Mode: API Key"
    echo "  API Key: ${API_KEY:0:10}..."
fi
if [[ -n "$ENTITY_ID" ]]; then
    echo "  Entity ID: $ENTITY_ID"
fi
echo "  Target: $TARGET"
echo ""

# Generate configs based on target
case $TARGET in
    claude)
        generate_claude_config
        ;;
    cursor)
        generate_cursor_config
        ;;
    generic)
        generate_generic_config
        ;;
    all)
        generate_claude_config
        generate_cursor_config
        generate_generic_config
        generate_env_file
        generate_python_snippet
        ;;
    *)
        print_error "Unknown target: $TARGET"
        echo "Valid targets: claude, cursor, generic, all"
        exit 1
        ;;
esac

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_success "Configuration files generated in: $OUTPUT_DIR"
echo ""

# List generated files
echo "📁 Generated files:"
ls -la "$OUTPUT_DIR" | grep -v "^total" | grep -v "^\." | awk '{print "   " $NF}'
echo ""
