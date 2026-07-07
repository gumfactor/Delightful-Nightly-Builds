import report_html


def make_diff_report(entries, ai_summary=None):
    return {
        "mode": "diff",
        "old_label": "old.json",
        "new_label": "new.json",
        "entries": entries,
        "overall_severity": None,
        "ai_summary": ai_summary,
    }


def test_render_html_contains_severity_classes():
    entries = [
        {"field": "id", "change": "removed", "severity": "breaking", "old": "int", "new": None, "detail": "field removed"},
        {"field": "email", "change": "added", "severity": "safe", "old": None, "new": "str", "detail": "field added"},
    ]
    html_text = report_html.render_html(make_diff_report(entries))
    assert 'class="breaking"' in html_text
    assert 'class="safe"' in html_text
    assert "1 breaking" in html_text
    assert "1 safe" in html_text


def test_render_html_escapes_untrusted_field_names():
    entries = [
        {"field": "<script>alert(1)</script>", "change": "added", "severity": "safe", "old": None, "new": "str", "detail": "x"},
    ]
    html_text = report_html.render_html(make_diff_report(entries))
    assert "<script>alert(1)</script>" not in html_text
    assert "&lt;script&gt;" in html_text


def test_render_html_has_no_external_resources():
    entries = [{"field": "id", "change": "added", "severity": "safe", "old": None, "new": "int", "detail": "x"}]
    html_text = report_html.render_html(make_diff_report(entries))
    assert "http://" not in html_text
    assert "https://" not in html_text
    assert "<script src=" not in html_text
    assert '<link href="http' not in html_text


def test_render_html_no_changes_message():
    html_text = report_html.render_html(make_diff_report([]))
    assert "No structural changes detected" in html_text


def test_render_html_includes_ai_summary_when_present():
    html_text = report_html.render_html(make_diff_report([], ai_summary="Everything looks fine."))
    assert "Migration Summary" in html_text
    assert "Everything looks fine." in html_text


def test_render_html_history_mode_renders_each_revision():
    report = {
        "mode": "history",
        "path": "data.json",
        "timeline": [
            {"sha": "abc12345", "date": "2026-01-01", "entries": []},
            {
                "sha": "def67890",
                "date": "2026-01-02",
                "entries": [{"field": "id", "change": "type_changed", "severity": "breaking", "old": "int", "new": "str", "detail": "x"}],
            },
        ],
        "overall_severity": "breaking",
        "ai_summary": None,
    }
    html_text = report_html.render_html(report)
    assert "abc12345" in html_text
    assert "def67890" in html_text
    assert "1 breaking" in html_text
