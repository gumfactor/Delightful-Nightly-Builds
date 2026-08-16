"""Optional Claude Haiku enrichment: concept auto-marking and concept notes.

Every function here degrades to a safe, deterministic no-op when no API key
is present or the call fails for any reason — never raises, never blocks the
CLI's core (non-AI) functionality.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_VERSION = "2023-06-01"


def get_api_key() -> str | None:
    return os.environ.get("ANTHROPIC_API_KEY") or None


def _post_anthropic(prompt: str, api_key: str, model: str, max_tokens: int) -> str:
    body = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload["content"][0]["text"]


def auto_mark_concepts(text: str, api_key: str | None, model: str = DEFAULT_MODEL) -> str:
    """Ask Claude to wrap concept phrases in ``[[...]]`` markers.

    Returns the original text unchanged (and makes zero network calls) if no
    API key is set, or if the call fails or returns something unusable. The
    marked-up text is re-parsed by the same deterministic parser used for
    hand-marked input — this function never returns concepts directly, only
    text for the real parser to re-verify.
    """
    if not api_key or not text.strip():
        return text

    prompt = (
        "You will be given the raw text of a course syllabus or lecture outline. "
        "Return the exact same text, unchanged, except wrap every distinct academic "
        "concept, theory, or named construct phrase in double square brackets — for "
        "example 'the HPA axis' becomes 'the [[HPA axis]]'. Do not add, remove, "
        "reorder, or rephrase any other text. Do not add any explanation before or "
        "after. Return only the marked-up text.\n\n---\n\n" + text
    )
    try:
        marked = _post_anthropic(prompt, api_key, model, max_tokens=4096)
    except (OSError, KeyError, IndexError, ValueError, TypeError):
        return text
    return marked if marked.strip() else text


def generate_concept_notes(
    concepts: list, api_key: str | None, model: str = DEFAULT_MODEL
) -> dict:
    """Batch-generate one-sentence notes for concepts needing one.

    ``concepts`` is a list of ``(normalized_name, display_name)`` tuples.
    Returns ``{normalized_name: note}`` — empty dict on no key, empty input,
    or any failure. Exactly one network call regardless of concept count.
    """
    if not api_key or not concepts:
        return {}

    numbered = "\n".join(f"{i + 1}. {display}" for i, (_, display) in enumerate(concepts))
    prompt = (
        "For each of the following academic concepts, write exactly one concise "
        "plain-English sentence (max 20 words) explaining what it is. Reply with a "
        "numbered list matching the input numbering exactly, one line per concept, "
        "and no other text.\n\n" + numbered
    )
    try:
        response = _post_anthropic(prompt, api_key, model, max_tokens=1024)
    except (OSError, KeyError, IndexError, ValueError, TypeError):
        return {}

    notes = {}
    for line in response.splitlines():
        m = re.match(r"\s*(\d+)[.)]\s*(.+)$", line)
        if not m:
            continue
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(concepts):
            notes[concepts[idx][0]] = m.group(2).strip()
    return notes
