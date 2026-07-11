from datetime import date

import pipeline_stats as ps


def make_record(date_str, category="A", complexity="ambitious", title="T", status="complete", rating=None):
    return {
        "date": date_str,
        "category": category,
        "complexity": complexity,
        "title": title,
        "description": "d",
        "tech": "Python",
        "status": status,
        "rating": rating,
        "notes": "",
    }


def test_reconcile_marks_folder_on_default_branch_as_merged():
    records = [make_record("2026-06-06", title="Merged Build")]
    statuses = ps.reconcile(
        records,
        folders_on_default_branch={"2026-06-06-merged-build"},
        folder_branch_map={},
        today=date(2026, 7, 9),
    )
    assert statuses[0]["merged"] is True
    assert statuses[0]["branch"] is None
    assert statuses[0]["backlog_days"] is None


def test_reconcile_marks_folder_in_branch_map_as_backlog_with_age():
    records = [make_record("2026-07-01", title="Stuck Build")]
    statuses = ps.reconcile(
        records,
        folders_on_default_branch=set(),
        folder_branch_map={"2026-07-01-stuck-build": "origin/claude/xyz"},
        today=date(2026, 7, 9),
    )
    assert statuses[0]["merged"] is False
    assert statuses[0]["branch"] == "origin/claude/xyz"
    assert statuses[0]["backlog_days"] == 8


def test_reconcile_no_matching_folder_anywhere():
    records = [make_record("2026-07-01", title="Untracked")]
    statuses = ps.reconcile(records, set(), {}, today=date(2026, 7, 9))
    assert statuses[0]["merged"] is False
    assert statuses[0]["folder"] is None
    assert statuses[0]["branch"] is None


def test_summarize_counts_and_percentages():
    statuses = ps.reconcile(
        [make_record("2026-06-06"), make_record("2026-07-01")],
        folders_on_default_branch={"2026-06-06-t"},
        folder_branch_map={"2026-07-01-t": "origin/b"},
        today=date(2026, 7, 9),
    )
    summary = ps.summarize(statuses)
    assert summary["total"] == 2
    assert summary["merged_count"] == 1
    assert summary["backlog_count"] == 1
    assert summary["merged_pct"] == 50.0
    assert summary["backlog_pct"] == 50.0


def test_summarize_oldest_unmerged_is_the_largest_backlog_days():
    statuses = ps.reconcile(
        [make_record("2026-07-01", title="Older"), make_record("2026-07-05", title="Newer")],
        folders_on_default_branch=set(),
        folder_branch_map={"2026-07-01-older": "origin/a", "2026-07-05-newer": "origin/b"},
        today=date(2026, 7, 9),
    )
    summary = ps.summarize(statuses)
    assert summary["oldest_unmerged"]["title"] == "Older"


def test_summarize_rating_coverage_ignores_none_ratings():
    statuses = ps.reconcile(
        [make_record("2026-06-06", rating=8), make_record("2026-06-07", rating=None)],
        folders_on_default_branch={"2026-06-06-t", "2026-06-07-t"},
        folder_branch_map={},
        today=date(2026, 7, 9),
    )
    summary = ps.summarize(statuses)
    assert summary["rated_count"] == 1
    assert summary["rating_coverage_pct"] == 50.0
    assert summary["average_rating"] == 8.0


def test_summarize_distributions_tally_correctly():
    statuses = ps.reconcile(
        [
            make_record("2026-06-06", category="A", complexity="focused"),
            make_record("2026-06-07", category="A", complexity="ambitious"),
            make_record("2026-06-08", category="B", complexity="ambitious", status="discarded"),
        ],
        folders_on_default_branch={"2026-06-06-t", "2026-06-07-t", "2026-06-08-t"},
        folder_branch_map={},
        today=date(2026, 7, 9),
    )
    summary = ps.summarize(statuses)
    assert summary["category_distribution"] == {"A": 2, "B": 1}
    assert summary["complexity_distribution"] == {"focused": 1, "ambitious": 2}
    assert summary["status_distribution"] == {"complete": 2, "discarded": 1}


def test_summarize_empty_catalog_does_not_crash():
    summary = ps.summarize([])
    assert summary["total"] == 0
    assert summary["merged_pct"] == 0.0
    assert summary["backlog_pct"] == 0.0
    assert summary["average_rating"] is None
    assert summary["oldest_unmerged"] is None


def test_summarize_excludes_discarded_and_aborted_from_backlog():
    statuses = ps.reconcile(
        [
            make_record("2026-06-09", title="Discarded Experiment", status="discarded"),
            make_record("2026-06-10", title="Aborted Attempt", status="aborted"),
            make_record("2026-06-11", title="Real Backlog Item", status="complete"),
        ],
        folders_on_default_branch=set(),
        folder_branch_map={"2026-06-11-real-backlog-item": "origin/b"},
        today=date(2026, 7, 9),
    )
    summary = ps.summarize(statuses)
    assert summary["backlog_count"] == 1
    assert summary["oldest_unmerged"]["title"] == "Real Backlog Item"
    titles_in_attention = {s["title"] for s in summary["needs_attention"]}
    assert "Discarded Experiment" not in titles_in_attention
    assert "Aborted Attempt" not in titles_in_attention
    # still counted in totals and status distribution even though excluded from backlog
    assert summary["total"] == 3
    assert summary["status_distribution"]["discarded"] == 1


def test_summarize_needs_attention_respects_limit_and_ordering():
    records = [make_record(f"2026-06-{d:02d}", title=f"B{d}") for d in range(1, 5)]
    folder_map = {f"2026-06-{d:02d}-b{d}": f"origin/b{d}" for d in range(1, 5)}
    statuses = ps.reconcile(records, set(), folder_map, today=date(2026, 7, 9))
    summary = ps.summarize(statuses, attention_limit=2)
    assert len(summary["needs_attention"]) == 2
    assert summary["needs_attention"][0]["title"] == "B1"
