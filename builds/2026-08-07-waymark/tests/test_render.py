"""Tests for the self-contained HTML dashboard renderer."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src import render as render_module


class FakeRow(dict):
    """Mimics sqlite3.Row's mapping-style access used by render.py."""

    def __getitem__(self, key):
        return dict.__getitem__(self, key)


def _row(commit_hash: str, **overrides) -> FakeRow:
    base = {
        "repo_label": "repo-a",
        "commit_hash": commit_hash,
        "author": "Test User",
        "committed_at": "2026-01-01T00:00:00+00:00",
        "subject": "feat: add thing",
        "body": "",
        "files_changed": 2,
        "insertions": 10,
        "deletions": 3,
        "decision_score": 6,
        "tags": json.dumps(["feat"]),
        "summary": "Added a thing",
        "ai_summary": None,
    }
    base.update(overrides)
    return FakeRow(base)


def test_render_dashboard_writes_file(tmp_path: Path):
    output = tmp_path / "dashboard.html"
    result = render_module.render_dashboard([_row("hash1")], output)
    assert result == output
    assert output.exists()


def test_render_dashboard_creates_parent_directories(tmp_path: Path):
    output = tmp_path / "nested" / "dir" / "dashboard.html"
    render_module.render_dashboard([_row("hash1")], output)
    assert output.exists()


def test_render_dashboard_is_valid_html_document(tmp_path: Path):
    output = tmp_path / "dashboard.html"
    render_module.render_dashboard([_row("hash1")], output)
    content = output.read_text(encoding="utf-8")
    assert content.strip().startswith("<!doctype html>")
    assert "</html>" in content


def test_render_dashboard_embeds_commit_count(tmp_path: Path):
    output = tmp_path / "dashboard.html"
    render_module.render_dashboard([_row("hash1"), _row("hash2")], output)
    content = output.read_text(encoding="utf-8")
    match = re.search(r'"hash":\s*"[a-z0-9]+"', content)
    assert match is not None
    assert content.count('"hash":') == 2


def test_render_dashboard_escapes_script_injection_in_subject(tmp_path: Path):
    output = tmp_path / "dashboard.html"
    malicious = _row("hash1", subject="</script><script>alert(1)</script>")
    render_module.render_dashboard([malicious], output)
    content = output.read_text(encoding="utf-8")
    # The literal closing-script-tag sequence must never appear unescaped inside the payload
    assert "</script><script>alert" not in content
    # But the escaped unicode form should be present, proving the text wasn't dropped
    assert "\\u003c/script\\u003e\\u003cscript\\u003ealert(1)" in content


def test_render_dashboard_embedded_json_is_parseable(tmp_path: Path):
    output = tmp_path / "dashboard.html"
    render_module.render_dashboard([_row("hash1", subject="feat: <b>bold</b> & 'quotes'")], output)
    content = output.read_text(encoding="utf-8")
    script_match = re.search(
        r'<script id="waymark-data" type="application/json">(.*?)</script>', content, re.DOTALL
    )
    assert script_match is not None
    payload = json.loads(script_match.group(1))
    assert payload[0]["subject"] == "feat: <b>bold</b> & 'quotes'"


def test_render_dashboard_handles_empty_commit_list(tmp_path: Path):
    output = tmp_path / "dashboard.html"
    render_module.render_dashboard([], output)
    content = output.read_text(encoding="utf-8")
    assert "0 indexed commits" in content


def test_render_dashboard_lists_distinct_repos_and_tags(tmp_path: Path):
    output = tmp_path / "dashboard.html"
    rows = [
        _row("h1", repo_label="repo-a", tags=json.dumps(["feat"])),
        _row("h2", repo_label="repo-b", tags=json.dumps(["fix"])),
    ]
    render_module.render_dashboard(rows, output)
    content = output.read_text(encoding="utf-8")
    assert "2 indexed commits across 2 repos" in content
