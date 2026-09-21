import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import github_client, main, store  # noqa: E402

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "sample_data" / "starred_page.json"


def _fixture_entries():
    return json.loads(FIXTURE_PATH.read_text())


def _patch_fetch(monkeypatch, entries):
    def fake_fetch(token, since=None, **kwargs):
        filtered = [e for e in entries if since is None or e["starred_at"] > since]
        return [github_client._parse_repo(e) for e in filtered]

    monkeypatch.setattr(main.github_client, "fetch_starred", fake_fetch)


def test_sync_requires_token(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    db_path = str(tmp_path / "test.db")
    rc = main.main(["--db", db_path, "sync"])
    assert rc == 1
    assert "token" in capsys.readouterr().err.lower()


def test_sync_ingests_fixture_repos(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _patch_fetch(monkeypatch, _fixture_entries())
    db_path = str(tmp_path / "test.db")

    rc = main.main(["--db", db_path, "sync"])
    assert rc == 0

    conn = store.connect(db_path)
    assert store.count_repos(conn) == 5
    conn.close()


def test_sync_is_idempotent_on_rerun(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    _patch_fetch(monkeypatch, _fixture_entries())
    db_path = str(tmp_path / "test.db")

    main.main(["--db", db_path, "sync"])
    main.main(["--db", db_path, "sync"])

    conn = store.connect(db_path)
    assert store.count_repos(conn) == 5
    conn.close()


def test_sync_without_ai_flag_always_produces_tag_and_note(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _patch_fetch(monkeypatch, _fixture_entries())
    db_path = str(tmp_path / "test.db")

    main.main(["--db", db_path, "sync"])

    conn = store.connect(db_path)
    for repo in store.list_repos(conn):
        assert repo["tag"]
        assert repo["note"]
        assert repo["source"] == "rule"
    conn.close()


def test_search_command_prints_matches(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    _patch_fetch(monkeypatch, _fixture_entries())
    db_path = str(tmp_path / "test.db")
    main.main(["--db", db_path, "sync"])

    capsys.readouterr()
    rc = main.main(["--db", db_path, "search", "llm"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "acme/llm-agent-toolkit" in out


def test_list_command_with_no_repos(tmp_path, capsys):
    db_path = str(tmp_path / "empty.db")
    rc = main.main(["--db", db_path, "list"])
    assert rc == 0
    assert "No repos found." in capsys.readouterr().out


def test_stats_command_reports_totals(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    _patch_fetch(monkeypatch, _fixture_entries())
    db_path = str(tmp_path / "test.db")
    main.main(["--db", db_path, "sync"])

    capsys.readouterr()
    rc = main.main(["--db", db_path, "stats"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Total repos: 5" in out


def test_render_command_writes_html_file(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    _patch_fetch(monkeypatch, _fixture_entries())
    db_path = str(tmp_path / "test.db")
    out_path = str(tmp_path / "dashboard.html")
    main.main(["--db", db_path, "sync"])

    rc = main.main(["--db", db_path, "render", "--out", out_path])
    assert rc == 0
    content = Path(out_path).read_text()
    assert "acme/llm-agent-toolkit" in content
    assert "</script><script>window.__xss=true;</script>" not in content
