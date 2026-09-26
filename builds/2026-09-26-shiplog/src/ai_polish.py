"""Optional AI prose polish for changelog sections.

Sends only already-classified structure (type/scope/subject/breaking) to Claude —
never diffs, file paths, or file contents. Any missing key or failure falls back
to a deterministic bulleted list built entirely locally. Zero network calls are
made when no API key is supplied.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Callable, Optional

from classify import Commit

MODEL = "claude-haiku-4-5-20251001"
API_URL = "https://api.anthropic.com/v1/messages"

CallFn = Callable[[str, str], str]


def _deterministic_bullets(commits: list[Commit]) -> str:
    lines = []
    for commit in commits:
        scope_part = f"**{commit.scope}**: " if commit.scope else ""
        lines.append(f"- {scope_part}{commit.subject}")
    return "\n".join(lines)


def default_call_fn(api_key: str, prompt: str) -> str:
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 400,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=payload,
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        body = json.loads(response.read())
    return body["content"][0]["text"].strip()


def _build_prompt(section_name: str, commits: list[Commit]) -> str:
    structure = [
        {"type": c.type, "scope": c.scope, "subject": c.subject, "breaking": c.breaking}
        for c in commits
    ]
    return (
        f"Write a short (2-4 sentence) changelog paragraph summarizing these '{section_name}' "
        "commits for a release notes reader. Group related items naturally, plain prose, no "
        "preamble, no markdown headers. Only use the information given below:\n\n"
        f"{json.dumps(structure, indent=2)}"
    )


def polish_sections(
    sections: dict[str, list[Commit]],
    api_key: Optional[str],
    call_fn: CallFn = default_call_fn,
) -> dict[str, str]:
    result: dict[str, str] = {}
    for section_name, commits in sections.items():
        if not api_key:
            result[section_name] = _deterministic_bullets(commits)
            continue
        try:
            prompt = _build_prompt(section_name, commits)
            result[section_name] = call_fn(api_key, prompt)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, KeyError, ValueError, json.JSONDecodeError):
            result[section_name] = _deterministic_bullets(commits)
    return result
