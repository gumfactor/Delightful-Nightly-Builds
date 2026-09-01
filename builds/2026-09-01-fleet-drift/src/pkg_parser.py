"""``package.json`` dependency-pin parser (npm ecosystem).

Reads ``dependencies`` and ``devDependencies`` (a name present in both wins
from ``dependencies``, matching normal npm convention that runtime deps take
precedence for reasoning about what actually ships). A leading range
operator (``^``, ``~``, ``>=``, ``<=``, ``>``, ``<``) is stripped to recover
the base pinned version and the entry is classified as a ``range`` pin
rather than an ``exact`` one.
"""
from __future__ import annotations

import json
from typing import List

from .req_parser import RequirementEntry
from .semver import parse_version

_RANGE_PREFIXES = ("^", "~", ">=", "<=", ">", "<")
_UNRESOLVABLE_SPECS = {"*", "latest", "", "next"}


def _classify_npm_spec(name: str, spec: str) -> RequirementEntry:
    spec = spec.strip()
    if spec in _UNRESOLVABLE_SPECS or spec.startswith(("file:", "link:", "workspace:", "git+", "http://", "https://")):
        return {"name": name, "pinned_version": None, "pin_kind": "unparseable"}

    prefix = ""
    rest = spec
    for candidate in _RANGE_PREFIXES:
        if rest.startswith(candidate):
            prefix = candidate
            rest = rest[len(candidate):].strip()
            break

    if parse_version(rest) is None:
        return {"name": name, "pinned_version": None, "pin_kind": "unparseable"}

    pin_kind = "range" if prefix else "exact"
    return {"name": name, "pinned_version": rest, "pin_kind": pin_kind}


def parse_package_json(text: str) -> List[RequirementEntry]:
    """Parse a package.json file's text into dependency-pin entries.

    Returns an empty list (never raises) on malformed JSON or an
    unexpected top-level shape — a single broken manifest in one repo
    should never abort a fleet-wide sync.
    """
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return []
    if not isinstance(data, dict):
        return []

    merged: dict = {}
    dev = data.get("devDependencies")
    direct = data.get("dependencies")
    if isinstance(dev, dict):
        merged.update(dev)
    if isinstance(direct, dict):
        merged.update(direct)

    entries: List[RequirementEntry] = []
    for name, spec in merged.items():
        if not isinstance(name, str) or not isinstance(spec, str):
            continue
        entries.append(_classify_npm_spec(name, spec))
    return entries
