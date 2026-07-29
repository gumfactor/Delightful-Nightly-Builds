"""Tag-overlap + recency resurfacing logic.

A paper "resurfaces" if:
  - its status is read or cited (it's settled, not actively in progress)
  - its status_changed_at is at least `days` old
  - it shares at least one tag with some paper currently to-read or reading
"""

from datetime import datetime, timedelta, timezone

SETTLED_STATUSES = ("read", "cited")
ACTIVE_STATUSES = ("to-read", "reading")


def _parse_ts(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def find_resurfacing_candidates(papers: list, days: int = 60, now: datetime = None) -> list:
    """papers: list of paper dicts (see store.paper_to_dict). Returns a list of
    {"paper": dict, "matched_with": dict, "shared_tags": [str]} sorted by
    oldest status_changed_at first.
    """
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)

    active = [p for p in papers if p["status"] in ACTIVE_STATUSES]
    settled = [p for p in papers if p["status"] in SETTLED_STATUSES]

    results = []
    for old in settled:
        if _parse_ts(old["status_changed_at"]) > cutoff:
            continue
        best_match = None
        best_shared = []
        for new in active:
            shared = sorted(set(old["tags"]) & set(new["tags"]))
            if shared and len(shared) > len(best_shared):
                best_shared = shared
                best_match = new
        if best_match:
            results.append({"paper": old, "matched_with": best_match, "shared_tags": best_shared})

    results.sort(key=lambda r: r["paper"]["status_changed_at"])
    return results
