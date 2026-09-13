"""Deterministic trend analysis over a set of papers.

Everything here is pure arithmetic over paper publication dates and text —
no external calls, no AI, fully unit-testable and hand-verifiable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from arxiv_client import Paper

_WORD_RE = re.compile(r"[a-z][a-z\-]{2,}")

_STOPWORDS = frozenset(
    """
    the and for are with that this from into their they them then than have
    has had was were been being will would could should shall might must can
    may not but you your our its his her him she who what when where which
    how why all any both each few more most other some such only own same
    also using used use based upon between across over under above below
    however therefore thus while about between paper study results show
    shown showed shows across data analysis approach method methods result
    these those into onto within without during before after among per via
    each new one two three among across effect effects also there here
    """.split()
)

FLAT_SLOPE_RATIO = 0.05  # slope magnitude below this fraction of the mean count -> "flat"


@dataclass
class TrendBucket:
    period_label: str
    count: int


@dataclass
class TrendResult:
    buckets: list[TrendBucket]
    slope: float
    direction: str  # "rising" | "declining" | "flat"
    first_half_count: int
    second_half_count: int
    pct_change: Optional[float]  # None when first_half_count == 0


def _month_labels(months: int, now: date) -> list[str]:
    """Return `months` consecutive "YYYY-MM" labels ending with `now`'s month."""
    labels = []
    year, month = now.year, now.month
    for _ in range(months):
        labels.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(labels))


def bucket_by_month(papers: list[Paper], months: int, now: date) -> list[TrendBucket]:
    labels = _month_labels(months, now)
    counts = {label: 0 for label in labels}
    for paper in papers:
        label = f"{paper.published.year:04d}-{paper.published.month:02d}"
        if label in counts:
            counts[label] += 1
    return [TrendBucket(period_label=label, count=counts[label]) for label in labels]


def _least_squares_slope(counts: list[int]) -> float:
    n = len(counts)
    if n < 2:
        return 0.0
    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(counts) / n
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, counts))
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _classify_direction(slope: float, counts: list[int]) -> str:
    if len(counts) < 2:
        return "flat"
    mean_count = sum(counts) / len(counts)
    threshold = max(FLAT_SLOPE_RATIO * mean_count, 0.05)
    if abs(slope) < threshold:
        return "flat"
    return "rising" if slope > 0 else "declining"


def compute_trend(papers: list[Paper], months: int, now: Optional[date] = None) -> TrendResult:
    now = now or datetime.now(timezone.utc).date()
    buckets = bucket_by_month(papers, months, now)
    counts = [b.count for b in buckets]

    slope = _least_squares_slope(counts)
    direction = _classify_direction(slope, counts)

    half = len(counts) // 2
    first_half_count = sum(counts[:half]) if half > 0 else 0
    second_half_count = sum(counts[half:])

    if first_half_count == 0:
        pct_change = None
    else:
        pct_change = ((second_half_count - first_half_count) / first_half_count) * 100

    return TrendResult(
        buckets=buckets,
        slope=slope,
        direction=direction,
        first_half_count=first_half_count,
        second_half_count=second_half_count,
        pct_change=pct_change,
    )


def _terms_for_paper(paper: Paper) -> set[str]:
    text = f"{paper.title} {paper.abstract}".lower()
    return {w for w in _WORD_RE.findall(text) if w not in _STOPWORDS}


def rising_keywords(
    papers: list[Paper],
    months: int,
    now: Optional[date] = None,
    top_n: int = 8,
    min_support: int = 2,
) -> list[str]:
    """Terms whose per-paper mention count grew from the first half of the
    window to the second half, filtered to terms appearing in at least
    `min_support` papers overall."""
    now = now or datetime.now(timezone.utc).date()
    window_days = 30 * months
    cutoff = now - timedelta(days=window_days)
    midpoint = cutoff + (now - cutoff) / 2

    first_counts: dict[str, int] = {}
    second_counts: dict[str, int] = {}

    for paper in papers:
        if paper.published < cutoff:
            continue
        terms = _terms_for_paper(paper)
        bucket = second_counts if paper.published >= midpoint else first_counts
        for term in terms:
            bucket[term] = bucket.get(term, 0) + 1

    all_terms = set(first_counts) | set(second_counts)
    scored = []
    for term in all_terms:
        first_n = first_counts.get(term, 0)
        second_n = second_counts.get(term, 0)
        total = first_n + second_n
        if total < min_support:
            continue
        score = second_n - first_n
        if score <= 0:
            continue
        scored.append((score, second_n, term))

    scored.sort(key=lambda t: (-t[0], -t[1], t[2]))
    return [term for _, _, term in scored[:top_n]]
