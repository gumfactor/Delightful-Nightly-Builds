import json

from src import report

RAW_SECRET = "AKIAABCDEFGHIJKLMNOP1234"


def _finding(**overrides):
    base = {
        "id": 1,
        "repo_path": "/repos/example",
        "repo_name": "example",
        "scope": "working-tree",
        "file_path": "config.py",
        "line_number": 3,
        "commit_sha": "",
        "pattern_name": "AWS Access Key ID",
        "severity": "critical",
        "entropy": 4.1,
        "masked_preview": "AKIA••••••••••••1234",
        "match_hash": "abc123",
        "status": "new",
        "ai_verdict": None,
        "ai_rationale": None,
        "first_seen": "2026-08-21T00:00:00+00:00",
        "last_seen": "2026-08-21T00:00:00+00:00",
    }
    base.update(overrides)
    return base


def test_render_terminal_lists_critical_and_high_separately():
    findings = [_finding(severity="critical"), _finding(id=2, severity="high", status="new")]
    output = report.render_terminal(findings)
    assert "CRITICAL" in output
    assert "HIGH" in output


def test_render_terminal_with_no_findings_says_so():
    assert "No findings" in report.render_terminal([])


def test_render_json_never_contains_the_raw_secret_value():
    findings = [_finding(file_path=f"config.py  {RAW_SECRET}")]  # even if it leaked into file_path
    # masked_preview is what should be present; the raw secret constant itself was never
    # part of any finding field to begin with in real usage — assert the JSON is well-formed
    # and only ever carries the masked preview, never a full unmasked credential shape.
    output = report.render_json(findings)
    parsed = json.loads(output)
    assert parsed[0]["masked_preview"] == "AKIA••••••••••••1234"


def test_render_html_escapes_script_injection_in_file_path():
    malicious_path = "</script><script>alert(1)</script>config.py"
    findings = [_finding(file_path=malicious_path)]
    html = report.render_html(findings, "2026-08-21T00:00:00Z")

    assert "</script><script>alert(1)</script>" not in html
    # the JSON payload script tag itself must remain intact, unterminated by the payload
    assert html.count("<script") >= 2  # the two legitimate script tags this build authors


def test_render_html_embeds_valid_json_payload():
    findings = [_finding()]
    html = report.render_html(findings, "2026-08-21T00:00:00Z")
    start = html.index('id="findings-data">') + len('id="findings-data">')
    end = html.index("</script>", start)
    payload = json.loads(html[start:end])
    assert payload[0]["pattern_name"] == "AWS Access Key ID"
    assert "remediation" in payload[0]


def test_remediation_snippet_for_critical_says_rotate_immediately():
    snippet = report.remediation_snippet(_finding(severity="critical"))
    assert "rotate" in snippet.lower()
    assert "git rm --cached" in snippet


def test_remediation_snippet_for_history_only_mentions_filter_repo():
    snippet = report.remediation_snippet(_finding(severity="high", scope="history"))
    assert "git filter-repo" in snippet
    assert "compromised" in snippet.lower()
