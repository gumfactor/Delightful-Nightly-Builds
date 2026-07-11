"""Schema diff engine: compares two inferred schemas and classifies each
change as breaking, risky, or safe."""
from __future__ import annotations

from typing import Dict, List, Optional, Set

SEVERITY_ORDER = {"safe": 1, "risky": 2, "breaking": 3}


def _fmt_types(types: Set[str]) -> str:
    return "|".join(sorted(types)) if types else "none"


def _make_entry(field: str, change: str, severity: str, old, new, detail: str) -> dict:
    return {
        "field": field,
        "change": change,
        "severity": severity,
        "old": old,
        "new": new,
        "detail": detail,
    }


def diff_schemas(
    old: Dict[str, dict],
    new: Dict[str, dict],
    ignore_fields: Optional[Set[str]] = None,
    prefix: str = "",
) -> List[dict]:
    ignore_fields = ignore_fields or set()
    entries: List[dict] = []
    for field in sorted(set(old) | set(new)):
        full_path = f"{prefix}.{field}" if prefix else field
        if full_path in ignore_fields or field in ignore_fields:
            continue

        old_entry = old.get(field)
        new_entry = new.get(field)

        if old_entry is None:
            entries.append(
                _make_entry(
                    full_path, "added", "safe", None, _fmt_types(new_entry["types"]),
                    f"field added with type(s) {_fmt_types(new_entry['types'])}",
                )
            )
            continue
        if new_entry is None:
            entries.append(
                _make_entry(
                    full_path, "removed", "breaking", _fmt_types(old_entry["types"]), None,
                    f"field removed (was type(s) {_fmt_types(old_entry['types'])})",
                )
            )
            continue

        entries.extend(_diff_field(full_path, old_entry, new_entry))

        old_children = old_entry.get("children")
        new_children = new_entry.get("children")
        if old_children is not None and new_children is not None:
            entries.extend(diff_schemas(old_children, new_children, ignore_fields, prefix=full_path))
        elif old_children is not None and new_children is None:
            entries.append(
                _make_entry(
                    full_path, "type_changed", "breaking", "object/array-of-object",
                    _fmt_types(new_entry["types"]), "nested structure removed",
                )
            )
    return entries


def _diff_field(path: str, old_entry: dict, new_entry: dict) -> List[dict]:
    entries: List[dict] = []

    old_core = old_entry["types"] - {"null"}
    new_core = new_entry["types"] - {"null"}
    if old_core != new_core:
        severity = "safe" if old_core == {"int"} and new_core == {"float"} else "breaking"
        entries.append(
            _make_entry(
                path, "type_changed", severity, _fmt_types(old_core), _fmt_types(new_core),
                f"type changed from {_fmt_types(old_core)} to {_fmt_types(new_core)}",
            )
        )

    if old_entry["required"] and not new_entry["required"]:
        entries.append(
            _make_entry(
                path, "presence_changed", "risky", "required", "optional",
                "field became optional (was always present, now sometimes missing/null)",
            )
        )
    elif not old_entry["required"] and new_entry["required"]:
        entries.append(
            _make_entry(
                path, "presence_changed", "safe", "optional", "required",
                "field became required (was sometimes missing/null, now always present)",
            )
        )

    if old_entry.get("enum_candidate") and new_entry.get("enum_candidate"):
        old_values = old_entry.get("enum_values", set())
        new_values = new_entry.get("enum_values", set())
        for value in sorted(new_values - old_values):
            entries.append(
                _make_entry(
                    path, "enum_changed", "risky", None, value,
                    f"new enum value observed: '{value}'",
                )
            )
        for value in sorted(old_values - new_values):
            entries.append(
                _make_entry(
                    path, "enum_changed", "safe", value, None,
                    f"enum value no longer observed: '{value}'",
                )
            )

    return entries


def overall_severity(entries: List[dict]) -> Optional[str]:
    if not entries:
        return None
    return max(entries, key=lambda e: SEVERITY_ORDER[e["severity"]])["severity"]


def exceeds_threshold(entries: List[dict], threshold: str) -> bool:
    limit = SEVERITY_ORDER[threshold]
    return any(SEVERITY_ORDER[e["severity"]] >= limit for e in entries)
