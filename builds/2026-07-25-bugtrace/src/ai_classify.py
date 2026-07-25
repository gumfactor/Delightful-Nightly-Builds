"""Optional Claude Haiku classification pass.

Design contract: any failure here (no API key, network error, malformed
response, unknown category in the response) must fall back to the
deterministic keyword classifier for the affected commit(s), never raise
out of classify_batch(). Tests must mock every network call — this module
is never exercised against the live Anthropic API during the build or in
CI.
"""

import json
import urllib.error
import urllib.request

from .classify import TAXONOMY, keyword_classify

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"


class AIClassificationError(Exception):
    pass


def build_prompt(items):
    taxonomy_str = ", ".join(TAXONOMY)
    lines = [
        f"Classify each commit below into exactly one category from this fixed list: {taxonomy_str}.",
        'Respond with ONLY a JSON array, no prose, like: '
        '[{"sha": "<sha>", "category": "<one of the categories above>", "explanation": "<one short sentence>"}]',
        "",
    ]
    for item in items:
        lines.append(f"--- commit {item['sha']} ---")
        lines.append(f"message: {item['message']}")
        lines.append(f"diff: {item.get('diff_excerpt', '')[:1500]}")
        lines.append("")
    return "\n".join(lines)


def _default_request(api_key, prompt):
    body = json.dumps(
        {
            "model": MODEL,
            "max_tokens": 1536,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        ANTHROPIC_URL,
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_ai_response(response_json):
    """Raises AIClassificationError on any malformed/unexpected shape."""
    try:
        text = response_json["content"][0]["text"]
        start = text.index("[")
        end = text.rindex("]") + 1
        data = json.loads(text[start:end])
        if not isinstance(data, list):
            raise ValueError("response JSON is not a list")
        results = {}
        for entry in data:
            sha = entry["sha"]
            category = entry["category"]
            if category not in TAXONOMY:
                raise ValueError(f"unknown category '{category}'")
            results[sha] = {"category": category, "explanation": entry.get("explanation", "")}
        return results
    except (KeyError, ValueError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise AIClassificationError(str(exc)) from exc


def classify_batch(api_key, items, request_fn=None):
    """Classify a batch of fix commits.

    items: list of dicts with keys sha, message, diff_excerpt, changed_files (optional).
    Returns: dict sha -> {"category": str, "explanation": str, "source": "ai"|"keyword"}.
    """
    request_fn = request_fn or _default_request
    results = {}

    if not api_key or not items:
        for item in items:
            category, explanation = keyword_classify(
                item["message"], item.get("diff_excerpt", ""), item.get("changed_files", [])
            )
            results[item["sha"]] = {"category": category, "explanation": explanation, "source": "keyword"}
        return results

    ai_results = {}
    try:
        prompt = build_prompt(items)
        response = request_fn(api_key, prompt)
        ai_results = parse_ai_response(response)
    except (AIClassificationError, urllib.error.URLError, TimeoutError, OSError, ValueError):
        ai_results = {}

    for item in items:
        sha = item["sha"]
        if sha in ai_results:
            r = ai_results[sha]
            results[sha] = {"category": r["category"], "explanation": r["explanation"], "source": "ai"}
        else:
            category, explanation = keyword_classify(
                item["message"], item.get("diff_excerpt", ""), item.get("changed_files", [])
            )
            results[sha] = {"category": category, "explanation": explanation, "source": "keyword"}
    return results


def ai_coaching_summary(api_key, counts, request_fn=None):
    """Return a short plain-English coaching paragraph, or None on any failure/no key."""
    if not api_key or not counts:
        return None
    request_fn = request_fn or _default_request
    total = sum(c["count"] for c in counts)
    breakdown = ", ".join(f"{c['category']}: {c['count']}" for c in counts[:6])
    prompt = (
        "You are a terse coding coach. Given this frequency breakdown of a developer's own "
        f"bug-fix commit categories (total {total} fixes): {breakdown}. "
        "Write exactly one short paragraph (3-4 sentences, no markdown, no bullet points) "
        "naming the top 1-2 recurring patterns and one concrete, specific suggestion for each."
    )
    try:
        response = request_fn(api_key, prompt)
        return response["content"][0]["text"].strip()
    except (KeyError, IndexError, TypeError, urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None
