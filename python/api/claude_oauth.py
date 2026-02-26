"""
Claude Max Token Authentication Handler
Direct OAuth URL generation (no CLI dependency)
"""
import json
import os
import time
import secrets
import hashlib
import base64
import urllib.parse
from typing import Any
from python.helpers.api import ApiHandler, Request, Response
from python.helpers import files, dotenv
from python.helpers.print_style import PrintStyle


# Claude OAuth configuration (from Claude Code)
CLAUDE_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
CLAUDE_AUTH_URL = "https://claude.ai/oauth/authorize"
CLAUDE_TOKEN_URL = "https://claude.ai/api/oauth/token"

# Storage paths
TOKEN_FILE = "conf/claude_oauth.json"
OAUTH_STATE_FILE = "conf/claude_oauth_state.json"


def get_token_path() -> str:
    return files.get_abs_path(TOKEN_FILE)


def get_state_path() -> str:
    return files.get_abs_path(OAUTH_STATE_FILE)


def generate_pkce() -> tuple[str, str]:
    """Generate PKCE code verifier and challenge"""
    # Generate a random code verifier (43-128 chars)
    code_verifier = secrets.token_urlsafe(43)
    
    # Create code challenge using S256 method
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip('=')
    
    return code_verifier, code_challenge


def save_oauth_state(state: str, code_verifier: str) -> None:
    """Save OAuth state for later verification"""
    data = {
        "state": state,
        "code_verifier": code_verifier,
        "created_at": time.time()
    }
    files.write_file(get_state_path(), json.dumps(data, indent=2))


def load_oauth_state() -> dict | None:
    """Load saved OAuth state"""
    try:
        content = files.read_file(get_state_path())
        return json.loads(content)
    except Exception:
        return None


def clear_oauth_state() -> None:
    """Clear OAuth state"""
    try:
        state_path = get_state_path()
        if os.path.exists(state_path):
            os.remove(state_path)
    except Exception:
        pass


def save_token(token: str, source: str = "manual") -> dict:
    """Save Claude token"""
    data = {
        "access_token": token,
        "source": source,
        "saved_at": time.time(),
        "authenticated": True
    }
    files.write_file(get_token_path(), json.dumps(data, indent=2))
    
    # Also update .env with the access token for API usage
    env_path = files.get_abs_path(".env")
    dotenv.set_dotenv_value("API_KEY_ANTHROPIC", token, env_path)
    dotenv.set_dotenv_value("API_KEY_INNOVATEHUB", token, env_path)
    
    return data


def load_token() -> dict | None:
    """Load saved token"""
    try:
        content = files.read_file(get_token_path())
        return json.loads(content)
    except Exception:
        return None


def delete_token() -> bool:
    """Delete saved token"""
    try:
        token_path = get_token_path()
        if os.path.exists(token_path):
            os.remove(token_path)
        
        clear_oauth_state()
        
        # Also remove from .env
        env_path = files.get_abs_path(".env")
        dotenv.set_dotenv_value("API_KEY_ANTHROPIC", "", env_path)
        dotenv.set_dotenv_value("API_KEY_INNOVATEHUB", "", env_path)
        return True
    except Exception:
        return False


async def try_refresh_token() -> dict | None:
    """
    Attempt to refresh the OAuth token using the refresh token.
    Returns the new token data if successful, None otherwise.
    """
    import httpx
    
    try:
        token_data = load_token()
        if not token_data:
            return None
        
        refresh_token = token_data.get("refresh_token")
        if not refresh_token:
            PrintStyle.warning("No refresh token available")
            return None
        
        PrintStyle.info("Attempting to refresh OAuth token...")
        
        # Build refresh request (same as Claude Code)
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": CLAUDE_CLIENT_ID
        }
        
        headers = {
            "content-type": "application/json",
            "accept": "application/json",
            "user-agent": "claude-cli/2.1.2 (external, cli)",
            "x-app": "cli"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(CLAUDE_TOKEN_URL, json=payload, headers=headers)
            
            if response.status_code != 200:
                PrintStyle.error(f"Token refresh failed: {response.status_code} - {response.text}")
                return None
            
            result = response.json()
            
            # Save new tokens
            new_token_data = {
                "access_token": result.get("access_token"),
                "refresh_token": result.get("refresh_token", refresh_token),  # Keep old if not provided
                "expires_at": time.time() + result.get("expires_in", 86400),
                "subscription_type": token_data.get("subscription_type", "max"),
                "rate_limit_tier": token_data.get("rate_limit_tier", "default_claude_max_20x"),
                "source": "refresh",
                "saved_at": time.time()
            }
            
            files.write_file(get_token_path(), json.dumps(new_token_data, indent=2))
            
            # Update .env
            env_path = files.get_abs_path(".env")
            dotenv.set_dotenv_value("API_KEY_ANTHROPIC", new_token_data["access_token"], env_path)
            dotenv.set_dotenv_value("API_KEY_INNOVATEHUB", new_token_data["access_token"], env_path)
            
            PrintStyle.success("OAuth token refreshed successfully!")
            return new_token_data
            
    except Exception as e:
        PrintStyle.error(f"Token refresh error: {e}")
        return None


def generate_auth_url() -> dict:
    """Generate OAuth authorization URL with PKCE"""
    # Generate PKCE parameters
    code_verifier, code_challenge = generate_pkce()
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Save state for verification
    save_oauth_state(state, code_verifier)
    
    # Build authorization URL
    params = {
        "response_type": "code",
        "client_id": CLAUDE_CLIENT_ID,
        "redirect_uri": "https://claude.ai/oauth/callback",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
        "scope": "user:inference"
    }
    
    auth_url = f"{CLAUDE_AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    return {
        "auth_url": auth_url,
        "state": state
    }


class ClaudeOauth(ApiHandler):
    """
    Claude Max Token Authentication
    
    Endpoints:
    - GET /claude_oauth?action=status - Check authentication status
    - POST /claude_oauth (action=start_auth) - Generate OAuth URL
    - POST /claude_oauth (action=save_token) - Save token after login
    - POST /claude_oauth (action=disconnect) - Remove saved token
    """

    @staticmethod
    def requires_auth() -> bool:
        return True

    @staticmethod
    def requires_csrf() -> bool:
        return True

    @staticmethod
    def get_methods() -> list[str]:
        return ["GET", "POST"]

    async def process(self, input: Request, request: Any) -> Response:
        try:
            if request.method == "GET":
                return await self._handle_get(input)
            else:
                return await self._handle_post(input)
        except Exception as e:
            PrintStyle.error(f"Claude OAuth error: {e}")
            return Response(
                message=str(e),
                error=True,
                data={"status": "error", "message": str(e)}
            )

    async def _handle_get(self, input: Request) -> Response:
        action = input.data.get("action", "status")
        
        if action == "status":
            return self._get_status()
        else:
            return Response(
                message="Unknown action",
                error=True,
                data={"status": "error", "message": f"Unknown action: {action}"}
            )

    async def _handle_post(self, input: Request) -> Response:
        action = input.data.get("action", "")
        
        if action == "start_auth":
            return self._start_auth()
        elif action == "save_token":
            return self._save_token(input)
        elif action == "disconnect":
            return self._disconnect()
        else:
            return Response(
                message="Unknown action",
                error=True,
                data={"status": "error", "message": f"Unknown action: {action}"}
            )

    def _get_status(self) -> Response:
        """Get current authentication status"""
        token_data = load_token()
        oauth_state = load_oauth_state()
        
        # Check if there's a pending auth flow
        pending_auth = None
        if oauth_state and time.time() - oauth_state.get("created_at", 0) < 600:
            pending_auth = {
                "state": oauth_state.get("state"),
                "age_seconds": int(time.time() - oauth_state.get("created_at", 0))
            }
        
        if token_data and token_data.get("access_token"):
            token = token_data["access_token"]
            masked = f"{token[:8]}...{token[-4:]}" if len(token) > 12 else "****"
            
            saved_at = token_data.get("saved_at", 0)
            age_hours = (time.time() - saved_at) / 3600 if saved_at else 0
            
            return Response(
                message="Authenticated",
                data={
                    "status": "authenticated",
                    "authenticated": True,
                    "token_preview": masked,
                    "source": token_data.get("source", "unknown"),
                    "saved_at": saved_at,
                    "age_hours": round(age_hours, 1),
                    "pending_auth": pending_auth
                }
            )
        else:
            return Response(
                message="Not authenticated",
                data={
                    "status": "not_authenticated",
                    "authenticated": False,
                    "pending_auth": pending_auth
                }
            )

    def _start_auth(self) -> Response:
        """Generate OAuth URL for authentication"""
        try:
            result = generate_auth_url()
            return Response(
                message="Auth URL generated",
                data={
                    "status": "success",
                    "auth_url": result["auth_url"],
                    "state": result["state"],
                    "instructions": "Open the URL in a new browser tab, log in to Claude, and copy the token shown after authentication."
                }
            )
        except Exception as e:
            return Response(
                message=f"Failed to generate auth URL: {e}",
                error=True,
                data={"status": "error", "message": str(e)}
            )

    def _save_token(self, input: Request) -> Response:
        """Save token after authentication"""
        token = input.data.get("token", "").strip()
        
        if not token:
            return Response(
                message="Token required",
                error=True,
                data={"status": "error", "message": "Please provide a token"}
            )
        
        if len(token) < 20:
            return Response(
                message="Invalid token",
                error=True,
                data={"status": "error", "message": "Token appears to be too short"}
            )
        
        try:
            save_token(token, source="oauth_flow")
            clear_oauth_state()
            
            return Response(
                message="Token saved successfully",
                data={
                    "status": "success",
                    "authenticated": True,
                    "source": "oauth_flow"
                }
            )
        except Exception as e:
            return Response(
                message=f"Failed to save token: {e}",
                error=True,
                data={"status": "error", "message": str(e)}
            )

    def _disconnect(self) -> Response:
        """Remove saved token"""
        success = delete_token()
        if success:
            return Response(
                message="Disconnected successfully",
                data={"status": "success", "authenticated": False}
            )
        else:
            return Response(
                message="Failed to disconnect",
                error=True,
                data={"status": "error", "message": "Failed to remove token"}
            )
