"""Deterministic concept and objective extraction from syllabus/lecture text.

No network calls, no third-party libraries. Three concept sources, in
descending confidence order:

1. ``marker``    — explicit ``[[Concept Name]]`` wiki-style markers.
2. ``heading``   — the topic portion of a heading line that contains a
                    colon/dash separator (``## Week 3: Stress and the HPA Axis``).
3. ``heuristic`` — runs of 2-4 consecutive capitalized words in body text.

Concepts are deduplicated across sources by a shared normalized name, with
higher-confidence sources winning the display name on a collision.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

MARKER_RE = re.compile(r"\[\[([^\[\]]+)\]\]")

MD_HEADING_RE = re.compile(r"^\s*#{1,6}\s+")
H1_ONLY_RE = re.compile(r"^\s*#(?!#)\s+")
NAMED_HEADING_RE = re.compile(
    r"^\s*(?:#{1,6}\s+)?(week|session|unit|module|lecture)\s+\d+\b", re.IGNORECASE
)
NAMED_HEADING_PREFIX_RE = re.compile(
    r"^(week|session|unit|module|lecture)\s+\d+\s*[:\-–—]?\s*(.*)$",
    re.IGNORECASE,
)
SEPARATOR_SPLIT_RE = re.compile(r"[:\-–—]\s*(.+)$")

CAP_WORD_RE = re.compile(r"^[A-Z][A-Za-z]*$")
COMMON_CAP_WORDS = {
    "The", "This", "That", "These", "Those", "It", "In", "On", "At", "We",
    "You", "I", "And", "Or", "But", "A", "An", "Students", "By", "For",
    "With", "Is", "Are", "Was", "Were", "Please", "Note", "See", "Also",
}

OBJECTIVE_RE = re.compile(
    r"^\s*(?:[-*•]\s*)?(?:"
    r"students will\s+|"
    r"learners will\s+|"
    r"by the end of (?:this|the) (?:course|week|session|unit|module|lecture)[,]?\s+|"
    r"objective\s*\d*[:.]\s*"
    r")(?P<obj>.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

_SOURCE_PRIORITY = {"marker": 3, "heading": 2, "heuristic": 1}


@dataclass(frozen=True)
class ParsedConcept:
    display_name: str
    normalized_name: str
    source: str


@dataclass(frozen=True)
class ParsedObjective:
    text: str


@dataclass
class ParsedDocument:
    concepts: list
    objectives: list


def normalize_name(name: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace, naive per-word singularize."""
    s = name.lower()
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    words = []
    for w in s.split(" "):
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        words.append(w)
    return " ".join(words)


def _is_heading(line: str) -> bool:
    return bool(MD_HEADING_RE.match(line)) or bool(NAMED_HEADING_RE.match(line))


def _heading_concept_text(line: str) -> str | None:
    text = line.strip()
    m = MD_HEADING_RE.match(text)
    if m:
        text = text[m.end():].strip()

    named = NAMED_HEADING_PREFIX_RE.match(text)
    if named:
        remainder = named.group(2).strip()
        return remainder or None

    sep = SEPARATOR_SPLIT_RE.search(text)
    if sep:
        remainder = sep.group(1).strip()
        return remainder or None

    return None


def extract_markers(text: str) -> list[str]:
    return [m.strip() for m in MARKER_RE.findall(text) if m.strip()]


def extract_headings(text: str) -> list[str]:
    concepts = []
    for line in text.splitlines():
        if not line.strip():
            continue
        # Strip any [[marker]] first so heading extraction never re-captures
        # the same bracketed text as a second, redundant concept.
        clean_line = MARKER_RE.sub(lambda m: m.group(1), line)
        if not _is_heading(clean_line):
            continue
        # A bare h1 ("# Course Name — Term") is almost always the document's
        # title/metadata line, not a content concept — skip it unless it also
        # carries a Week/Session/etc. prefix, which means it's a real section.
        if H1_ONLY_RE.match(clean_line) and not NAMED_HEADING_RE.match(clean_line):
            continue
        concept = _heading_concept_text(clean_line)
        if concept:
            concepts.append(concept)
    return concepts


def extract_heuristic_phrases(text: str) -> list[str]:
    body_lines = [
        line for line in text.splitlines()
        if line.strip() and not _is_heading(line)
    ]
    body = " ".join(MARKER_RE.sub(" ", line) for line in body_lines)
    sentences = re.split(r"(?<=[.!?])\s+|\n+", body)

    def clean(word: str) -> str:
        return re.sub(r"^[^\w]+|[^\w]+$", "", word)

    phrases = []
    for sentence in sentences:
        words = sentence.split()
        i = 0
        n = len(words)
        while i < n:
            cw = clean(words[i])
            if CAP_WORD_RE.match(cw):
                run = [cw]
                j = i + 1
                while j < n:
                    cw2 = clean(words[j])
                    if CAP_WORD_RE.match(cw2):
                        run.append(cw2)
                        j += 1
                    else:
                        break
                if 2 <= len(run) <= 4 and not all(w in COMMON_CAP_WORDS for w in run):
                    phrases.append(" ".join(run))
                i = j
            else:
                i += 1
    return phrases


def _flatten_soft_wraps(text: str) -> str:
    """Join line-wrapped sentences within a paragraph into a single line.

    OBJECTIVE_RE matches per physical line, so an objective sentence that
    the author simply word-wrapped across two lines (common in plain-text
    syllabi) would otherwise be truncated at the first line break. Blank
    lines (paragraph breaks) are preserved as real separators.
    """
    paragraphs = re.split(r"\n\s*\n", text)
    return "\n\n".join(re.sub(r"[ \t]*\n[ \t]*", " ", p).strip() for p in paragraphs)


def extract_objectives(text: str) -> list[ParsedObjective]:
    seen = set()
    objectives = []
    for m in OBJECTIVE_RE.finditer(_flatten_soft_wraps(text)):
        obj_text = m.group("obj").strip().rstrip(".")
        if obj_text and obj_text.lower() not in seen:
            seen.add(obj_text.lower())
            objectives.append(ParsedObjective(text=obj_text))
    return objectives


def parse_document(text: str) -> ParsedDocument:
    """Extract concepts (deduplicated across sources) and objectives."""
    candidates: list[tuple[str, str]] = []
    for name in extract_markers(text):
        candidates.append((name, "marker"))
    for name in extract_headings(text):
        candidates.append((name, "heading"))
    for name in extract_heuristic_phrases(text):
        candidates.append((name, "heuristic"))

    best: dict[str, ParsedConcept] = {}
    for display_name, source in candidates:
        norm = normalize_name(display_name)
        if not norm:
            continue
        existing = best.get(norm)
        if existing is None or _SOURCE_PRIORITY[source] > _SOURCE_PRIORITY[existing.source]:
            best[norm] = ParsedConcept(display_name=display_name, normalized_name=norm, source=source)

    concepts = sorted(best.values(), key=lambda c: c.normalized_name)
    objectives = extract_objectives(text)
    return ParsedDocument(concepts=concepts, objectives=objectives)
