import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import checklist, db, render, reviewer

SECTIONS = {"aims": "Aim 1: X. Our central hypothesis is that Y. This work will provide Z."}
INJECTION_PAYLOAD = "</script><script>window.__pwned = true;</script>"


@pytest.fixture
def conn(tmp_path):
    connection = db.connect(str(tmp_path / "test.db"))
    yield connection
    connection.close()


def _seed(conn, project_name, sections):
    checklist_result = checklist.run(sections)
    review = reviewer.build_review(sections, checklist_result, api_key=None)
    db.insert_version(conn, project_name, sections, checklist_result, review)


def test_render_terminal_contains_project_name_and_score(conn):
    _seed(conn, "Terminal Project", SECTIONS)
    latest = db.get_latest(conn, "Terminal Project")
    output = render.render_terminal("Terminal Project", latest)
    assert "Terminal Project" in output
    assert "Overall Impact estimate" in output


def test_render_html_raises_on_empty_history():
    with pytest.raises(ValueError):
        render.render_html("Empty Project", [])


def test_render_html_contains_project_name(conn):
    _seed(conn, "HTML Project", SECTIONS)
    history = db.get_history(conn, "HTML Project")
    html = render.render_html("HTML Project", history)
    assert "HTML Project" in html


def test_render_html_embeds_valid_json_payload(conn):
    _seed(conn, "JSON Project", SECTIONS)
    history = db.get_history(conn, "JSON Project")
    html = render.render_html("JSON Project", history)
    match = re.search(r'<script id="panel-data" type="application/json">(.*?)</script>', html, re.DOTALL)
    assert match is not None
    payload = json.loads(match.group(1))
    assert payload["project"] == "JSON Project"


def test_render_html_injection_payload_never_breaks_out_of_json_block(conn):
    malicious_sections = {"aims": f"Aim 1: {INJECTION_PAYLOAD} rest of aim text."}
    _seed(conn, "Injection Project", malicious_sections)
    history = db.get_history(conn, "Injection Project")
    html = render.render_html("Injection Project", history)

    # The literal, dangerous substring must never appear unescaped in the
    # output -- it must only exist inside the JSON blob as escaped unicode.
    assert "</script><script>window.__pwned" not in html
    assert "\\u003c/script\\u003e\\u003cscript\\u003e" in html

    match = re.search(r'<script id="panel-data" type="application/json">(.*?)</script>', html, re.DOTALL)
    payload = json.loads(match.group(1))
    aims_section = next(s for s in payload["latest"]["checklist_sections"] if s["label"] == "Specific Aims")
    assert INJECTION_PAYLOAD in aims_section["excerpt"]


def test_render_html_trend_data_reflects_multiple_versions(conn):
    _seed(conn, "Trend Project", SECTIONS)
    _seed(conn, "Trend Project", {})
    history = db.get_history(conn, "Trend Project")
    html = render.render_html("Trend Project", history)
    match = re.search(r'<script id="panel-data" type="application/json">(.*?)</script>', html, re.DOTALL)
    payload = json.loads(match.group(1))
    assert len(payload["versions"]) == 2
    assert payload["versions"][0]["version_num"] == 1
    assert payload["versions"][1]["version_num"] == 2


def test_render_html_lists_missing_sections(conn):
    _seed(conn, "Sparse Project", {"aims": "A vague paragraph."})
    history = db.get_history(conn, "Sparse Project")
    html = render.render_html("Sparse Project", history)
    match = re.search(r'<script id="panel-data" type="application/json">(.*?)</script>', html, re.DOTALL)
    payload = json.loads(match.group(1))
    assert "Significance" in payload["latest"]["missing_sections"]
