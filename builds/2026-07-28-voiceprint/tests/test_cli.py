import json

from src import cli


def test_cmd_analyze_end_to_end_terminal_report(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    draft = tmp_path / "draft.md"
    draft.write_text("We should delve into this seamless synergy today.")
    db_path = tmp_path / "history.db"

    exit_code = cli.main(["analyze", str(draft), "--db", str(db_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Human Voice Score" in captured.out
    assert "delve into" in captured.out


def test_cmd_analyze_with_ai_flag_uses_fallback_with_no_key(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    draft = tmp_path / "draft.md"
    draft.write_text("Clean simple text here about the project.")
    db_path = tmp_path / "history.db"

    exit_code = cli.main(["analyze", str(draft), "--ai", "--db", str(db_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Second opinion (fallback)" in captured.out


def test_cmd_analyze_json_output_is_valid_json(tmp_path):
    draft = tmp_path / "draft.md"
    draft.write_text("Some text for the JSON output test.")
    db_path = tmp_path / "history.db"

    import io
    import contextlib

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        exit_code = cli.main(["analyze", str(draft), "--json", "--db", str(db_path)])

    assert exit_code == 0
    payload = json.loads(buffer.getvalue())
    assert "score" in payload
    assert payload["file_path"] == str(draft)


def test_cmd_analyze_writes_html_report(tmp_path):
    draft = tmp_path / "draft.md"
    draft.write_text("Some html report test text about the lab.")
    db_path = tmp_path / "history.db"
    html_path = tmp_path / "report.html"

    exit_code = cli.main(
        ["analyze", str(draft), "--html", str(html_path), "--db", str(db_path)]
    )

    assert exit_code == 0
    assert html_path.exists()
    assert "<!doctype html>" in html_path.read_text()


def test_cmd_analyze_missing_file_returns_error_exit_code(tmp_path, capsys):
    exit_code = cli.main(
        ["analyze", str(tmp_path / "missing.md"), "--db", str(tmp_path / "history.db")]
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "not found" in captured.err


def test_cmd_history_records_two_runs_with_delta(tmp_path, capsys):
    draft = tmp_path / "draft.md"
    db_path = tmp_path / "history.db"

    draft.write_text("First revision has delve into issues today.")
    cli.main(["analyze", str(draft), "--db", str(db_path)])
    draft.write_text("Second revision is much cleaner text now.")
    cli.main(["analyze", str(draft), "--db", str(db_path)])
    capsys.readouterr()

    exit_code = cli.main(["history", str(draft), "--db", str(db_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "History for" in captured.out
    assert "2 run" in captured.out


def test_cmd_history_no_runs_reports_none(tmp_path, capsys):
    exit_code = cli.main(
        ["history", str(tmp_path / "never.md"), "--db", str(tmp_path / "history.db")]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "No history recorded" in captured.out


def test_cmd_batch_processes_only_md_and_txt_files(tmp_path, capsys):
    (tmp_path / "a.md").write_text("First file text about lab research today.")
    (tmp_path / "b.txt").write_text("Second file text about lab research today.")
    (tmp_path / "c.png").write_bytes(b"not text")
    db_path = tmp_path / "history.db"

    exit_code = cli.main(["batch", str(tmp_path), "--db", str(db_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "a.md" in captured.out
    assert "b.txt" in captured.out
    assert "c.png" not in captured.out


def test_cmd_batch_missing_directory_returns_error(tmp_path, capsys):
    exit_code = cli.main(
        ["batch", str(tmp_path / "nope"), "--db", str(tmp_path / "h.db")]
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "not found" in captured.err


def test_cmd_batch_writes_one_html_report_per_file(tmp_path):
    (tmp_path / "a.md").write_text("Some content for the html dir test today.")
    db_path = tmp_path / "history.db"
    html_dir = tmp_path / "reports"

    exit_code = cli.main(
        ["batch", str(tmp_path), "--html-dir", str(html_dir), "--db", str(db_path)]
    )

    assert exit_code == 0
    assert (html_dir / "a.html").exists()


def test_cmd_batch_empty_directory_reports_no_files(tmp_path, capsys):
    db_path = tmp_path / "history.db"
    exit_code = cli.main(["batch", str(tmp_path), "--db", str(db_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "No .md or .txt files found" in captured.err
