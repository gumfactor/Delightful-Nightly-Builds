"""Language detection, deterministic tag/description extraction, and optional
Claude Haiku enrichment for Snipvault. Every AI path has an unconditional
deterministic fallback and makes zero network calls without ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

EXTENSION_LANGUAGE = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".sh": "bash",
    ".bash": "bash",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".rb": "ruby",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".r": "r",
    ".md": "markdown",
    ".dart": "dart",
}

STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "from", "into", "true", "false",
    "none", "null", "self", "return", "import", "export", "const", "let", "var",
    "def", "class", "function", "async", "await", "print", "console", "log",
    "if", "else", "elif", "while", "in", "is", "not", "of", "to", "a", "an",
}

_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")


def detect_language(filename: str | None) -> str:
    if not filename:
        return "text"
    for ext, lang in EXTENSION_LANGUAGE.items():
        if filename.lower().endswith(ext):
            return lang
    return "text"


def extract_tags(code: str, language: str, max_tags: int = 5) -> list:
    """Deterministic tag extraction from identifier frequency, stopword-filtered."""
    counts: dict = {}
    for match in _IDENTIFIER_RE.findall(code):
        word = match.lower()
        if word in STOPWORDS:
            continue
        counts[word] = counts.get(word, 0) + 1

    ranked = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    tags = [word for word, _ in ranked[:max_tags]]
    if language and language != "text":
        tags = [language] + [t for t in tags if t != language]
    return tags[:max_tags]


def default_description(code: str, language: str) -> str:
    """Deterministic one-line description fallback: first non-empty comment,
    else the first non-empty code line, truncated."""
    comment_markers = {
        "python": "#", "bash": "#", "ruby": "#", "yaml": "#",
        "javascript": "//", "typescript": "//", "java": "//", "go": "//",
        "c": "//", "cpp": "//", "rust": "//",
        "sql": "--",
    }
    marker = comment_markers.get(language)
    lines = [ln.strip() for ln in code.splitlines() if ln.strip()]
    if not lines:
        return ""

    if marker:
        for line in lines:
            if line.startswith(marker):
                text = line.lstrip(marker).strip()
                if text:
                    return _truncate(text)

    return _truncate(lines[0])


def _truncate(text: str, limit: int = 100) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _call_claude(prompt: str, api_key: str, model: str = "claude-haiku-4-5-20251001") -> str | None:
    """Call the Anthropic Messages API. Returns None on any failure so callers
    can fall back unconditionally."""
    payload = json.dumps(
        {
            "model": model,
            "max_tokens": 200,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
        return body["content"][0]["text"]
    except (
        urllib.error.URLError,
        TimeoutError,
        KeyError,
        IndexError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ):
        # TypeError covers a structurally valid but unexpected response shape
        # (e.g. body is None, or body["content"] is None) — any malformed
        # response must fall back, never raise.
        return None


def enrich_snippet(code: str, language: str, title: str) -> tuple:
    """Returns (description, tags). Uses Claude Haiku when ANTHROPIC_API_KEY is
    set and the call succeeds and parses cleanly; otherwise falls back to the
    deterministic extractor with zero network calls."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    fallback_description = default_description(code, language)
    fallback_tags = extract_tags(code, language)

    if not api_key:
        return fallback_description, fallback_tags

    prompt = (
        "Given this code snippet, respond with ONLY a compact JSON object of the form "
        '{"description": "<one line, under 100 chars>", "tags": ["tag1", "tag2", "tag3"]}. '
        f"Title: {title}\nLanguage: {language}\nCode:\n{code}"
    )
    text = _call_claude(prompt, api_key)
    if text is None:
        return fallback_description, fallback_tags

    try:
        parsed = json.loads(text)
        description = str(parsed["description"]).strip()
        tags = [str(t).strip().lower() for t in parsed["tags"] if str(t).strip()]
        if not description or not tags:
            return fallback_description, fallback_tags
        return _truncate(description), tags
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return fallback_description, fallback_tags


def expand_query(query: str) -> list:
    """Returns a list of keyword terms. Uses Claude Haiku to expand a natural-
    language query into search keywords when ANTHROPIC_API_KEY is set and the
    call succeeds; otherwise falls back to splitting the raw query on
    whitespace, with zero network calls."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    fallback = [w for w in re.split(r"\s+", query.strip()) if w]

    if not api_key or not query.strip():
        return fallback

    prompt = (
        "A developer is searching their personal code-snippet library with this natural-language "
        "query. Respond with ONLY a compact JSON array of 2-6 short lowercase keyword strings "
        f'likely to appear in a matching snippet\'s title, tags, description, or code. Query: "{query}"'
    )
    text = _call_claude(prompt, api_key)
    if text is None:
        return fallback

    try:
        parsed = json.loads(text)
        keywords = [str(k).strip().lower() for k in parsed if str(k).strip()]
        return keywords if keywords else fallback
    except (json.JSONDecodeError, TypeError, ValueError):
        return fallback
