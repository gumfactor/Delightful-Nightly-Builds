"""Optional AI polishing layer for author response text.

Design rule: this module must never make a network call unless the caller
explicitly opts in (``use_ai=True``) *and* supplies an API key. The client
is obtained through an injectable ``client_factory`` specifically so tests
can assert the factory is never invoked on the default/no-AI path, without
needing the real ``anthropic`` package installed.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Optional

DEFAULT_MODEL = "claude-haiku-4-5-20251001"

_SYSTEM_PROMPT = (
    "You are helping an academic author polish one point of a 'Response to "
    "Reviewers' letter. Rewrite the author's response in courteous, "
    "professional, publication-register prose. Preserve every factual claim, "
    "number, and citation exactly as given. Do NOT add any new claim, "
    "justification, data point, or citation that is not already present in "
    "the author's own response text. Return only the rewritten response "
    "text, with no preamble or labels."
)


def fallback_format(text: str) -> str:
    """Deterministic cleanup used when AI polishing is unavailable or disabled."""
    collapsed = re.sub(r"[ \t]+", " ", text.strip())
    collapsed = re.sub(r"\n{3,}", "\n\n", collapsed)
    if not collapsed:
        return collapsed
    if collapsed[0].isalpha():
        collapsed = collapsed[0].upper() + collapsed[1:]
    if collapsed[-1] not in ".!?":
        collapsed += "."
    return collapsed


def _default_client_factory(api_key: str) -> Any:
    import anthropic  # imported lazily so it is only required when --ai is used

    return anthropic.Anthropic(api_key=api_key)


def polish_response(
    comment_text: str,
    response_text: str,
    *,
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    use_ai: bool = False,
    client_factory: Callable[[str], Any] = _default_client_factory,
) -> str:
    """Return a polished version of ``response_text``.

    Falls back to deterministic formatting (no network call) whenever
    ``use_ai`` is False, ``api_key`` is empty, the client raises, or the
    model returns empty text.
    """
    if not use_ai or not api_key:
        return fallback_format(response_text)

    try:
        client = client_factory(api_key)
        prompt = (
            f"Reviewer comment:\n{comment_text}\n\n"
            f"Author's raw response notes:\n{response_text}"
        )
        message = client.messages.create(
            model=model,
            max_tokens=400,
            temperature=0,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        polished = message.content[0].text.strip()
        return polished if polished else fallback_format(response_text)
    except Exception:
        return fallback_format(response_text)
