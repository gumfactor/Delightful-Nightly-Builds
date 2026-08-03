"""Tests for text/JSON/HTML report rendering."""

from __future__ import annotations

import json

from landing_pattern import report as report_module

SAMPLE_REPORT = {
    "repo": "owner/repo",
    "synced_at": "2026-08-03T12:00:00+00:00",
    "prs": [{"number": 1, "title": "Fix bug", "url": "u", "label": "ready", "age_days": 1, "files": []}],
    "batch1": [{"number": 1, "title": "Fix bug", "age_days": 1}],
    "batch2": [{"number": 2, "title": "Add feature", "age_days": 2, "conflicts_with": [1]}],
    "blocked": [{"number": 3, "title": "Broken thing", "label": "ci_failing", "age_days": 5}],
    "drafts": [{"number": 4, "title": "WIP", "age_days": 0}],
    "overlap_graph": {"1": {"2": ["a.py"]}},
}


def test_text_output_includes_every_pr_number():
    output = report_module.render_text(SAMPLE_REPORT)
    for number in (1, 2, 3, 4):
        assert f"#{number}" in output


def test_text_output_is_non_empty():
    assert len(report_module.render_text(SAMPLE_REPORT)) > 0


def test_text_output_includes_ai_note():
    output = report_module.render_text(SAMPLE_REPORT, ai_notes={3: "Fix the CI failure."})
    assert "Fix the CI failure." in output


def test_json_output_round_trips():
    output = report_module.render_json(SAMPLE_REPORT)
    parsed = json.loads(output)
    assert parsed == SAMPLE_REPORT


def test_html_output_contains_repo_name():
    output = report_module.render_html(SAMPLE_REPORT)
    assert "owner/repo" in output


def test_html_output_escapes_script_payload_in_title():
    malicious_report = dict(SAMPLE_REPORT)
    malicious_report["batch1"] = [
        {"number": 99, "title": "<script>alert(1)</script>", "age_days": 1}
    ]
    output = report_module.render_html(malicious_report)
    assert "<script>alert(1)</script>" not in output
    assert "&lt;script&gt;" in output


def test_html_output_escapes_ai_note():
    malicious_report = dict(SAMPLE_REPORT)
    output = report_module.render_html(
        malicious_report, ai_notes={3: "<img src=x onerror=alert(1)>"}
    )
    assert "<img src=x onerror=alert(1)>" not in output
    assert "&lt;img" in output


def test_html_output_shows_conflict_relationship():
    output = report_module.render_html(SAMPLE_REPORT)
    assert "conflicts with #1" in output


def test_html_output_is_valid_enough_to_have_matching_tags():
    output = report_module.render_html(SAMPLE_REPORT)
    assert output.count("<table>") == output.count("</table>")
    assert output.count("<tr>") == output.count("</tr>")
