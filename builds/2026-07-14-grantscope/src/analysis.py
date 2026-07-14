"""Aggregation and lightweight keyword extraction over locally stored NIH RePORTER projects.

Every function accepts a list of dict-like rows (a sqlite3.Row or a plain dict
both work since both support `row["field"]` access) so this module can be unit
tested against plain fixture dicts without touching the database.
"""

import re
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Sequence, Tuple

_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "will", "are", "was",
    "were", "has", "have", "had", "not", "but", "our", "their", "these",
    "those", "into", "which", "when", "than", "then", "also", "may", "can",
    "such", "its", "his", "her", "they", "them", "been", "being", "over",
    "more", "most", "some", "other", "each", "using", "used", "use", "study",
    "research", "project", "aim", "aims", "specific", "based", "provide",
    "provides", "including", "include", "among", "between", "within", "both",
    "how", "who", "what", "where", "while", "one", "two", "three", "however",
    "aim1", "aim2", "aim3",
}

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z\-]{2,}")


def funding_by_year(projects: Sequence[Any]) -> Dict[int, Dict[str, int]]:
    """Return {fiscal_year: {"total_amount": int, "count": int}} sorted is caller's job."""
    result: Dict[int, Dict[str, int]] = defaultdict(lambda: {"total_amount": 0, "count": 0})
    for project in projects:
        year = project["fiscal_year"]
        if year is None:
            continue
        amount = project["award_amount"] or 0
        result[year]["total_amount"] += amount
        result[year]["count"] += 1
    return dict(result)


def _rank_by_field(projects: Sequence[Any], field: str, top_n: int) -> List[Tuple[str, Dict[str, int]]]:
    grouped: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total_amount": 0, "count": 0})
    for project in projects:
        key = project[field]
        if not key:
            continue
        amount = project["award_amount"] or 0
        grouped[key]["total_amount"] += amount
        grouped[key]["count"] += 1
    ranked = sorted(grouped.items(), key=lambda item: item[1]["total_amount"], reverse=True)
    return ranked[:top_n]


def top_institutes(projects: Sequence[Any], top_n: int = 10) -> List[Tuple[str, Dict[str, int]]]:
    return _rank_by_field(projects, "ic_admin", top_n)


def top_organizations(projects: Sequence[Any], top_n: int = 10) -> List[Tuple[str, Dict[str, int]]]:
    return _rank_by_field(projects, "org_name", top_n)


def mechanism_breakdown(projects: Sequence[Any]) -> Dict[str, int]:
    counter: Counter = Counter()
    for project in projects:
        code = project["activity_code"]
        if code:
            counter[code] += 1
    return dict(counter.most_common())


def extract_keywords(projects: Sequence[Any], top_n: int = 15) -> List[Tuple[str, int]]:
    """Corpus-wide word-frequency scan over titles + abstracts, stopword-filtered."""
    counter: Counter = Counter()
    for project in projects:
        text = f"{project['title'] or ''} {project['abstract'] or ''}".lower()
        for word in _WORD_RE.findall(text):
            if word not in _STOPWORDS:
                counter[word] += 1
    return counter.most_common(top_n)


def summary_stats(projects: Sequence[Any]) -> Dict[str, Any]:
    """A compact set of headline numbers used by both the terminal `stats` command and the AI briefing prompt."""
    total_amount = sum((project["award_amount"] or 0) for project in projects)
    years = sorted({project["fiscal_year"] for project in projects if project["fiscal_year"] is not None})
    return {
        "project_count": len(projects),
        "total_amount": total_amount,
        "fiscal_year_range": (years[0], years[-1]) if years else (None, None),
        "distinct_institutes": len({project["ic_admin"] for project in projects if project["ic_admin"]}),
        "distinct_organizations": len({project["org_name"] for project in projects if project["org_name"]}),
    }
