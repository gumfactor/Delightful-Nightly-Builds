"""Format commit history as a standup report."""

from typing import Dict, List


def format_standup(
    commits_by_repo: Dict[str, List[dict]],
    hours: int,
    format_type: str = "text",
) -> str:
    """Render a standup summary from a mapping of repo name → commit list.

    Returns a formatted string. If all commit lists are empty, returns a message
    stating that nothing was committed in the given window. Repos are sorted
    alphabetically in the output. Empty repos within a non-empty dict are skipped.
    """
    total = sum(len(commits) for commits in commits_by_repo.values())
    hour_label = "hour" if hours == 1 else "hours"

    if total == 0:
        return f"Nothing committed in the last {hours} {hour_label}.\n"

    lines: List[str] = []

    if format_type == "markdown":
        lines.append(f"## Standup — last {hours} {hour_label}\n")
    else:
        lines.append(f"Standup — last {hours} {hour_label}")
        lines.append("=" * 40)

    for repo_name in sorted(commits_by_repo):
        commits = commits_by_repo[repo_name]
        if not commits:
            continue

        if format_type == "markdown":
            lines.append(f"\n### {repo_name}\n")
            for commit in commits:
                lines.append(f"- {commit['message']}  `{commit['hash']}`")
        else:
            lines.append(f"\n[{repo_name}]")
            for commit in commits:
                lines.append(f"  • {commit['message']}  ({commit['hash']})")

    lines.append("")
    return "\n".join(lines)
