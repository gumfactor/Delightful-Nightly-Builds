"""Tests for report rendering (text, JSON, HTML)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.bids_rules import Finding
from src.report import build_report_dict, render_html, render_json, render_text
from src.scanner import ScanResult


def _fake_result(findings, root=Path("/tmp/dataset")):
    return ScanResult(root=root, files=[], findings=findings)


def test_build_report_dict_counts_errors_and_warnings():
    findings = [
        Finding("error", "MISSING_SUB_ENTITY", "no sub", "a.nii.gz"),
        Finding("warning", "MISSING_SIDECAR", "no sidecar", "b.nii.gz"),
        Finding("warning", "MISSING_SIDECAR", "no sidecar", "c.nii.gz"),
    ]
    report = build_report_dict(_fake_result(findings))
    assert report["summary"] == {"errors": 1, "warnings": 2}
    assert len(report["findings"]) == 3


def test_render_text_reports_no_violations_when_clean():
    report = build_report_dict(_fake_result([]))
    text = render_text(report)
    assert "No violations found." in text


def test_render_text_includes_each_finding():
    findings = [Finding("error", "MISSING_SUB_ENTITY", "no sub entity", "a.nii.gz")]
    report = build_report_dict(_fake_result(findings))
    text = render_text(report)
    assert "MISSING_SUB_ENTITY" in text
    assert "a.nii.gz" in text


def test_render_json_round_trips():
    findings = [Finding("warning", "MISSING_EVENTS", "missing events", "x.nii.gz")]
    report = build_report_dict(_fake_result(findings))
    parsed = json.loads(render_json(report))
    assert parsed["summary"]["warnings"] == 1
    assert parsed["findings"][0]["code"] == "MISSING_EVENTS"


def test_render_html_escapes_malicious_filename():
    findings = [
        Finding(
            "warning",
            "UNRECOGNIZED_SUFFIX",
            "weird file",
            "<script>alert(1)</script>.nii.gz",
        )
    ]
    report = build_report_dict(_fake_result(findings))
    html_out = render_html(report)
    assert "<script>alert(1)</script>" not in html_out
    assert "&lt;script&gt;" in html_out


def test_render_html_includes_ai_summary_when_present():
    report = build_report_dict(_fake_result([]), ai_summary="Fix the sidecars first.")
    html_out = render_html(report)
    assert "Fix the sidecars first." in html_out


def test_render_html_is_valid_document_shell():
    report = build_report_dict(_fake_result([]))
    html_out = render_html(report)
    assert html_out.strip().startswith("<!DOCTYPE html>")
    assert "<html" in html_out and "</html>" in html_out
