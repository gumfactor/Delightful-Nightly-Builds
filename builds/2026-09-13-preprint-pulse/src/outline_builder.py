"""Assembles the deterministic DigestOutline from trend + fact data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from arxiv_client import Paper
from fact_extractor import Fact, extract_facts
from trend_engine import TrendResult, compute_trend, rising_keywords

TOP_PAPERS_LIMIT = 8
NOTABLE_FACTS_LIMIT = 6
RISING_KEYWORDS_LIMIT = 8


@dataclass
class DigestOutline:
    topic: str
    window_months: int
    total_papers: int
    trend: TrendResult
    rising_keywords: list[str]
    top_papers: list[Paper]
    notable_facts: list[Fact]
    hook_stat: str
    generated_at: str


def _hook_stat(topic: str, trend: TrendResult, window_months: int, total_papers: int) -> str:
    if total_papers == 0:
        return f'No arXiv papers matched "{topic}" in the past {window_months} months.'

    if trend.pct_change is None:
        return (
            f'{total_papers} papers on "{topic}" appeared on arXiv over the past '
            f"{window_months} months, with activity concentrated in the second half "
            f"of the window ({trend.second_half_count} of {total_papers})."
        )

    direction_word = {
        "rising": "grew",
        "declining": "fell",
        "flat": "held roughly steady, changing",
    }[trend.direction]

    sign = "+" if trend.pct_change >= 0 else ""
    return (
        f'Papers on "{topic}" {direction_word} {sign}{trend.pct_change:.0f}% from the '
        f"first half to the second half of the past {window_months} months "
        f"({trend.first_half_count} → {trend.second_half_count} papers)."
    )


def build_outline(
    papers: list[Paper],
    topic: str,
    window_months: int,
    now: Optional[datetime] = None,
) -> DigestOutline:
    now = now or datetime.now(timezone.utc)
    trend = compute_trend(papers, window_months, now.date())
    keywords = rising_keywords(papers, window_months, now.date(), top_n=RISING_KEYWORDS_LIMIT)
    facts = extract_facts(papers)[:NOTABLE_FACTS_LIMIT]
    top_papers = sorted(papers, key=lambda p: p.published, reverse=True)[:TOP_PAPERS_LIMIT]

    return DigestOutline(
        topic=topic,
        window_months=window_months,
        total_papers=len(papers),
        trend=trend,
        rising_keywords=keywords,
        top_papers=top_papers,
        notable_facts=facts,
        hook_stat=_hook_stat(topic, trend, window_months, len(papers)),
        generated_at=now.isoformat(),
    )
