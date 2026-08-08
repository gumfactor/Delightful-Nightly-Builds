import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import main

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "cli_test.db")


def test_submit_end_to_end_writes_version_and_prints_summary(db_path, capsys):
    sample = REPO_ROOT / "sample_proposal.txt"
    main.main(["--db", db_path, "submit", str(sample), "--project", "R01 Test"])
    out = capsys.readouterr().out
    assert "R01 Test" in out
    assert "version 1" in out


def test_submit_on_missing_file_exits_nonzero(db_path):
    with pytest.raises(SystemExit) as exc_info:
        main.main(["--db", db_path, "submit", "/no/such/file.txt", "--project", "X"])
    assert exc_info.value.code != 0


def test_submit_on_empty_file_exits_nonzero(db_path, tmp_path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("   \n\n  ")
    with pytest.raises(SystemExit):
        main.main(["--db", db_path, "submit", str(empty_file), "--project", "Empty"])


def test_list_reports_no_projects_initially(db_path, capsys):
    main.main(["--db", db_path, "list"])
    out = capsys.readouterr().out
    assert "No projects yet" in out


def test_list_reports_project_after_submit(db_path, capsys):
    sample = REPO_ROOT / "sample_proposal.txt"
    main.main(["--db", db_path, "submit", str(sample), "--project", "R01 Test"])
    capsys.readouterr()
    main.main(["--db", db_path, "list"])
    out = capsys.readouterr().out
    assert "R01 Test" in out


def test_history_on_unknown_project_exits_nonzero(db_path):
    with pytest.raises(SystemExit):
        main.main(["--db", db_path, "history", "Nonexistent"])


def test_history_shows_multiple_versions(db_path, capsys):
    sample = REPO_ROOT / "sample_proposal.txt"
    main.main(["--db", db_path, "submit", str(sample), "--project", "R01 Test"])
    main.main(["--db", db_path, "submit", str(sample), "--project", "R01 Test"])
    capsys.readouterr()
    main.main(["--db", db_path, "history", "R01 Test"])
    out = capsys.readouterr().out
    assert "v1" in out
    assert "v2" in out


def test_render_writes_html_file(db_path, tmp_path):
    sample = REPO_ROOT / "sample_proposal.txt"
    main.main(["--db", db_path, "submit", str(sample), "--project", "R01 Test"])
    out_path = tmp_path / "report.html"
    main.main(["--db", db_path, "render", "R01 Test", "--out", str(out_path)])
    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    assert "R01 Test" in content
    assert "<!doctype html>" in content.lower()


def test_render_on_unknown_project_exits_nonzero(db_path):
    with pytest.raises(SystemExit):
        main.main(["--db", db_path, "render", "Nonexistent"])
