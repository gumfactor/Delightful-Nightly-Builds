from pathlib import Path

import pytest

from src.checks import (
    check_broken_anchors,
    check_broken_file_references,
    check_modal_contradictions,
    check_required_sections,
)
from src.parser import parse_document

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str):
    path = FIXTURES / name / "instructions.md"
    return parse_document(path.read_text(encoding="utf-8")), path.parent


def test_check_broken_file_references_flags_missing_file():
    doc, root = _load("broken")
    findings = check_broken_file_references(doc, root)
    flagged = {f["excerpt"] for f in findings}
    assert "missing_reference.md" in flagged
    assert "also_missing.json" in flagged
    assert all(f["severity"] == "error" for f in findings)


def test_check_broken_file_references_passes_existing_file():
    doc, root = _load("clean")
    findings = check_broken_file_references(doc, root)
    assert findings == []


def test_check_broken_anchors_flags_missing_heading():
    doc, _ = _load("broken")
    findings = check_broken_anchors(doc)
    assert len(findings) == 1
    assert "does-not-exist" in findings[0]["message"]


def test_check_broken_anchors_passes_valid_anchor():
    doc, _ = _load("clean")
    findings = check_broken_anchors(doc)
    assert findings == []


def test_check_required_sections_flags_missing():
    doc, _ = _load("broken")
    findings = check_required_sections(doc, ["Goal", "Scope", "Testing"])
    assert len(findings) == 1
    assert "Testing" in findings[0]["excerpt"]


def test_check_required_sections_passes_when_present():
    doc, _ = _load("clean")
    findings = check_required_sections(doc, ["Goal", "Scope", "Testing"])
    assert findings == []


def test_check_required_sections_ignores_blank_entries():
    doc, _ = _load("clean")
    findings = check_required_sections(doc, ["Goal", "", "  "])
    assert findings == []


def test_check_modal_contradiction_flags_overlapping_always_never():
    doc, _ = _load("broken")
    findings = check_modal_contradictions(doc)
    assert len(findings) == 1
    assert findings[0]["severity"] == "warning"
    assert "manual review" in findings[0]["message"]


def test_check_modal_contradiction_ignores_unrelated_statements():
    doc, _ = _load("clean")
    findings = check_modal_contradictions(doc)
    assert findings == []


@pytest.mark.parametrize("threshold", [0.9])
def test_check_modal_contradiction_respects_higher_threshold(threshold):
    doc, _ = _load("broken")
    findings = check_modal_contradictions(doc, overlap_threshold=threshold)
    assert findings == []
