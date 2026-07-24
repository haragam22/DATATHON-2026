"""Catalyst QuickML GLM chat client — self-client OAuth2 token refresh +
POST to the published chat/completions endpoint. Self-contained copy of
data_generation/quickml_client.py: Catalyst Functions deploy as isolated
packages, no cross-directory imports from the repo's data_generation/ tree,
so the client lives here too rather than as a shared dependency that would
require a packaging step neither module currently has.

Real response shape (confirmed live, differs from the docs' OpenAI-style
sample): {"response": "...", "tool_calls": [...], "usage": {...}}.

Required env vars (set via Catalyst console -> this Function -> Environment
Variables, never committed to catalyst-config.json):
  QUICKML_ENDPOINT_URL, CATALYST_ORG_ID,
  CATALYST_REFRESH_TOKEN, CATALYST_CLIENT_ID, CATALYST_CLIENT_SECRET
"""

from __future__ import annotations

import os
import time

import requests

_ACCOUNTS_URL = os.environ.get("CATALYST_ACCOUNTS_URL", "https://accounts.zoho.in/oauth/v2/token")
_MODEL = os.environ.get("QUICKML_MODEL", "crm-di-glm47b_30b_it")

_token_cache: dict[str, float | str] = {"access_token": "", "expires_at": 0.0}


def _refresh_access_token() -> str:
    resp = requests.post(_ACCOUNTS_URL, data={
        "refresh_token": os.environ["CATALYST_REFRESH_TOKEN"],
        "client_id": os.environ["CATALYST_CLIENT_ID"],
        "client_secret": os.environ["CATALYST_CLIENT_SECRET"],
        "grant_type": "refresh_token",
    }, timeout=30)
    resp.raise_for_status()
    body = resp.json()
    if "access_token" not in body:
        raise RuntimeError(f"QuickML token refresh failed: {body}")
    _token_cache["access_token"] = body["access_token"]
    _token_cache["expires_at"] = time.time() + body.get("expires_in", 3600) - 60
    return body["access_token"]


def _access_token() -> str:
    if time.time() >= _token_cache["expires_at"]:
        return _refresh_access_token()
    return _token_cache["access_token"]


def get_access_token() -> str:
    """Public alias — the same self-client OAuth token also authenticates
    the Zia AutoML predict endpoint (risk_score.py, Phase 15), just with a
    different Authorization header prefix (Zoho-oauthtoken, not Bearer)."""
    return _access_token()


def chat(
    messages: list[dict[str, str]], *, max_tokens: int = 500, temperature: float = 0.7,
    enable_thinking: bool = False,
) -> str:
    """One chat-completion call against the published GLM endpoint. Raises
    on HTTP/API failure — callers decide whether/how to fall back; this
    function never swallows errors (CLAUDE.md's no-silent-failure rule)."""
    resp = requests.post(
        os.environ["QUICKML_ENDPOINT_URL"],
        json={
            "model": _MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
            "chat_template_kwargs": {"enable_thinking": enable_thinking},
        },
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_access_token()}",
            "CATALYST-ORG": os.environ["CATALYST_ORG_ID"],
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["response"]
