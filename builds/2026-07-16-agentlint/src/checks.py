"""Deterministic checks for AgentLint.

Each check function takes a parsed document (and whatever extra context
it needs) and returns a list of Finding dicts. Findings are plain dicts
(not a class) so they serialize to JSON and template into HTML without
any extra glue.
"""

from __future__ import annotations

import re
from pathlib import Path

from .parser import ParsedDocument

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"
SEVERITY_INFO = "info"

_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "when",
    "have", "has", "not", "are", "was", "were", "will", "shall", "must",
    "should", "never", "always", "use", "using", "used", "only", "also",
    "any", "all", "one", "two", "before", "after", "without", "your",
    "you", "its", "it's", "can", "may", "might", "would", "could", "than",
}

_MODAL_LINE_RE = re.compile(
    r"^[-*\d.\s]*(?:\*\*)?(always|never)(?:\*\*)?[:\s]+(.+)$",
    re.IGNORECASE,
)


def make_finding(check: str, severity: str, message: str, excerpt: str = "", line=None) -> dict:
    return {
        "check": check,
        "severity": severity,
        "message": message,
        "excerpt": excerpt,
        "line": line,
    }


def check_broken_file_references(doc: ParsedDocument, root: Path) -> list:
    findings = []
    seen = set()
    candidates = [(cs.text, cs.line) for cs in doc.code_spans]
    candidates += [(link.target, link.line) for link in doc.links if link.kind == "relative"]

    for candidate, line in candidates:
        key = (candidate, line)
        if key in seen:
            continue
        seen.add(key)
        target_path = (root / candidate).resolve()
        if not target_path.exists():
            findings.append(make_finding(
                check="broken_file_reference",
                severity=SEVERITY_ERROR,
                message=f"Referenced path does not exist relative to {root}: {candidate}",
                excerpt=candidate,
                line=line,
            ))
    return findings


def check_broken_anchors(doc: ParsedDocument) -> list:
    findings = []
    known_slugs = {h.slug for h in doc.headings}
    for link in doc.links:
        if link.kind != "anchor":
            continue
        anchor = link.target[1:]
        if anchor not in known_slugs:
            findings.append(make_finding(
                check="broken_anchor",
                severity=SEVERITY_ERROR,
                message=f"Internal link points to a heading anchor that doesn't exist: #{anchor}",
                excerpt=f"[{link.label}]({link.target})",
                line=link.line,
            ))
    return findings


def check_required_sections(doc: ParsedDocument, required_sections: list) -> list:
    findings = []
    present = {h.text.strip().lower() for h in doc.headings}
    for section in required_sections:
        normalized = section.strip().lower()
        if not normalized:
            continue
        if normalized not in present:
            findings.append(make_finding(
                check="missing_required_section",
                severity=SEVERITY_ERROR,
                message=f"Required section heading not found: \"{section.strip()}\"",
                excerpt=section.strip(),
                line=None,
            ))
    return findings


def _extract_modal_statements(doc: ParsedDocument) -> list:
    statements: list = []
    for line_no, raw_line in enumerate(doc.lines, start=1):
        match = _MODAL_LINE_RE.match(raw_line.strip())
        if match:
            modal = match.group(1).lower()
            statement = match.group(2).strip()
            statements.append((modal, statement, line_no))
    return statements


def _significant_words(text: str) -> set:
    words = re.findall(r"[a-zA-Z']+", text.lower())
    return {w for w in words if len(w) >= 3 and w not in _STOPWORDS}


def check_modal_contradictions(doc: ParsedDocument, overlap_threshold: float = 0.5) -> list:
    findings = []
    statements = _extract_modal_statements(doc)
    always_statements = [s for s in statements if s[0] == "always"]
    never_statements = [s for s in statements if s[0] == "never"]

    for always_text, always_words, always_line in (
        (s[1], _significant_words(s[1]), s[2]) for s in always_statements
    ):
        if not always_words:
            continue
        for never_text, never_words, never_line in (
            (s[1], _significant_words(s[1]), s[2]) for s in never_statements
        ):
            if not never_words:
                continue
            overlap = always_words & never_words
            ratio = len(overlap) / min(len(always_words), len(never_words))
            if ratio >= overlap_threshold:
                findings.append(make_finding(
                    check="possible_modal_contradiction",
                    severity=SEVERITY_WARNING,
                    message=(
                        "Possible contradiction — needs manual review: an \"Always\" statement "
                        f"(line {always_line}) and a \"Never\" statement (line {never_line}) "
                        f"share overlapping subject matter ({', '.join(sorted(overlap))})."
                    ),
                    excerpt=f"Always {always_text} | Never {never_text}",
                    line=always_line,
                ))
    return findings


def run_all_checks(doc: ParsedDocument, root: Path, required_sections: list) -> list:
    findings: list = []
    findings += check_broken_file_references(doc, root)
    findings += check_broken_anchors(doc)
    findings += check_required_sections(doc, required_sections)
    findings += check_modal_contradictions(doc)
    return findings
