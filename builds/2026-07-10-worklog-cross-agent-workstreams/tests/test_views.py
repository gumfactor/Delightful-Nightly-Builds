from worklog import views
from worklog.ledger import Event, Ledger
from worklog.project import discover_project
from worklog.sync import run_sync

from conftest import commit as make_commit

PROJECT = "proj-1"


def _commit(ledger, event_id, ref, ws, timestamp, summary="did work", files=None):
    ledger.upsert_event(
        Event(
            id=event_id,
            project_id=PROJECT,
            timestamp=timestamp,
            type="commit",
            actor_kind="human",
            actor_name="tester",
            summary=summary,
            status="completed",
            source_provider="git",
            source_ref=ref,
            workstream_id=ws,
            metadata={"files": files or []},
        )
    )


def _checkpoint(ledger, event_id, ws, timestamp, unresolved=None, next_steps=None, validation=None):
    ledger.upsert_event(
        Event(
            id=event_id,
            project_id=PROJECT,
            timestamp=timestamp,
            type="checkpoint",
            actor_kind="agent",
            actor_name="claude",
            summary="objective text",
            status="open",
            source_provider="checkpoint",
            source_ref=event_id,
            workstream_id=ws,
            metadata={
                "unresolved": unresolved or [],
                "next_steps": next_steps or [],
                "validation": validation or [],
                "files": [],
            },
        )
    )


def _decision(ledger, event_id, ws, timestamp, summary, reason=""):
    ledger.upsert_event(
        Event(
            id=event_id,
            project_id=PROJECT,
            timestamp=timestamp,
            type="decision",
            actor_kind="agent",
            actor_name="claude",
            summary=summary,
            status="recorded",
            source_provider="checkpoint",
            source_ref=event_id,
            workstream_id=ws,
            metadata={"reason": reason},
        )
    )


def test_standup_groups_completed_commits(tmp_path):
    ledger = Ledger(str(tmp_path))
    ledger.upsert_workstream("ws1", PROJECT, "Feature A", "2026-07-01T00:00:00Z")
    now = views.util.utc_now_iso()
    _commit(ledger, "c1", "sha1", "ws1", now, summary="did the thing")
    report = views.standup(ledger, PROJECT, "24h")
    assert len(report.completed) == 1
    assert report.completed[0]["title"] == "Feature A"
    assert report.completed[0]["commit_count"] == 1


def test_standup_excludes_old_commits(tmp_path):
    ledger = Ledger(str(tmp_path))
    ledger.upsert_workstream("ws1", PROJECT, "Feature A", "2020-01-01T00:00:00Z")
    _commit(ledger, "c1", "sha1", "ws1", "2020-01-01T00:00:00Z")
    report = views.standup(ledger, PROJECT, "24h")
    assert report.completed == []


def test_standup_blocked_on_failed_validation(tmp_path):
    ledger = Ledger(str(tmp_path))
    ledger.upsert_workstream("ws1", PROJECT, "Feature A", "2026-07-01T00:00:00Z")
    now = views.util.utc_now_iso()
    _checkpoint(ledger, "cp1", "ws1", now, validation=[{"command": "pytest", "result": "failed"}])
    report = views.standup(ledger, PROJECT, "24h")
    assert len(report.blocked) == 1
    assert "pytest" in report.blocked[0]["reason"]


def test_standup_in_progress_on_unresolved(tmp_path):
    ledger = Ledger(str(tmp_path))
    ledger.upsert_workstream("ws1", PROJECT, "Feature A", "2026-07-01T00:00:00Z")
    now = views.util.utc_now_iso()
    _checkpoint(ledger, "cp1", "ws1", now, unresolved=["open question"])
    report = views.standup(ledger, PROJECT, "24h")
    assert len(report.in_progress) == 1


def test_standup_next_actions_from_checkpoint(tmp_path):
    ledger = Ledger(str(tmp_path))
    ledger.upsert_workstream("ws1", PROJECT, "Feature A", "2026-07-01T00:00:00Z")
    now = views.util.utc_now_iso()
    _checkpoint(ledger, "cp1", "ws1", now, next_steps=["add fixtures", "write docs"])
    report = views.standup(ledger, PROJECT, "24h")
    steps = {item["step"] for item in report.next_actions}
    assert steps == {"add fixtures", "write docs"}


def test_why_finds_matching_decision(tmp_path):
    ledger = Ledger(str(tmp_path))
    ledger.upsert_workstream("ws1", PROJECT, "Feature A", "2026-07-01T00:00:00Z")
    _decision(ledger, "d1", "ws1", "2026-07-01T00:00:00Z", "Reject automatic coercion", "corrupts ids")
    results = views.why(ledger, PROJECT, "coercion")
    assert len(results) == 1
    assert results[0].workstream_title == "Feature A"


def test_why_case_insensitive_no_match(tmp_path):
    ledger = Ledger(str(tmp_path))
    ledger.upsert_workstream("ws1", PROJECT, "Feature A", "2026-07-01T00:00:00Z")
    _decision(ledger, "d1", "ws1", "2026-07-01T00:00:00Z", "Reject automatic COERCION", "")
    results = views.why(ledger, PROJECT, "coercion")
    assert len(results) == 1


def test_why_includes_later_events(tmp_path):
    ledger = Ledger(str(tmp_path))
    ledger.upsert_workstream("ws1", PROJECT, "Feature A", "2026-07-01T00:00:00Z")
    _decision(ledger, "d1", "ws1", "2026-07-01T00:00:00Z", "Reject coercion", "")
    _commit(ledger, "c1", "sha1", "ws1", "2026-07-02T00:00:00Z", summary="later commit")
    results = views.why(ledger, PROJECT, "coercion")
    assert any("later commit" in e for e in results[0].later_events)


def test_timeline_all_events_sorted(tmp_path):
    ledger = Ledger(str(tmp_path))
    _commit(ledger, "c2", "sha2", None, "2026-07-02T00:00:00Z", summary="second")
    _commit(ledger, "c1", "sha1", None, "2026-07-01T00:00:00Z", summary="first")
    events = views.timeline(ledger, PROJECT)
    assert [e.summary for e in events] == ["first", "second"]


def test_workstreams_view_lists_signals(tmp_path):
    ledger = Ledger(str(tmp_path))
    ledger.upsert_workstream("ws1", PROJECT, "Feature A", "2026-07-01T00:00:00Z")
    _commit(ledger, "c1", "sha1", "ws1", "2026-07-01T00:00:00Z")
    ledger.set_event_workstream("c1", "ws1", {"signal": "branch", "confidence": "medium"})
    rows = views.workstreams_view(ledger, PROJECT)
    assert rows[0]["signals"] == ["branch"]


def test_show_event_found_and_missing(tmp_path):
    ledger = Ledger(str(tmp_path))
    _commit(ledger, "c1", "sha1", None, "2026-07-01T00:00:00Z")
    assert views.show_event(ledger, "c1") is not None
    assert views.show_event(ledger, "does-not-exist") is None


def test_search_matches_summary(tmp_path):
    ledger = Ledger(str(tmp_path))
    _commit(ledger, "c1", "sha1", None, "2026-07-01T00:00:00Z", summary="fix the CSV parser")
    results = views.search(ledger, PROJECT, "csv")
    assert len(results) == 1


def test_resume_no_data(tmp_path):
    ledger = Ledger(str(tmp_path))
    project = None  # resume should short-circuit before touching project on empty ledger
    from worklog.project import ProjectState

    fake_project = ProjectState(
        repo_root="/tmp/x", project_id=PROJECT, github_owner_repo=None, branch="main", head_sha=""
    )
    package = views.resume(ledger, fake_project)
    assert package.no_data is True


def test_resume_detects_head_drift(git_repo, tmp_path):
    data_dir = str(tmp_path / "data")
    run_sync(str(git_repo), data_dir=data_dir, use_github=False)

    # Move HEAD forward after the sync.
    make_commit(git_repo, "extra.txt", "more\n", "Add extra file")

    project = discover_project(str(git_repo))
    ledger = Ledger(data_dir)
    package = views.resume(ledger, project)
    assert package.head_stale is True
    assert "current HEAD" in package.head_stale_detail


def test_resume_not_stale_immediately_after_sync(git_repo, tmp_path):
    data_dir = str(tmp_path / "data")
    run_sync(str(git_repo), data_dir=data_dir, use_github=False)
    project = discover_project(str(git_repo))
    ledger = Ledger(data_dir)
    package = views.resume(ledger, project)
    assert package.head_stale is False
