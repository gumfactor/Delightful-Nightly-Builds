"""Data aggregation logic: commits + language data → analytics payload."""

from datetime import datetime, timezone
from typing import Any


def generate_month_labels(months_back: int) -> list[str]:
    """Return list of 'YYYY-MM' strings from months_back months ago to now."""
    now = datetime.now(timezone.utc)
    labels = []
    for delta in range(months_back - 1, -1, -1):
        year = now.year
        month = now.month - delta
        while month <= 0:
            month += 12
            year -= 1
        labels.append(f"{year:04d}-{month:02d}")
    return labels


def build_timeline_heatmap(
    commits_by_repo: dict[str, list[datetime]],
    months_back: int = 12,
    top_n: int = 15,
) -> dict[str, Any]:
    """
    Build matrix data for the project activity heatmap.

    Returns:
        {
            "months": [...],          # list of "YYYY-MM" strings
            "repos": [...],           # top_n repo names by total commits
            "data": [[int, ...]],     # data[repo_idx][month_idx] = count
            "max_val": int            # for colour scaling
        }
    """
    months = generate_month_labels(months_back)
    month_index = {m: i for i, m in enumerate(months)}

    # Rank repos by total commits within the window
    totals = {
        repo: len(dts) for repo, dts in commits_by_repo.items() if dts
    }
    top_repos = sorted(totals, key=lambda r: totals[r], reverse=True)[:top_n]

    data: list[list[int]] = []
    max_val = 0
    for repo in top_repos:
        row = [0] * len(months)
        for dt in commits_by_repo.get(repo, []):
            ym = f"{dt.year:04d}-{dt.month:02d}"
            if ym in month_index:
                row[month_index[ym]] += 1
        max_val = max(max_val, max(row, default=0))
        data.append(row)

    return {"months": months, "repos": top_repos, "data": data, "max_val": max_val}


def build_hour_heatmap(all_datetimes: list[datetime]) -> list[int]:
    """Return 24-element list of commit counts by UTC hour (0–23)."""
    counts = [0] * 24
    for dt in all_datetimes:
        counts[dt.hour] += 1
    return counts


def build_weekday_heatmap(all_datetimes: list[datetime]) -> list[int]:
    """Return 7-element list of commit counts by weekday (0=Mon, 6=Sun)."""
    counts = [0] * 7
    for dt in all_datetimes:
        counts[dt.weekday()] += 1
    return counts


def build_top_repos(
    commits_by_repo: dict[str, list[datetime]],
    top_n: int = 10,
) -> list[dict[str, Any]]:
    """Return top repos ranked by commit count."""
    ranked = sorted(
        commits_by_repo.items(),
        key=lambda item: len(item[1]),
        reverse=True,
    )
    return [{"name": repo, "commits": len(dts)} for repo, dts in ranked[:top_n]]


def build_language_chart(
    languages_by_repo: dict[str, dict[str, int]],
    top_repos_n: int = 10,
    top_langs_n: int = 8,
) -> dict[str, Any]:
    """
    Build stacked bar chart data for language usage by repo.

    Returns:
        {
            "repos": [...],    # up to top_repos_n repo names
            "langs": [...],    # up to top_langs_n language names
            "data": [[int]]    # data[repo_idx][lang_idx] = byte count
        }
    """
    # Sum bytes across all repos to find top languages globally
    lang_totals: dict[str, int] = {}
    for lang_map in languages_by_repo.values():
        for lang, count in lang_map.items():
            lang_totals[lang] = lang_totals.get(lang, 0) + count

    top_langs = sorted(lang_totals, key=lambda l: lang_totals[l], reverse=True)[:top_langs_n]

    # Only include repos that have any language data
    repos_with_data = [r for r, lm in languages_by_repo.items() if lm]
    # Sort by total bytes descending, take top N
    repos_sorted = sorted(
        repos_with_data,
        key=lambda r: sum(languages_by_repo[r].values()),
        reverse=True,
    )[:top_repos_n]

    data: list[list[int]] = []
    for repo in repos_sorted:
        lang_map = languages_by_repo.get(repo, {})
        row = [lang_map.get(lang, 0) for lang in top_langs]
        data.append(row)

    return {"repos": repos_sorted, "langs": top_langs, "data": data}


def aggregate(
    commits_by_repo: dict[str, list[datetime]],
    languages_by_repo: dict[str, dict[str, int]],
    months_back: int = 12,
    generated_at: str = "",
) -> dict[str, Any]:
    """Combine all analytics into the final payload for the HTML dashboard."""
    all_datetimes: list[datetime] = [
        dt for dts in commits_by_repo.values() for dt in dts
    ]
    total_commits = len(all_datetimes)
    active_repos = sum(1 for dts in commits_by_repo.values() if dts)

    top_repos = build_top_repos(commits_by_repo)
    most_active = top_repos[0]["name"] if top_repos else ""

    all_langs: dict[str, int] = {}
    for lm in languages_by_repo.values():
        for lang, count in lm.items():
            all_langs[lang] = all_langs.get(lang, 0) + count
    top_language = max(all_langs, key=lambda l: all_langs[l]) if all_langs else ""

    return {
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "total_commits": total_commits,
        "active_repos": active_repos,
        "most_active_repo": most_active,
        "top_language": top_language,
        "timeline": build_timeline_heatmap(commits_by_repo, months_back),
        "hour_counts": build_hour_heatmap(all_datetimes),
        "weekday_counts": build_weekday_heatmap(all_datetimes),
        "top_repos": top_repos,
        "languages": build_language_chart(languages_by_repo),
    }
