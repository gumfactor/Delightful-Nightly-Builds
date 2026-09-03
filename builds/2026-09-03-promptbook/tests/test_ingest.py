from pathlib import Path

from src.ingest import ingest_directory
from src.storage import connect, search_prompts
from tests.helpers import bash_episode, edit_episode, user_prompt, write_jsonl


def test_ingest_directory_extracts_and_scores_prompts(tmp_path: Path):
    claude_dir = tmp_path / "claude"
    session_file = claude_dir / "proj" / "session1.jsonl"
    session = [user_prompt("fix the bug", prompt_uuid="p1")] + bash_episode(
        "git commit -m fix", "1 file changed"
    )
    write_jsonl(session_file, session)

    conn = connect(tmp_path / "db.sqlite")
    result = ingest_directory(conn, claude_dir)

    assert result.files_scanned == 1
    assert result.prompts_seen == 1
    assert result.prompts_inserted == 1

    rows = search_prompts(conn)
    assert len(rows) == 1
    assert rows[0]["task_type"] == "bug-fix"
    assert rows[0]["score"] == 4  # commit-only bonus
    assert rows[0]["git_commit"] == 1


def test_ingest_is_idempotent_on_unchanged_file(tmp_path: Path):
    claude_dir = tmp_path / "claude"
    session_file = claude_dir / "proj" / "session1.jsonl"
    write_jsonl(session_file, [user_prompt("add a feature", prompt_uuid="p1")])

    conn = connect(tmp_path / "db.sqlite")
    first = ingest_directory(conn, claude_dir)
    second = ingest_directory(conn, claude_dir)

    assert first.prompts_inserted == 1
    assert second.files_with_new_lines == 0
    assert second.prompts_inserted == 0
    assert len(search_prompts(conn)) == 1


def test_ingest_picks_up_appended_lines_incrementally(tmp_path: Path):
    claude_dir = tmp_path / "claude"
    session_file = claude_dir / "proj" / "session1.jsonl"
    write_jsonl(session_file, [user_prompt("first prompt", prompt_uuid="p1")])

    conn = connect(tmp_path / "db.sqlite")
    ingest_directory(conn, claude_dir)
    assert len(search_prompts(conn)) == 1

    # Simulate the session continuing: append a second prompt to the same file.
    existing = session_file.read_text(encoding="utf-8")
    with session_file.open("a", encoding="utf-8") as fh:
        import json

        fh.write(json.dumps(user_prompt("second prompt", prompt_uuid="p2")) + "\n")

    result = ingest_directory(conn, claude_dir)
    assert result.files_with_new_lines == 1
    assert result.prompts_inserted == 1
    rows = search_prompts(conn)
    assert len(rows) == 2
    assert {r["prompt_uuid"] for r in rows} == {"p1", "p2"}


def test_ingest_across_multiple_projects(tmp_path: Path):
    claude_dir = tmp_path / "claude"
    write_jsonl(
        claude_dir / "proj-a" / "s1.jsonl",
        [user_prompt("prompt in project a", prompt_uuid="pa", cwd="/home/user/a")],
    )
    write_jsonl(
        claude_dir / "proj-b" / "s2.jsonl",
        [user_prompt("prompt in project b", prompt_uuid="pb", cwd="/home/user/b")],
    )
    conn = connect(tmp_path / "db.sqlite")
    result = ingest_directory(conn, claude_dir)
    assert result.files_scanned == 2
    assert result.prompts_inserted == 2
    rows = search_prompts(conn)
    projects = {r["project"] for r in rows}
    assert projects == {"/home/user/a", "/home/user/b"}


def test_ingest_scores_edit_only_episode(tmp_path: Path):
    claude_dir = tmp_path / "claude"
    session_file = claude_dir / "proj" / "session1.jsonl"
    session = [user_prompt("clean up the module", prompt_uuid="p1")] + edit_episode("/x/f.py")
    write_jsonl(session_file, session)

    conn = connect(tmp_path / "db.sqlite")
    ingest_directory(conn, claude_dir)
    rows = search_prompts(conn)
    assert rows[0]["task_type"] == "refactor"
    assert rows[0]["score"] == 2
