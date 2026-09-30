from conftest import cc_record, write_jsonl
from sessionmemory import brief, parsers


def test_brief_orders_newest_first_and_lists_open_items(demo_store):
    text = brief.build_brief(demo_store, "canada-list")
    assert text.startswith("# canada-list: resume brief")
    assert text.index("2026-09-19") < text.index("2026-09-12")
    assert "Should chain locations be merged" in text and "Add a regression test" in text


def test_brief_counts_files_across_sessions(demo_store):
    text = brief.build_brief(demo_store, "canada-list")
    assert "`pipeline/load.py` (2 sessions)" in text
    assert "`pipeline/dedupe.py` (1 session)" in text


def test_brief_deduplicates_open_items(store, tmp_path):
    for name in ("a", "b"):
        path = write_jsonl(tmp_path / f"{name}.jsonl", [
            cc_record("user", f"go {name}"), {**cc_record("assistant", "Next steps:\n- Write the docs"), "sessionId": name},
        ])
        record = parsers.parse_claude_code(path)
        record.id = f"claude-code:{name}"
        store.upsert_session(record)
    section = brief.build_brief(store, "demo").split("## Open items")[1].split("##")[0]
    assert section.count("- Write the docs") == 1


def test_brief_for_unknown_project_is_graceful(store):
    assert "No sessions found" in brief.build_brief(store, "ghost")


def test_days_window_excludes_old_sessions(demo_store):
    assert "No sessions found" in brief.build_brief(demo_store, "canada-list", days=1)


def test_brief_prefers_cached_ai_summary(demo_store):
    session_id = demo_store.sessions("stress-book")[0]["id"]
    demo_store.save_summary(session_id, "ai", {"title": "T", "summary": "AI wrote this", "decisions": [], "open_items": ["AI open item"]})
    text = brief.build_brief(demo_store, "stress-book")
    assert "AI wrote this" in text and "AI open item" in text


def test_ai_brief_is_saved(demo_store):
    post = lambda *a, **k: {"content": [{"type": "text", "text": "# tight brief"}]}  # noqa: E731
    assert brief.ai_brief(demo_store, "canada-list", api_key="k", post=post) == "# tight brief"
    assert demo_store.get_brief("canada-list", "ai") == "# tight brief"
