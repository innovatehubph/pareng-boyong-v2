"""
InnovateHub Claude SDK
Custom Anthropic client for OAuth tokens (Claude Max subscription)
Mimics Claude Code identity for OAuth authentication
"""

import os
import json
import httpx
from typing import AsyncIterator, Optional, Dict, Any, List

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_CODE_VERSION = "2.1.2"

# Claude Code identity - REQUIRED for OAuth tokens
CLAUDE_CODE_SYSTEM = "You are Claude Code, Anthropic's official CLI for Claude."

# OAuth-specific headers mimicking Claude Code exactly
OAUTH_HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "anthropic-dangerous-direct-browser-access": "true",
    "anthropic-beta": "claude-code-20250219,oauth-2025-04-20,fine-grained-tool-streaming-2025-05-14,interleaved-thinking-2025-05-14",
    "user-agent": f"claude-cli/{CLAUDE_CODE_VERSION} (external, cli)",
    "x-app": "cli",
    "anthropic-version": "2023-06-01"
}


def is_oauth_token(api_key: str) -> bool:
    """Check if the API key is an OAuth token"""
    return "sk-ant-oat" in api_key


def get_innovatehub_api_key() -> Optional[str]:
    """Get the InnovateHub API key from environment or OAuth storage"""
    import time

    # First try environment variables
    api_key = os.environ.get("API_KEY_INNOVATEHUB") or os.environ.get("API_KEY_ANTHROPIC")
    if api_key:
        return api_key

    # Try loading from OAuth storage
    try:
        oauth_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "conf", "claude_oauth.json")
        if os.path.exists(oauth_path):
            with open(oauth_path, 'r') as f:
                tokens = json.load(f)
            # Check if token is expired
            expires_at = tokens.get("expires_at", 0)
            if expires_at and time.time() < expires_at:
                return tokens.get("access_token")
            # Token is expired, but return it anyway - caller should handle refresh
            elif expires_at:
                return tokens.get("access_token")
    except Exception:
        pass

    return None


async def get_valid_innovatehub_api_key() -> Optional[str]:
    """
    Get a valid InnovateHub API key, attempting token refresh if needed.
    This should be used before making API calls.
    """
    import time

    # First try environment variables (always valid)
    api_key = os.environ.get("API_KEY_INNOVATEHUB") or os.environ.get("API_KEY_ANTHROPIC")
    if api_key:
        return api_key

    # Try loading from OAuth storage
    try:
        oauth_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "conf", "claude_oauth.json")
        if os.path.exists(oauth_path):
            with open(oauth_path, 'r') as f:
                tokens = json.load(f)

            expires_at = tokens.get("expires_at", 0)
            current_time = time.time()

            # Token is still valid
            if expires_at and current_time < expires_at:
                return tokens.get("access_token")

            # Token is expired, try to refresh
            refresh_token = tokens.get("refresh_token")
            if refresh_token and expires_at and current_time > expires_at:
                try:
                    # Attempt refresh via API
                    from python.api.claude_oauth import try_refresh_token
                    refreshed = await try_refresh_token()
                    if refreshed:
                        return refreshed.get("access_token")
                except Exception:
                    pass

            # Return expired token anyway - let API call fail with proper error
            return tokens.get("access_token")

    except Exception:
        pass

    return None


async def innovatehub_completion(
    messages: List[Dict[str, Any]],
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 8192,
    temperature: float = 0.7,
    system: Optional[str] = None,
    stream: bool = False,
    tools: Optional[List[Dict]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Make a completion request using InnovateHub Claude (OAuth token)
    Includes Claude Code identity for OAuth authentication
    Automatically handles token refresh if needed
    """
    api_key = await get_valid_innovatehub_api_key()
    if not api_key:
        raise ValueError("No InnovateHub API key found. Set API_KEY_INNOVATEHUB environment variable or authenticate via OAuth.")
    
    headers = OAUTH_HEADERS.copy()
    
    # OAuth tokens use Authorization Bearer, not x-api-key
    if is_oauth_token(api_key):
        headers["authorization"] = f"Bearer {api_key}"
    else:
        headers["x-api-key"] = api_key
    
    # Build system prompt with Claude Code identity (REQUIRED for OAuth)
    system_blocks = [
        {"type": "text", "text": CLAUDE_CODE_SYSTEM}
    ]
    if system:
        system_blocks.append({"type": "text", "text": system})
    
    # Build request payload
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
        "system": system_blocks,  # Array format with Claude Code identity
    }
    
    if temperature is not None:
        payload["temperature"] = temperature
    if tools:
        payload["tools"] = tools
    if stream:
        payload["stream"] = True
        
    # Add any extra kwargs
    for k, v in kwargs.items():
        if k not in payload:
            payload[k] = v
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(ANTHROPIC_API_URL, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Anthropic API error {response.status_code}: {response.text}")
        
        return response.json()


async def innovatehub_stream(
    messages: List[Dict[str, Any]],
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 8192,
    temperature: float = 0.7,
    system: Optional[str] = None,
    tools: Optional[List[Dict]] = None,
    **kwargs
) -> AsyncIterator[Dict[str, Any]]:
    """
    Stream a completion request using InnovateHub Claude (OAuth token)
    Automatically handles token refresh if needed
    """
    api_key = await get_valid_innovatehub_api_key()
    if not api_key:
        raise ValueError("No InnovateHub API key found. Set API_KEY_INNOVATEHUB environment variable or authenticate via OAuth.")
    
    headers = OAUTH_HEADERS.copy()
    
    if is_oauth_token(api_key):
        headers["authorization"] = f"Bearer {api_key}"
    else:
        headers["x-api-key"] = api_key
    
    # Build system prompt with Claude Code identity
    system_blocks = [
        {"type": "text", "text": CLAUDE_CODE_SYSTEM}
    ]
    if system:
        system_blocks.append({"type": "text", "text": system})
    
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
        "system": system_blocks,
        "stream": True,
    }
    
    if temperature is not None:
        payload["temperature"] = temperature
    if tools:
        payload["tools"] = tools
    for k, v in kwargs.items():
        if k not in payload:
            payload[k] = v
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        async with client.stream("POST", ANTHROPIC_API_URL, headers=headers, json=payload) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                raise Exception(f"Anthropic API error {response.status_code}: {error_text.decode()}")
            
            async for line in response.aiter_lines():
                line = line.strip()
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        event = json.loads(data)
                        yield event
                    except json.JSONDecodeError:
                        continue
