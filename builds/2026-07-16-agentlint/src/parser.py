"""Markdown parsing helpers for AgentLint.

Everything here is line-oriented on purpose: agent instruction files
(CLAUDE.md / AGENTS.md style docs) overwhelmingly put one heading, one
link, or one inline-code reference per line. Line-oriented parsing keeps
line-number attribution simple and correct for that common case, at the
cost of not handling multi-line markdown constructs — an acceptable
trade-off for a tool that reports "best-effort" line numbers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")

# Extensions (or trailing slash for directories) that make a code-span
# candidate look like an actual file/path reference rather than a shell
# command, function name, or generic code identifier.
PATH_LIKE_EXTENSIONS = (
    ".md", ".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yml", ".yaml",
    ".toml", ".txt", ".sh", ".html", ".css", ".cfg", ".ini", ".csv",
    ".gitignore", ".env",
)


@dataclass
class Heading:
    level: int
    text: str
    line: int
    slug: str


@dataclass
class CodeSpanRef:
    text: str
    line: int


@dataclass
class LinkRef:
    label: str
    target: str
    line: int
    kind: str  # "anchor" | "external" | "relative"


@dataclass
class ParsedDocument:
    lines: list = field(default_factory=list)
    headings: list = field(default_factory=list)
    code_spans: list = field(default_factory=list)
    links: list = field(default_factory=list)


def slugify_heading(text: str, seen_counts: dict) -> str:
    """Approximate GitHub's heading-to-anchor slugification.

    Lowercases, strips characters that aren't word characters/spaces/hyphens,
    collapses whitespace to single hyphens, and — matching GitHub's actual
    behavior — appends -1, -2, ... to repeated slugs in order of appearance.
    `seen_counts` is mutated across calls so callers can slugify a full
    document's headings in a single left-to-right pass.
    """
    base = text.strip().lower()
    base = re.sub(r"[^\w\s-]", "", base)
    base = re.sub(r"\s+", "-", base).strip("-")
    count = seen_counts.get(base, 0)
    seen_counts[base] = count + 1
    if count == 0:
        return base
    return f"{base}-{count}"


def _looks_like_path(candidate: str) -> bool:
    if not candidate or "\n" in candidate:
        return False
    if candidate.startswith(("http://", "https://", "mailto:")):
        return False
    if any(ch.isspace() for ch in candidate):
        return False
    if candidate.endswith("/"):
        return True
    lower = candidate.lower()
    if any(lower.endswith(ext) for ext in PATH_LIKE_EXTENSIONS):
        return True
    # Bare relative/absolute paths with a directory separator and no
    # obviously code-like characters (parens, quotes) are treated as
    # path candidates too, e.g. `builds/index.md` already covered above,
    # `src/components` (a directory reference with no extension).
    if "/" in candidate and not any(ch in candidate for ch in "(){}<>\"'"):
        return True
    return False


def parse_document(content: str) -> ParsedDocument:
    """Parse a markdown document into headings, code spans, and links."""
    lines = content.splitlines()
    doc = ParsedDocument(lines=lines)
    seen_slugs: dict = {}

    for line_no, raw_line in enumerate(lines, start=1):
        heading_match = HEADING_RE.match(raw_line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            slug = slugify_heading(text, seen_slugs)
            doc.headings.append(Heading(level=level, text=text, line=line_no, slug=slug))
            # Headings can't also contain meaningful code-span/link refs
            # worth checking as file paths, so skip further parsing of
            # this line — matches how CLAUDE.md-style docs are written.
            continue

        for code_match in CODE_SPAN_RE.finditer(raw_line):
            candidate = code_match.group(1)
            if _looks_like_path(candidate):
                doc.code_spans.append(CodeSpanRef(text=candidate, line=line_no))

        for link_match in LINK_RE.finditer(raw_line):
            label, target = link_match.group(1), link_match.group(2)
            if target.startswith("#"):
                kind = "anchor"
            elif target.startswith(("http://", "https://", "mailto:")):
                kind = "external"
            else:
                kind = "relative"
            doc.links.append(LinkRef(label=label, target=target, line=line_no, kind=kind))

    return doc
