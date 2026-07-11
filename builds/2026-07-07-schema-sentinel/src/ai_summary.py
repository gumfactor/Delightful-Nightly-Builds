"""Optional plain-English migration summary via the Anthropic Messages API.

Uses `urllib.request` directly (no `anthropic` SDK dependency, keeping the
tool stdlib-only). Only field names, change types, and severities are ever
sent — never raw record data or file contents.
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import List, Optional

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_VERSION = "2023-06-01"


def generate_summary(
    diff_entries: List[dict],
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> str:
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback_summary(diff_entries)

    try:
        payload = json.dumps(
            {
                "model": model,
                "max_tokens": 400,
                "messages": [{"role": "user", "content": _build_prompt(diff_entries)}],
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            API_URL,
            data=payload,
            headers={
                "x-api-key": api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
        text = "".join(
            block.get("text", "") for block in body.get("content", []) if block.get("type") == "text"
        ).strip()
        return text if text else _fallback_summary(diff_entries)
    except Exception:
        # Any network, auth, or parsing failure degrades to the deterministic
        # template below — this call must never crash a run.
        return _fallback_summary(diff_entries)


def _build_prompt(diff_entries: List[dict]) -> str:
    lines = [
        "Summarize the following data schema changes for a developer in 3-5 sentences. "
        "Group by severity and call out what code should be reviewed first.",
        "",
    ]
    for entry in diff_entries:
        lines.append(f"- [{entry['severity']}] {entry['field']}: {entry['detail']}")
    return "\n".join(lines)


def _fallback_summary(diff_entries: List[dict]) -> str:
    if not diff_entries:
        return "No structural changes detected between the two schemas."

    by_severity = {"breaking": [], "risky": [], "safe": []}
    for entry in diff_entries:
        by_severity[entry["severity"]].append(entry)

    parts = []
    if by_severity["breaking"]:
        details = "; ".join(e["detail"] for e in by_severity["breaking"])
        parts.append(f"{len(by_severity['breaking'])} breaking change(s) requiring immediate review: {details}.")
    if by_severity["risky"]:
        details = "; ".join(e["detail"] for e in by_severity["risky"])
        parts.append(f"{len(by_severity['risky'])} risky change(s) worth checking: {details}.")
    if by_severity["safe"]:
        details = "; ".join(e["detail"] for e in by_severity["safe"])
        parts.append(f"{len(by_severity['safe'])} additive/safe change(s): {details}.")
    return " ".join(parts)
