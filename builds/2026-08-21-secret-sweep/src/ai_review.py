"""Optional Claude Haiku second opinion on a candidate finding.

CRITICAL invariant, enforced by construction: this module never receives or
transmits a raw secret value. Callers pass only a masked context snippet
(see src/redact.py:masked_context), the pattern name, file extension, and
entropy score. When ANTHROPIC_API_KEY is unset, no network call is made at
all — a deterministic fallback verdict is returned instead.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_VERSION = "2023-06-01"
REQUEST_TIMEOUT_SECONDS = 15

VALID_VERDICTS = {"likely_secret", "likely_placeholder", "uncertain"}


def _build_prompt(pattern_name: str, file_ext: str, entropy: float, masked_snippet: str) -> str:
    return (
        "You are reviewing a candidate secret/credential detection from an automated scanner. "
        "The actual secret value has been redacted and replaced with [REDACTED] below — you will "
        "never see the real value. Based only on the surrounding context, classify this as one of: "
        "likely_secret, likely_placeholder, or uncertain. Then give a one-sentence rationale.\n\n"
        f"Detector: {pattern_name}\n"
        f"File type: {file_ext or '(none)'}\n"
        f"Entropy: {entropy:.2f} bits/char\n"
        f"Context: {masked_snippet}\n\n"
        "Respond in the exact format:\nVERDICT: <one of the three labels>\nRATIONALE: <one sentence>"
    )


def _deterministic_fallback(pattern_name: str, entropy: float) -> dict:
    if pattern_name.startswith("Generic High-Entropy"):
        verdict = "uncertain"
        rationale = (
            f"No AI review available — generic entropy detector ({entropy:.2f} bits/char) "
            "flagged this; named-pattern matches are more reliable than entropy alone."
        )
    else:
        verdict = "likely_secret"
        rationale = f"No AI review available — matches the known '{pattern_name}' credential format."
    return {"verdict": verdict, "rationale": rationale, "source": "fallback"}


def review_finding(
    pattern_name: str,
    file_ext: str,
    entropy: float,
    masked_snippet: str,
    api_key: str | None = None,
) -> dict:
    """Return {'verdict': ..., 'rationale': ..., 'source': 'ai'|'fallback'}."""
    api_key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _deterministic_fallback(pattern_name, entropy)

    prompt = _build_prompt(pattern_name, file_ext, entropy, masked_snippet)
    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 150,
        "messages": [{"role": "user", "content": prompt}],
    }
    request = urllib.request.Request(
        ANTHROPIC_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
        text = "".join(
            block.get("text", "") for block in body.get("content", []) if block.get("type") == "text"
        )
        return _parse_ai_response(text) or _deterministic_fallback(pattern_name, entropy)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError):
        return _deterministic_fallback(pattern_name, entropy)


def _parse_ai_response(text: str) -> dict | None:
    verdict = None
    rationale = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("VERDICT:"):
            candidate = stripped.split(":", 1)[1].strip().lower()
            if candidate in VALID_VERDICTS:
                verdict = candidate
        elif stripped.upper().startswith("RATIONALE:"):
            rationale = stripped.split(":", 1)[1].strip()
    if verdict is None:
        return None
    return {"verdict": verdict, "rationale": rationale or "(no rationale given)", "source": "ai"}
