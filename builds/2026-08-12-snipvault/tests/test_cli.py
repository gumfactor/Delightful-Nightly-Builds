import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.cli import build_parser, main


def run(argv, db_path):
    main(["--db", str(db_path), *argv])


def test_add_from_code_flag(tmp_path, capsys):
    db = tmp_path / "test.db"
    run(["add", "--title", "Foo", "--code", "x = 1", "--lang", "python"], db)
    out = capsys.readouterr().out
    assert "Saved snippet #1" in out


def test_add_from_file(tmp_path, capsys):
    db = tmp_path / "test.db"
    source_file = tmp_path / "snippet.py"
    source_file.write_text("def foo():\n    return 1\n")
    run(["add", "--title", "Foo func", "--file", str(source_file)], db)
    out = capsys.readouterr().out
    assert "[python]" in out


def test_add_from_stdin(tmp_path, capsys, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setattr("sys.stdin.read", lambda: "echo hello\n")
    run(["add", "--title", "Shell echo", "--lang", "bash"], db)
    out = capsys.readouterr().out
    assert "Saved snippet #1" in out


def test_add_empty_stdin_exits_with_error(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setattr("sys.stdin.read", lambda: "   ")
    with pytest.raises(SystemExit) as exc_info:
        run(["add", "--title", "Nothing"], db)
    assert exc_info.value.code == 1


def test_add_missing_file_exits_with_error(tmp_path):
    db = tmp_path / "test.db"
    with pytest.raises(SystemExit) as exc_info:
        run(["add", "--title", "Missing", "--file", str(tmp_path / "nope.py")], db)
    assert exc_info.value.code == 1


def test_get_missing_id_exits_cleanly_not_a_traceback(tmp_path):
    db = tmp_path / "test.db"
    with pytest.raises(SystemExit) as exc_info:
        run(["get", "999"], db)
    assert exc_info.value.code == 1


def test_remove_missing_id_exits_cleanly(tmp_path):
    db = tmp_path / "test.db"
    with pytest.raises(SystemExit) as exc_info:
        run(["remove", "999"], db)
    assert exc_info.value.code == 1


def test_list_filters_by_lang_flag(tmp_path, capsys):
    db = tmp_path / "test.db"
    run(["add", "--title", "Py one", "--code", "x = 1", "--lang", "python"], db)
    capsys.readouterr()
    run(["add", "--title", "JS one", "--code", "let x = 1;", "--lang", "javascript"], db)
    capsys.readouterr()
    run(["list", "--lang", "python"], db)
    out = capsys.readouterr().out
    assert "Py one" in out
    assert "JS one" not in out


def test_search_command_prints_results(tmp_path, capsys):
    db = tmp_path / "test.db"
    run(["add", "--title", "Retry wrapper", "--code", "def f(): pass", "--lang", "python"], db)
    capsys.readouterr()
    run(["search", "retry"], db)
    out = capsys.readouterr().out
    assert "Retry wrapper" in out


def test_render_command_writes_file(tmp_path, capsys):
    db = tmp_path / "test.db"
    run(["add", "--title", "Foo", "--code", "x = 1", "--lang", "python"], db)
    capsys.readouterr()
    output_path = tmp_path / "out.html"
    run(["render", "--output", str(output_path)], db)
    assert output_path.exists()
    assert "<!DOCTYPE html>" in output_path.read_text()


def test_render_command_orders_by_usage_then_recency(tmp_path, capsys):
    db = tmp_path / "test.db"
    run(["add", "--title", "Rarely used", "--code", "x = 1", "--lang", "python"], db)
    capsys.readouterr()
    run(["add", "--title", "Frequently used", "--code", "y = 2", "--lang", "python"], db)
    capsys.readouterr()
    # Bump "Frequently used"'s usage_count above "Rarely used"'s (id 2 was added second, id 1 first).
    run(["get", "2"], db)
    run(["get", "2"], db)
    capsys.readouterr()

    output_path = tmp_path / "out.html"
    run(["render", "--output", str(output_path)], db)
    html = output_path.read_text()

    assert html.index("Frequently used") < html.index("Rarely used")


def test_parser_requires_a_subcommand():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])
