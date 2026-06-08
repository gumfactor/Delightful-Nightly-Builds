"""Format commit history as a standup report."""


def format_standup(
    commits_by_repo: dict[str, list[dict]],
    hours: int,
    format_type: str = "text",
) -> str:
    """Render a standup summary from a mapping of repo name → commit list.

    Commits with source='local_unpushed' are tagged with *(local)* to
    distinguish them from pushed commits. Repos are sorted alphabetically.
    Returns a plain 'nothing committed' message when there are no commits.
    """
    total = sum(len(commits) for commits in commits_by_repo.values())
    hour_label = "hour" if hours == 1 else "hours"

    if total == 0:
        return f"Nothing committed in the last {hours} {hour_label}.\n"

    lines: list[str] = []

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
                tag = " *(local)*" if commit.get("source") == "local_unpushed" else ""
                lines.append(f"- {commit['message']}  `{commit['hash']}`{tag}")
        else:
            lines.append(f"\n[{repo_name}]")
            for commit in commits:
                tag = " (local)" if commit.get("source") == "local_unpushed" else ""
                lines.append(f"  • {commit['message']}  ({commit['hash']}){tag}")

    lines.append("")
    return "\n".join(lines)
