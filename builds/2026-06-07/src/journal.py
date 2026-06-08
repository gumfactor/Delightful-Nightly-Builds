"""Append standup runs to a JSONL journal file."""

import json
from datetime import datetime, timezone
from pathlib import Path


def append_entry(
    journal_path: str,
    commits_by_repo: dict[str, list[dict]],
    hours: int,
    formatted: str,
) -> None:
    """Write one standup run as a JSON line to the journal file.

    Creates the file and any parent directories if they don't exist.
    Each line is a self-contained JSON object — the file is valid JSONL.
    """
    path = Path(journal_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hours": hours,
        "commit_count": sum(len(c) for c in commits_by_repo.values()),
        "repos": {
            repo: [
                {
                    "hash": c["hash"],
                    "message": c["message"],
                    "source": c.get("source", "unknown"),
                }
                for c in commits
            ]
            for repo, commits in commits_by_repo.items()
            if commits
        },
        "formatted": formatted,
    }

    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
