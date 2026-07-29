"""Optional Claude Haiku integration: tag suggestion and resurface rationale.

Both entry points check for ANTHROPIC_API_KEY first and fall through to a
deterministic implementation with zero network calls when it is absent, or
whenever the API call fails or returns something unparseable. The Anthropic
Messages API is called directly via urllib — no `anthropic` package
dependency, matching the pattern used by prior builds in this catalog.
"""

import json
import os
import re
import urllib.request
from typing import Callable, Optional

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
MODEL = "claude-haiku-4-5-20251001"

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "in", "on", "for", "to", "with", "is",
    "are", "was", "were", "be", "been", "this", "that", "these", "those", "as",
    "by", "at", "from", "we", "our", "it", "its", "into", "using", "used",
    "study", "studies", "results", "between", "across", "than", "also",
    "which", "their", "not", "but", "can", "may", "have", "has", "had",
}


def default_request_fn(payload: dict) -> bytes:
    api_key = os.environ["ANTHROPIC_API_KEY"]
    req = urllib.request.Request(
        ANTHROPIC_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


def _deterministic_tags(title: str, abstract: Optional[str], max_tags: int = 5) -> list:
    text = f"{title} {abstract or ''}".lower()
    words = re.findall(r"[a-z][a-z\-]{3,}", text)
    freq = {}
    for w in words:
        if w in STOPWORDS:
            continue
        freq[w] = freq.get(w, 0) + 1
    ranked = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in ranked[:max_tags]]


def suggest_tags(
    title: str,
    abstract: Optional[str],
    request_fn: Callable[[dict], bytes] = default_request_fn,
    max_tags: int = 5,
) -> list:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return _deterministic_tags(title, abstract, max_tags)

    prompt = (
        f"Suggest up to {max_tags} short lowercase concept tags (single words or "
        f"short hyphenated phrases, no explanations) for this paper. Reply with "
        f"only a comma-separated list.\n\nTitle: {title}\nAbstract: {abstract or '(none)'}"
    )
    payload = {
        "model": MODEL,
        "max_tokens": 100,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        raw = request_fn(payload)
        data = json.loads(raw)
        text = data["content"][0]["text"]
        tags = [t.strip().lower() for t in text.split(",") if t.strip()]
        if not tags:
            return _deterministic_tags(title, abstract, max_tags)
        return tags[:max_tags]
    except Exception:
        return _deterministic_tags(title, abstract, max_tags)


def _deterministic_rationale(old_title: str, new_title: str, shared_tags: list) -> str:
    tag_str = ", ".join(shared_tags) if shared_tags else "related topics"
    return f"Shares {tag_str} with \"{new_title}\" — worth a second look before continuing."


def resurface_rationale(
    old_paper: dict,
    new_paper: dict,
    shared_tags: list,
    request_fn: Callable[[dict], bytes] = default_request_fn,
) -> str:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return _deterministic_rationale(old_paper["title"], new_paper["title"], shared_tags)

    prompt = (
        "In one short sentence, explain why this previously-read paper might be "
        "worth revisiting given a paper currently in the to-read queue. Be concrete "
        "about the connection.\n\n"
        f"Previously read: {old_paper['title']}\n"
        f"Currently to-read: {new_paper['title']}\n"
        f"Shared tags: {', '.join(shared_tags)}"
    )
    payload = {
        "model": MODEL,
        "max_tokens": 100,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        raw = request_fn(payload)
        data = json.loads(raw)
        text = data["content"][0]["text"].strip()
        if not text:
            return _deterministic_rationale(old_paper["title"], new_paper["title"], shared_tags)
        return text
    except Exception:
        return _deterministic_rationale(old_paper["title"], new_paper["title"], shared_tags)
