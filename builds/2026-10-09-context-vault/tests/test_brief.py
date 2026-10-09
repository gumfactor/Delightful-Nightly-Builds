import json

from ctxvault import summarize
from ctxvault.brief import build_brief

FAKE = json.dumps({"title": "Dedupe work", "goal": "Fix dupes", "decisions": ["Use normalised host"],
                   "open_threads": ["Franchise locations merged"], "next_steps": ["Write migration"]})


def test_brief_without_summaries_says_so_and_lists_files(conn):
    text = build_brief(conn, "canada-list")
    assert "No AI summaries yet" in text and "dedupe.py" in text and "fix/dedupe-ingest" not in text
    assert "Recent sessions" in text


def test_brief_with_summaries_has_threads_decisions_steps(conn):
    summarize.summarize_pending(conn, "canada-list", complete=lambda p: FAKE)
    text = build_brief(conn, "canada-list")
    assert "## Open threads" in text and "Franchise locations merged" in text
    assert "Use normalised host" in text and "Write migration" in text
    assert text.count("Franchise locations merged") == 1  # de-duplicated across sessions


def test_brief_unknown_project_is_none(conn):
    assert build_brief(conn, "nope") is None


def test_brief_names_latest_branch(conn):
    assert "`main`" in build_brief(conn, "canada-list")
