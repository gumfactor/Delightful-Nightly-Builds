import io
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import db
from src.main import build_parser


@pytest.fixture
def conn(tmp_path):
    db_path = str(tmp_path / "test.db")
    connection = db.connect(db_path)
    yield connection
    connection.close()


def _run(conn, argv):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args, conn)


def test_add_via_cli(conn, capsys):
    _run(conn, ["add", "--title", "T", "--authors", "Doe", "--journal", "J",
                "--submitted", "2026-08-01"])
    out = capsys.readouterr().out
    assert "Added manuscript #1" in out


def test_update_rejects_invalid_status_gracefully(conn):
    _run(conn, ["add", "--title", "T", "--authors", "Doe", "--journal", "J",
                "--submitted", "2026-08-01"])
    with pytest.raises(SystemExit) as excinfo:
        _run(conn, ["update", "1", "--status", "not_a_real_status"])
    # argparse itself rejects unknown choices before reaching cmd_update
    assert excinfo.value.code != 0


def test_update_on_nonexistent_manuscript_fails_gracefully(conn, capsys):
    with pytest.raises(SystemExit) as excinfo:
        _run(conn, ["update", "999", "--status", "under_review"])
    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert "No manuscript with id 999" in err


def test_capture_on_nonexistent_manuscript_fails_gracefully(conn, capsys):
    with pytest.raises(SystemExit) as excinfo:
        _run(conn, ["capture", "999", "--text", "We are pleased to accept."])
    assert excinfo.value.code == 1


def test_capture_with_ambiguous_text_degrades_without_crashing(conn, capsys):
    _run(conn, ["add", "--title", "T", "--authors", "Doe", "--journal", "J",
                "--submitted", "2026-08-01"])
    _run(conn, ["capture", "1", "--text", "Thank you for your submission."])
    out = capsys.readouterr().out
    assert "Could not confidently determine" in out
    row = db.get_manuscript(conn, 1)
    assert row["status"] == "submitted"  # unchanged


def test_capture_with_empty_text_does_not_raise(conn, capsys):
    _run(conn, ["add", "--title", "T", "--authors", "Doe", "--journal", "J",
                "--submitted", "2026-08-01"])
    _run(conn, ["capture", "1", "--text", ""])
    out = capsys.readouterr().out
    assert "Could not confidently determine" in out


def test_capture_with_no_text_flag_reads_stdin(conn, capsys, monkeypatch):
    _run(conn, ["add", "--title", "T", "--authors", "Doe", "--journal", "J",
                "--submitted", "2026-08-01"])
    monkeypatch.setattr(sys, "stdin", io.StringIO("We are pleased to accept your manuscript."))
    _run(conn, ["capture", "1"])
    row = db.get_manuscript(conn, 1)
    assert row["status"] == "accepted"


def test_capture_accept_email_updates_status(conn, capsys):
    _run(conn, ["add", "--title", "T", "--authors", "Doe", "--journal", "J",
                "--submitted", "2026-08-01"])
    _run(conn, ["capture", "1", "--text", "We are pleased to accept your manuscript."])
    row = db.get_manuscript(conn, 1)
    assert row["status"] == "accepted"


def test_sync_updates_manuscript_on_mocked_crossref_match(conn, capsys):
    _run(conn, ["add", "--title", "A Study of Things", "--authors", "Jane Doe",
                "--journal", "J", "--submitted", "2026-01-01"])
    match = {
        "doi": "10.1000/found",
        "container_title": "Journal of Examples",
        "published_date": "2026-08-01",
        "similarity": 0.95,
    }
    with patch("src.main.crossref.find_publication_match", return_value=match):
        _run(conn, ["sync"])
    row = db.get_manuscript(conn, 1)
    assert row["status"] == "published"
    assert row["doi"] == "10.1000/found"


def test_sync_skips_manuscripts_already_in_terminal_state(conn):
    _run(conn, ["add", "--title", "T", "--authors", "Doe", "--journal", "J",
                "--submitted", "2026-08-01"])
    _run(conn, ["update", "1", "--status", "rejected"])
    with patch("src.main.crossref.find_publication_match") as mock_find:
        _run(conn, ["sync"])
    mock_find.assert_not_called()


def test_report_writes_html_file(conn, tmp_path, capsys):
    _run(conn, ["add", "--title", "T", "--authors", "Doe", "--journal", "J",
                "--submitted", "2026-08-01"])
    out_file = tmp_path / "report.html"
    _run(conn, ["report", "--out", str(out_file)])
    assert out_file.exists()
    assert "<html" in out_file.read_text()
