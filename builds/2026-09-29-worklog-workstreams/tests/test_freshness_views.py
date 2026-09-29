from datetime import datetime, timezone

import pytest

from worklog import checkpoint, freshness, gitcollect, views
from worklog.correlate import correlate
from worklog.project import WorklogError

NOW = datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc)


def _setup(project, ledger, scenario, **cp_over):
    ledger.ingest(gitcollect.collect_commits(project))
    tip = scenario.git("rev-parse", "feature/41-csv-validation")
    cp = {"provider": "codex", "session_id": "s1", "timestamp": "2026-09-02T13:00:00Z",
          "objective": "Add CSV validation", "branch": "feature/41-csv-validation", "head": tip,
          "source_refs": [{"issue": "41"}], "accomplished": ["Added schema checks"],
          "next_steps": ["Add malformed-row fixtures"], "unresolved": ["Blank optional columns?"],
          "decisions": [{"summary": "Reject automatic type coercion", "reason": "Can corrupt identifiers",
                         "rejected": ["Coerce to int"], "files": ["src/validation.py"]}]}
    cp.update(cp_over)
    checkpoint.capture(project, ledger, cp)
    workstreams = correlate(ledger.events(project.project_id))
    return next(w for w in workstreams if w.by_type("checkpoint"))


def test_fresh_checkpoint_has_no_stale_findings(project, ledger, scenario):
    ws = _setup(project, ledger, scenario)
    assert not freshness.is_stale(freshness.check(project, ws, NOW))


def test_checkpoint_is_stale_after_branch_moves_on(project, ledger, scenario):
    ws = _setup(project, ledger, scenario)
    scenario.git("checkout", "-q", "feature/41-csv-validation")
    scenario.commit("Handle unicode headers", {"src/other.py": "x"}, date="2026-09-06T09:00:00+00:00")
    findings = freshness.check(project, ws, NOW)
    assert freshness.is_stale(findings) and "+1 commit(s) since" in findings[0]["text"]


def test_checkpoint_stale_when_branch_deleted(project, ledger, scenario):
    ws = _setup(project, ledger, scenario)
    scenario.git("branch", "-D", "feature/41-csv-validation")
    assert "no longer exists" in freshness.check(project, ws, NOW)[0]["text"]


def test_old_but_unchanged_checkpoint_only_warns(project, ledger, scenario):
    ws = _setup(project, ledger, scenario)
    findings = freshness.check(project, ws, datetime(2026, 12, 1, tzinfo=timezone.utc))
    assert findings[0]["level"] == "warn" and not freshness.is_stale(findings)


def test_next_step_already_done_is_flagged_as_inferred(project, ledger, scenario):
    ws = _setup(project, ledger, scenario, next_steps=["Handle unicode headers in validation"],
                head=scenario.git("rev-parse", "feature/41-csv-validation"))
    scenario.git("checkout", "-q", "feature/41-csv-validation")
    scenario.commit("Handle unicode headers in validation", {"src/u.py": "1"}, date="2026-09-06T09:00:00+00:00")
    ledger.ingest(gitcollect.collect_commits(project))
    ws = next(w for w in correlate(ledger.events(project.project_id)) if w.by_type("checkpoint"))
    texts = [f["text"] for f in freshness.check(project, ws, NOW)]
    assert any(t.startswith("inferred: next step") for t in texts)


def test_standup_groups_by_status_and_lists_next_steps_without_per_commit_noise(project, ledger, scenario):
    ws = _setup(project, ledger, scenario)
    data = views.standup_data(correlate(ledger.events(project.project_id)), {}, "2026-09-01T00:00:00Z")
    active = [i for i in data["in_progress"] if i["id"] == ws.id][0]
    assert "commit(s)" in active["activity"] and active["accomplished"] == ["Added schema checks"]
    assert data["next"][0]["steps"] == ["Add malformed-row fixtures"]
    text = views.render_standup(data, "2026-09-01T00:00:00Z")
    assert text.count("Add schema checks before ingestion") == 0  # commits are summarised, not listed


def test_standup_excludes_workstreams_without_recent_activity(project, ledger, scenario):
    _setup(project, ledger, scenario)
    data = views.standup_data(correlate(ledger.events(project.project_id)), {}, "2026-10-01T00:00:00Z")
    assert all(not v for v in data.values())


def test_resume_contains_decisions_next_steps_freshness_and_observed_state(project, ledger, scenario):
    ws = _setup(project, ledger, scenario)
    data = views.resume_data(ws, freshness.check(project, ws, NOW), {"branch": "main", "head": "a" * 40,
                                                                      "dirty": ["src/validation.py"], "untracked": []}, None)
    text = views.render_resume(data)
    for expected in ("Reject automatic type coercion", "Can corrupt identifiers", "Coerce to int",
                     "Add malformed-row fixtures", "Blank optional columns?", "[observed]",
                     "uncommitted changes touching this workstream's files: src/validation.py"):
        assert expected in text


def test_resume_flags_stale_state_prominently(project, ledger, scenario):
    ws = _setup(project, ledger, scenario)
    scenario.git("branch", "-D", "feature/41-csv-validation")
    data = views.resume_data(ws, freshness.check(project, ws, NOW), {}, None)
    assert data["stale"] and "[STALE]" in views.render_resume(data)


def test_why_finds_decision_with_reason_and_rejected_alternatives(project, ledger, scenario):
    _setup(project, ledger, scenario)
    workstreams = correlate(ledger.events(project.project_id))
    text = views.render_why(views.why_data(workstreams, "type coercion"))
    assert "Can corrupt identifiers" in text and "Coerce to int" in text and "[recorded]" in text


def test_why_marks_superseded_decisions(project, ledger, scenario):
    _setup(project, ledger, scenario)
    checkpoint.capture(project, ledger, {"provider": "claude-code", "session_id": "s2", "timestamp": "2026-09-04T10:00:00Z",
                                        "objective": "Add CSV validation",
                                        "decisions": [{"summary": "Allow coercion for numeric columns only",
                                                       "supersedes": "Reject automatic type coercion"}]})
    data = views.why_data(correlate(ledger.events(project.project_id)), "reject coercion")
    assert data["matches"][0]["superseded_by"] == "Allow coercion for numeric columns only"
    assert "SUPERSEDED" in views.render_why(data)


def test_why_without_a_recorded_decision_does_not_invent_one(project, ledger, scenario):
    _setup(project, ledger, scenario)
    data = views.why_data(correlate(ledger.events(project.project_id)), "schema checks")
    assert data["matches"] == [] and data["commit_mentions"]
    assert "No recorded decision" in views.render_why(data)


def test_three_views_differ_and_all_cite_evidence(project, ledger, scenario):
    ws = _setup(project, ledger, scenario)
    workstreams = correlate(ledger.events(project.project_id))
    standup = views.render_standup(views.standup_data(workstreams, {}, "2026-09-01T00:00:00Z"), "x")
    resume = views.render_resume(views.resume_data(ws, [], {}, None))
    why = views.render_why(views.why_data(workstreams, "coercion"))
    assert len({standup, resume, why}) == 3
    for text in (standup, resume, why):
        assert "evt_" in text


def test_timeline_explains_grouping_evidence(project, ledger, scenario):
    ws = _setup(project, ledger, scenario)
    text = views.render_timeline(ws)
    assert "Why these events are grouped" in text and "shared gh:41" in text


@pytest.mark.parametrize("text, expected", [("today", "2026-09-06T00:00:00Z"), ("yesterday", "2026-09-05T00:00:00Z"),
                                            ("2d", "2026-09-04T12:00:00Z"), ("12 hours", "2026-09-06T00:00:00Z"),
                                            ("1 week", "2026-08-30T12:00:00Z"), ("2026-09-01", "2026-09-01T00:00:00Z")])
def test_parse_since_formats(text, expected):
    assert views.parse_since(text, NOW) == expected


def test_parse_since_rejects_garbage():
    with pytest.raises(WorklogError):
        views.parse_since("whenever", NOW)
