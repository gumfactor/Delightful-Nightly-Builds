"""CLI integration tests — network calls mocked, filesystem confined to tmp_path."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import main  # noqa: E402
import openalex  # noqa: E402


def test_missing_author_id_produces_clean_usage_error(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main.main(["sync"])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "required" in captured.err or "--author-id" in captured.err


def test_search_author_prints_candidates(tmp_path, capsys):
    fake_candidates = [
        {
            "author_id": "A1",
            "display_name": "Jane Doe",
            "institution": "Example University",
            "works_count": 10,
            "cited_by_count": 100,
        }
    ]
    with patch.object(openalex, "search_authors", return_value=fake_candidates):
        exit_code = main.main(["--db-path", str(tmp_path / "t.db"), "search-author", "Jane Doe"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Jane Doe" in captured.out
    assert "A1" in captured.out


def test_search_author_handles_no_results(tmp_path, capsys):
    with patch.object(openalex, "search_authors", return_value=[]):
        exit_code = main.main(["--db-path", str(tmp_path / "t.db"), "search-author", "Nobody Findable"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "No OpenAlex authors found" in captured.out


def test_history_before_any_sync_reports_no_history(tmp_path, capsys):
    db_path = tmp_path / "t.db"
    exit_code = main.main(["--db-path", str(db_path), "history", "--author-id", "A1"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "No sync history" in captured.out


def test_sync_then_render_end_to_end(tmp_path, capsys):
    db_path = tmp_path / "t.db"
    fake_author = {
        "author_id": "A1",
        "display_name": "Jane Doe",
        "works_count": 1,
        "cited_by_count": 10,
        "h_index": 2,
        "i10_index": 1,
    }
    fake_works = [
        {
            "work_id": "W1",
            "title": "A Paper",
            "publication_year": 2020,
            "doi": "10.1/x",
            "host_venue": "Journal A",
            "cited_by_count": 10,
            "concepts": ["Neuroscience"],
            "abstract": "Findings.",
        }
    ]

    with patch.object(openalex, "get_author", return_value=fake_author), patch.object(
        openalex, "iter_author_works", return_value=iter(fake_works)
    ):
        sync_exit = main.main(
            ["--db-path", str(db_path), "sync", "--author-id", "A1", "--sync-date", "2026-08-05"]
        )
    assert sync_exit == 0
    captured = capsys.readouterr()
    assert "Synced Jane Doe" in captured.out

    out_path = tmp_path / "dashboard.html"
    render_exit = main.main(
        ["--db-path", str(db_path), "render", "--author-id", "A1", "--out", str(out_path)]
    )
    assert render_exit == 0
    assert out_path.exists()
    html = out_path.read_text(encoding="utf-8")
    assert "A Paper" in html


def test_render_without_prior_sync_errors_clearly(tmp_path, capsys):
    db_path = tmp_path / "t.db"
    exit_code = main.main(
        ["--db-path", str(db_path), "render", "--author-id", "UNKNOWN", "--out", str(tmp_path / "d.html")]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "No data for author" in captured.err


def test_sync_reports_openalex_error(tmp_path, capsys):
    db_path = tmp_path / "t.db"
    with patch.object(openalex, "get_author", side_effect=openalex.OpenAlexError("boom")):
        exit_code = main.main(["--db-path", str(db_path), "sync", "--author-id", "A1"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "boom" in captured.err
