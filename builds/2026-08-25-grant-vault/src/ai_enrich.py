"""Optional Claude Haiku enrichment for grant text chunks.

This module is the ONLY place in Grant Vault that ever makes a network
call. It is invoked exclusively when the caller passes an api_key AND the
CLI's --ai flag was set; every other code path (ingest without --ai,
search, stats, render) never imports or calls anything here. Any failure
(network error, timeout, malformed response) is caught and reported as
None so the caller can fall back to the deterministic tags/no-summary
path without the whole ingest run failing.
"""

import json
import urllib.error
import urllib.request

_API_URL = "https://api.anthropic.com/v1/messages"
_MODEL = "claude-haiku-4-5-20251001"
_ANTHROPIC_VERSION = "2023-06-01"
_TIMEOUT_SECONDS = 15

_PROMPT_TEMPLATE = (
    "You are helping organize a personal grant-writing knowledge base. "
    "Given the grant proposal paragraph below, respond with ONLY a JSON "
    "object of the exact shape "
    '{{"summary": "<one sentence, under 25 words, describing what this '
    'paragraph argues or does>", "tags": ["<3 to 5 short lowercase '
    'keyword tags>"]}}. No other text.\n\n'
    "Paragraph:\n{chunk}"
)


def enrich_chunk(text: str, api_key: str) -> dict | None:
    """Return {"summary": str, "tags": list[str]} or None on any failure."""
    if not text or not api_key:
        return None

    payload = json.dumps(
        {
            "model": _MODEL,
            "max_tokens": 200,
            "messages": [
                {"role": "user", "content": _PROMPT_TEMPLATE.format(chunk=text)}
            ],
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        _API_URL,
        data=payload,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None

    return _parse_enrichment(body)


def _parse_enrichment(body: dict) -> dict | None:
    try:
        raw_text = body["content"][0]["text"]
        parsed = json.loads(raw_text)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return None

    summary = parsed.get("summary")
    tags = parsed.get("tags")
    if not isinstance(summary, str) or not isinstance(tags, list):
        return None
    if not all(isinstance(tag, str) for tag in tags):
        return None

    return {"summary": summary, "tags": [t.lower() for t in tags]}
