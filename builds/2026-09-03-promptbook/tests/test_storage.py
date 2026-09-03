from pathlib import Path

from src.storage import (
    StoredPrompt,
    connect,
    get_last_line_count,
    get_stats,
    search_prompts,
    set_last_line_count,
    upsert_prompt,
)


def _sp(uuid: str, **overrides) -> StoredPrompt:
    base = dict(
        prompt_uuid=uuid,
        session_id="s1",
        project="/home/user/proj",
        git_branch="main",
        entrypoint="cli",
        timestamp="2026-09-01T00:00:00Z",
        prompt_text="fix the bug",
        task_type="bug-fix",
        score=5,
        tools_used=["Bash"],
        files_edited=1,
        test_run=False,
        test_passed=None,
        git_commit=False,
        had_error=False,
    )
    base.update(overrides)
    return StoredPrompt(**base)


def test_upsert_inserts_new_prompt(tmp_path: Path):
    conn = connect(tmp_path / "db.sqlite")
    inserted = upsert_prompt(conn, _sp("p1"))
    conn.commit()
    assert inserted is True
    rows = search_prompts(conn)
    assert len(rows) == 1


def test_upsert_ignores_duplicate_uuid(tmp_path: Path):
    conn = connect(tmp_path / "db.sqlite")
    upsert_prompt(conn, _sp("p1", prompt_text="first version"))
    conn.commit()
    inserted_again = upsert_prompt(conn, _sp("p1", prompt_text="second version"))
    conn.commit()
    assert inserted_again is False
    rows = search_prompts(conn)
    assert len(rows) == 1
    assert rows[0]["prompt_text"] == "first version"


def test_line_count_tracking_round_trips(tmp_path: Path):
    conn = connect(tmp_path / "db.sqlite")
    assert get_last_line_count(conn, "/some/file.jsonl") == 0
    set_last_line_count(conn, "/some/file.jsonl", 42, "2026-09-01T00:00:00Z")
    conn.commit()
    assert get_last_line_count(conn, "/some/file.jsonl") == 42


def test_line_count_tracking_updates_on_conflict(tmp_path: Path):
    conn = connect(tmp_path / "db.sqlite")
    set_last_line_count(conn, "/some/file.jsonl", 10, "2026-09-01T00:00:00Z")
    set_last_line_count(conn, "/some/file.jsonl", 20, "2026-09-02T00:00:00Z")
    conn.commit()
    assert get_last_line_count(conn, "/some/file.jsonl") == 20


def test_search_filters_by_task_type(tmp_path: Path):
    conn = connect(tmp_path / "db.sqlite")
    upsert_prompt(conn, _sp("p1", task_type="bug-fix"))
    upsert_prompt(conn, _sp("p2", task_type="feature"))
    conn.commit()
    rows = search_prompts(conn, task_type="feature")
    assert len(rows) == 1
    assert rows[0]["prompt_uuid"] == "p2"


def test_search_filters_by_min_score(tmp_path: Path):
    conn = connect(tmp_path / "db.sqlite")
    upsert_prompt(conn, _sp("p1", score=2))
    upsert_prompt(conn, _sp("p2", score=8))
    conn.commit()
    rows = search_prompts(conn, min_score=5)
    assert len(rows) == 1
    assert rows[0]["prompt_uuid"] == "p2"


def test_search_filters_by_query_text(tmp_path: Path):
    conn = connect(tmp_path / "db.sqlite")
    upsert_prompt(conn, _sp("p1", prompt_text="please refactor the parser"))
    upsert_prompt(conn, _sp("p2", prompt_text="add tests for the API"))
    conn.commit()
    rows = search_prompts(conn, query="parser")
    assert len(rows) == 1
    assert rows[0]["prompt_uuid"] == "p1"


def test_search_orders_by_score_desc(tmp_path: Path):
    conn = connect(tmp_path / "db.sqlite")
    upsert_prompt(conn, _sp("low", score=1))
    upsert_prompt(conn, _sp("high", score=9))
    upsert_prompt(conn, _sp("mid", score=5))
    conn.commit()
    rows = search_prompts(conn)
    assert [r["prompt_uuid"] for r in rows] == ["high", "mid", "low"]


def test_stats_aggregate_counts(tmp_path: Path):
    conn = connect(tmp_path / "db.sqlite")
    upsert_prompt(conn, _sp("p1", task_type="bug-fix", project="/a", score=4))
    upsert_prompt(conn, _sp("p2", task_type="bug-fix", project="/a", score=6))
    upsert_prompt(conn, _sp("p3", task_type="feature", project="/b", score=8))
    conn.commit()
    stats = get_stats(conn)
    assert stats["total"] == 3
    assert stats["by_task_type"]["bug-fix"] == 2
    assert stats["by_task_type"]["feature"] == 1
    assert stats["by_project"]["/a"] == 2
    assert stats["avg_score"] == 6.0


def test_stats_on_empty_db(tmp_path: Path):
    conn = connect(tmp_path / "db.sqlite")
    stats = get_stats(conn)
    assert stats["total"] == 0
    assert stats["avg_score"] == 0.0
