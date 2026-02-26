"""
InnovateHub Claude SDK
Custom Anthropic client for OAuth tokens (Claude Max subscription)
Mimics Claude Code identity for OAuth authentication
Includes prompt caching for 90% token reduction on repeated content
"""

import os
import json
import httpx
from typing import AsyncIterator, Optional, Dict, Any, List

# TOKEN_TRACKER_HOOK_START
# Injected by token-tracker skill for exact token usage logging
def token_tracker_hook(usage_data, agent_name="pareng-boyong", model="", chat_id=""):
    """Log token usage from API response or streaming capture.

    Accepts two formats:
    1. Direct dict from streaming capture: {input_tokens, output_tokens, cache_creation, cache_read, model}
    2. Response metadata dict with nested usage: {usage: {input_tokens, ...}}
    """
    import json, os
    from datetime import datetime, timezone
    tracking_file = "/a0/tmp/token_tracking/usage_log.jsonl"
    os.makedirs(os.path.dirname(tracking_file), exist_ok=True)
    try:
        # Handle both formats
        if "input_tokens" in usage_data or "cache_creation" in usage_data:
            # Direct format from streaming capture
            usage = usage_data
        else:
            # Nested format from response metadata
            usage = usage_data.get("usage", usage_data.get("token_usage", {}))
            if not usage:
                return

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": agent_name,
            "model": model or usage.get("model", "unknown"),
            "chat_id": chat_id,
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cache_creation_tokens": usage.get("cache_creation", 0) or usage.get("cache_creation_input_tokens", 0),
            "cache_read_tokens": usage.get("cache_read", 0) or usage.get("cache_read_input_tokens", 0),
            "total_tokens": 0,
            "source": "api_hook"
        }
        record["total_tokens"] = (record["input_tokens"] + record["output_tokens"] +
                                   record["cache_creation_tokens"] + record["cache_read_tokens"])
        with open(tracking_file, "a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass  # Never break the main pipeline
# TOKEN_TRACKER_HOOK_END


ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_CODE_VERSION = "2.1.2"

# Claude Code identity - REQUIRED for OAuth tokens
CLAUDE_CODE_SYSTEM = "You are Claude Code, Anthropic's official CLI for Claude."

# OAuth-specific headers mimicking Claude Code exactly
# Added prompt-caching beta for token optimization
OAUTH_HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "anthropic-dangerous-direct-browser-access": "true",
    "anthropic-beta": "claude-code-20250219,oauth-2025-04-20,fine-grained-tool-streaming-2025-05-14,interleaved-thinking-2025-05-14,prompt-caching-2024-07-31",
    "user-agent": f"claude-cli/{CLAUDE_CODE_VERSION} (external, cli)",
    "x-app": "cli",
    "anthropic-version": "2023-06-01"
}


def is_oauth_token(api_key: str) -> bool:
    """Check if the API key is an OAuth token"""
    return "sk-ant-oat" in api_key


def get_innovatehub_api_key_DISABLED() -> Optional[str]:
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


async def get_valid_innovatehub_api_key_DISABLED() -> Optional[str]:
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


def _add_cache_control_to_system(system_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Add cache_control to system blocks for prompt caching.
    Caches system prompts to reduce token usage by up to 90%.
    
    Note: Cache breakpoint must be at the end of the system array.
    """
    if not system_blocks:
        return system_blocks
    
    result = [block.copy() for block in system_blocks]
    # Add cache_control to last system block
    if result:
        result[-1]["cache_control"] = {"type": "ephemeral"}
    return result


def _prepare_messages_for_caching(messages: List[Dict[str, Any]], max_cache_blocks: int = 3) -> List[Dict[str, Any]]:
    """
    Prepare messages for prompt caching.
    Adds cache_control to messages for context caching.
    This caches the conversation prefix, reducing tokens on follow-up messages.
    
    Note: Anthropic allows max 4 cache_control blocks total.
    We use 1 for system prompt, so max 3 for messages.
    """
    if not messages:
        return messages
    
    result = []
    cache_blocks_used = 0
    
    for i, msg in enumerate(messages):
        msg_copy = msg.copy()
        
        # Only cache if we haven't hit the limit
        # Cache early user messages (first 2 exchanges only to stay under limit)
        content = msg_copy.get("content")
        should_cache = (
            cache_blocks_used < max_cache_blocks and
            i < 4 and  # Only first 2 exchanges (4 messages)
            msg.get("role") == "user" and
            content
        )
        
        if should_cache:
            # Convert string content to list format with cache_control
            if isinstance(content, str):
                msg_copy["content"] = [
                    {
                        "type": "text",
                        "text": content,
                        "cache_control": {"type": "ephemeral"}
                    }
                ]
                cache_blocks_used += 1
            elif isinstance(content, list):
                # Already a list, add cache_control to last item
                content_copy = [c.copy() if isinstance(c, dict) else c for c in content]
                if content_copy and isinstance(content_copy[-1], dict):
                    content_copy[-1]["cache_control"] = {"type": "ephemeral"}
                    cache_blocks_used += 1
                msg_copy["content"] = content_copy
        
        result.append(msg_copy)
    
    return result


async def innovatehub_completion(
    messages: List[Dict[str, Any]],
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 8192,
    temperature: float = 0.7,
    system: Optional[str] = None,
    stream: bool = False,
    tools: Optional[List[Dict]] = None,
    enable_caching: bool = True,  # Enable prompt caching by default
    **kwargs
) -> Dict[str, Any]:
    """
    Make a completion request using InnovateHub Claude (OAuth token)
    Includes Claude Code identity for OAuth authentication
    Automatically handles token refresh if needed
    
    Prompt Caching: Enabled by default, reduces token usage by up to 90%
    for repeated system prompts and context.
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
    # Apply cache_control to system prompts for caching
    system_blocks = [
        {"type": "text", "text": CLAUDE_CODE_SYSTEM}
    ]
    if system:
        system_blocks.append({"type": "text", "text": system})
    
    # Add cache_control to system blocks (cache the system prompt)
    if enable_caching and system_blocks:
        system_blocks = _add_cache_control_to_system(system_blocks)
    
    # Prepare messages for caching
    cached_messages = _prepare_messages_for_caching(messages) if enable_caching else messages
    
    # Build request payload
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": cached_messages,
        "system": system_blocks,  # Array format with Claude Code identity
    }
    
    if temperature is not None:
        payload["temperature"] = temperature
    if tools:
        # Don't cache tools - we're already using cache blocks for system + messages
        # Anthropic limit is 4 blocks total
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
        
        result = response.json()
        
        # Log cache performance if available
        usage = result.get("usage", {})
        cache_creation = usage.get("cache_creation_input_tokens", 0)
        cache_read = usage.get("cache_read_input_tokens", 0)
        if cache_creation or cache_read:
            # Cache stats available - log for monitoring
            from python.helpers.print_style import PrintStyle
            PrintStyle(font_color="cyan", padding=False).print(
                f"💾 Cache: created={cache_creation}, read={cache_read} tokens"
            )
        
        return result


async def innovatehub_stream(
    messages: List[Dict[str, Any]],
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 8192,
    temperature: float = 0.7,
    system: Optional[str] = None,
    tools: Optional[List[Dict]] = None,
    enable_caching: bool = True,  # Enable prompt caching by default
    **kwargs
) -> AsyncIterator[Dict[str, Any]]:
    """
    Stream a completion request using InnovateHub Claude (OAuth token)
    Automatically handles token refresh if needed
    
    Prompt Caching: Enabled by default, reduces token usage by up to 90%
    for repeated system prompts and context.
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
    
    # Add cache_control to system blocks
    if enable_caching and system_blocks:
        system_blocks = _add_cache_control_to_system(system_blocks)
    
    # Prepare messages for caching
    cached_messages = _prepare_messages_for_caching(messages) if enable_caching else messages
    
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": cached_messages,
        "system": system_blocks,
        "stream": True,
    }
    
    if temperature is not None:
        payload["temperature"] = temperature
    if tools:
        # Don't cache tools - we're already using cache blocks for system + messages
        # Anthropic limit is 4 blocks total
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
                        
                        # Log cache stats from message_start event
                        if event.get("type") == "message_start":
                            usage = event.get("message", {}).get("usage", {})
                            cache_creation = usage.get("cache_creation_input_tokens", 0)
                            cache_read = usage.get("cache_read_input_tokens", 0)
                            if cache_creation or cache_read:
                                from python.helpers.print_style import PrintStyle
                                PrintStyle(font_color="cyan", padding=False).print(
                                    f"💾 Cache: created={cache_creation}, read={cache_read} tokens"
                                )
                        
                        yield event
                    except json.JSONDecodeError:
                        continue


# ============================================================
# PATCHED: Enforce environment variable priority (2026-02-24)
# This fixes stale token issues from claude_oauth.json fallback
# ============================================================

def get_innovatehub_api_key() -> Optional[str]:
    """Get API key - ENV VARS ONLY (no oauth.json fallback)"""
    token = os.environ.get('API_KEY_INNOVATEHUB', '').strip()
    if token and token not in ('', 'None'):
        return token
    token = os.environ.get('API_KEY_ANTHROPIC', '').strip()
    if token and token not in ('', 'None'):
        return token
    return None

async def get_valid_innovatehub_api_key() -> Optional[str]:
    """Get valid API key - ENV VARS ONLY (no oauth.json fallback)"""
    return get_innovatehub_api_key()
