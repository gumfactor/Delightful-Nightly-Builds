"""Session summaries: deterministic offline heuristic, plus opt-in Anthropic AI summary."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Callable

from .models import Session

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
TRANSCRIPT_BUDGET = 24000
PER_MESSAGE_CAP = 1500

DECISION_RE = re.compile(r"\b(decided|we(?:'ll| will) go with|going with|chose|chosen|instead of|switch(?:ed|ing) to|settled on)\b", re.I)
OPEN_HEADING_RE = re.compile(r"^\W*(next steps?|todo|to-do|remaining|open questions?|follow[- ]ups?|still (?:need|to do))\b", re.I)
BULLET_RE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+(.*\S)")


class SummaryError(Exception):
    """Raised for AI summary failures the caller should show to the user."""


def _clip(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def heuristic_summary(session: Session) -> dict[str, Any]:
    users = [m for m in session.messages if m.role == "user"]
    assistants = [m for m in session.messages if m.role == "assistant"]
    decisions: list[str] = []
    open_items: list[str] = []
    for message in assistants:
        in_open_section = False
        for line in _lines(message.text):
            bullet = BULLET_RE.match(line)
            if OPEN_HEADING_RE.match(line) and not bullet:
                in_open_section = True
                continue
            if bullet and in_open_section:
                open_items.append(_clip(bullet.group(1), 200))
                continue
            if not bullet:
                in_open_section = bool(OPEN_HEADING_RE.match(line))
            if DECISION_RE.search(line) and len(line) < 300:
                decisions.append(_clip(re.sub(r"^\W+", "", line), 200))
    last_asks = [_clip(m.text, 220) for m in users[-3:]]
    first_ask = _clip(users[0].text, 160) if users else ""
    return {
        "title": session.title,
        "summary": f"{len(session.messages)} messages. Started with: {first_ask}" if first_ask else f"{len(session.messages)} messages.",
        "last_asks": last_asks,
        "left_off": _clip(assistants[-1].text, 400) if assistants else "",
        "files": session.files[:15],
        "decisions": list(dict.fromkeys(decisions))[:8],
        "open_items": list(dict.fromkeys(open_items))[:10],
    }


# ---- AI summary ----------------------------------------------------------

SYSTEM_PROMPT = (
    "You summarise a conversation between a person and an AI assistant so the person can resume the work later. "
    "Be concrete and terse. No filler, no praise, no marketing tone. Only state things present in the transcript. "
    "Reply with a single JSON object and nothing else."
)
USER_TEMPLATE = (
    "Summarise this conversation. JSON keys: "
    '"title" (max 10 words), "summary" (2-3 sentences: goal, what was done, current state), '
    '"decisions" (list of decisions actually made, with the reason if given), '
    '"open_items" (unresolved questions and concrete next steps). Use empty lists when none.\n\n'
    "TRANSCRIPT:\n{transcript}"
)


def compact_transcript(session: Session, budget: int = TRANSCRIPT_BUDGET) -> str:
    """Keep the start and the end of long sessions; the middle is dropped first."""
    rendered = [f"[{m.role}] {_clip(m.text, PER_MESSAGE_CAP)}" for m in session.messages]
    if sum(len(r) + 1 for r in rendered) <= budget:
        return "\n".join(rendered)
    head_budget, tail_budget = budget // 3, budget - budget // 3
    head, tail, used = [], [], 0
    for line in rendered:
        if used + len(line) > head_budget:
            break
        head.append(line)
        used += len(line) + 1
    used = 0
    for line in reversed(rendered[len(head):]):
        if used + len(line) > tail_budget:
            break
        tail.append(line)
        used += len(line) + 1
    return "\n".join(head + ["[... middle of conversation omitted ...]"] + list(reversed(tail)))


def _urllib_post(url: str, headers: dict[str, str], body: dict[str, Any], timeout: int = 90) -> dict[str, Any]:
    request = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed https URL
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as err:
        raise SummaryError(f"Anthropic API returned HTTP {err.code}") from err
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as err:
        raise SummaryError(f"Could not reach the Anthropic API: {err}") from err


def call_claude(system: str, user: str, api_key: str | None = None, model: str | None = None,
                post: Callable[..., dict[str, Any]] = _urllib_post, max_tokens: int = 1200) -> str:
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise SummaryError("ANTHROPIC_API_KEY is not set. AI summaries are optional; the offline summary still works.")
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    body = {"model": model or os.environ.get("SESSION_MEMORY_MODEL", DEFAULT_MODEL), "max_tokens": max_tokens,
            "system": system, "messages": [{"role": "user", "content": user}]}
    reply = post(API_URL, headers, body)
    blocks = reply.get("content") if isinstance(reply, dict) else None
    text = "".join(b.get("text", "") for b in blocks or [] if isinstance(b, dict))
    if not text.strip():
        raise SummaryError("The Anthropic API returned an empty reply.")
    return text


def parse_ai_json(text: str) -> dict[str, Any]:
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if fenced:
        text = fenced.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise SummaryError("The AI reply was not valid JSON.")
        text = text[start:end + 1]
    try:
        data = json.loads(text)
    except json.JSONDecodeError as err:
        raise SummaryError("The AI reply was not valid JSON.") from err
    if not isinstance(data, dict):
        raise SummaryError("The AI reply was not a JSON object.")
    return data


def _string_list(value: Any) -> list[str]:
    return [_clip(str(item), 300) for item in value if str(item).strip()] if isinstance(value, list) else []


def ai_summary(session: Session, api_key: str | None = None, model: str | None = None,
               post: Callable[..., dict[str, Any]] = _urllib_post) -> dict[str, Any]:
    raw = call_claude(SYSTEM_PROMPT, USER_TEMPLATE.format(transcript=compact_transcript(session)), api_key, model, post)
    data = parse_ai_json(raw)
    base = heuristic_summary(session)  # keeps files, last asks and left-off, which are exact, not generated
    return {
        **base,
        "title": _clip(str(data.get("title") or base["title"]), 100),
        "summary": _clip(str(data.get("summary") or base["summary"]), 700),
        "decisions": _string_list(data.get("decisions")),
        "open_items": _string_list(data.get("open_items")),
    }
