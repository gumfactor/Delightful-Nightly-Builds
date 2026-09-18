"""Optional Claude Haiku review layer for Eligible Spend.

Only called for line items already flagged `requires_justification` or
`no_blocking_rule_found` by the deterministic rule engine (never for
items the deterministic engine already found `ineligible` or
`outside_grant_period` -- there is nothing an AI note could usefully add
to an unambiguous rule match).

Design constraints (per CLAUDE.md):
- ANTHROPIC_API_KEY is not present in the build environment; it is
  supplied by the user at runtime.
- Zero network calls may be attempted when the key is unset.
- The prompt is grounded strictly in the line item's own category/
  description/justification text -- never any file paths, never any
  other budget data, never real personal data.
- On any error (network, malformed response, timeout) fall back to a
  deterministic template rather than failing the whole report.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from rules import Verdict

_API_URL = "https://api.anthropic.com/v1/messages"
_MODEL = "claude-haiku-4-5-20251001"
_TIMEOUT_SECONDS = 20

_FALLBACK_NOTE = (
    "AI review not available -- principles-based judgment required. "
    "Confirm this item satisfies the direct-cost and "
    "not-institution-provided principles before submitting."
)


def _build_prompt(verdict: Verdict) -> str:
    line = verdict.line
    return (
        "You are assisting a Canadian university researcher in checking "
        "a single grant budget line item against the Tri-Agency "
        "(NSERC/CIHR/SSHRC) Guide on Financial Administration's "
        "principles-based framework. Using ONLY the information given "
        "below (never invent facts, other budget items, or dollar "
        "figures not shown here), write ONE plain-English sentence "
        "assessing whether the stated justification plausibly "
        "satisfies these two principles: (1) the expense is a direct "
        "cost attributable to the funded research, and (2) it is not "
        "a good/service the institution normally provides (i.e. not "
        "an overhead cost). Be direct and specific to this item.\n\n"
        f"Category: {line.category}\n"
        f"Item: {line.item}\n"
        f"Justification provided: {line.justification or '(none provided)'}\n"
        f"Rule engine's current flag: {verdict.status} -- {verdict.reason}"
    )


def _call_anthropic(prompt: str, api_key: str) -> str:
    payload = json.dumps(
        {
            "model": _MODEL,
            "max_tokens": 150,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        _API_URL,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
        body = json.loads(response.read().decode("utf-8"))

    content = body.get("content")
    if not isinstance(content, list) or not content:
        raise ValueError("Malformed Anthropic response: no content blocks")
    text = content[0].get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Malformed Anthropic response: empty text block")
    return text.strip()


def get_ai_note(verdict: Verdict, api_key: str | None = None) -> str:
    """Return an AI-assisted note for a verdict, or the deterministic
    fallback if no API key is set or the call fails for any reason.
    """
    api_key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _FALLBACK_NOTE

    prompt = _build_prompt(verdict)
    try:
        return _call_anthropic(prompt, api_key)
    except (urllib.error.URLError, ValueError, TimeoutError, json.JSONDecodeError, OSError):
        return _FALLBACK_NOTE


def annotate_all(verdicts: list[Verdict], use_ai: bool, api_key: str | None = None) -> dict[int, str]:
    """Return a mapping of verdict index -> AI note for verdicts eligible
    for review (requires_justification / no_blocking_rule_found only).
    Empty dict if use_ai is False.
    """
    if not use_ai:
        return {}
    notes: dict[int, str] = {}
    reviewable = {"requires_justification", "no_blocking_rule_found"}
    for idx, verdict in enumerate(verdicts):
        if verdict.status in reviewable:
            notes[idx] = get_ai_note(verdict, api_key=api_key)
    return notes
