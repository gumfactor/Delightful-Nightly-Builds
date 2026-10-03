"""Optional AI layer: a short 'where I left off' summary per session via the Anthropic API."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Callable

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"
Transport = Callable[[dict[str, Any], str], dict[str, Any]]


class SummarizeError(RuntimeError):
    pass


def _http_transport(payload: dict[str, Any], api_key: str) -> dict[str, Any]:
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json", "x-api-key": api_key, "anthropic-version": "2023-06-01"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise SummarizeError(str(exc)) from exc


def build_payload(session: dict[str, Any]) -> dict[str, Any]:
    files = ", ".join(sorted(session["files"], key=session["files"].get, reverse=True)[:6]) or "none"
    material = (
        f"Project: {session['project']}\nFirst request: {session['first_prompt'][:600]}\n"
        f"Last request: {session['last_prompt'][:600]}\nFiles edited: {files}\n"
        f"Final assistant message: {session['last_assistant'][:900]}"
    )
    return {
        "model": MODEL,
        "max_tokens": 160,
        "system": "You summarise coding-assistant sessions for the person who ran them. In two plain sentences, "
        "say what was being worked on and where it stopped (done, blocked, or half-finished). No preamble.",
        "messages": [{"role": "user", "content": material}],
    }


def summarize_session(session: dict[str, Any], api_key: str, transport: Transport = _http_transport) -> str:
    response = transport(build_payload(session), api_key)
    blocks = response.get("content") if isinstance(response, dict) else None
    if not isinstance(blocks, list):
        raise SummarizeError("unexpected API response shape")
    text = " ".join(b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text").strip()
    if not text:
        raise SummarizeError("empty summary returned")
    return text


def summarize_missing(store: Any, sessions: list[dict[str, Any]], limit: int = 25,
                      transport: Transport = _http_transport, api_key: str | None = None) -> dict[str, int]:
    """Summarise the most recent sessions that lack a cached summary. Failures are counted, not fatal."""
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise SummarizeError("ANTHROPIC_API_KEY is not set")
    done = failed = 0
    for session in sessions:
        if done + failed >= limit:
            break
        if session.get("summary") or not (session["first_prompt"] or session["last_assistant"]):
            continue
        try:
            text = summarize_session(session, key, transport)
        except SummarizeError:
            failed += 1
            continue
        store.save_summary(session["source"], text)
        session["summary"] = text
        done += 1
    return {"summarized": done, "failed": failed}
