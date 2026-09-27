import pytest

from matcher import jaccard_similarity, normalize_title, reconcile, summarize


def tw(title, completed=False):
    return {"id": "tw-1", "title": title, "completed": completed, "due_date": None,
            "project_id": 1, "url": "https://example.com/tw"}


def coda(title, is_done=False, status_text="Not Started"):
    return {"id": "c-1", "title": title, "status_text": status_text,
            "is_done": is_done, "url": "https://example.com/coda"}


def test_normalize_title_strips_punctuation_and_case():
    assert normalize_title("Q3 Report Draft!!") == normalize_title("q3 report draft")


def test_normalize_title_collapses_whitespace():
    assert normalize_title("Finish   the   report") == normalize_title("finish the report")


def test_jaccard_similarity_identical_sets_is_one():
    a = normalize_title("Renew certification")
    assert jaccard_similarity(a, a) == 1.0


def test_jaccard_similarity_disjoint_sets_is_zero():
    a = normalize_title("Renew certification")
    b = normalize_title("Order new cables")
    assert jaccard_similarity(a, b) == 0.0


def test_jaccard_similarity_empty_sets_is_zero():
    assert jaccard_similarity(frozenset(), frozenset()) == 0.0
    assert jaccard_similarity(frozenset(["x"]), frozenset()) == 0.0


def test_exact_title_match_is_matched_ok():
    results = reconcile([tw("Finish Q3 Report")], [coda("Finish Q3 Report")])
    assert len(results) == 1
    assert results[0].bucket == "matched_ok"


def test_near_identical_titles_match_above_threshold():
    results = reconcile([tw("Q3 Report Draft")], [coda("q3 report draft!!")])
    assert len(results) == 1
    assert results[0].bucket == "matched_ok"
    assert results[0].similarity == 1.0


def test_unrelated_titles_stay_unmatched():
    results = reconcile([tw("Order new cables")], [coda("Renew safety certification")])
    buckets = {r.bucket for r in results}
    assert buckets == {"teamwork_only", "coda_only"}


def test_below_threshold_similarity_is_rejected():
    # Shares only one token ("report") out of many -> similarity well under the 0.5 default.
    results = reconcile(
        [tw("Finish quarterly report")],
        [coda("Draft the annual budget report narrative")],
        threshold=0.5,
    )
    buckets = {r.bucket for r in results}
    assert buckets == {"teamwork_only", "coda_only"}


def test_matched_pair_with_agreeing_status_is_matched_ok():
    results = reconcile([tw("Close audit", completed=True)], [coda("Close audit", is_done=True)])
    assert results[0].bucket == "matched_ok"


def test_matched_pair_done_in_teamwork_not_coda_is_conflict():
    results = reconcile([tw("Close audit", completed=True)], [coda("Close audit", is_done=False)])
    assert results[0].bucket == "status_conflict"
    assert "done in Teamwork" in results[0].detail


def test_matched_pair_done_in_coda_not_teamwork_is_conflict():
    results = reconcile([tw("Close audit", completed=False)], [coda("Close audit", is_done=True)])
    assert results[0].bucket == "status_conflict"
    assert "done in Coda" in results[0].detail


def test_unmatched_teamwork_item_is_teamwork_only():
    results = reconcile([tw("Solo task")], [])
    assert len(results) == 1
    assert results[0].bucket == "teamwork_only"
    assert results[0].coda_item is None


def test_unmatched_coda_item_is_coda_only():
    results = reconcile([], [coda("Solo row")])
    assert len(results) == 1
    assert results[0].bucket == "coda_only"
    assert results[0].teamwork_item is None


def test_each_item_matched_at_most_once():
    # Two Teamwork items both resemble the same single Coda row title; only one can claim it.
    results = reconcile(
        [tw("Finish Q3 report"), tw("Finish Q3 report draft")],
        [coda("Finish Q3 report")],
    )
    matched = [r for r in results if r.bucket in ("matched_ok", "status_conflict")]
    assert len(matched) == 1
    unmatched = [r for r in results if r.bucket == "teamwork_only"]
    assert len(unmatched) == 1


def test_empty_input_on_both_sides_returns_empty_list():
    assert reconcile([], []) == []


def test_summarize_counts_all_four_buckets():
    results = reconcile(
        [tw("Match me"), tw("Lone teamwork task")],
        [coda("Match me"), coda("Lone coda row")],
    )
    counts = summarize(results)
    assert counts == {"matched_ok": 1, "status_conflict": 0, "teamwork_only": 1, "coda_only": 1}
