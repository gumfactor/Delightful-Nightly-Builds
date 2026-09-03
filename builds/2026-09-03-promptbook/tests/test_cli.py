from pathlib import Path

import pytest

from src.cli import main
from tests.helpers import bash_episode, user_prompt, write_jsonl


def test_ingest_search_stats_render_end_to_end(tmp_path: Path, capsys):
    claude_dir = tmp_path / "claude"
    write_jsonl(claude_dir / "proj" / "s1.jsonl", [user_prompt("add a new endpoint", prompt_uuid="p1")])
    db_path = tmp_path / "db.sqlite"
    out_path = tmp_path / "dashboard.html"

    rc1 = main(["--db", str(db_path), "ingest", "--claude-dir", str(claude_dir)])
    assert rc1 == 0
    out = capsys.readouterr().out
    assert "new prompts stored: 1" in out

    rc2 = main(["--db", str(db_path), "search", "--query", "endpoint"])
    assert rc2 == 0
    search_out = capsys.readouterr().out
    assert "feature" in search_out

    rc3 = main(["--db", str(db_path), "stats"])
    assert rc3 == 0
    stats_out = capsys.readouterr().out
    assert "Total prompts: 1" in stats_out

    rc4 = main(["--db", str(db_path), "render", "--out", str(out_path)])
    assert rc4 == 0
    assert out_path.exists()
    assert "Promptbook" in out_path.read_text(encoding="utf-8")


def test_search_no_results_prints_message(tmp_path: Path, capsys):
    db_path = tmp_path / "db.sqlite"
    main(["--db", str(db_path), "search", "--query", "nothing will match"])
    out = capsys.readouterr().out
    assert "No matching prompts." in out


def test_invalid_min_score_exits_nonzero(tmp_path: Path):
    db_path = tmp_path / "db.sqlite"
    with pytest.raises(SystemExit) as exc_info:
        main(["--db", str(db_path), "search", "--min-score", "15"])
    assert exc_info.value.code != 0


def test_missing_command_exits_nonzero():
    with pytest.raises(SystemExit):
        main([])


def test_render_with_ai_uses_deterministic_fallback_with_no_key(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    claude_dir = tmp_path / "claude"
    # commit(+4) + test pass(+3) = score 7, clearing the --ai enrichment threshold.
    session = [user_prompt("fix the bug", prompt_uuid="p1")] + bash_episode(
        "python -m pytest tests/ -v", "9 passed in 0.2s"
    ) + bash_episode("git commit -m fix", "1 file changed")
    write_jsonl(claude_dir / "proj" / "s1.jsonl", session)
    db_path = tmp_path / "db.sqlite"
    out_path = tmp_path / "dashboard.html"

    main(["--db", str(db_path), "ingest", "--claude-dir", str(claude_dir)])
    rc = main(["--db", str(db_path), "render", "--out", str(out_path), "--ai"])
    assert rc == 0
    html = out_path.read_text(encoding="utf-8")
    assert "bug-fix" in html
    assert "score 7/10" in html
