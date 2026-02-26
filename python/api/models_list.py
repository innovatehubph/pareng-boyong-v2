"""
models_list.py — Dynamic model fetching API for Pareng Boyong
Fetches available models from each provider and validates API key connectivity.

Special handling for InnovateHub (Claude Max OAuth) provider.
"""

import httpx
from typing import Any

from python.helpers.api import ApiHandler, Request, Response
import models as models_module

# ─── Current Anthropic / Claude model catalogue (fallback when API unavailable) ─────────────────
# Last synced: 2026-02
CLAUDE_MODELS_FALLBACK = [
    {"id": "claude-sonnet-4-6",          "name": "Claude Sonnet 4.6   ⭐ (current default)"},
    {"id": "claude-opus-4-6",            "name": "Claude Opus 4.6     🔥 (most capable)"},
    {"id": "claude-haiku-4-6",           "name": "Claude Haiku 4.6    ⚡ (fastest)"},
    {"id": "claude-opus-4-5-20251101",   "name": "Claude Opus 4.5"},
    {"id": "claude-haiku-4-5-20251001",  "name": "Claude Haiku 4.5"},
    {"id": "claude-sonnet-4-5-20250929", "name": "Claude Sonnet 4.5"},
    {"id": "claude-opus-4-1-20250805",   "name": "Claude Opus 4.1"},
    {"id": "claude-opus-4-20250514",     "name": "Claude Opus 4"},
    {"id": "claude-sonnet-4-20250514",   "name": "Claude Sonnet 4"},
    {"id": "claude-3-haiku-20240307",    "name": "Claude Haiku 3"},
]

# OAuth headers that mimic Claude Code identity (required for OAuth tokens)
_OAUTH_HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "anthropic-dangerous-direct-browser-access": "true",
    "anthropic-beta": "claude-code-20250219,oauth-2025-04-20,fine-grained-tool-streaming-2025-05-14,interleaved-thinking-2025-05-14,prompt-caching-2024-07-31",
    "user-agent": "claude-cli/2.1.2 (external, cli)",
    "x-app": "cli",
    "anthropic-version": "2023-06-01",
}

_HTTP_TIMEOUT = 12.0  # seconds


class ModelsList(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        provider: str = (input.get("provider") or "").lower().strip()
        api_key_ui: str = (input.get("api_key") or "").strip()
        api_base: str = (input.get("api_base") or "").rstrip("/").strip()

        if not provider:
            return {"models": [], "count": 0, "provider": "", "error": "No provider specified"}

        # API key: prefer UI-provided value (if not masked), fall back to env
        api_key = api_key_ui if (api_key_ui and "****" not in api_key_ui) else ""
        if not api_key:
            api_key = models_module.get_api_key(provider) or ""

        self._used_fallback = False  # track per-request fallback use
        try:
            model_list = await self._fetch(provider, api_key, api_base)
            resp = {
                "models": model_list,
                "count": len(model_list),
                "provider": provider,
            }
            if self._used_fallback:
                resp["fallback"] = True
                resp["warning"] = "Using cached model list — API token may need refresh (run /fresh)"
            return resp
        except Exception as exc:
            return {
                "models": [],
                "count": 0,
                "provider": provider,
                "error": str(exc),
            }

    # ─── Dispatcher ───────────────────────────────────────────────────────────────────────────

    async def _fetch(self, provider: str, api_key: str, api_base: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT, follow_redirects=True) as client:
            if provider == "innovatehub":
                return await self._fetch_innovatehub(client, api_key)
            elif provider == "anthropic":
                return await self._fetch_anthropic(client, api_key)
            elif provider == "openrouter":
                return await self._fetch_openrouter(client, api_key)
            elif provider == "google":
                return await self._fetch_google(client, api_key)
            elif provider == "ollama":
                base = api_base or "http://localhost:11434"
                return await self._fetch_ollama(client, base)
            elif provider == "lm_studio":
                base = api_base or "http://localhost:1234/v1"
                return await self._fetch_openai_compat(client, base, api_key, auth=False)
            elif provider == "groq":
                return await self._fetch_openai_compat(client, "https://api.groq.com/openai/v1", api_key)
            elif provider == "mistral":
                return await self._fetch_openai_compat(client, "https://api.mistral.ai/v1", api_key)
            elif provider == "deepseek":
                return await self._fetch_openai_compat(client, "https://api.deepseek.com", api_key)
            elif provider == "xai":
                return await self._fetch_openai_compat(client, "https://api.x.ai/v1", api_key)
            elif provider in ("openai",):
                base = api_base or "https://api.openai.com/v1"
                return await self._fetch_openai_compat(client, base, api_key)
            elif provider in ("venice", "a0_venice"):
                base = api_base or "https://api.venice.ai/api/v1"
                return await self._fetch_openai_compat(client, base, api_key)
            elif provider == "sambanova":
                return await self._fetch_openai_compat(client, "https://api.sambanova.ai/v1", api_key)
            elif provider == "cometapi":
                base = api_base or "https://api.cometapi.com/v1"
                return await self._fetch_openai_compat(client, base, api_key)
            elif provider == "other":
                if not api_base:
                    return []
                return await self._fetch_openai_compat(client, api_base, api_key)
            elif provider in ("azure",):
                # Azure needs api_base set — return empty if missing
                if not api_base:
                    return []
                return await self._fetch_openai_compat(client, api_base, api_key)
            else:
                # Generic fallback: try OpenAI-compat with api_base if set
                if api_base:
                    return await self._fetch_openai_compat(client, api_base, api_key)
                return []

    # ─── Provider implementations ─────────────────────────────────────────────────────────────

    async def _fetch_innovatehub(self, client: httpx.AsyncClient, api_key: str) -> list[dict]:
        """InnovateHub = Claude Max via OAuth. Uses Claude Code identity headers."""
        if not api_key:
            # No token available — return curated fallback
            self._used_fallback = True
            return CLAUDE_MODELS_FALLBACK

        headers = _OAUTH_HEADERS.copy()
        if "oat" in api_key:
            # OAuth token — Bearer auth
            headers["Authorization"] = f"Bearer {api_key}"
        else:
            # Regular API key
            headers["x-api-key"] = api_key

        try:
            r = await client.get("https://api.anthropic.com/v1/models", headers=headers)
            r.raise_for_status()
            data = r.json()
            result = [
                {"id": m["id"], "name": m.get("display_name", m["id"])}
                for m in data.get("data", [])
            ]
            # Add Haiku 4.6 if not returned by API yet (may not be listed but is accessible)
            known_ids = {m["id"] for m in result}
            if "claude-haiku-4-6" not in known_ids:
                result.insert(2, {"id": "claude-haiku-4-6", "name": "Claude Haiku 4.6  ⚡ (fastest)"})
            if not result:
                self._used_fallback = True
                return CLAUDE_MODELS_FALLBACK
            return result
        except Exception:
            self._used_fallback = True
            return CLAUDE_MODELS_FALLBACK

    async def _fetch_anthropic(self, client: httpx.AsyncClient, api_key: str) -> list[dict]:
        if not api_key:
            return CLAUDE_MODELS_FALLBACK
        r = await client.get(
            "https://api.anthropic.com/v1/models",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        )
        r.raise_for_status()
        return [
            {"id": m["id"], "name": m.get("display_name", m["id"])}
            for m in r.json().get("data", [])
        ]

    async def _fetch_openai_compat(
        self,
        client: httpx.AsyncClient,
        base: str,
        api_key: str,
        auth: bool = True,
    ) -> list[dict]:
        headers: dict[str, str] = {}
        if auth and api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        r = await client.get(f"{base}/models", headers=headers)
        r.raise_for_status()
        raw = r.json()
        items: list[Any] = raw.get("data", raw.get("models", []))
        return [
            {
                "id": m.get("id") or m.get("name") or "",
                "name": m.get("name") or m.get("id") or "",
            }
            for m in items
            if m.get("id") or m.get("name")
        ]

    async def _fetch_openrouter(self, client: httpx.AsyncClient, api_key: str) -> list[dict]:
        r = await client.get(
            "https://openrouter.ai/api/v1/models",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://ai.innovatehub.site/",
                "X-Title": "Pareng Boyong",
            },
        )
        r.raise_for_status()
        return [
            {"id": m["id"], "name": m.get("name", m["id"])}
            for m in r.json().get("data", [])
        ]

    async def _fetch_google(self, client: httpx.AsyncClient, api_key: str) -> list[dict]:
        r = await client.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        )
        r.raise_for_status()
        raw_models = r.json().get("models", [])
        # Filter to only generative models
        return [
            {"id": m["name"].replace("models/", ""), "name": m.get("displayName", m["name"])}
            for m in raw_models
            if "generateContent" in m.get("supportedGenerationMethods", [])
        ]

    async def _fetch_ollama(self, client: httpx.AsyncClient, base: str) -> list[dict]:
        r = await client.get(f"{base}/api/tags")
        r.raise_for_status()
        return [{"id": m["name"], "name": m["name"]} for m in r.json().get("models", [])]

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]
