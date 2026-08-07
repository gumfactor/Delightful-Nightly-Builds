"""Tests for the Waymark CLI entrypoint."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.cli import build_parser, main


def test_index_command_indexes_a_real_repo(tmp_git_repo: Path, db_path: Path, capsys):
    exit_code = main(["--db", str(db_path), "index", str(tmp_git_repo), "--label", "myrepo"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Indexed 3 new commit" in captured.out


def test_index_command_is_incremental_on_rerun(tmp_git_repo: Path, db_path: Path, capsys):
    main(["--db", str(db_path), "index", str(tmp_git_repo), "--label", "myrepo"])
    capsys.readouterr()
    exit_code = main(["--db", str(db_path), "index", str(tmp_git_repo), "--label", "myrepo"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Indexed 0 new commit" in captured.out


def test_index_command_errors_on_non_git_path(tmp_path: Path, db_path: Path, capsys):
    not_a_repo = tmp_path / "not_a_repo"
    not_a_repo.mkdir()
    exit_code = main(["--db", str(db_path), "index", str(not_a_repo), "--label", "bad"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "error" in captured.err.lower()


def test_search_command_returns_results_after_index(tmp_git_repo: Path, db_path: Path, capsys):
    main(["--db", str(db_path), "index", str(tmp_git_repo), "--label", "myrepo"])
    capsys.readouterr()
    exit_code = main(["--db", str(db_path), "search"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "myrepo" in captured.out


def test_search_command_with_no_results_reports_none(db_path: Path, capsys):
    exit_code = main(["--db", str(db_path), "search", "nonexistent query text"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "No matching commits" in captured.out


def test_render_command_writes_html_file(tmp_git_repo: Path, db_path: Path, tmp_path: Path, capsys):
    main(["--db", str(db_path), "index", str(tmp_git_repo), "--label", "myrepo"])
    capsys.readouterr()
    output_path = tmp_path / "out.html"
    exit_code = main(["--db", str(db_path), "render", "--output", str(output_path)])
    assert exit_code == 0
    assert output_path.exists()


def test_list_repos_command_after_indexing(tmp_git_repo: Path, db_path: Path, capsys):
    main(["--db", str(db_path), "index", str(tmp_git_repo), "--label", "myrepo"])
    capsys.readouterr()
    exit_code = main(["--db", str(db_path), "list-repos"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "myrepo" in captured.out


def test_list_repos_command_with_no_repos(db_path: Path, capsys):
    exit_code = main(["--db", str(db_path), "list-repos"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "No repos indexed" in captured.out


def test_enrich_command_without_api_key_makes_zero_network_calls(db_path: Path, monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    exit_code = main(["--db", str(db_path), "enrich"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "ANTHROPIC_API_KEY is not set" in captured.out


def test_parser_requires_a_subcommand():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_parser_rejects_unknown_subcommand():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["not-a-real-command"])
