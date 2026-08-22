"""Urgency bucket classification, computed live from days-until-expiration."""

from __future__ import annotations

from typing import Optional

BUCKETS = ["Overdue", "Due This Week", "Due This Month", "Upcoming", "Healthy", "Unknown"]

# (upper_bound_inclusive, bucket_name) — evaluated in order; days_remaining is
# an int, or None for "Unknown" (no successful check / no data yet).
_THRESHOLDS = [
    (-1, "Overdue"),       # days_remaining <= -1
    (7, "Due This Week"),  # -1 < days_remaining <= 7
    (30, "Due This Month"),  # 7 < days_remaining <= 30
    (90, "Upcoming"),      # 30 < days_remaining <= 90
]


def classify(days_remaining: Optional[int]) -> str:
    """Classify a days-remaining count into an urgency bucket.

    Boundaries: <0 Overdue, 0-7 Due This Week, 8-30 Due This Month,
    31-90 Upcoming, >90 Healthy, None Unknown.
    """
    if days_remaining is None:
        return "Unknown"
    if days_remaining < 0:
        return "Overdue"
    if days_remaining <= 7:
        return "Due This Week"
    if days_remaining <= 30:
        return "Due This Month"
    if days_remaining <= 90:
        return "Upcoming"
    return "Healthy"


def bucket_sort_key(bucket: str) -> int:
    order = {name: i for i, name in enumerate(BUCKETS)}
    return order.get(bucket, len(BUCKETS))
