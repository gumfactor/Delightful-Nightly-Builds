import os

import pytest

from conftest import assistant, user, write_jsonl
from atlas.pricing import DEFAULT_PRICES
from atlas.store import Store


@pytest.fixture
def store(tmp_path):
    s = Store(tmp_path / "t.db")
    yield s
    s.close()


def test_index_then_query_sessions(store, basic_log):
    counts = store.index_directory(basic_log.parent.parent, DEFAULT_PRICES)
    assert counts["parsed"] == 1
    row = store.sessions()[0]
    assert row["project"] == "proj" and row["prompts"] == 1 and row["tool_errors"] == 1
    assert row["cost_usd"] > 0 and row["files"] == {"/work/proj/a.py": 1}


def test_unchanged_files_are_skipped_on_reindex(store, basic_log):
    root = basic_log.parent.parent
    store.index_directory(root, DEFAULT_PRICES)
    assert store.index_directory(root, DEFAULT_PRICES) == {"parsed": 0, "skipped": 1, "removed": 0, "empty": 0}


def test_changed_file_is_reparsed_without_duplicating_prompts(store, basic_log):
    root = basic_log.parent.parent
    store.index_directory(root, DEFAULT_PRICES)
    with basic_log.open("a") as handle:
        handle.write('{"type":"user","timestamp":"2026-09-01T11:00:00Z","message":{"role":"user","content":"second ask"}}\n')
    os.utime(basic_log, (1, 1))
    assert store.index_directory(root, DEFAULT_PRICES)["parsed"] == 1
    assert store.sessions()[0]["prompts"] == 2
    assert len(store.search("second")) == 1 and len(store.search("parser")) == 1


def test_deleted_log_is_removed_from_index(store, basic_log):
    root = basic_log.parent.parent
    store.index_directory(root, DEFAULT_PRICES)
    basic_log.unlink()
    assert store.index_directory(root, DEFAULT_PRICES)["removed"] == 1
    assert store.sessions() == []


def test_search_finds_prompt_text_with_project(store, basic_log):
    store.index_directory(basic_log.parent.parent, DEFAULT_PRICES)
    hits = store.search("parser bug")
    assert hits and hits[0]["project"] == "proj"


def test_search_like_fallback_handles_wildcards(store, basic_log):
    store.index_directory(basic_log.parent.parent, DEFAULT_PRICES)
    store.fts = False
    assert store.search("parser")
    assert store.search("100%") == []  # '%' is literal, not a wildcard


def test_search_with_fts_syntax_characters_does_not_error(store, basic_log):
    store.index_directory(basic_log.parent.parent, DEFAULT_PRICES)
    assert store.search('"parser" OR (') is not None
    assert store.search("   ") == []


def test_since_filter(store, tmp_path):
    write_jsonl(tmp_path / "l" / "a.jsonl", [user("2026-01-01T10:00:00Z", "old")])
    write_jsonl(tmp_path / "l" / "b.jsonl", [user("2026-09-01T10:00:00Z", "new")])
    store.index_directory(tmp_path / "l", DEFAULT_PRICES)
    assert [s["first_prompt"] for s in store.sessions(since="2026-06-01")] == ["new"]


def test_project_falls_back_to_decoded_dir_name_when_cwd_missing(store, tmp_path):
    rec = {"type": "user", "timestamp": "2026-09-01T10:00:00Z", "message": {"role": "user", "content": "x"}}
    write_jsonl(tmp_path / "l" / "-home-me-lab" / "a.jsonl", [rec])
    store.index_directory(tmp_path / "l", DEFAULT_PRICES)
    assert store.sessions()[0]["project"] == "lab"


def test_reprice_updates_cost(store, basic_log):
    store.index_directory(basic_log.parent.parent, DEFAULT_PRICES)
    before = store.sessions()[0]["cost_usd"]
    doubled = {k: {kk: vv * 2 for kk, vv in v.items()} for k, v in DEFAULT_PRICES.items()}
    store.reprice(doubled)
    assert store.sessions()[0]["cost_usd"] == pytest.approx(before * 2, rel=1e-3)
