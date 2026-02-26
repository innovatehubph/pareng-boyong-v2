#!/usr/bin/env python3
"""
Claude Max OAuth Client
=======================
Python client for making API calls using Claude Max OAuth tokens.

Usage:
    from claude_max_client import ClaudeMaxClient
    
    client = ClaudeMaxClient()
    response = await client.chat([
        {"role": "user", "content": "Hello!"}
    ])
    print(response)
"""

import os
import json
import httpx
from typing import Optional, Dict, Any, List, AsyncIterator
from pathlib import Path


ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_CODE_VERSION = "2.1.2"

# OAuth-specific headers mimicking Claude Code exactly
OAUTH_HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "anthropic-dangerous-direct-browser-access": "true",
    "anthropic-beta": "claude-code-20250219,oauth-2025-04-20,prompt-caching-2024-07-31",
    "user-agent": f"claude-cli/{CLAUDE_CODE_VERSION} (external, cli)",
    "x-app": "cli",
    "anthropic-version": "2023-06-01"
}


def is_oauth_token(api_key: str) -> bool:
    """Check if the API key is an OAuth token (starts with sk-ant-oat)"""
    return api_key and "sk-ant-oat" in api_key


def load_token_from_env() -> Optional[str]:
    """Load token from environment variables"""
    for var in ["CLAUDE_MAX_TOKEN", "API_KEY_ANTHROPIC", "API_KEY_INNOVATEHUB"]:
        token = os.environ.get(var, "").strip()
        if token and token != "None":
            return token
    return None


def load_token_from_credentials() -> Optional[str]:
    """Load token from Claude Code credentials file"""
    creds_path = Path.home() / ".claude" / ".credentials.json"
    
    if not creds_path.exists():
        return None
    
    try:
        with open(creds_path, 'r') as f:
            data = json.load(f)
        
        oauth_data = data.get("claudeAiOauth", {})
        return oauth_data.get("accessToken")
    except Exception:
        return None


def get_api_key() -> Optional[str]:
    """Get API key with priority: env vars > credentials file"""
    # Environment variables take priority
    token = load_token_from_env()
    if token:
        return token
    
    # Fall back to credentials file
    return load_token_from_credentials()


class ClaudeMaxClient:
    """Client for Claude Max OAuth API calls"""
    
    def __init__(self, api_key: Optional[str] = None, timeout: float = 300.0):
        self.api_key = api_key or get_api_key()
        self.timeout = timeout
        
        if not self.api_key:
            raise ValueError(
                "No API key found. Set CLAUDE_MAX_TOKEN env var or run 'claude auth login'"
            )
    
    def _build_headers(self) -> Dict[str, str]:
        """Build request headers"""
        headers = OAUTH_HEADERS.copy()
        
        if is_oauth_token(self.api_key):
            headers["authorization"] = f"Bearer {self.api_key}"
        else:
            headers["x-api-key"] = self.api_key
        
        return headers
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        temperature: Optional[float] = None,
        system: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make a non-streaming chat completion request.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (default: claude-sonnet-4-20250514)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            system: System prompt
            **kwargs: Additional parameters passed to the API
        
        Returns:
            API response dict
        """
        headers = self._build_headers()
        
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
            "stream": False,
        }
        
        if system:
            payload["system"] = system
        
        if temperature is not None:
            payload["temperature"] = temperature
        
        # Add any extra kwargs
        payload.update(kwargs)
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                ANTHROPIC_API_URL,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(
                    f"Anthropic API error {response.status_code}: {response.text}"
                )
            
            return response.json()
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        temperature: Optional[float] = None,
        system: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Make a streaming chat completion request.
        
        Yields:
            SSE event dicts from the API
        """
        headers = self._build_headers()
        
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
            "stream": True,
        }
        
        if system:
            payload["system"] = system
        
        if temperature is not None:
            payload["temperature"] = temperature
        
        payload.update(kwargs)
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                ANTHROPIC_API_URL,
                headers=headers,
                json=payload
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise Exception(
                        f"Anthropic API error {response.status_code}: {error_text.decode()}"
                    )
                
                async for line in response.aiter_lines():
                    line = line.strip()
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            yield json.loads(data)
                        except json.JSONDecodeError:
                            continue
    
    async def simple_chat(
        self,
        prompt: str,
        model: str = "claude-sonnet-4-20250514",
        **kwargs
    ) -> str:
        """
        Simple helper for single-turn conversations.
        
        Args:
            prompt: User prompt
            model: Model name
            **kwargs: Additional parameters
        
        Returns:
            Assistant's response text
        """
        response = await self.chat(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            **kwargs
        )
        
        return response.get("content", [{}])[0].get("text", "")


# Available models
CLAUDE_MODELS = {
    # Aliases
    "opus": "claude-opus-4-20250514",
    "sonnet": "claude-sonnet-4-20250514",
    "haiku": "claude-haiku-3-5-20250620",
    
    # Full names
    "claude-opus-4": "claude-opus-4-20250514",
    "claude-opus-4-20250514": "claude-opus-4-20250514",
    "claude-sonnet-4": "claude-sonnet-4-20250514",
    "claude-sonnet-4-20250514": "claude-sonnet-4-20250514",
    "claude-haiku-3-5": "claude-haiku-3-5-20250620",
    "claude-haiku-3-5-20250620": "claude-haiku-3-5-20250620",
}


def resolve_model(model: str) -> str:
    """Resolve model alias to full name"""
    return CLAUDE_MODELS.get(model, model)


# CLI usage
if __name__ == "__main__":
    import asyncio
    import sys
    
    async def main():
        prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Hello! What can you do?"
        
        try:
            client = ClaudeMaxClient()
            print(f"Using token: {client.api_key[:30]}...")
            print(f"Prompt: {prompt}\n")
            
            response = await client.simple_chat(prompt)
            print(f"Response:\n{response}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    asyncio.run(main())
