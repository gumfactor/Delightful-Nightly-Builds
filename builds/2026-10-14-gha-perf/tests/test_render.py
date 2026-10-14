import json
import re

from conftest import NOW, make_job, make_run, make_step
from gha_perf.analyze import analyze
from gha_perf.render import render_html


def _report(**run_kwargs):
    jobs = [make_job(1, steps=[make_step("Install deps", 100)])]
    runs = [make_run(i, jobs=[make_job(i, steps=[make_step("Install deps", 100)])], **run_kwargs) for i in range(1, 5)]
    return analyze(runs, 30, NOW)


def test_html_is_self_contained_with_pinned_chartjs():
    html = render_html(_report())
    assert html.startswith("<!doctype html>") and "chart.js@4.4.4" in html
    assert "@latest" not in html and "Install deps" in html


def test_repo_and_workflow_names_are_escaped():
    report = analyze([make_run(1, repo="me/<script>alert(1)</script>", workflow='<img src=x onerror="x">')], 30, NOW)
    html = render_html(report)
    assert "<script>alert(1)</script>" not in html and "<img src=x" not in html
    assert "&lt;script&gt;" in html


def test_embedded_json_cannot_break_out_of_script_tag():
    report = analyze([make_run(1, repo="me/</script><b>x")], 30, NOW)
    html = render_html(report)
    payload = re.search(r'id="report-data" type="application/json">(.*?)</script>', html, re.S).group(1)
    assert "</" not in payload
    assert json.loads(payload)["repos"][0]["repo"] == "me/</script><b>x"


def test_ai_summary_is_escaped_and_optional():
    assert "AI briefing" not in render_html(_report())
    html = render_html(_report(), "Fix <b>this</b>")
    assert "AI briefing" in html and "Fix &lt;b&gt;this" in html


def test_collection_errors_are_shown():
    report = analyze([make_run(1)], 30, NOW, errors={"me/bad": "HTTP 500"})
    assert "me/bad: HTTP 500" in render_html(report)


def test_empty_report_renders_placeholders():
    html = render_html(analyze([], 30, NOW))
    assert "No workflow runs in this window." in html and "No job detail was fetched." in html
