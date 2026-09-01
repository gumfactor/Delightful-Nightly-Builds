import json
import re

from src.report import build_payload, render


def _drift_entry(dependency="requests", repo_versions=None):
    repo_versions = repo_versions or {"user/a": "1.0.0", "user/b": "2.0.0"}
    return {
        "ecosystem": "python",
        "dependency": dependency,
        "repo_versions": repo_versions,
        "severity": "major",
        "min_version": "1.0.0",
        "max_version": "2.0.0",
    }


def _staleness_entry(repo="user/a", dependency="requests"):
    return {
        "repo": repo,
        "ecosystem": "python",
        "dependency": dependency,
        "pinned_version": "1.0.0",
        "latest_version": "2.0.0",
        "classification": "major-behind",
    }


def _repo_summary():
    return {"user/a": {"total": 3, "behind_count": 1, "major_count": 1}}


def test_build_payload_hero_stats():
    payload = build_payload(
        "2026-09-01", 2, [_drift_entry()], [_staleness_entry(), _staleness_entry(repo="user/b")],
        _repo_summary(), None,
    )
    assert payload["hero"]["repos_scanned"] == 2
    assert payload["hero"]["drifted_count"] == 1
    assert payload["hero"]["major_drift_count"] == 1
    assert payload["hero"]["unique_dependencies"] == 1


def test_render_produces_full_html_document():
    html = render("2026-09-01", 1, [], [], {}, None)
    assert html.startswith("<!DOCTYPE html>")
    assert "<title>Fleet Drift</title>" in html
    assert "</html>" in html


def test_render_includes_chart_js_cdn_pinned_version():
    html = render("2026-09-01", 1, [], [], {}, None)
    assert "chart.js@4.4.4" in html


def test_malicious_repo_name_never_appears_as_unescaped_script_tag():
    payload_script_close_attack = "</script><script>window.__xss=true;</script>"
    entry = _drift_entry(repo_versions={payload_script_close_attack: "1.0.0", "user/b": "2.0.0"})
    html = render("2026-09-01", 2, [entry], [], {}, None)
    assert "<script>window.__xss=true;</script>" not in html
    assert "<\\/script><script>window.__xss=true;<\\/script>" in html


def test_malicious_dependency_name_escaped_in_json_payload():
    payload_attack = '<img src=x onerror=alert(1)>'
    entry = _drift_entry(dependency=payload_attack)
    html = render("2026-09-01", 2, [entry], [], {}, None)
    # the raw tag must never appear unescaped outside the JSON payload
    assert "<img src=x onerror=alert(1)>" not in html.split('id="fleet-drift-data">')[0]


def test_data_payload_is_valid_json_after_unescaping():
    entry = _drift_entry()
    html = render("2026-09-01", 2, [entry], [], {}, None)
    match = re.search(
        r'<script type="application/json" id="fleet-drift-data">(.*?)</script>', html, re.DOTALL
    )
    assert match is not None
    raw_json = match.group(1).replace("<\\/", "</")
    data = json.loads(raw_json)
    assert data["hero"]["drifted_count"] == 1
    assert data["drift_rows"][0]["dependency"] == "requests"


def test_briefing_included_when_provided():
    html = render("2026-09-01", 1, [], [], {}, "Fix requests first.")
    match = re.search(
        r'<script type="application/json" id="fleet-drift-data">(.*?)</script>', html, re.DOTALL
    )
    raw_json = match.group(1).replace("<\\/", "</")
    data = json.loads(raw_json)
    assert data["briefing"] == "Fix requests first."


def test_briefing_none_when_not_provided():
    payload = build_payload("2026-09-01", 1, [], [], {}, None)
    assert payload["briefing"] is None


def test_dom_construction_uses_textcontent_not_innerhtml():
    html = render("2026-09-01", 1, [], [], {}, None)
    assert "innerHTML" not in html
