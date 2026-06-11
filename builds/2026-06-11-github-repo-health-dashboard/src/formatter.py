"""Terminal table and JSON rendering for enriched repo dicts."""
import json


HEALTH_SYMBOLS = {
    "active": "●",
    "quiet": "◐",
    "stale": "○",
    "archived": "▪",
}


def _truncate(s: str, max_len: int) -> str:
    """Truncate string to max_len, appending ellipsis if trimmed."""
    if len(s) <= max_len:
        return s
    return s[:max_len - 1] + "…"


def format_table(repos: list[dict]) -> str:
    """
    Render enriched repos as a fixed-width terminal table.
    Returns a plain message string if the list is empty.
    """
    if not repos:
        return "No repositories found."

    name_width = max(len("Repository"), max(len(r["full_name"]) for r in repos))
    name_width = min(name_width, 45)

    lang_width = max(len("Language"), max(len(r["language"]) for r in repos))
    lang_width = min(lang_width, 14)

    header = (
        f"{'Repository':<{name_width}}  "
        f"{'Language':<{lang_width}}  "
        f"{'★':>4}  "
        f"{'Issues':>6}  "
        f"{'Days':>5}  "
        f"Health"
    )
    sep = "─" * len(header)

    lines = [header, sep]
    for repo in repos:
        name = _truncate(repo["full_name"], name_width)
        lang = _truncate(repo["language"], lang_width)
        days = repo["days_since_push"]
        days_str = "—" if days == 9999 else str(days)
        health = repo["health"]
        symbol = HEALTH_SYMBOLS.get(health, " ")

        lines.append(
            f"{name:<{name_width}}  "
            f"{lang:<{lang_width}}  "
            f"{repo['stars']:>4}  "
            f"{repo['open_issues']:>6}  "
            f"{days_str:>5}  "
            f"{symbol} {health}"
        )

    lines.append("")
    lines.append("Health: ● active (<30d)  ◐ quiet (30–90d)  ○ stale (>90d)  ▪ archived")
    lines.append("Note: Issues column includes open PRs (GitHub conflates issues and PRs in this count).")

    return "\n".join(lines)


def format_json(repos: list[dict]) -> str:
    """Render enriched repos as a JSON array with key fields only."""
    output = [
        {
            "name": r["name"],
            "full_name": r["full_name"],
            "language": r["language"],
            "stars": r["stars"],
            "open_issues": r["open_issues"],
            "days_since_push": r["days_since_push"],
            "health": r["health"],
            "archived": r["archived"],
            "private": r["private"],
            "url": r["html_url"],
        }
        for r in repos
    ]
    return json.dumps(output, indent=2)
