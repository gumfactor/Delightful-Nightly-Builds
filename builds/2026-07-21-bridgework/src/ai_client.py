"""Optional Claude Haiku polish of a deterministic analogy draft. Reads
ANTHROPIC_API_KEY at call time only — never during the build, never in tests
(all HTTP calls in tests are mocked). Returns None on any failure so the
caller can fall back to the deterministic template unconditionally.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Optional

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
TIMEOUT_SECONDS = 20

_AUDIENCE_GUIDANCE = {
    "undergrad_lecture": "a technical-but-accessible undergraduate psychology lecture: precise, may use research terms, explains the structural parallel explicitly",
    "public_talk": "a public talk to a general audience: vivid, hook-first, avoids jargon",
    "book_chapter": "a trade nonfiction book chapter: literary, scene-setting, sets up a longer argument",
}

_SYSTEM_PROMPT = (
    "You write short, scientifically honest analogies bridging neuroscience concepts "
    "to everyday domains for a psychology professor's book and public talks. "
    "Given a concept, an everyday domain, an audience register, and a deterministic draft, "
    "rewrite it in that register. Respond with ONLY a JSON object with exactly three string "
    "keys: hook (one punchy sentence), analogy (a 3-5 sentence paragraph), and caveat "
    "(one sentence on where the analogy breaks down, grounded in the concept's own caveat). "
    "Do not include markdown fences or any text outside the JSON object."
)


def _build_user_prompt(concept, domain, audience: str, draft: dict) -> str:
    guidance = _AUDIENCE_GUIDANCE.get(audience, audience)
    return (
        f"Concept: {concept.name} ({concept.description})\n"
        f"Concept structure: trigger='{concept.trigger}'; mechanism='{concept.mechanism}'; "
        f"consequence='{concept.consequence}'\n"
        f"Concept caveat: {concept.caveat}\n"
        f"Domain: {domain.name} ({domain.description})\n"
        f"Domain structure: trigger='{domain.trigger_word}'; process='{domain.process_word}'; "
        f"outcome='{domain.outcome_word}'\n"
        f"Audience register: {audience} — {guidance}\n"
        f"Deterministic draft hook: {draft['hook']}\n"
        f"Deterministic draft analogy: {draft['analogy']}\n"
        f"Deterministic draft caveat: {draft['caveat']}\n"
    )


def call_claude(
    concept,
    domain,
    audience: str,
    draft: dict,
    api_key: Optional[str],
    model: str = DEFAULT_MODEL,
    timeout: int = TIMEOUT_SECONDS,
) -> Optional[dict]:
    """Returns {'hook', 'analogy', 'caveat'} on success, None on any failure
    (including no api_key) so the caller can fall back to the template."""
    if not api_key:
        return None

    payload = {
        "model": model,
        "max_tokens": 500,
        "system": _SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": _build_user_prompt(concept, domain, audience, draft)}
        ],
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                return None
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None

    try:
        text = body["content"][0]["text"].strip()
        parsed = json.loads(text)
        hook = parsed["hook"]
        analogy = parsed["analogy"]
        caveat = parsed["caveat"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return None

    if not (isinstance(hook, str) and isinstance(analogy, str) and isinstance(caveat, str)):
        return None
    if not (hook.strip() and analogy.strip() and caveat.strip()):
        return None

    return {"hook": hook.strip(), "analogy": analogy.strip(), "caveat": caveat.strip()}
