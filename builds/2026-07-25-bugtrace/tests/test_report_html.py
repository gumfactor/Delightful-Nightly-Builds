import json
import re

import pytest

from src import store
from src.report_html import render_html


@pytest.fixture
def conn(tmp_path):
    return store.init_db(str(tmp_path / "bugtrace.db"))


def test_render_html_contains_pinned_chart_cdn_version(conn):
    html = render_html(conn)
    assert "chart.js@4.4.4" in html


def test_render_html_embeds_valid_json_data_block(conn):
    store.upsert_fix(conn, "owner/repo", "sha1", "fix bug", "2026-06-01T00:00:00Z", "type_mismatch", "keyword", "expl", "diff")
    html = render_html(conn)
    match = re.search(
        r'<script type="application/json" id="bugtrace-data">(.*?)</script>', html, re.DOTALL
    )
    assert match is not None
    data = json.loads(match.group(1))
    assert data["total"] == 1
    assert data["fixes"][0]["sha"] == "sha1"


def test_render_html_uses_deterministic_coaching_without_ai_key(conn):
    store.upsert_fix(conn, "owner/repo", "sha1", "fix bug", "2026-06-01T00:00:00Z", "type_mismatch", "keyword", "expl", "diff")
    html = render_html(conn)
    assert "Consider adding a targeted check" in html


def test_render_html_uses_ai_coaching_when_key_and_request_fn_provided(conn):
    store.upsert_fix(conn, "owner/repo", "sha1", "fix bug", "2026-06-01T00:00:00Z", "type_mismatch", "keyword", "expl", "diff")

    def fake_request(api_key, prompt):
        return {"content": [{"text": "You keep tripping on type checks — add mypy."}]}

    html = render_html(conn, ai_api_key="fake-key", ai_request_fn=fake_request)
    assert "add mypy" in html


def test_render_html_escapes_script_injection_in_commit_message(conn):
    malicious_message = '</script><script>window.__pwned = true;</script>'
    store.upsert_fix(conn, "owner/repo", "sha1", malicious_message, "2026-06-01T00:00:00Z", "other", "keyword", "expl", "diff")
    html = render_html(conn)

    # The literal payload must never appear as an unescaped closing tag inside our data block.
    assert "</script><script>window.__pwned" not in html
    # It should still be present, but escaped so it can't split out of the JSON script block.
    assert "window.__pwned" in html

    match = re.search(
        r'<script type="application/json" id="bugtrace-data">(.*?)</script>', html, re.DOTALL
    )
    assert match is not None
    data = json.loads(match.group(1))
    assert data["fixes"][0]["message"] == malicious_message


def test_render_html_empty_state_has_placeholder_coaching(conn):
    html = render_html(conn)
    assert "run `sync`" in html
