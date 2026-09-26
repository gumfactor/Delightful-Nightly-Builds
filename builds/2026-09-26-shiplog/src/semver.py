"""Semver bump suggestion from grouped commit sections."""
from __future__ import annotations

from classify import Commit


def suggest_bump(sections: dict[str, list[Commit]]) -> str:
    if sections.get("Breaking Changes"):
        return "major"
    if sections.get("Features"):
        return "minor"
    if sections.get("Fixes"):
        return "patch"
    return "none"
