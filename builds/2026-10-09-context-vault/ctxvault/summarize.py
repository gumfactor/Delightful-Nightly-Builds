"""AI session summaries via the Anthropic Messages API (stdlib HTTP, key from env)."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Callable

from . import store

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-5-5"
MAX_TRANSCRIPT_CHARS = 24_000
LIST_KEYS = ("decisions", "open_threads", "next_steps")

PROMPT = """You are indexing a past AI coding session so the user can resume the work later.
Read the transcript and reply with ONLY a JSON object with these keys:
"title" (max 80 chars), "goal" (one sentence), "decisions" (list of concrete decisions made),
"open_threads" (list of unfinished items, unresolved bugs or unanswered questions),
"next_steps" (list of the most sensible next actions). Use short plain sentences.
Use empty lists when there is nothing. Do not invent facts not in the transcript.

Transcript:
"""

Completer = Callable[[str], str]


class SummarizeError(RuntimeError):
    pass


def condense(messages: list[dict], limit: int = MAX_TRANSCRIPT_CHARS) -> str:
    """Render messages compactly; keep the start and end when over the limit."""
    lines = [f"{m['role'].upper()}: {m['text'][:1500]}" for m in messages]
    text = "\n\n".join(lines)
    if len(text) <= limit:
        return text
    half = limit // 2
    return text[:half] + "\n\n[... middle of session omitted ...]\n\n" + text[-half:]


def parse_summary(raw: str) -> dict:
    """Extract the JSON object from a model reply (tolerates code fences and prose)."""
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not match:
        raise SummarizeError("model reply contained no JSON object")
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise SummarizeError(f"model reply was not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SummarizeError("model reply JSON was not an object")
    summary = {"title": str(data.get("title", "")).strip()[:120],
               "goal": str(data.get("goal", "")).strip()}
    for key in LIST_KEYS:
        value = data.get(key, [])
        summary[key] = [str(v).strip() for v in value if str(v).strip()] if isinstance(value, list) else []
    return summary


def anthropic_complete(prompt: str) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise SummarizeError("ANTHROPIC_API_KEY is not set")
    body = json.dumps({"model": MODEL, "max_tokens": 1024,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    request = urllib.request.Request(API_URL, data=body, method="POST", headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        raise SummarizeError(f"Anthropic API returned HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise SummarizeError(f"could not reach Anthropic API: {exc}") from exc
    blocks = payload.get("content", [])
    return "".join(b.get("text", "") for b in blocks if isinstance(b, dict))


def summarize_session(conn, session_id: str, complete: Completer = anthropic_complete) -> dict:
    session = store.get_session(conn, session_id)
    if session is None:
        raise SummarizeError(f"unknown session {session_id}")
    summary = parse_summary(complete(PROMPT + condense(session["messages"])))
    store.save_summary(conn, session_id, summary, datetime.now(timezone.utc).isoformat())
    return summary


def summarize_pending(conn, project: str | None = None, limit: int = 10,
                      complete: Completer = anthropic_complete) -> dict:
    """Summarize the most recent un-summarized sessions. Failures are collected, not fatal."""
    sql = "SELECT id FROM sessions WHERE summary_json IS NULL AND msg_count >= 2"
    args: list = []
    if project:
        sql += " AND project=?"
        args.append(project)
    sql += " ORDER BY ended DESC LIMIT ?"
    args.append(limit)
    done, errors = 0, []
    for row in conn.execute(sql, args).fetchall():
        try:
            summarize_session(conn, row["id"], complete)
            done += 1
        except SummarizeError as exc:
            errors.append(f"{row['id']}: {exc}")
            if "ANTHROPIC_API_KEY" in str(exc):
                break
    return {"summarized": done, "errors": errors}
