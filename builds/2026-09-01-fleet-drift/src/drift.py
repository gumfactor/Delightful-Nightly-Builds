"""Cross-repo drift computation and per-repo staleness rollup.

This is the build's differentiating layer: dep-check (2026-06-19) already
audits one repo's dependencies against PyPI in isolation. This module
answers a question no single-repo audit can — which dependency is pinned to
*different* versions across the repos the user actually owns.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, TypedDict

from . import semver


class DriftEntry(TypedDict):
    ecosystem: str
    dependency: str
    repo_versions: Dict[str, str]
    severity: str
    min_version: str
    max_version: str


class StalenessEntry(TypedDict):
    repo: str
    ecosystem: str
    dependency: str
    pinned_version: Optional[str]
    latest_version: Optional[str]
    classification: str


def _version_sort_key(version: str):
    parsed = semver.parse_version(version)
    if parsed is None:
        return (float("inf"), float("inf"), float("inf"))
    return (parsed.major, parsed.minor, parsed.patch)


def compute_drift(snapshots: List[dict]) -> List[DriftEntry]:
    """Flag every dependency pinned to 2+ distinct versions across 2+ repos."""
    groups: Dict[tuple, Dict[str, str]] = defaultdict(dict)
    for snap in snapshots:
        pinned = snap.get("pinned_version")
        if not pinned:
            continue
        key = (snap["ecosystem"], snap["dependency"])
        groups[key][snap["repo"]] = pinned

    entries: List[DriftEntry] = []
    for (ecosystem, dependency), repo_versions in groups.items():
        distinct_versions = set(repo_versions.values())
        if len(repo_versions) < 2 or len(distinct_versions) < 2:
            continue
        sorted_versions = sorted(distinct_versions, key=_version_sort_key)
        severity = semver.classify(sorted_versions[0], sorted_versions[-1])
        entries.append(
            {
                "ecosystem": ecosystem,
                "dependency": dependency,
                "repo_versions": dict(repo_versions),
                "severity": severity,
                "min_version": sorted_versions[0],
                "max_version": sorted_versions[-1],
            }
        )

    entries.sort(key=lambda e: (-semver.SEVERITY_RANK.get(e["severity"], 0), e["dependency"]))
    return entries


def compute_staleness(snapshots: List[dict]) -> List[StalenessEntry]:
    """Classify each (repo, dependency) pin against its known latest version."""
    entries: List[StalenessEntry] = []
    for snap in snapshots:
        pinned = snap.get("pinned_version")
        latest = snap.get("latest_version")
        if not pinned or not latest:
            classification = "unknown"
        else:
            cmp_result = semver.compare(pinned, latest)
            if cmp_result is None:
                classification = "unknown"
            elif cmp_result == 0:
                classification = "current"
            else:
                sev = semver.classify(pinned, latest)
                classification = "current" if sev == "none" else f"{sev}-behind"
        entries.append(
            {
                "repo": snap["repo"],
                "ecosystem": snap["ecosystem"],
                "dependency": snap["dependency"],
                "pinned_version": pinned,
                "latest_version": latest,
                "classification": classification,
            }
        )
    return entries


def repo_staleness_summary(staleness_entries: List[StalenessEntry]) -> Dict[str, dict]:
    """Per-repo rollup: total dependencies tracked, how many are behind, and
    how many of those are major-version-behind."""
    summary: Dict[str, dict] = defaultdict(lambda: {"total": 0, "behind_count": 0, "major_count": 0})
    for entry in staleness_entries:
        repo_stats = summary[entry["repo"]]
        repo_stats["total"] += 1
        if entry["classification"].endswith("-behind"):
            repo_stats["behind_count"] += 1
            if entry["classification"] == "major-behind":
                repo_stats["major_count"] += 1
    return dict(summary)
