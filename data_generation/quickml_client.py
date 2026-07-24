"""Catalyst QuickML GLM chat client — self-client OAuth2 token refresh +
POST to the published chat/completions endpoint (confirmed request/response
shape via a real sample from the console's Model Details popup, OpenAI-
compatible chat-completion format). Used by narratives.py's paraphrase pass
(Phase 4) and any later pipeline stage needing an LLM call — Stage 1 intent
extraction, SQL generation, answer generation (technical.md's pipeline) all
go through this same chat() call, just different prompts/messages.
"""

from __future__ import annotations

import os
import time

import requests
from dotenv import load_dotenv

# load_dotenv()'s default search (cwd + parents) won't find a .env sitting
# in a sibling dir. streamlit_harness/.env already holds the real creds
# (same CATALYST_* names) — reuse that file instead of asking for a second
# copy of the same secrets.
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "streamlit_harness", ".env"), override=False)

# accounts.zoho.in matches the .in data center implied by the confirmed
# QUICKML_ENDPOINT_URL host (api.catalyst.zoho.in) — Zoho OAuth token
# endpoints are data-center-scoped, not a global URL.
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


def chat(
    messages: list[dict[str, str]], *, max_tokens: int = 500, temperature: float = 0.7,
    enable_thinking: bool = False,
) -> str:
    """One chat-completion call against the published GLM endpoint. Returns
    the assistant's text content. Raises on HTTP/API failure — callers that
    can tolerate a failure (see narratives.paraphrase_brief_facts) catch and
    fall back explicitly; this function never swallows errors itself.

    enable_thinking=False by default: without it, GLM emits its
    step-by-step reasoning as the response body instead of a direct answer
    (confirmed live — a paraphrase call got "1. Analyze the Request..."
    chain-of-thought instead of rewritten text). Callers whose prompt
    actually wants reasoning (e.g. a future Stage 1 intent-extraction call
    that benefits from chain-of-thought) can pass True."""
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
    # Docs' sample response shows OpenAI-style choices[0].message.content;
    # the real deployed endpoint (confirmed via a live call) instead returns
    # {"response": "...", "tool_calls": [...], "usage": {...}} — trust the
    # live shape over the doc sample.
    return resp.json()["response"]


if __name__ == "__main__":
    # Live smoke check — needs real creds in .env, hits the real endpoint.
    reply = chat([
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'ok' and nothing else."},
    ], max_tokens=10)
    print(reply)
    assert reply.strip()
