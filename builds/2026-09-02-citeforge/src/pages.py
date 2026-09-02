"""Page-range parsing and the ICMJE/AMA digit-elision convention.

ICMJE's recommended format elides shared leading digits between a start and
end page number (e.g. "284-287" -> "284-7"), so the fewest digits needed to
disambiguate the end page are shown. Cross-checked in tests against real
published ICMJE sample citations.
"""

from __future__ import annotations

import re

_RANGE_RE = re.compile(r"^\s*([^\s\-–—]+)\s*[\-–—]\s*([^\s\-–—]+)\s*$")


def parse_page_range(pages: str) -> tuple[str, str]:
    if not pages:
        return "", ""
    match = _RANGE_RE.match(pages)
    if not match:
        return pages.strip(), ""
    return match.group(1), match.group(2)


def icmje_truncate(start: str, end: str) -> str:
    if not end:
        return start
    if start == end:
        return start
    if not (start.isdigit() and end.isdigit()) or len(end) < len(start):
        return f"{start}-{end}"
    i = 0
    while i < len(start) and i < len(end) and start[i] == end[i]:
        i += 1
    truncated_end = end[i:] or end[-1]
    return f"{start}-{truncated_end}"


def format_pages_ama_vancouver(pages: str) -> str:
    start, end = parse_page_range(pages)
    if not start:
        return ""
    if not end:
        return start
    return icmje_truncate(start, end)


def format_pages_full(pages: str, dash: str = "–") -> str:
    start, end = parse_page_range(pages)
    if not start:
        return ""
    if not end:
        return start
    return f"{start}{dash}{end}"
