"""Deterministic rule-based tagging, plus optional AI enrichment.

Every repo always gets a tag and a note from `rule_tag` first. `ai_enrich`
is purely additive and falls back to the rule-based result on any error,
so the tool never produces an empty tag/note regardless of network
conditions or whether an API key is configured.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Callable, Optional

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"

# Ordered rule table: first matching rule wins. Each rule checks topics,
# language, and description (lowercased) for keyword hits.
_RULES = [
    (
        "AI/ML",
        {"llm", "machine-learning", "deep-learning", "ai", "artificial-intelligence",
         "nlp", "neural-network", "agent", "agents", "chatbot", "rag", "embeddings",
         "anthropic", "openai", "transformer", "pytorch", "tensorflow"},
    ),
    (
        "Data & Analytics",
        {"data-science", "data-engineering", "analytics", "etl", "pandas",
         "dataframe", "visualization", "dataviz", "sql", "database", "warehouse"},
    ),
    (
        "Dev Tools & CLI",
        {"cli", "developer-tools", "devtools", "productivity", "terminal",
         "automation", "vscode-extension", "linter", "formatter", "build-tool"},
    ),
    (
        "Testing & QA",
        {"testing", "test", "qa", "e2e", "unit-testing", "mocking", "playwright",
         "pytest", "jest"},
    ),
    (
        "Infra & DevOps",
        {"devops", "kubernetes", "docker", "terraform", "ci-cd", "infrastructure",
         "cloud", "aws", "gcp", "azure", "deployment", "monitoring"},
    ),
    (
        "Web & Frontend",
        {"react", "vue", "svelte", "frontend", "web", "css", "html", "ui",
         "component-library", "design-system"},
    ),
    (
        "Docs & Reference",
        {"documentation", "docs", "awesome-list", "cheatsheet", "reference",
         "tutorial", "guide", "book"},
    ),
]

_LANGUAGE_HINTS = {
    "Python": "Dev Tools & CLI",
    "Jupyter Notebook": "Data & Analytics",
    "TypeScript": "Web & Frontend",
    "JavaScript": "Web & Frontend",
    "HCL": "Infra & DevOps",
    "Dockerfile": "Infra & DevOps",
    "Go": "Infra & DevOps",
}

FALLBACK_TAG = "Other"


def rule_tag(
    language: Optional[str], topics: list, description: Optional[str]
) -> tuple:
    """Return (tag, note) using deterministic keyword rules only."""
    topic_set = {t.lower() for t in (topics or [])}
    desc_lower = (description or "").lower()

    for tag, keywords in _RULES:
        if topic_set & keywords:
            break
        if any(kw in desc_lower for kw in keywords):
            break
    else:
        tag = _LANGUAGE_HINTS.get(language or "", FALLBACK_TAG)

    if description:
        note = description.strip()
        if len(note) > 140:
            note = note[:137].rstrip() + "..."
    elif topics:
        note = f"{language or 'Untitled language'} project tagged {', '.join(topics[:3])}"
    else:
        note = f"{language or 'Untagged'} repository, no description provided"

    return tag, note


RequestFn = Callable[[dict, str], dict]


def _default_request(payload: dict, api_key: str) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=data,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _build_prompt(repo: dict) -> str:
    return (
        "You are categorizing a GitHub repository the user has already starred, "
        "using only public repository metadata below. Reply with exactly one line "
        "in the form: TAG: <short category, 1-3 words> | NOTE: <one sentence on "
        "why this might be useful>.\n\n"
        f"Repo: {repo.get('full_name')}\n"
        f"Description: {repo.get('description') or '(none)'}\n"
        f"Language: {repo.get('language') or '(unknown)'}\n"
        f"Topics: {', '.join(repo.get('topics') or []) or '(none)'}\n"
    )


def _parse_reply(text: str) -> Optional[tuple]:
    if "TAG:" not in text or "NOTE:" not in text:
        return None
    try:
        _, rest = text.split("TAG:", 1)
        tag_part, note_part = rest.split("| NOTE:", 1)
        tag = tag_part.strip()
        note = note_part.strip()
        if not tag or not note:
            return None
        return tag, note
    except ValueError:
        return None


def ai_enrich(
    repo: dict,
    api_key: Optional[str],
    request_fn: RequestFn = _default_request,
) -> tuple:
    """Return (tag, note, source). Falls back to rule_tag on any failure."""
    fallback_tag, fallback_note = rule_tag(
        repo.get("language"), repo.get("topics") or [], repo.get("description")
    )

    if not api_key:
        return fallback_tag, fallback_note, "rule"

    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 100,
        "messages": [{"role": "user", "content": _build_prompt(repo)}],
    }

    try:
        response = request_fn(payload, api_key)
        content_blocks = response.get("content") or []
        text = "".join(
            block.get("text", "") for block in content_blocks if isinstance(block, dict)
        )
        parsed = _parse_reply(text)
        if parsed is None:
            return fallback_tag, fallback_note, "rule"
        tag, note = parsed
        if len(note) > 200:
            note = note[:197].rstrip() + "..."
        return tag, note, "ai"
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            ValueError, KeyError, OSError):
        return fallback_tag, fallback_note, "rule"
