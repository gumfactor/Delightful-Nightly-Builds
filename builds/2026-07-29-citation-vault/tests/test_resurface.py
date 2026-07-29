import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import resurface

NOW = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def ts(days_ago: int) -> str:
    return (NOW - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def paper(id, status, tags, days_ago=0, title=None):
    return {
        "id": id,
        "title": title or f"Paper {id}",
        "status": status,
        "tags": tags,
        "status_changed_at": ts(days_ago),
    }


def test_resurfaces_old_read_paper_sharing_tag():
    papers = [
        paper(1, "read", ["stress"], days_ago=90),
        paper(2, "to-read", ["stress"], days_ago=1),
    ]
    results = resurface.find_resurfacing_candidates(papers, days=60, now=NOW)
    assert len(results) == 1
    assert results[0]["paper"]["id"] == 1
    assert results[0]["matched_with"]["id"] == 2
    assert results[0]["shared_tags"] == ["stress"]


def test_does_not_resurface_recent_read_paper():
    papers = [
        paper(1, "read", ["stress"], days_ago=10),
        paper(2, "to-read", ["stress"], days_ago=1),
    ]
    results = resurface.find_resurfacing_candidates(papers, days=60, now=NOW)
    assert results == []


def test_does_not_resurface_without_shared_tag():
    papers = [
        paper(1, "read", ["stress"], days_ago=90),
        paper(2, "to-read", ["cortisol"], days_ago=1),
    ]
    results = resurface.find_resurfacing_candidates(papers, days=60, now=NOW)
    assert results == []


def test_does_not_resurface_to_read_paper_against_itself():
    # A to-read paper sharing a tag with another to-read paper should never
    # appear as a resurfacing candidate — only settled (read/cited) papers do.
    papers = [
        paper(1, "to-read", ["stress"], days_ago=90),
        paper(2, "to-read", ["stress"], days_ago=1),
    ]
    results = resurface.find_resurfacing_candidates(papers, days=60, now=NOW)
    assert results == []


def test_cited_paper_can_resurface():
    papers = [
        paper(1, "cited", ["empathy"], days_ago=100),
        paper(2, "reading", ["empathy"], days_ago=1),
    ]
    results = resurface.find_resurfacing_candidates(papers, days=60, now=NOW)
    assert len(results) == 1
    assert results[0]["paper"]["id"] == 1


def test_no_active_papers_means_no_candidates():
    papers = [paper(1, "read", ["stress"], days_ago=100)]
    results = resurface.find_resurfacing_candidates(papers, days=60, now=NOW)
    assert results == []


def test_boundary_exactly_at_cutoff_days_resurfaces():
    papers = [
        paper(1, "read", ["stress"], days_ago=60),
        paper(2, "to-read", ["stress"], days_ago=1),
    ]
    results = resurface.find_resurfacing_candidates(papers, days=60, now=NOW)
    assert len(results) == 1


def test_picks_match_with_most_shared_tags():
    papers = [
        paper(1, "read", ["stress", "cortisol", "empathy"], days_ago=90),
        paper(2, "to-read", ["stress"], days_ago=1),
        paper(3, "to-read", ["stress", "cortisol"], days_ago=1),
    ]
    results = resurface.find_resurfacing_candidates(papers, days=60, now=NOW)
    assert len(results) == 1
    assert results[0]["matched_with"]["id"] == 3
    assert set(results[0]["shared_tags"]) == {"stress", "cortisol"}


def test_results_sorted_oldest_first():
    papers = [
        paper(1, "read", ["x"], days_ago=70, title="Newer settled"),
        paper(2, "read", ["x"], days_ago=200, title="Older settled"),
        paper(3, "to-read", ["x"], days_ago=1),
    ]
    results = resurface.find_resurfacing_candidates(papers, days=60, now=NOW)
    assert [r["paper"]["title"] for r in results] == ["Older settled", "Newer settled"]
