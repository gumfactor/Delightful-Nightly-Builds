"""``requirements.txt`` dependency-pin parser.

Deliberately narrow: this build's differentiating feature is the cross-repo
drift matrix, not exhaustive requirements-file support (dep-check, the
2026-06-19 build, already owns deep single-repo PyPI staleness auditing).
Lines this parser cannot meaningfully turn into a (name, version) pair are
either skipped outright (includes, editable installs, VCS/URL requirements —
none of which name a resolvable package version) or recorded with
``pin_kind='unparseable'`` when a package name is present but no exact
version is pinned.
"""
from __future__ import annotations

import re
from typing import List, Optional, TypedDict

_SKIP_PREFIXES = ("-r", "-e", "--", "git+", "http://", "https://")

_NAME_VERSION_RE = re.compile(
    r"^([A-Za-z0-9][A-Za-z0-9._-]*)"  # package name
    r"(?:\[[^\]]*\])?"  # optional extras, e.g. [security]
    r"\s*(==|>=|<=|~=|!=|>|<)?\s*"  # optional comparison operator
    r"([A-Za-z0-9_.\-+]*)$"  # optional version
)

_RANGE_OPS = {">=", "<=", "~=", "!=", ">", "<"}


class RequirementEntry(TypedDict):
    name: str
    pinned_version: Optional[str]
    pin_kind: str  # 'exact' | 'range' | 'unparseable'


def parse_requirements(text: str) -> List[RequirementEntry]:
    """Parse a requirements.txt file's text into dependency-pin entries."""
    entries: List[RequirementEntry] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(_SKIP_PREFIXES):
            continue
        # Strip an inline comment (a space followed by '#').
        line = re.split(r"\s+#", line, maxsplit=1)[0].strip()
        # Strip an environment marker (e.g. "; python_version >= '3.8'").
        line = line.split(";", 1)[0].strip()
        if not line:
            continue

        match = _NAME_VERSION_RE.match(line)
        if not match:
            continue

        name, op, version = match.groups()
        if op == "==" and version:
            entries.append({"name": name, "pinned_version": version, "pin_kind": "exact"})
        elif op in _RANGE_OPS and version:
            entries.append({"name": name, "pinned_version": version, "pin_kind": "range"})
        else:
            entries.append({"name": name, "pinned_version": None, "pin_kind": "unparseable"})
    return entries
