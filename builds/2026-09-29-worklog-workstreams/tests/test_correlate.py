from worklog.correlate import correlate, find_workstream
from worklog.ledger import make_event


def ev(ref, ts, etype="commit", keys=(), files=(), summary=None, provider="git", status="completed", meta=None):
    return make_event(ts=ts, project_id="p", etype=etype, provider=provider, ref=ref, summary=summary or ref,
                      keys=list(keys), files=list(files), status=status, metadata=meta or {})


def ids(ws):
    return {e["ref"] for e in ws.events}


def test_shared_sha_links_commit_pr_and_ci_into_one_workstream():
    events = [ev("c1", "2026-09-01T10:00:00Z", keys=["sha:c1"]),
              ev("pr:1:opened", "2026-09-01T11:00:00Z", "pr", keys=["sha:c1", "gh:1"], provider="github"),
              ev("check:9", "2026-09-01T12:00:00Z", "ci", keys=["sha:c1"], provider="github")]
    (ws,) = correlate(events)
    assert ids(ws) == {"c1", "pr:1:opened", "check:9"}
    assert any(l.signal == "sha" and "shared sha:c1" in l.rationale for l in ws.links)


def test_issue_number_links_commit_to_issue_and_pr():
    events = [ev("i", "2026-09-01T08:00:00Z", "issue", keys=["gh:41"], provider="github"),
              ev("c", "2026-09-01T09:00:00Z", keys=["gh:41"]),
              ev("pr", "2026-09-01T10:00:00Z", "pr", keys=["gh:52", "gh:41"], provider="github")]
    assert len(correlate(events)) == 1


def test_unrelated_events_stay_separate():
    events = [ev("a", "2026-09-01T10:00:00Z", keys=["sha:a"], files=["x.py"]),
              ev("b", "2026-12-01T10:00:00Z", keys=["sha:b"], files=["y.py"])]
    assert len(correlate(events)) == 2


def test_checkpoint_objective_and_commit_sha_join_agent_work_to_git():
    events = [ev("cp1", "2026-09-01T10:00:00Z", "checkpoint", keys=["obj:add-csv", "sha:c1"], provider="codex"),
              ev("c1", "2026-09-01T09:00:00Z", keys=["sha:c1"]),
              ev("cp2", "2026-09-02T10:00:00Z", "checkpoint", keys=["obj:add-csv"], provider="claude-code")]
    (ws,) = correlate(events)
    assert {e["provider"] for e in ws.events} == {"git", "codex", "claude-code"}


def test_weak_file_and_time_overlap_merges_only_when_confident_and_is_labelled_inferred():
    files = ["a.py", "b.py", "c.py"]
    events = [ev("x", "2026-09-01T10:00:00Z", files=files), ev("y", "2026-09-01T12:00:00Z", files=files)]
    (ws,) = correlate(events)
    inferred = [l for l in ws.links if l.kind == "inferred"]
    assert inferred and inferred[0].signal == "files+time" and "3 shared file(s)" in inferred[0].rationale


def test_medium_confidence_overlap_is_only_a_suggestion():
    events = [ev("x", "2026-09-01T10:00:00Z", files=["a.py", "b.py", "c.py"]),
              ev("y", "2026-09-02T10:00:00Z", files=["a.py", "b.py", "d.py"])]
    workstreams = correlate(events)
    assert len(workstreams) == 2 and any(ws.suggestions for ws in workstreams)
    assert all(not [l for l in ws.links if l.kind == "inferred"] for ws in workstreams)


def test_same_files_far_apart_in_time_do_not_merge():
    events = [ev("x", "2026-01-01T10:00:00Z", files=["a.py"]), ev("y", "2026-09-01T10:00:00Z", files=["a.py"])]
    assert len(correlate(events)) == 2


def test_split_override_detaches_an_event_from_strong_links():
    events = [ev("c1", "2026-09-01T10:00:00Z", keys=["gh:1"]), ev("c2", "2026-09-01T11:00:00Z", keys=["gh:1"])]
    target = events[1]["id"]
    assert len(correlate(events, [{"kind": "split", "event": target}])) == 2


def test_merge_override_joins_unrelated_workstreams():
    events = [ev("a", "2026-01-01T10:00:00Z"), ev("b", "2026-09-01T10:00:00Z")]
    (ws,) = correlate(events, [{"kind": "merge", "events": [events[0]["id"], events[1]["id"]]}])
    assert any(l.rationale == "merged by user" for l in ws.links)


def test_rename_override_wins_over_derived_title():
    events = [ev("c", "2026-09-01T10:00:00Z", summary="wip")]
    (ws,) = correlate(events, [{"kind": "rename", "event": events[0]["id"], "title": "CSV validation"}])
    assert ws.title == "CSV validation"


def test_title_prefers_checkpoint_objective_then_pr_title():
    cp = ev("cp", "2026-09-01T10:00:00Z", "checkpoint", keys=["gh:1"], meta={"objective": "Ship validation"})
    pr = ev("pr", "2026-09-01T09:00:00Z", "pr", keys=["gh:1"], meta={"title": "PR title"})
    assert correlate([cp, pr])[0].title == "Ship validation"
    assert correlate([pr])[0].title == "PR title"


def test_failing_ci_blocks_until_a_later_commit_or_resolve():
    ci = ev("check:1", "2026-09-01T10:00:00Z", "ci", keys=["gh:1"], status="failed")
    commit = ev("c", "2026-09-01T09:00:00Z", keys=["gh:1"])
    (ws,) = correlate([commit, ci])
    assert ws.status == "blocked" and ws.blockers[0]["kind"] == "failing CI"
    (resolved,) = correlate([commit, ci], [{"kind": "resolve", "event": ci["id"]}])
    assert resolved.status == "in_progress"
    fix = ev("c2", "2026-09-01T11:00:00Z", keys=["gh:1"])
    assert correlate([commit, ci, fix])[0].status == "in_progress"


def test_merged_pr_completes_workstream_even_after_earlier_failure():
    events = [ev("c", "2026-09-01T09:00:00Z", keys=["gh:1"]),
              ev("check:1", "2026-09-01T10:00:00Z", "ci", keys=["gh:1"], status="failed"),
              ev("pr:1:merged", "2026-09-02T10:00:00Z", "pr", keys=["gh:1"], provider="github")]
    (ws,) = correlate(events)
    assert ws.status == "completed" and ws.blockers == []


def test_new_commit_after_merge_reopens_workstream():
    events = [ev("pr:1:merged", "2026-09-02T10:00:00Z", "pr", keys=["gh:1"]), ev("c", "2026-09-03T10:00:00Z", keys=["gh:1"])]
    assert correlate(events)[0].status == "in_progress"


def test_open_blocker_note_and_checkpoint_blockers_block():
    note = ev("n", "2026-09-01T10:00:00Z", "blocker", keys=["gh:1"], status="open")
    assert correlate([note])[0].status == "blocked"
    cp = ev("cp", "2026-09-01T10:00:00Z", "checkpoint", status="blocked", meta={"blockers": ["need data"]})
    assert correlate([cp])[0].blockers[0]["reason"] == "need data"


def test_workstream_ids_are_stable_across_recomputation():
    events = [ev("a", "2026-09-01T10:00:00Z", keys=["gh:1"]), ev("b", "2026-09-01T11:00:00Z", keys=["gh:1"])]
    assert correlate(events)[0].id == correlate(list(reversed(events)))[0].id


def test_find_workstream_by_id_title_and_ambiguity():
    events = [ev("a", "2026-09-01T10:00:00Z", summary="alpha task"), ev("b", "2026-12-01T10:00:00Z", summary="beta task")]
    workstreams = correlate(events)
    assert find_workstream(workstreams, workstreams[0].id) is workstreams[0]
    assert find_workstream(workstreams, "alpha").title == "alpha task"
    assert find_workstream(workstreams, "task") is None
