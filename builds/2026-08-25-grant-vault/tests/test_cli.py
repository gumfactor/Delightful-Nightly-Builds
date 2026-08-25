import os

from src.cli import main


def _write(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return str(path)


def test_ingest_command_runs(tmp_path, capsys):
    grant_path = _write(tmp_path, "grant.txt", "Significance\nBroadly applicable framework text here.")
    db_path = str(tmp_path / "vault.db")
    exit_code = main(["--db", db_path, "ingest", grant_path])
    assert exit_code == 0
    assert os.path.exists(db_path)
    out = capsys.readouterr().out
    assert "Ingested 1 document" in out


def test_search_command_with_no_results_prints_message(tmp_path, capsys):
    db_path = str(tmp_path / "vault.db")
    exit_code = main(["--db", db_path, "search", "nothing will match this"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "No matching chunks found." in out


def test_search_command_prints_results(tmp_path, capsys):
    grant_path = _write(tmp_path, "grant.txt", "Significance\nStress reactivity and empathic accuracy.")
    db_path = str(tmp_path / "vault.db")
    main(["--db", db_path, "ingest", grant_path])
    capsys.readouterr()

    exit_code = main(["--db", db_path, "search", "empathic"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Significance" in out


def test_stats_command_runs(tmp_path, capsys):
    grant_path = _write(tmp_path, "grant.txt", "Significance\nSome reusable text about the field.")
    db_path = str(tmp_path / "vault.db")
    main(["--db", db_path, "ingest", grant_path])
    capsys.readouterr()

    exit_code = main(["--db", db_path, "stats"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Documents: 1" in out
    assert "Chunks: 1" in out


def test_render_command_creates_file(tmp_path, capsys):
    grant_path = _write(tmp_path, "grant.txt", "Significance\nSome reusable text about the field.")
    db_path = str(tmp_path / "vault.db")
    main(["--db", db_path, "ingest", grant_path])
    capsys.readouterr()

    output_path = str(tmp_path / "out.html")
    exit_code = main(["--db", db_path, "render", "--output", output_path])
    assert exit_code == 0
    assert os.path.exists(output_path)


def test_missing_ingest_path_returns_exit_code_1(tmp_path, capsys):
    db_path = str(tmp_path / "vault.db")
    exit_code = main(["--db", db_path, "ingest", "/definitely/not/real.txt"])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "Error" in err


def test_custom_db_path_used(tmp_path):
    db_path = str(tmp_path / "custom_name.db")
    assert not os.path.exists(db_path)
    main(["--db", db_path, "stats"])
    assert os.path.exists(db_path)


def test_ai_flag_without_api_key_warns_and_continues(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    grant_path = _write(tmp_path, "grant.txt", "Significance\nSome reusable text about the field.")
    db_path = str(tmp_path / "vault.db")
    exit_code = main(["--db", db_path, "ingest", grant_path, "--ai"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Warning" in out
    chunk_ai_summary_present = "ai_summary" in out
    assert not chunk_ai_summary_present
