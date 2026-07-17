import json
import os

import pytest

from src import ai_client
from src.cli import main


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "cli_test.db")


def test_add_command_persists_row(db_path, capsys):
    exit_code = main([
        "--db", db_path,
        "add",
        "--title", "IRB renewal",
        "--category", "IRB/Ethics",
        "--due-date", "2027-03-15",
        "--recurrence", "annual",
    ])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Added deadline #1" in out
    assert os.path.isfile(db_path)


def test_add_command_rejects_invalid_category(db_path):
    with pytest.raises(SystemExit) as exc_info:
        main([
            "--db", db_path,
            "add",
            "--title", "X",
            "--category", "NotACategory",
            "--due-date", "2027-03-15",
        ])
    assert exc_info.value.code != 0


def test_add_command_missing_required_arg_exits_nonzero(db_path):
    with pytest.raises(SystemExit) as exc_info:
        main(["--db", db_path, "add", "--title", "X"])
    assert exc_info.value.code != 0


def test_capture_command_fallback_no_api_key(db_path, capsys, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    exit_code = main([
        "--db", db_path,
        "capture",
        "--text", "IRB renewal due 2027-03-15 for the stress study.",
    ])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "fallback extraction" in out


def test_capture_command_uses_ai_when_key_present(db_path, capsys, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    canned_reply = (
        '{"title": "Grant Report", "category": "Grant", "due_date": "2027-05-01", '
        '"recurrence": "none", "recurrence_months": null, "notes": null}'
    )
    monkeypatch.setattr(ai_client, "call_claude", lambda prompt, api_key, **kw: canned_reply)
    exit_code = main([
        "--db", db_path,
        "capture",
        "--text", "Your grant progress report is due.",
    ])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "ai extraction" in out


def test_capture_command_no_date_found_returns_error_exit_code(db_path, capsys, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    exit_code = main([
        "--db", db_path,
        "capture",
        "--text", "This message has no date in it whatsoever.",
    ])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "error" in err.lower()


def test_capture_command_empty_text_returns_error(db_path, capsys):
    exit_code = main(["--db", db_path, "capture", "--text", "   "])
    assert exit_code == 1


def test_complete_command_creates_next_occurrence_for_recurring(db_path, capsys):
    main([
        "--db", db_path, "add", "--title", "Annual IRB", "--category", "IRB/Ethics",
        "--due-date", "2027-03-15", "--recurrence", "annual",
    ])
    capsys.readouterr()
    exit_code = main(["--db", db_path, "complete", "--id", "1", "--on", "2027-03-10"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "next occurrence #2 due 2028-03-15" in out


def test_complete_command_unknown_id_returns_error(db_path):
    exit_code = main(["--db", db_path, "complete", "--id", "999"])
    assert exit_code == 1


def test_list_json_output_valid_json(db_path, capsys):
    main([
        "--db", db_path, "add", "--title", "X", "--category", "Other", "--due-date", "2027-01-01",
    ])
    capsys.readouterr()
    exit_code = main(["--db", db_path, "list", "--json"])
    assert exit_code == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert len(parsed) == 1
    assert parsed[0]["title"] == "X"


def test_list_human_output_no_deadlines(db_path, capsys):
    exit_code = main(["--db", db_path, "list"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "No deadlines found." in out


def test_list_excludes_completed_by_default(db_path, capsys):
    main(["--db", db_path, "add", "--title", "X", "--category", "Other", "--due-date", "2027-01-01"])
    capsys.readouterr()
    main(["--db", db_path, "complete", "--id", "1"])
    capsys.readouterr()
    main(["--db", db_path, "list"])
    out = capsys.readouterr().out
    assert "No deadlines found." in out


def test_render_command_writes_file(db_path, tmp_path):
    main(["--db", db_path, "add", "--title", "X", "--category", "Other", "--due-date", "2027-01-01"])
    output_path = str(tmp_path / "out.html")
    exit_code = main(["--db", db_path, "render", "--output", output_path])
    assert exit_code == 0
    assert os.path.isfile(output_path)
    with open(output_path, "r", encoding="utf-8") as handle:
        content = handle.read()
    assert "Deadline Guardian" in content
