"""Merge and deduplicate commits from GitHub and local git sources."""


def merge_commits(
    github_by_repo: dict[str, list[dict]],
    local_by_repo: dict[str, list[dict]],
) -> dict[str, list[dict]]:
    """Combine GitHub and local-unpushed commits, deduplicating by full SHA.

    GitHub commits take precedence. A local commit whose full SHA already
    appears in the GitHub set is dropped — it was pushed and is already
    represented. Repos with no commits in either source are omitted.
    """
    pushed_shas: set[str] = set()
    for commits in github_by_repo.values():
        for c in commits:
            if c.get("sha"):
                pushed_shas.add(c["sha"])

    merged: dict[str, list[dict]] = {}

    for repo, commits in github_by_repo.items():
        if commits:
            merged.setdefault(repo, []).extend(commits)

    for repo, commits in local_by_repo.items():
        for c in commits:
            if c.get("sha") not in pushed_shas:
                merged.setdefault(repo, []).append(c)

    return merged
