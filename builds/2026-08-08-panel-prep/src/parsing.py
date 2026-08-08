"""Split a pasted/loaded grant-proposal draft into named sections.

Recognizes three header styles, checked line by line:
  - Markdown headers:      "# Specific Aims", "## Significance"
  - ALL-CAPS headers:      "SPECIFIC AIMS" alone on a line
  - "Header:" style lines: "Significance:" (rest of the line, if any, is
    treated as the start of that section's content)

If no recognized header is found anywhere in the document, the entire
document is treated as the Specific Aims section — most researchers'
first draft is exactly that, an aims-only paragraph, and the tool should
still produce a useful (if partial) checklist rather than an empty one.
"""

from __future__ import annotations

import re

# Canonical section key -> phrases that identify it. Order within each list
# does not matter; matching is against the whole normalized header line.
SECTION_ALIASES: dict[str, list[str]] = {
    "aims": ["specific aims", "specific aim", "aims"],
    "significance": ["significance"],
    "innovation": ["innovation"],
    "approach": ["approach", "research strategy", "research design and methods", "methods"],
    "rigor": ["rigor and reproducibility", "rigor & reproducibility", "rigor"],
}

# Longer/more specific aliases must be checked before shorter ones so
# "specific aims" matches before the bare "aims" fallback, etc.
_ORDERED_ALIASES: list[tuple[str, str]] = sorted(
    ((key, alias) for key, aliases in SECTION_ALIASES.items() for alias in aliases),
    key=lambda pair: -len(pair[1]),
)

_MARKDOWN_HEADER = re.compile(r"^\s{0,3}#{1,4}\s*(?P<title>.+?)\s*#*\s*$")
_COLON_HEADER = re.compile(r"^\s{0,3}(?P<title>[A-Za-z][A-Za-z &/'\-]{1,60}):\s*(?P<rest>.*)$")
_ALLCAPS_HEADER = re.compile(r"^\s{0,3}(?P<title>[A-Z][A-Z &/'\-]{2,60})\s*$")


def _normalize(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip().lower()


def _match_section_key(title: str) -> str | None:
    normalized = _normalize(title)
    for key, alias in _ORDERED_ALIASES:
        if normalized == alias or normalized.startswith(alias + " ") or alias in normalized:
            return key
    return None


def _detect_header(line: str) -> tuple[str, str] | None:
    """Return (section_key, leftover_content_on_same_line) if `line` is a
    recognized section header, else None."""
    match = _MARKDOWN_HEADER.match(line)
    if match:
        key = _match_section_key(match.group("title"))
        if key:
            return key, ""

    match = _COLON_HEADER.match(line)
    if match:
        key = _match_section_key(match.group("title"))
        if key:
            return key, match.group("rest")

    match = _ALLCAPS_HEADER.match(line)
    if match:
        key = _match_section_key(match.group("title"))
        if key:
            return key, ""

    return None


def parse(text: str) -> dict[str, str]:
    """Split `text` into {section_key: section_text}. Sections not present
    in the input are simply absent from the returned dict. Returns an
    empty dict for blank/whitespace-only input."""
    if not text or not text.strip():
        return {}

    lines = text.splitlines()
    buckets: dict[str, list[str]] = {}
    current_key: str | None = None

    for line in lines:
        detected = _detect_header(line)
        if detected:
            current_key, leftover = detected
            buckets.setdefault(current_key, [])
            if leftover.strip():
                buckets[current_key].append(leftover)
            continue

        if current_key is not None:
            buckets[current_key].append(line)
        # Lines before any recognized header are preamble and dropped
        # (title pages, PI name, grant number, etc.) unless nothing else
        # is ever found, handled by the whole-document fallback below.

    if not buckets:
        return {"aims": text.strip()}

    return {key: "\n".join(content_lines).strip() for key, content_lines in buckets.items() if "\n".join(content_lines).strip()}
