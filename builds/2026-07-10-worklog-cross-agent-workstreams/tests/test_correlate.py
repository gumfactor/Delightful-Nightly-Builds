from worklog.correlate import CorrelationInput, resolve_workstream
from worklog.ledger import Event, Ledger

PROJECT = "proj-1"
TS = "2026-07-01T00:00:00Z"


def _commit_event(ledger, event_id, ref, workstream_id, files):
    event = Event(
        id=event_id,
        project_id=PROJECT,
        timestamp=TS,
        type="commit",
        actor_kind="human",
        actor_name="tester",
        summary="a commit",
        status="completed",
        source_provider="git",
        source_ref=ref,
        workstream_id=workstream_id,
        metadata={"files": files},
    )
    ledger.upsert_event(event)


def test_explicit_hint_wins(tmp_path):
    ledger = Ledger(str(tmp_path))
    params = CorrelationInput(timestamp=TS, explicit_hint="CSV validation", issue_refs=[5], branch="feature/x")
    ws_id, correlation = resolve_workstream(ledger, PROJECT, params)
    assert correlation["signal"] == "explicit_hint"
    assert correlation["confidence"] == "high"
    assert "csv-validation" in ws_id


def test_issue_reference_creates_new_workstream(tmp_path):
    ledger = Ledger(str(tmp_path))
    params = CorrelationInput(timestamp=TS, issue_refs=[41])
    ws_id, correlation = resolve_workstream(ledger, PROJECT, params)
    assert correlation["signal"] == "issue_reference"
    ws = ledger.get_workstream(ws_id)
    assert "41" in ws["title"]


def test_issue_reference_reuses_existing_workstream(tmp_path):
    ledger = Ledger(str(tmp_path))
    first_params = CorrelationInput(timestamp=TS, issue_refs=[41], fallback_title="First event")
    first_ws, _ = resolve_workstream(ledger, PROJECT, first_params)

    second_params = CorrelationInput(timestamp=TS, issue_refs=[41], fallback_title="Second event")
    second_ws, correlation = resolve_workstream(ledger, PROJECT, second_params)
    assert second_ws == first_ws
    assert correlation["signal"] == "issue_reference"


def test_branch_signal_creates_workstream(tmp_path):
    ledger = Ledger(str(tmp_path))
    params = CorrelationInput(timestamp=TS, branch="feature/csv-validation")
    ws_id, correlation = resolve_workstream(ledger, PROJECT, params)
    assert correlation["signal"] == "branch"
    assert correlation["confidence"] == "medium"


def test_default_branch_does_not_anchor(tmp_path):
    ledger = Ledger(str(tmp_path))
    params = CorrelationInput(timestamp=TS, branch="main")
    ws_id, correlation = resolve_workstream(ledger, PROJECT, params)
    # main is a default branch, so it should fall through to the general bucket, not branch.
    assert correlation["signal"] == "general_bucket"


def test_branch_reuses_existing_workstream(tmp_path):
    ledger = Ledger(str(tmp_path))
    first_ws, _ = resolve_workstream(ledger, PROJECT, CorrelationInput(timestamp=TS, branch="feature/y"))
    second_ws, correlation = resolve_workstream(ledger, PROJECT, CorrelationInput(timestamp=TS, branch="feature/y"))
    assert first_ws == second_ws
    assert correlation["signal"] == "branch"


def test_file_overlap_signal(tmp_path):
    ledger = Ledger(str(tmp_path))
    _commit_event(ledger, "c1", "sha1", "ws_existing", ["src/a.py", "src/b.py"])
    params = CorrelationInput(timestamp=TS, files=["src/a.py", "src/c.py"])
    ws_id, correlation = resolve_workstream(ledger, PROJECT, params)
    assert ws_id == "ws_existing"
    assert correlation["signal"] == "file_overlap"


def test_file_overlap_below_threshold_falls_through(tmp_path):
    ledger = Ledger(str(tmp_path))
    _commit_event(ledger, "c1", "sha1", "ws_existing", ["src/a.py", "src/b.py", "src/c.py", "src/d.py", "src/e.py"])
    params = CorrelationInput(timestamp=TS, files=["src/z.py"])
    ws_id, correlation = resolve_workstream(ledger, PROJECT, params)
    assert ws_id != "ws_existing"
    assert correlation["signal"] == "general_bucket"


def test_general_bucket_fallback(tmp_path):
    ledger = Ledger(str(tmp_path))
    params = CorrelationInput(timestamp=TS)
    ws_id, correlation = resolve_workstream(ledger, PROJECT, params)
    assert correlation["signal"] == "general_bucket"
    assert correlation["confidence"] == "low"
    assert "2026-07-01" in ws_id


def test_signal_priority_issue_over_branch(tmp_path):
    ledger = Ledger(str(tmp_path))
    params = CorrelationInput(timestamp=TS, issue_refs=[9], branch="feature/z")
    ws_id, correlation = resolve_workstream(ledger, PROJECT, params)
    assert correlation["signal"] == "issue_reference"
