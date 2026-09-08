import json

from src.classifier import Finding
from src.report import render_html, render_json, render_terminal, tier_counts


def _make_finding(**overrides) -> Finding:
    defaults = dict(
        repo="myrepo",
        commit="abc123def456",
        file="config.py",
        line=7,
        pattern_name="AWS Access Key ID",
        tier="high",
        redacted_snippet='AWS_KEY = "[REDACTED:20chars]"',
        still_in_head=True,
        ai_verdict=None,
    )
    defaults.update(overrides)
    return Finding(**defaults)


def test_tier_counts_tallies_each_tier_correctly():
    findings = [
        _make_finding(tier="high"),
        _make_finding(tier="high"),
        _make_finding(tier="medium"),
        _make_finding(tier="low"),
    ]
    counts = tier_counts(findings)
    assert counts == {"high": 2, "medium": 1, "low": 1}


def test_tier_counts_empty_list_is_all_zero():
    assert tier_counts([]) == {"high": 0, "medium": 0, "low": 0}


def test_render_terminal_includes_finding_details():
    finding = _make_finding()
    output = render_terminal([finding])
    assert "myrepo" in output
    assert "config.py:7" in output
    assert "AWS Access Key ID" in output
    assert "STILL IN HEAD" in output


def test_render_terminal_no_findings_message():
    output = render_terminal([])
    assert "No findings." in output


def test_render_json_round_trips_finding_fields(tmp_path):
    finding = _make_finding(tier="medium", ai_verdict="uncertain")
    out_path = tmp_path / "report.json"
    render_json([finding], out_path)
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(payload) == 1
    assert payload[0]["repo"] == "myrepo"
    assert payload[0]["tier"] == "medium"
    assert payload[0]["ai_verdict"] == "uncertain"


def test_render_html_escapes_script_injection_in_file_path(tmp_path):
    finding = _make_finding(file='<script>alert(1)</script>.py')
    out_path = tmp_path / "report.html"
    render_html([finding], out_path)
    html_text = out_path.read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in html_text
    assert "&lt;script&gt;" in html_text


def test_render_html_escapes_injection_in_redacted_snippet(tmp_path):
    finding = _make_finding(redacted_snippet='<img src=x onerror="alert(1)">')
    out_path = tmp_path / "report.html"
    render_html([finding], out_path)
    html_text = out_path.read_text(encoding="utf-8")
    assert '<img src=x onerror="alert(1)">' not in html_text


def test_render_html_shows_tier_summary_counts(tmp_path):
    findings = [_make_finding(tier="high"), _make_finding(tier="medium")]
    out_path = tmp_path / "report.html"
    render_html(findings, out_path)
    html_text = out_path.read_text(encoding="utf-8")
    assert "Secrets Sentinel Report" in html_text
    assert "high confidence" in html_text


def test_render_html_no_findings_renders_placeholder_row(tmp_path):
    out_path = tmp_path / "report.html"
    render_html([], out_path)
    html_text = out_path.read_text(encoding="utf-8")
    assert "No findings." in html_text
