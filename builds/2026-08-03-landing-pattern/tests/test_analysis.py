"""Tests for the pure readiness/overlap/ordering engine."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from landing_pattern import analysis

NOW = datetime(2026, 8, 3, 12, 0, 0, tzinfo=timezone.utc)


def make_pr(number, **overrides):
    base = {
        "number": number,
        "title": f"PR #{number}",
        "created_at": "2026-08-01T12:00:00Z",
        "draft": False,
        "mergeable_state": "clean",
        "ci_state": "success",
        "review_state": "none",
        "files": [],
    }
    base.update(overrides)
    return base


def test_classify_ready():
    pr = make_pr(1)
    assert analysis.classify_readiness(pr) == "ready"


def test_classify_draft_beats_everything_else():
    pr = make_pr(1, draft=True, mergeable_state="dirty", ci_state="failure")
    assert analysis.classify_readiness(pr) == "draft"


def test_classify_conflict():
    pr = make_pr(1, mergeable_state="dirty")
    assert analysis.classify_readiness(pr) == "conflict"


def test_classify_ci_failing():
    pr = make_pr(1, ci_state="failure")
    assert analysis.classify_readiness(pr) == "ci_failing"


def test_classify_ci_error_also_counts_as_failing():
    pr = make_pr(1, ci_state="error")
    assert analysis.classify_readiness(pr) == "ci_failing"


def test_classify_changes_requested():
    pr = make_pr(1, review_state="changes_requested")
    assert analysis.classify_readiness(pr) == "changes_requested"


def test_classify_ci_pending():
    pr = make_pr(1, ci_state="pending")
    assert analysis.classify_readiness(pr) == "ci_pending"


def test_classify_awaiting_review():
    pr = make_pr(1, review_state="review_required")
    assert analysis.classify_readiness(pr) == "awaiting_review"


def test_classify_behind_base():
    pr = make_pr(1, mergeable_state="behind")
    assert analysis.classify_readiness(pr) == "behind_base"


def test_classify_unknown_mergeable_state():
    pr = make_pr(1, mergeable_state="unknown")
    assert analysis.classify_readiness(pr) == "unknown"


def test_classify_approved_review_is_still_ready():
    pr = make_pr(1, review_state="approved")
    assert analysis.classify_readiness(pr) == "ready"


def test_age_days_computes_whole_days():
    assert analysis.age_days("2026-07-24T12:00:00Z", NOW) == 10


def test_age_days_never_negative():
    future = "2026-08-10T12:00:00Z"
    assert analysis.age_days(future, NOW) == 0


def test_overlap_graph_no_overlap():
    prs = [make_pr(1, files=["a.py"]), make_pr(2, files=["b.py"])]
    graph = analysis.build_overlap_graph(prs)
    assert graph[1] == {}
    assert graph[2] == {}


def test_overlap_graph_single_overlap():
    prs = [make_pr(1, files=["a.py", "b.py"]), make_pr(2, files=["b.py", "c.py"])]
    graph = analysis.build_overlap_graph(prs)
    assert graph[1] == {2: ["b.py"]}
    assert graph[2] == {1: ["b.py"]}


def test_overlap_graph_multiway():
    prs = [
        make_pr(1, files=["a.py"]),
        make_pr(2, files=["a.py"]),
        make_pr(3, files=["a.py"]),
    ]
    graph = analysis.build_overlap_graph(prs)
    assert set(graph[1].keys()) == {2, 3}
    assert set(graph[2].keys()) == {1, 3}
    assert set(graph[3].keys()) == {1, 2}


def test_overlap_graph_empty_files_no_crash():
    prs = [make_pr(1, files=[]), make_pr(2, files=[])]
    graph = analysis.build_overlap_graph(prs)
    assert graph == {1: {}, 2: {}}


def test_merge_order_batch1_only_when_no_overlaps():
    prs = [
        make_pr(1, files=["a.py"], created_at="2026-08-01T12:00:00Z"),
        make_pr(2, files=["b.py"], created_at="2026-08-02T12:00:00Z"),
    ]
    order = analysis.recommend_merge_order(prs, NOW)
    assert [p["number"] for p in order["batch1"]] == [1, 2]
    assert order["batch2"] == []


def test_merge_order_demotes_overlapping_pr_to_batch2():
    prs = [
        make_pr(1, files=["a.py"], created_at="2026-08-01T12:00:00Z"),
        make_pr(2, files=["a.py"], created_at="2026-08-02T12:00:00Z"),
    ]
    order = analysis.recommend_merge_order(prs, NOW)
    assert [p["number"] for p in order["batch1"]] == [1]
    assert len(order["batch2"]) == 1
    assert order["batch2"][0]["number"] == 2
    assert order["batch2"][0]["conflicts_with"] == [1]
    assert "age_days" in order["batch2"][0]


def test_merge_order_three_way_overlap_does_not_crash():
    prs = [
        make_pr(1, files=["a.py"], created_at="2026-08-01T12:00:00Z"),
        make_pr(2, files=["a.py"], created_at="2026-08-02T12:00:00Z"),
        make_pr(3, files=["a.py"], created_at="2026-08-03T12:00:00Z"),
    ]
    order = analysis.recommend_merge_order(prs, NOW)
    assert [p["number"] for p in order["batch1"]] == [1]
    assert {p["number"] for p in order["batch2"]} == {2, 3}


def test_blocked_sort_prioritizes_actionable_reasons():
    prs = [
        make_pr(1, mergeable_state="behind", created_at="2026-07-01T12:00:00Z"),
        make_pr(2, ci_state="failure", created_at="2026-08-01T12:00:00Z"),
        make_pr(3, review_state="changes_requested", created_at="2026-08-01T12:00:00Z"),
    ]
    order = analysis.recommend_merge_order(prs, NOW)
    labels_in_order = [p["label"] for p in order["blocked"]]
    assert labels_in_order == ["ci_failing", "changes_requested", "behind_base"]


def test_blocked_sort_ties_broken_by_age_oldest_first():
    prs = [
        make_pr(1, ci_state="failure", created_at="2026-08-01T12:00:00Z"),
        make_pr(2, ci_state="failure", created_at="2026-07-01T12:00:00Z"),
    ]
    order = analysis.recommend_merge_order(prs, NOW)
    assert [p["number"] for p in order["blocked"]] == [2, 1]


def test_drafts_excluded_from_batches_and_blocked():
    prs = [make_pr(1, draft=True)]
    order = analysis.recommend_merge_order(prs, NOW)
    assert order["batch1"] == []
    assert order["blocked"] == []
    assert [p["number"] for p in order["drafts"]] == [1]


def test_build_report_shape():
    prs = [make_pr(1)]
    result = analysis.build_report(prs, "owner/repo", NOW)
    assert result["repo"] == "owner/repo"
    assert result["synced_at"] == NOW.isoformat()
    assert len(result["prs"]) == 1
    assert result["prs"][0]["label"] == "ready"


def test_build_report_empty_pr_list():
    result = analysis.build_report([], "owner/repo", NOW)
    assert result["prs"] == []
    assert result["batch1"] == []
    assert result["blocked"] == []
