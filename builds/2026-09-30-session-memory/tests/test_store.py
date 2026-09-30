from conftest import cc_record, write_jsonl
from sessionmemory import parsers
from sessionmemory.store import Store, fts_query


def make_session(tmp_path, text="alpha beta", name="a.jsonl"):
    return parsers.parse_claude_code(write_jsonl(tmp_path / name, [cc_record("user", text)]))


def test_ingest_is_incremental(store, tmp_path):
    session = make_session(tmp_path)
    assert store.upsert_session(session) == "added"
    assert store.upsert_session(session) == "unchanged"
    changed = make_session(tmp_path, "gamma delta")
    assert store.upsert_session(changed) == "updated"


def test_update_leaves_no_stale_fts_rows(store, tmp_path):
    store.upsert_session(make_session(tmp_path, "zebra crossing"))
    store.upsert_session(make_session(tmp_path, "giraffe walking"))
    assert store.search("zebra") == []
    assert len(store.search("giraffe")) == 1


def test_search_highlights_and_stems(demo_store):
    hits = demo_store.search("normalising province")
    assert hits and "\x02" in hits[0]["snippet"]
    assert demo_store.search("normalise")  # porter stemming matches "normalising"


def test_search_prefix_on_last_term(demo_store):
    assert demo_store.search("postal cod")


def test_search_filters(demo_store):
    assert demo_store.search("cortisol", source="chatgpt")
    assert demo_store.search("cortisol", source="claude-code")  # the book outline
    assert not demo_store.search("cortisol", project="canada-list")
    assert demo_store.search("cortisol", project="stress-book")


def test_hostile_queries_never_raise(demo_store):
    for query in ['"', "AND OR NOT", "foo* NEAR(", "'; DROP TABLE sessions;--", "   ", "((("]:
        demo_store.search(query)
    assert demo_store.stats()["sessions"] == 5


def test_fts_query_quotes_terms():
    assert fts_query('rapid "fuzz') == '"rapid" "fuzz"*'
    assert fts_query("!!!") is None


def test_projects_and_sessions_ordering(demo_store):
    projects = {p["project"]: p for p in demo_store.projects()}
    assert projects["canada-list"]["sessions"] == 2
    ordered = [s["ended"] for s in demo_store.sessions("canada-list")]
    assert ordered == sorted(ordered, reverse=True)


def test_session_roundtrip_preserves_messages_and_files(demo_store):
    row = next(s for s in demo_store.sessions("canada-list") if s["files"] and "dedupe.py" in " ".join(s["files"]))
    full = demo_store.session(row["id"])
    assert full["messages"][0]["role"] == "user"
    assert demo_store.session("nope") is None


def test_summary_cache_invalidates_when_session_changes(store, tmp_path):
    session = make_session(tmp_path)
    store.upsert_session(session)
    store.save_summary(session.id, "ai", {"summary": "s"})
    assert store.get_summary(session.id)["kind"] == "ai"
    store.upsert_session(make_session(tmp_path, "different content now"))
    assert store.get_summary(session.id) is None


def test_save_summary_for_unknown_session_raises(store):
    try:
        store.save_summary("missing", "ai", {})
    except KeyError:
        return
    raise AssertionError("expected KeyError")


def test_database_persists_across_connections(tmp_path):
    first = Store(tmp_path / "p.db")
    first.upsert_session(make_session(tmp_path))
    first.close()
    second = Store(tmp_path / "p.db")
    assert second.stats()["sessions"] == 1
    second.close()
