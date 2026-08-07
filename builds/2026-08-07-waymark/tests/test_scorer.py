"""Tests for the deterministic decision-worthiness scorer."""

from __future__ import annotations

from src import scorer


def _commit(**overrides):
    base = {
        "subject": "chore: bump version",
        "body": "",
        "files_changed": 1,
        "insertions": 1,
        "deletions": 1,
    }
    base.update(overrides)
    return base


def test_chore_commit_scores_low():
    score = scorer.score_commit(_commit(subject="chore: bump version"))
    assert score <= 2


def test_feat_commit_scores_higher_than_chore():
    feat_score = scorer.score_commit(_commit(subject="feat: add export to CSV"))
    chore_score = scorer.score_commit(_commit(subject="chore: bump version"))
    assert feat_score > chore_score


def test_breaking_change_marker_increases_score():
    normal = scorer.score_commit(_commit(subject="refactor: simplify parser"))
    breaking = scorer.score_commit(_commit(subject="refactor!: simplify parser"))
    assert breaking > normal


def test_decision_keywords_in_body_increase_score():
    plain = scorer.score_commit(_commit(subject="fix: adjust timeout", body=""))
    with_reasoning = scorer.score_commit(
        _commit(
            subject="fix: adjust timeout",
            body="We decided to increase the timeout because the downstream service is slow.",
        )
    )
    assert with_reasoning > plain


def test_large_diff_scores_higher_than_small_diff():
    small = scorer.score_commit(_commit(files_changed=1, insertions=2, deletions=1))
    large = scorer.score_commit(_commit(files_changed=15, insertions=400, deletions=120))
    assert large > small


def test_merge_commit_with_no_body_scores_zero():
    score = scorer.score_commit(_commit(subject="Merge branch 'main' into feature", body=""))
    assert score == 0


def test_merge_commit_with_substantive_body_is_not_forced_to_zero():
    score = scorer.score_commit(
        _commit(
            subject="Merge branch 'main' into feature",
            body="This merge resolves the conflicting approach to session storage; "
            "we chose the Redis-backed implementation over the in-memory one.",
        )
    )
    assert score > 0


def test_score_is_clamped_to_range_0_10():
    huge = scorer.score_commit(
        _commit(
            subject="security!: rewrite auth because of a critical vulnerability",
            body="We decided to switch to a workaround instead of the previous approach, "
            "rather than the old trade-off, in favor of a safer rollback plan. "
            "This is a breaking change.\n\nSecond paragraph with more detail about the root cause.",
            files_changed=50,
            insertions=2000,
            deletions=1000,
        )
    )
    assert 0 <= huge <= 10


def test_empty_body_and_subject_does_not_crash():
    score = scorer.score_commit({"subject": "", "body": "", "files_changed": 0, "insertions": 0, "deletions": 0})
    assert score >= 0


def test_extract_tags_includes_conventional_type():
    tags = scorer.extract_tags(_commit(subject="feat: add dashboard"))
    assert "feat" in tags


def test_extract_tags_includes_breaking_marker():
    tags = scorer.extract_tags(_commit(subject="feat!: change API shape"))
    assert "breaking" in tags


def test_extract_tags_includes_keyword_matches():
    tags = scorer.extract_tags(
        _commit(subject="fix: revert bad migration", body="Had to revert because the migration corrupted data.")
    )
    assert "revert" in tags


def test_extract_tags_has_no_duplicates():
    tags = scorer.extract_tags(
        _commit(subject="fix: revert revert revert", body="revert revert revert because because")
    )
    assert len(tags) == len(set(tags))


def test_deterministic_summary_includes_subject():
    commit = _commit(subject="feat: add CSV export", files_changed=3, insertions=40, deletions=5)
    summary = scorer.deterministic_summary(commit)
    assert "add CSV export" in summary


def test_deterministic_summary_handles_missing_subject():
    commit = {"subject": "", "body": "", "files_changed": 0, "insertions": 0, "deletions": 0}
    summary = scorer.deterministic_summary(commit)
    assert "(no subject)" in summary


def test_deterministic_summary_is_stable_for_same_input():
    commit = _commit(subject="fix: correct rounding error")
    assert scorer.deterministic_summary(commit) == scorer.deterministic_summary(commit)
