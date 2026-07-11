"""Schema inference from JSON, JSONL, and CSV data files."""
from __future__ import annotations

import csv
import io
import json
import os
from collections import Counter
from typing import Any, Dict, List, Optional

ENUM_MAX_CARDINALITY = 15
ENUM_MIN_OCCURRENCES = 2


class SchemaInferenceError(Exception):
    """Raised when a data file cannot be parsed into records."""


def load_records(path: str) -> List[dict]:
    """Read a file from disk and parse it into a list of record dicts."""
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    return load_records_from_text(text, path)


def load_records_from_text(text: str, path_hint: str) -> List[dict]:
    """Parse already-loaded text into records, dispatching on path_hint's extension.

    Used both for on-disk files and for content read from `git show` at a past
    revision, which never touches the filesystem.
    """
    ext = os.path.splitext(path_hint)[1].lower()
    if ext == ".csv":
        return _load_csv(text)
    if ext == ".jsonl":
        return _load_jsonl(text)
    if ext == ".json":
        return _load_json(text)
    raise SchemaInferenceError(
        f"Unsupported file extension '{ext}' — expected .json, .jsonl, or .csv"
    )


def _load_json(text: str) -> List[dict]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SchemaInferenceError(f"Malformed JSON: {exc}") from exc
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    raise SchemaInferenceError(
        "Top-level JSON value must be an object or an array of objects"
    )


def _load_jsonl(text: str) -> List[dict]:
    records = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SchemaInferenceError(f"Malformed JSON on line {lineno}: {exc}") from exc
    return records


def _load_csv(text: str) -> List[dict]:
    reader = csv.DictReader(io.StringIO(text))
    records = []
    for row in reader:
        records.append({key: _coerce_csv_value(value) for key, value in row.items() if key is not None})
    return records


def _coerce_csv_value(value: Optional[str]) -> Any:
    if value is None or value == "":
        return None
    lowered = value.strip().lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return "unknown"


def infer_schema(records: List[dict]) -> Dict[str, dict]:
    """Infer a dotted-path schema from a list of record dicts.

    Each entry describes the observed type set, presence rate, whether the
    field is required (non-null in every record), enum-candidacy for
    low-cardinality string fields, and a recursive `children` schema for
    dict fields or list-of-dict fields.
    """
    total = len(records)
    field_stats: Dict[str, dict] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        for key, value in record.items():
            stats = field_stats.setdefault(
                key,
                {"types": set(), "count_present": 0, "values": Counter(), "children": []},
            )
            t = type_name(value)
            stats["types"].add(t)
            if t == "null":
                continue
            stats["count_present"] += 1
            if t == "str":
                stats["values"][value] += 1
            elif t == "dict":
                stats["children"].append(value)
            elif t == "list":
                for item in value:
                    if isinstance(item, dict):
                        stats["children"].append(item)

    schema: Dict[str, dict] = {}
    for field, stats in field_stats.items():
        presence_rate = (stats["count_present"] / total) if total else 0.0
        entry: dict = {
            "types": set(stats["types"]),
            "required": total > 0 and stats["count_present"] == total,
            "presence_rate": presence_rate,
        }
        core_types = stats["types"] - {"null"}
        is_enum_candidate = (
            core_types == {"str"}
            and stats["count_present"] >= ENUM_MIN_OCCURRENCES
            and len(stats["values"]) <= ENUM_MAX_CARDINALITY
        )
        entry["enum_candidate"] = is_enum_candidate
        if is_enum_candidate:
            entry["enum_values"] = set(stats["values"].keys())
        if stats["children"]:
            entry["children"] = infer_schema(stats["children"])
        schema[field] = entry
    return schema
