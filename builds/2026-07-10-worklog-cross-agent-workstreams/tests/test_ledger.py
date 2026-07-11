from worklog.ledger import Event, Ledger


def _event(event_id="e1", ref="abc", ws=None):
    return Event(
        id=event_id,
        project_id="proj-1",
        timestamp="2026-07-01T00:00:00Z",
        type="commit",
        actor_kind="human",
        actor_name="tester",
        summary="Did a thing",
        status="completed",
        source_provider="git",
        source_ref=ref,
        workstream_id=ws,
        metadata={"files": ["a.py"]},
    )


def test_upsert_event_inserts_new(tmp_path):
    ledger = Ledger(str(tmp_path))
    inserted = ledger.upsert_event(_event())
    assert inserted is True
    ledger.close()


def test_upsert_event_dedupes(tmp_path):
    ledger = Ledger(str(tmp_path))
    ledger.upsert_event(_event())
    inserted_again = ledger.upsert_event(_event())
    assert inserted_again is False
    events = ledger.events_for_project("proj-1")
    assert len(events) == 1
    ledger.close()


def test_get_event_roundtrip(tmp_path):
    ledger = Ledger(str(tmp_path))
    ledger.upsert_event(_event())
    fetched = ledger.get_event("e1")
    assert fetched is not None
    assert fetched.summary == "Did a thing"
    assert fetched.metadata == {"files": ["a.py"]}
    ledger.close()


def test_events_for_project_filters_by_type(tmp_path):
    ledger = Ledger(str(tmp_path))
    ledger.upsert_event(_event(event_id="e1", ref="a"))
    other = _event(event_id="e2", ref="b")
    other.type = "branch"
    ledger.upsert_event(other)
    commits = ledger.events_for_project("proj-1", "commit")
    assert len(commits) == 1
    assert commits[0].id == "e1"
    ledger.close()


def test_set_event_workstream(tmp_path):
    ledger = Ledger(str(tmp_path))
    ledger.upsert_event(_event())
    ledger.set_event_workstream("e1", "ws_1", {"signal": "branch", "confidence": "medium"})
    fetched = ledger.get_event("e1")
    assert fetched.workstream_id == "ws_1"
    assert fetched.correlation == {"signal": "branch", "confidence": "medium"}
    ledger.close()


def test_upsert_workstream_creates_and_preserves_title(tmp_path):
    ledger = Ledger(str(tmp_path))
    ledger.upsert_workstream("ws_1", "proj-1", "Original Title", "2026-07-01T00:00:00Z")
    ledger.upsert_workstream("ws_1", "proj-1", "Different Title", "2026-07-02T00:00:00Z")
    ws = ledger.get_workstream("ws_1")
    assert ws["title"] == "Original Title"
    assert ws["updated_at"] == "2026-07-02T00:00:00Z"
    ledger.close()


def test_workstreams_for_project_sorted_by_recent(tmp_path):
    ledger = Ledger(str(tmp_path))
    ledger.upsert_workstream("ws_old", "proj-1", "Old", "2026-07-01T00:00:00Z")
    ledger.upsert_workstream("ws_new", "proj-1", "New", "2026-07-05T00:00:00Z")
    rows = ledger.workstreams_for_project("proj-1")
    assert rows[0]["id"] == "ws_new"


def test_find_workstream_by_issue(tmp_path):
    ledger = Ledger(str(tmp_path))
    event = _event(event_id="issue-1", ref="issue:12", ws="ws_issue_12")
    event.type = "github_issue"
    event.source_provider = "github"
    ledger.upsert_event(event)
    found = ledger.find_workstream_by_issue("proj-1", 12)
    assert found == "ws_issue_12"


def test_find_workstream_by_issue_missing(tmp_path):
    ledger = Ledger(str(tmp_path))
    assert ledger.find_workstream_by_issue("proj-1", 999) is None


def test_find_workstream_by_branch(tmp_path):
    ledger = Ledger(str(tmp_path))
    event = _event(event_id="commit-1", ref="sha1", ws="ws_branch_x")
    event.metadata = {"branch": "feature/x", "files": []}
    ledger.upsert_event(event)
    found = ledger.find_workstream_by_branch("proj-1", "feature/x")
    assert found == "ws_branch_x"


def test_sync_state_get_default(tmp_path):
    ledger = Ledger(str(tmp_path))
    assert ledger.get_state("proj-1", "last_sync_head", default="none") == "none"


def test_sync_state_set_and_get(tmp_path):
    ledger = Ledger(str(tmp_path))
    ledger.set_state("proj-1", "last_sync_head", "abc123")
    assert ledger.get_state("proj-1", "last_sync_head") == "abc123"


def test_sync_state_overwrite(tmp_path):
    ledger = Ledger(str(tmp_path))
    ledger.set_state("proj-1", "k", "v1")
    ledger.set_state("proj-1", "k", "v2")
    assert ledger.get_state("proj-1", "k") == "v2"


def test_recent_commit_events_limit(tmp_path):
    ledger = Ledger(str(tmp_path))
    for i in range(5):
        ledger.upsert_event(_event(event_id=f"c{i}", ref=f"sha{i}"))
    recent = ledger.recent_commit_events("proj-1", limit=3)
    assert len(recent) == 3


def test_ledger_context_manager_closes(tmp_path):
    with Ledger(str(tmp_path)) as ledger:
        ledger.upsert_event(_event())
    # Connection should be closed; a further operation should raise.
    import sqlite3

    try:
        ledger.conn.execute("SELECT 1")
        assert False, "expected closed connection to raise"
    except sqlite3.ProgrammingError:
        pass
