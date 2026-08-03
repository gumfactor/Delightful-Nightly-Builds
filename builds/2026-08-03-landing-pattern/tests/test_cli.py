"""Tests for the CLI. `sync` always mocks `github_client.fetch_repo_prs_full` —
no real GitHub call happens in this suite.
"""

from __future__ import annotations

import json

from landing_pattern import cli, github_client


def fake_prs():
    return [
        {
            "number": 1,
            "title": "Add feature",
            "url": "https://example/1",
            "created_at": "2026-08-01T00:00:00Z",
            "draft": False,
            "mergeable_state": "clean",
            "ci_state": "success",
            "review_state": "none",
            "files": ["a.py"],
        }
    ]


def test_sync_writes_snapshot_with_mocked_client(monkeypatch, tmp_path, capsys):
    db_path = str(tmp_path / "db.sqlite")
    monkeypatch.setattr(github_client, "fetch_repo_prs_full", lambda repo, token: fake_prs())

    exit_code = cli.main(["--db", db_path, "sync", "--repo", "owner/repo", "--token", "tok"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Synced 1 open PR" in captured.out


def test_sync_missing_token_returns_error(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    db_path = str(tmp_path / "db.sqlite")

    exit_code = cli.main(["--db", db_path, "sync", "--repo", "owner/repo"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "token" in captured.err.lower()


def test_sync_api_error_returns_clean_error_not_traceback(monkeypatch, tmp_path, capsys):
    db_path = str(tmp_path / "db.sqlite")

    def raise_error(repo, token):
        raise github_client.GitHubAPIError("GitHub API error 404")

    monkeypatch.setattr(github_client, "fetch_repo_prs_full", raise_error)
    exit_code = cli.main(["--db", db_path, "sync", "--repo", "owner/repo", "--token", "tok"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "404" in captured.err


def test_report_with_no_prior_snapshot_exits_cleanly(tmp_path, capsys):
    db_path = str(tmp_path / "db.sqlite")
    exit_code = cli.main(["--db", db_path, "report", "--repo", "owner/repo"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "no snapshot found" in captured.err.lower()


def test_report_after_sync_prints_text(monkeypatch, tmp_path, capsys):
    db_path = str(tmp_path / "db.sqlite")
    monkeypatch.setattr(github_client, "fetch_repo_prs_full", lambda repo, token: fake_prs())
    cli.main(["--db", db_path, "sync", "--repo", "owner/repo", "--token", "tok"])
    capsys.readouterr()

    exit_code = cli.main(["--db", db_path, "report", "--repo", "owner/repo"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "#1" in captured.out
    assert "Add feature" in captured.out


def test_report_json_format_writes_valid_file(monkeypatch, tmp_path):
    db_path = str(tmp_path / "db.sqlite")
    out_path = str(tmp_path / "report.json")
    monkeypatch.setattr(github_client, "fetch_repo_prs_full", lambda repo, token: fake_prs())
    cli.main(["--db", db_path, "sync", "--repo", "owner/repo", "--token", "tok"])

    exit_code = cli.main(
        ["--db", db_path, "report", "--repo", "owner/repo", "--format", "json", "--output", out_path]
    )
    assert exit_code == 0
    with open(out_path) as handle:
        parsed = json.load(handle)
    assert parsed["repo"] == "owner/repo"


def test_history_command_no_data_reports_none(tmp_path, capsys):
    db_path = str(tmp_path / "db.sqlite")
    exit_code = cli.main(["--db", db_path, "history", "--repo", "owner/repo", "--pr", "1"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "no snapshot history" in captured.out.lower()
