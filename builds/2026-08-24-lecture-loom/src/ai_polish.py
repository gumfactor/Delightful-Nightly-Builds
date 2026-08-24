"""Optional Claude Haiku polish layer.

Only the already-extracted structure (title, section headings, bullet text)
is ever sent — never raw file content beyond that, never personal data.
With no ANTHROPIC_API_KEY, the deterministic fallback below runs instead and
makes zero network calls.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from urllib.request import Request, urlopen

from parser import Lecture

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
_WHITESPACE_RE = re.compile(r"\s+")


@dataclass
class PolishResult:
    sections: dict[str, list[str]] = field(default_factory=dict)
    discussion_questions: list[str] = field(default_factory=list)
    used_ai: bool = False


def _clean_bullet(bullet: str) -> str:
    cleaned = _WHITESPACE_RE.sub(" ", bullet).strip()
    if cleaned and cleaned[0].isalpha():
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned


def _deterministic_fallback(lecture: Lecture) -> PolishResult:
    sections = {
        section.heading: [_clean_bullet(b) for b in section.bullets]
        for section in lecture.sections
    }
    return PolishResult(sections=sections, discussion_questions=[], used_ai=False)


def _build_prompt(lecture: Lecture) -> str:
    structure = {
        "title": lecture.title,
        "sections": [
            {"heading": s.heading, "bullets": s.bullets} for s in lecture.sections
        ],
    }
    return (
        "You are helping a professor clean up lecture bullet points for slides. "
        "Given this extracted structure, rewrite each section's bullets into "
        "clean, parallel-structured presenter phrasing (same meaning, tighter "
        "wording) and draft 2-3 short discussion questions for the whole "
        "lecture. Respond with ONLY a JSON object of the form "
        '{"sections": {"<heading>": ["bullet", ...]}, "discussion_questions": '
        '["question", ...]}. Structure:\n' + json.dumps(structure)
    )


def _call_anthropic(prompt: str, api_key: str) -> str:
    payload = json.dumps(
        {
            "model": ANTHROPIC_MODEL,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    request = Request(
        ANTHROPIC_API_URL,
        data=payload,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    with urlopen(request, timeout=30) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body["content"][0]["text"]


def polish_lecture(lecture: Lecture, api_key: str | None) -> PolishResult:
    if not api_key:
        return _deterministic_fallback(lecture)

    try:
        raw_text = _call_anthropic(_build_prompt(lecture), api_key)
        parsed = json.loads(raw_text)
        sections = {
            heading: [str(b) for b in bullets]
            for heading, bullets in parsed.get("sections", {}).items()
        }
        questions = [str(q) for q in parsed.get("discussion_questions", [])]
        if not sections:
            raise ValueError("empty sections in AI response")
        return PolishResult(sections=sections, discussion_questions=questions, used_ai=True)
    except Exception:
        return _deterministic_fallback(lecture)
