"""Load standup configuration from a TOML file (Python 3.11+ tomllib)."""

import tomllib
from pathlib import Path
from typing import Any

_DEFAULTS: dict[str, Any] = {
    "github_username": "",
    "hours": 24,
    "format": "text",
    "journal_path": "~/.standup_journal.jsonl",
    "local_roots": [],
    "exclude_repos": [],
}


def load_config(config_path: str | Path) -> dict[str, Any]:
    """Return config dict merged with defaults. Missing file → all defaults."""
    path = Path(config_path).expanduser()
    config = dict(_DEFAULTS)
    if not path.exists():
        return config
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    config.update(raw.get("standup", {}))
    return config
