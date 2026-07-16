"""Optional AI-powered semantic review, via a direct call to the Claude
Messages API (no `anthropic` SDK dependency — stdlib `urllib` only,
matching the pattern used elsewhere in this repo's builds).

`ANTHROPIC_API_KEY` is never set in the build container. This module is
only exercised in tests through a mocked `urllib.request.urlopen` — no
test in this build ever makes a live network call.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Optional

from .checks import SEVERITY_INFO, SEVERITY_WARNING, make_finding

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_TIMEOUT_SECONDS = 30

_SYSTEM_PROMPT = """You are auditing an AI agent instruction file (a CLAUDE.md/AGENTS.md-style \
document that a coding agent reads and follows) for problems a static parser cannot catch:
- internal contradictions between two rules or statements
- ambiguous instructions that could reasonably be followed two different ways
- factual or numeric claims in the instructions that are contradicted by the optional \
ground-truth document supplied below (if one is supplied)

Respond with ONLY a JSON array (no prose, no markdown code fences) of finding objects. \
Each object must have exactly these keys:
  "severity": one of "error", "warning", "info"
  "message": a short human-readable description of the issue
  "excerpt": the specific quoted text from the instructions that the finding refers to
If you find no issues, respond with an empty JSON array: []
"""


def _build_user_content(instructions_text: str, ground_truth_text: Optional[str]) -> str:
    parts = ["## Instructions to audit\n\n" + instructions_text]
    if ground_truth_text:
        parts.append("## Ground-truth data to cross-check claims against\n\n" + ground_truth_text)
    return "\n\n".join(parts)


def _call_claude(api_key: str, model: str, user_content: str, timeout: int) -> str:
    """Make the raw Messages API call and return the model's text response.

    Raises urllib.error.URLError / HTTPError / TimeoutError / OSError on
    transport failure, or ValueError if the response shape is unexpected —
    callers are expected to catch these and degrade gracefully.
    """
    payload = json.dumps({
        "model": model,
        "max_tokens": 1024,
        "system": _SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_content}],
    }).encode("utf-8")

    request = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=payload,
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))

    content_blocks = body.get("content", [])
    if not content_blocks or "text" not in content_blocks[0]:
        raise ValueError("Unexpected Claude API response shape: missing content[0].text")
    return content_blocks[0]["text"]


def _parse_findings(raw_text: str) -> list:
    text = raw_text.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("["), text.rfind("]")
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                parsed = None
        else:
            parsed = None

    if not isinstance(parsed, list):
        return [make_finding(
            check="ai_review",
            severity=SEVERITY_WARNING,
            message="AI review returned unparseable output; skipping AI findings.",
            excerpt=raw_text[:200],
            line=None,
        )]

    findings = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        severity = item.get("severity", SEVERITY_WARNING)
        if severity not in ("error", "warning", "info"):
            severity = SEVERITY_WARNING
        findings.append(make_finding(
            check="ai_review",
            severity=severity,
            message=str(item.get("message", "")),
            excerpt=str(item.get("excerpt", "")),
            line=None,
        ))
    return findings


def run_ai_review(instructions_text: str, ground_truth_text: Optional[str] = None,
                   api_key: Optional[str] = None, model: str = DEFAULT_MODEL,
                   timeout: int = DEFAULT_TIMEOUT_SECONDS) -> list:
    if not api_key:
        return [make_finding(
            check="ai_review",
            severity=SEVERITY_INFO,
            message="AI semantic review skipped — no ANTHROPIC_API_KEY set at runtime.",
            excerpt="",
            line=None,
        )]

    user_content = _build_user_content(instructions_text, ground_truth_text)
    try:
        raw_text = _call_claude(api_key, model, user_content, timeout)
    except (urllib.error.URLError, ValueError, OSError, TimeoutError) as exc:
        return [make_finding(
            check="ai_review",
            severity=SEVERITY_WARNING,
            message=f"AI semantic review failed and was skipped: {exc}",
            excerpt="",
            line=None,
        )]

    return _parse_findings(raw_text)
