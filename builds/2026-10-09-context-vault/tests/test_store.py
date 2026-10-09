import os

from conftest import write_jsonl

from ctxvault import store


def test_demo_indexes_all_sessions(conn):
    assert conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 4 - 1  # 2 + 1 sessions
    assert {p["project"] for p in store.list_projects(conn)} == {"canada-list", "kwyeter"}


def test_reindex_unchanged_skips_everything(conn, src):
    stats = store.index_directory(conn, src)
    assert stats["indexed"] == 0 and stats["skipped"] == 3


def test_changed_file_is_reindexed_without_duplicates(conn, src):
    path = next(src.glob("*/demo-kwyeter-0.jsonl"))
    with path.open("a") as handle:
        handle.write('{"type":"user","sessionId":"demo-kwyeter-0","timestamp":"2026-10-03T00:00:00Z",'
                     '"message":{"role":"user","content":"zebrafish followup"}}\n')
    stats = store.index_directory(conn, src)
    assert stats["indexed"] == 1
    assert conn.execute("SELECT COUNT(*) FROM messages WHERE session_id='demo-kwyeter-0'").fetchone()[0] == 4
    assert len(store.search(conn, "zebrafish")) == 1


def test_deleted_transcript_is_removed_and_unsearchable(conn, src):
    next(src.glob("*/demo-kwyeter-0.jsonl")).unlink()
    assert store.index_directory(conn, src)["removed"] == 1
    assert store.search(conn, "calibration") == []


def test_search_finds_with_snippet_and_title_fallback(conn):
    hits = store.search(conn, "dedupe")
    assert hits and "[[" in hits[0]["snippet"]
    assert {h["project"] for h in hits} == {"canada-list"}


def test_search_project_filter(conn):
    assert store.search(conn, "calibration", project="canada-list") == []
    assert store.search(conn, "calibration", project="kwyeter")


def test_search_stemming_and_prefix(conn):
    assert store.search(conn, "calib")  # prefix of the stored stem
    assert store.search(conn, "calibrated")  # stems to the same root as "calibrating"
    assert store.search(conn, "merging")   # porter stems merged/merging


def test_hostile_queries_do_not_raise(conn):
    for query in ['"', "AND OR NOT", "foo*(", "a:b", "'; DROP TABLE sessions;--", "", "   ", "NEAR("]:
        store.search(conn, query)
    assert conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 3


def test_summary_survives_reindex_of_changed_file(conn, src):
    store.save_summary(conn, "demo-kwyeter-0", {"title": "T", "goal": "G", "decisions": [],
                                                "open_threads": [], "next_steps": []}, "now")
    path = next(src.glob("*/demo-kwyeter-0.jsonl"))
    os.utime(path, (1, 1))
    store.index_directory(conn, src)
    assert store.get_session(conn, "demo-kwyeter-0")["summary"]["title"] == "T"


def test_get_session_includes_messages_and_files(conn):
    s = store.get_session(conn, "demo-canada-list-0")
    assert len(s["messages"]) == 4 and s["files"][0]["path"].endswith("dedupe.py")
    assert store.get_session(conn, "nope") is None


def test_empty_transcript_file_is_counted_not_crashing(conn, src):
    write_jsonl(src / "-work-x" / "empty.jsonl", [{"type": "summary", "summary": "s"}])
    assert store.index_directory(conn, src)["empty"] == 1
