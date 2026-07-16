import json

from src.checks import make_finding
from src.report import build_report, render_html, render_json, render_text


def _sample_findings():
    return [
        make_finding("broken_file_reference", "error", "Missing file.", "foo.md", line=3),
        make_finding("possible_modal_contradiction", "warning", "Might conflict.", "Always/Never", line=10),
        make_finding("ai_review", "info", "AI review skipped.", "", line=None),
    ]


def test_build_report_summarizes_counts():
    report = build_report(_sample_findings(), target="CLAUDE.md")
    assert report["summary"] == {"error": 1, "warning": 1, "info": 1}
    assert report["target"] == "CLAUDE.md"


def test_build_report_sorts_by_severity_then_line():
    report = build_report(_sample_findings(), target="CLAUDE.md")
    severities = [f["severity"] for f in report["findings"]]
    assert severities == ["error", "warning", "info"]


def test_render_json_report_structure():
    report = build_report(_sample_findings(), target="CLAUDE.md")
    rendered = render_json(report)
    parsed = json.loads(rendered)
    assert parsed["target"] == "CLAUDE.md"
    assert len(parsed["findings"]) == 3
    assert set(parsed["summary"].keys()) == {"error", "warning", "info"}


def test_render_text_report_contains_findings():
    report = build_report(_sample_findings(), target="CLAUDE.md")
    rendered = render_text(report)
    assert "Missing file." in rendered
    assert "Might conflict." in rendered
    assert "1 error(s)" in rendered


def test_render_text_report_no_issues_case():
    report = build_report([], target="CLAUDE.md")
    rendered = render_text(report)
    assert "No issues found." in rendered


def test_render_html_report_escapes_excerpt():
    malicious = make_finding(
        "ai_review", "error", "Injected content test.", "<script>alert(1)</script>", line=1
    )
    report = build_report([malicious], target="CLAUDE.md")
    rendered = render_html(report)
    assert "<script>alert(1)</script>" not in rendered
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rendered


def test_render_html_report_is_valid_shell():
    report = build_report(_sample_findings(), target="CLAUDE.md")
    rendered = render_html(report)
    assert rendered.startswith("<!doctype html>")
    assert "<title>" in rendered
    assert "AgentLint report" in rendered


def test_render_html_report_empty_state():
    report = build_report([], target="CLAUDE.md")
    rendered = render_html(report)
    assert "No issues found." in rendered
