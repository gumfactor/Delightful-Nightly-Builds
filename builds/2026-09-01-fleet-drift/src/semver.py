"""From-scratch semantic-version parsing, comparison, and drift classification.

No third-party semver library is used — dependency version strings in the
wild are not always strict SemVer (PyPI in particular allows things like
``2.31.0`` right next to ``2.31``), so this module parses the leading
``major[.minor[.patch]]`` numeric run and treats anything after it as a
pre-release/build tag for ordering purposes only.
"""
from __future__ import annotations

import re
from typing import NamedTuple, Optional

_VERSION_RE = re.compile(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?(.*)$")


class Version(NamedTuple):
    major: int
    minor: int
    patch: int
    rest: str


def parse_version(raw: str) -> Optional[Version]:
    """Parse a version string into a comparable Version, or None if it
    doesn't start with a recognizable numeric version."""
    if not raw:
        return None
    raw = raw.strip()
    match = _VERSION_RE.match(raw)
    if not match:
        return None
    major, minor, patch, rest = match.groups()
    return Version(
        major=int(major),
        minor=int(minor) if minor is not None else 0,
        patch=int(patch) if patch is not None else 0,
        rest=rest.strip(),
    )


def compare(a: str, b: str) -> Optional[int]:
    """Return -1/0/1 for a<b, a==b, a>b, or None if either side fails to parse.

    Pre-release/build tags are ignored for ordering (only the numeric
    major.minor.patch run is compared) — this build never needs to rank two
    pre-releases of the same numeric version against each other, only to
    classify how far apart two pinned releases are.
    """
    va, vb = parse_version(a), parse_version(b)
    if va is None or vb is None:
        return None
    ta = (va.major, va.minor, va.patch)
    tb = (vb.major, vb.minor, vb.patch)
    if ta < tb:
        return -1
    if ta > tb:
        return 1
    return 0


def classify(a: str, b: str) -> str:
    """Classify how far apart two version strings are.

    Returns one of 'none', 'patch', 'minor', 'major', or 'unknown' if either
    side fails to parse. The classification is symmetric — it describes the
    *distance* between the two versions, not a direction.
    """
    va, vb = parse_version(a), parse_version(b)
    if va is None or vb is None:
        return "unknown"
    if va.major != vb.major:
        return "major"
    if va.minor != vb.minor:
        return "minor"
    if va.patch != vb.patch:
        return "patch"
    return "none"


SEVERITY_RANK = {"none": 0, "patch": 1, "minor": 2, "major": 3, "unknown": 0}


def max_severity(severities) -> str:
    """Pick the worst severity from an iterable, by SEVERITY_RANK."""
    worst = "none"
    for sev in severities:
        if SEVERITY_RANK.get(sev, 0) > SEVERITY_RANK.get(worst, 0):
            worst = sev
    return worst
