"""Parse and validate the Anthropic API JSON response for lecture content."""

import json
import re


REQUIRED_SECTIONS = [
    "objectives",
    "outline",
    "hook",
    "discussion_questions",
    "quiz_items",
    "key_concepts",
    "homework",
]

_DEFAULTS = {
    "objectives": ["Review lecture content for key learning objectives"],
    "outline": [{"time_range": "0-end", "title": "Lecture", "activity": "See notes"}],
    "hook": "No hook generated.",
    "discussion_questions": [{"question": "Discuss the key points from this lecture.", "teaching_note": ""}],
    "quiz_items": [],
    "key_concepts": [],
    "homework": "Reflect on the lecture content and write a one-page summary.",
}


def _extract_json(raw: str) -> str:
    """Return the first {...} JSON object found in raw text."""
    raw = raw.strip()
    start = raw.find("{")
    if start == -1:
        return raw
    depth = 0
    for i, ch in enumerate(raw[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return raw[start : i + 1]
    return raw[start:]


def parse_response(raw: str) -> dict:
    """
    Parse a raw string from the Anthropic API into a lecture dict.

    Returns a dict with all REQUIRED_SECTIONS keys.
    Falls back to _DEFAULTS for any missing or malformed sections.
    """
    try:
        text = _extract_json(raw)
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return dict(_DEFAULTS)

    result = {}
    for key in REQUIRED_SECTIONS:
        value = data.get(key)
        if value is None:
            result[key] = _DEFAULTS[key]
        else:
            result[key] = value

    result["objectives"] = _ensure_list(result["objectives"], str, _DEFAULTS["objectives"])
    result["outline"] = _ensure_list(result["outline"], dict, _DEFAULTS["outline"])
    result["discussion_questions"] = _ensure_list(
        result["discussion_questions"], dict, _DEFAULTS["discussion_questions"]
    )
    result["quiz_items"] = _validate_quiz_items(result["quiz_items"])
    result["key_concepts"] = _ensure_list(result["key_concepts"], str, _DEFAULTS["key_concepts"])

    if not isinstance(result["hook"], str):
        result["hook"] = _DEFAULTS["hook"]
    if not isinstance(result["homework"], str):
        result["homework"] = _DEFAULTS["homework"]

    return result


def _ensure_list(value, item_type, default):
    if not isinstance(value, list) or len(value) == 0:
        return default
    cleaned = [v for v in value if isinstance(v, item_type)]
    return cleaned if cleaned else default


def _validate_quiz_items(items) -> list:
    """Return only structurally valid quiz items."""
    if not isinstance(items, list):
        return []
    valid = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if "question" not in item or "options" not in item:
            continue
        if not isinstance(item.get("options"), dict):
            continue
        if "answer" not in item:
            item["answer"] = list(item["options"].keys())[0] if item["options"] else "A"
        if "rationale" not in item:
            item["rationale"] = ""
        valid.append(item)
    return valid


def make_slug(text: str) -> str:
    """Convert free text to a URL-safe slug."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text[:80]
