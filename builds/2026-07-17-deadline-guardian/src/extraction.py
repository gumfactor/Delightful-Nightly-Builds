"""Turn unstructured text (a pasted email or portal notice) into a
structured deadline dict, either via Claude (when an API key is available)
or via a deterministic regex/keyword fallback parser (always available,
no network required).
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime

from . import ai_client
from .db import VALID_CATEGORIES

MAX_TITLE_LENGTH = 120

CATEGORY_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("IRB/Ethics", ("irb", "reb", "ethics board", "ethics renewal", "human subjects", "research ethics")),
    ("Grant", ("grant", "progress report", "funding renewal", "nih", "nsf", "sshrc", "cihr")),
    ("Conference", ("conference", "abstract deadline", "symposium", "call for papers", "poster submission")),
    ("Manuscript", ("manuscript", "revise and resubmit", "r&r", "journal submission", "peer review")),
    ("Course", ("syllabus", "course prep", "semester start", "lecture schedule")),
    ("Student Evaluation", ("evaluation", "grading", "grade submission", "rubric", "teaching evaluation")),
]

RECURRENCE_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("annual", ("annual", "yearly", "every year", "once a year")),
    ("semesterly", ("semester", "twice a year", "each term")),
)

_EVERY_N_MONTHS_RE = re.compile(r"every\s+(\d+)\s+months?", re.IGNORECASE)

_DATE_PATTERNS: tuple[tuple[re.Pattern, str], ...] = (
    (re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"), "iso"),
    (re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b"), "slash"),
    (
        re.compile(
            r"\b(January|February|March|April|May|June|July|August|September|October|"
            r"November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s+"
            r"(\d{1,2}),?\s+(\d{4})\b",
            re.IGNORECASE,
        ),
        "month_day_year",
    ),
    (
        re.compile(
            r"\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|"
            r"November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s+(\d{4})\b",
            re.IGNORECASE,
        ),
        "day_month_year",
    ),
)

_MONTH_NAMES = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}


class NoDateFoundError(ValueError):
    """Raised when the fallback parser cannot find any date in the text."""


def _find_date(text: str) -> date:
    for pattern, kind in _DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        try:
            if kind == "iso":
                y, m, d = match.groups()
                return date(int(y), int(m), int(d))
            if kind == "slash":
                m, d, y = match.groups()
                return date(int(y), int(m), int(d))
            if kind == "month_day_year":
                month_name, d, y = match.groups()
                return date(int(y), _MONTH_NAMES[month_name.lower().rstrip(".")], int(d))
            if kind == "day_month_year":
                d, month_name, y = match.groups()
                return date(int(y), _MONTH_NAMES[month_name.lower().rstrip(".")], int(d))
        except ValueError:
            continue
    raise NoDateFoundError(
        "Could not find a recognizable date in the supplied text. "
        "Try including an explicit date like 2027-03-15 or 'March 15, 2027'."
    )


def _infer_category(text: str) -> str:
    lowered = text.lower()
    for category, keywords in CATEGORY_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return category
    return "Other"


def _infer_recurrence(text: str) -> tuple[str, int | None]:
    lowered = text.lower()
    match = _EVERY_N_MONTHS_RE.search(lowered)
    if match:
        return "every_N_months", int(match.group(1))
    for rule, keywords in RECURRENCE_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return rule, None
    return "none", None


def _infer_title(text: str) -> str:
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if not first_line:
        first_line = "Untitled deadline"
    if len(first_line) > MAX_TITLE_LENGTH:
        first_line = first_line[: MAX_TITLE_LENGTH - 1].rstrip() + "…"
    return first_line


def fallback_extract(text: str) -> dict:
    """Deterministic regex/keyword extraction. Always available, no network."""
    if not text or not text.strip():
        raise NoDateFoundError("Cannot extract a deadline from empty text.")
    due = _find_date(text)
    category = _infer_category(text)
    recurrence_rule, recurrence_months = _infer_recurrence(text)
    return {
        "title": _infer_title(text),
        "category": category,
        "due_date": due,
        "recurrence": recurrence_rule,
        "recurrence_months": recurrence_months,
        "notes": None,
    }


_AI_PROMPT_TEMPLATE = """You extract structured administrative deadline data from pasted text \
(an email, a portal notice, a renewal reminder). Read the text below and respond with ONLY a \
single JSON object (no prose, no markdown fences) with exactly these keys:

- "title": short descriptive title (string, under 120 characters)
- "category": one of {categories}
- "due_date": the deadline date in YYYY-MM-DD format
- "recurrence": one of "none", "annual", "semesterly", "every_N_months"
- "recurrence_months": integer number of months if recurrence is "every_N_months", otherwise null
- "notes": a one-sentence summary of anything actionable, or null

If you cannot find an explicit date in the text, set "due_date" to null.

Text:
---
{text}
---
"""


def _parse_ai_json(raw_text: str) -> dict:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE | re.DOTALL)
    return json.loads(cleaned)


def ai_extract(text: str, api_key: str) -> dict:
    """Extract a deadline using Claude. Raises on any failure — callers should
    catch and fall back to fallback_extract()."""
    prompt = _AI_PROMPT_TEMPLATE.format(categories=", ".join(VALID_CATEGORIES), text=text)
    raw_reply = ai_client.call_claude(prompt, api_key)
    parsed = _parse_ai_json(raw_reply)

    due_date_str = parsed.get("due_date")
    if not due_date_str:
        raise NoDateFoundError("Claude could not find a date in the supplied text either.")
    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()

    category = parsed.get("category")
    if category not in VALID_CATEGORIES:
        category = "Other"

    recurrence_rule = parsed.get("recurrence") or "none"
    if recurrence_rule not in ("none", "annual", "semesterly", "every_N_months"):
        recurrence_rule = "none"
    recurrence_months = parsed.get("recurrence_months")
    if recurrence_rule != "every_N_months":
        recurrence_months = None

    title = parsed.get("title") or _infer_title(text)

    return {
        "title": title[:MAX_TITLE_LENGTH],
        "category": category,
        "due_date": due_date,
        "recurrence": recurrence_rule,
        "recurrence_months": recurrence_months,
        "notes": parsed.get("notes"),
    }


def extract_deadline(text: str, api_key: str | None) -> tuple[dict, str]:
    """Main entry point: try Claude if a key is present, otherwise (or on any
    Claude failure) fall back to the deterministic parser.

    Returns (fields_dict, extraction_method) where extraction_method is
    "ai" or "fallback".
    """
    if api_key:
        try:
            return ai_extract(text, api_key), "ai"
        except NoDateFoundError:
            raise
        except Exception:
            return fallback_extract(text), "fallback"
    return fallback_extract(text), "fallback"
