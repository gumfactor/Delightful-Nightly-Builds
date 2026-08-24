"""Deterministic Markdown structural parser for raw lecture notes."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
_BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+(.*\S)\s*$")
_OBJECTIVES_HEADING_RE = re.compile(r"^(learning )?objectives?$", re.IGNORECASE)
_BY_THE_END_RE = re.compile(
    r"by the end of (?:this |the )?(?:lecture|class|session|unit)\b[^.\n]*?"
    r"students will\b[^.\n]*\.",
    re.IGNORECASE,
)


@dataclass
class Section:
    heading: str
    level: int
    bullets: list[str] = field(default_factory=list)
    prose: list[str] = field(default_factory=list)

    @property
    def bullet_count(self) -> int:
        return len(self.bullets)

    @property
    def word_count(self) -> int:
        text = " ".join(self.bullets) + " " + " ".join(self.prose)
        return len(text.split())


@dataclass
class Lecture:
    path: str
    title: str
    objectives: list[str]
    sections: list[Section]
    heading_skip_warning: bool


def _title_from_filename(path: Path) -> str:
    return path.stem.replace("_", " ").replace("-", " ").strip().title()


def _extract_objectives_block(lines: list[str], start: int) -> tuple[list[str], int]:
    """Collect objective lines following an Objectives heading until the next heading."""
    objectives: list[str] = []
    i = start
    while i < len(lines):
        line = lines[i]
        if _HEADING_RE.match(line):
            break
        bullet_match = _BULLET_RE.match(line)
        if bullet_match:
            objectives.append(bullet_match.group(1).strip())
        elif line.strip():
            objectives.append(line.strip())
        i += 1
    return objectives, i


def parse_lecture(path: Path) -> Lecture:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    title: str | None = None
    heading_levels: list[int] = []
    objectives: list[str] = []
    sections: list[Section] = []
    current: Section | None = None

    i = 0
    while i < len(lines):
        line = lines[i]
        heading_match = _HEADING_RE.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()
            heading_levels.append(level)

            if level == 1 and title is None:
                title = heading_text
                i += 1
                continue

            if _OBJECTIVES_HEADING_RE.match(heading_text):
                block, i = _extract_objectives_block(lines, i + 1)
                objectives.extend(block)
                continue

            if level == 2:
                current = Section(heading=heading_text, level=level)
                sections.append(current)
            elif current is not None:
                # Sub-headings (H3+) become part of the current section's prose.
                current.prose.append(heading_text)
            i += 1
            continue

        bullet_match = _BULLET_RE.match(line)
        if bullet_match and current is not None:
            current.bullets.append(bullet_match.group(1).strip())
        elif line.strip() and current is not None:
            current.prose.append(line.strip())
        i += 1

    if title is None:
        title = _title_from_filename(path)

    heading_skip_warning = False
    for prev, curr in zip(heading_levels, heading_levels[1:]):
        if curr > prev + 1:
            heading_skip_warning = True
            break

    body_text = "\n".join(lines)
    seen_lower = {obj.lower() for obj in objectives}
    for match in _BY_THE_END_RE.finditer(body_text):
        sentence = match.group(0).strip()
        if sentence.lower() not in seen_lower:
            objectives.append(sentence)
            seen_lower.add(sentence.lower())

    return Lecture(
        path=str(path),
        title=title,
        objectives=objectives,
        sections=sections,
        heading_skip_warning=heading_skip_warning,
    )
