"""
Core profiling logic — type inference, column stats, file reading, text/JSON formatting.
All functions are pure (no I/O) except read_csv and read_json.
"""

import csv
import json
import statistics
import re
from collections import Counter
from pathlib import Path
from datetime import datetime


# Regex patterns for date/boolean detection
_DATE_PATTERNS = [
    re.compile(r"^\d{4}-\d{2}-\d{2}$"),                      # ISO 8601: 2024-01-15
    re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}"),        # ISO datetime
    re.compile(r"^\d{2}/\d{2}/\d{4}$"),                       # MM/DD/YYYY
    re.compile(r"^\d{2}-\d{2}-\d{4}$"),                       # MM-DD-YYYY
]
_BOOL_VALUES = {"true", "false", "yes", "no", "1", "0", "t", "f", "y", "n"}


def infer_type(values: list[str]) -> str:
    """
    Infer the dominant data type from a list of non-null string values.
    Returns one of: "integer", "float", "date", "boolean", "string".
    Uses majority vote — at least 80% of values must match to claim a type.
    """
    if not values:
        return "string"

    threshold = 0.8
    total = len(values)

    def pct(count: int) -> float:
        return count / total

    # Count how many values parse as each type
    int_count = 0
    float_count = 0
    date_count = 0
    bool_count = 0

    for v in values:
        stripped = v.strip()
        lower = stripped.lower()

        if lower in _BOOL_VALUES:
            bool_count += 1
            continue

        if any(pat.match(stripped) for pat in _DATE_PATTERNS):
            date_count += 1
            continue

        try:
            int(stripped)
            int_count += 1
            continue
        except ValueError:
            pass

        try:
            float(stripped)
            float_count += 1
            continue
        except ValueError:
            pass

    if pct(bool_count) >= threshold:
        return "boolean"
    if pct(date_count) >= threshold:
        return "date"
    if pct(int_count) >= threshold:
        return "integer"
    if pct(int_count + float_count) >= threshold:
        return "float"
    return "string"


def profile_column(
    name: str,
    values: list[str],
    top_n: int = 5,
    sample_n: int = 3,
) -> dict:
    """
    Build a statistical profile for a single column.

    values: all raw string values for the column (including empty strings as nulls).
    Returns a dict with type, null stats, unique count, sample, and type-specific stats.
    """
    total = len(values)

    # Treat empty string and whitespace-only as null
    nulls = [v for v in values if v.strip() == ""]
    non_null = [v for v in values if v.strip() != ""]
    null_count = len(nulls)
    null_pct = round(null_count / total * 100, 1) if total > 0 else 0.0

    col_type = infer_type(non_null)
    unique_count = len(set(v.strip() for v in non_null))

    # Build sample from non-null unique values (preserve first-seen order)
    seen = set()
    ordered_unique = []
    for v in non_null:
        s = v.strip()
        if s not in seen:
            seen.add(s)
            ordered_unique.append(s)
    sample = ordered_unique[:sample_n]

    result: dict = {
        "name": name,
        "type": col_type,
        "total": total,
        "null_count": null_count,
        "null_pct": null_pct,
        "unique_count": unique_count,
        "sample": sample,
    }

    # Numeric stats for integer and float columns
    if col_type in ("integer", "float") and non_null:
        try:
            nums = [float(v.strip()) for v in non_null]
            result["min"] = min(nums)
            result["max"] = max(nums)
            result["mean"] = round(statistics.mean(nums), 4)
            result["median"] = statistics.median(nums)
            result["std"] = round(statistics.stdev(nums), 4) if len(nums) > 1 else 0.0
        except (ValueError, statistics.StatisticsError):
            pass  # Fall through if unexpected mixed values

    # Top-values frequency table for low-cardinality columns
    # Show for string, boolean, date, and integer if unique count is small
    if unique_count <= 20 and non_null:
        counter = Counter(v.strip() for v in non_null)
        result["top_values"] = [
            {"value": val, "count": cnt}
            for val, cnt in counter.most_common(top_n)
        ]

    return result


def read_csv(path: str) -> tuple[list[str], list[list[str]]]:
    """
    Read a CSV file. Returns (header, rows) where rows is a list of string lists.
    Raises FileNotFoundError if path does not exist.
    Raises ValueError if the file is empty or has no columns.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")

    rows = []
    header = []
    with open(p, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError(f"File is empty: {path}")

        if not header:
            raise ValueError(f"CSV has no columns: {path}")

        for row in reader:
            # Pad short rows with empty strings to match header length
            padded = row + [""] * max(0, len(header) - len(row))
            rows.append(padded[: len(header)])

    return header, rows


def read_json(path: str) -> tuple[list[str], list[list[str]]]:
    """
    Read a JSON array or JSONL file.
    Returns (header, rows) in the same format as read_csv.
    Raises FileNotFoundError, ValueError on bad input.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")

    content = p.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"File is empty: {path}")

    records: list[dict] = []

    # Try JSON array first, then JSONL
    if content.startswith("["):
        try:
            data = json.loads(content)
            if not isinstance(data, list):
                raise ValueError(f"Expected a JSON array, got {type(data).__name__}: {path}")
            records = data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {path}: {e}")
    else:
        # JSONL: one JSON object per line
        for i, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    raise ValueError(f"Line {i} is not a JSON object in {path}")
                records.append(obj)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {i} of {path}: {e}")

    if not records:
        raise ValueError(f"No records found in {path}")

    # Collect all keys across records (preserve insertion order of first record)
    header = list(records[0].keys())
    for rec in records[1:]:
        for key in rec.keys():
            if key not in header:
                header.append(key)

    # Convert each record to a list of strings, using "" for missing/None
    rows = []
    for rec in records:
        row = []
        for key in header:
            val = rec.get(key)
            row.append("" if val is None else str(val))
        rows.append(row)

    return header, rows


def profile_file(
    path: str,
    top_n: int = 5,
    sample_n: int = 3,
) -> dict:
    """
    Profile an entire file. Returns a dict with file metadata and per-column profiles.
    Auto-detects format from file extension: .csv → CSV, .jsonl → JSONL, .json → JSON.
    """
    p = Path(path)
    ext = p.suffix.lower()

    if ext == ".csv":
        file_format = "CSV"
        header, rows = read_csv(path)
    elif ext == ".jsonl":
        file_format = "JSONL"
        header, rows = read_json(path)
    elif ext == ".json":
        file_format = "JSON"
        header, rows = read_json(path)
    else:
        raise ValueError(f"Unsupported file extension '{ext}'. Supported: .csv, .json, .jsonl")

    columns = []
    for i, col_name in enumerate(header):
        col_values = [row[i] if i < len(row) else "" for row in rows]
        col_profile = profile_column(col_name, col_values, top_n=top_n, sample_n=sample_n)
        columns.append(col_profile)

    return {
        "file": p.name,
        "format": file_format,
        "rows": len(rows),
        "columns": columns,
    }


def format_text(profile: dict) -> str:
    """Render a profile dict as a human-readable text report."""
    lines = []
    total_rows = profile["rows"]
    col_count = len(profile["columns"])

    lines.append(f"=== Data Profile: {profile['file']} ===")
    lines.append(
        f"Format: {profile['format']}  |  Rows: {total_rows:,}  |  Columns: {col_count}"
    )

    for idx, col in enumerate(profile["columns"], 1):
        lines.append("")
        lines.append(f"Column {idx}: \"{col['name']}\"")

        null_str = f"{col['null_count']:,} ({col['null_pct']}%)"
        lines.append(
            f"  Type: {col['type']}  |  Nulls: {null_str}  |  Unique: {col['unique_count']:,}"
        )

        if "min" in col:
            mean_str = f"{col['mean']:,.4f}".rstrip("0").rstrip(".")
            median_str = f"{col['median']:g}"
            std_str = f"{col['std']:,.4f}".rstrip("0").rstrip(".")
            lines.append(
                f"  Range: {col['min']:g}–{col['max']:g}"
                f"  |  Mean: {mean_str}"
                f"  |  Median: {median_str}"
                f"  |  Std: {std_str}"
            )

        if col["sample"]:
            sample_str = ", ".join(f'"{v}"' for v in col["sample"])
            lines.append(f"  Sample: {sample_str}")

        if "top_values" in col:
            top_str = "  |  ".join(
                f'"{tv["value"]}" ({tv["count"]:,})'
                for tv in col["top_values"]
            )
            lines.append(f"  Top values: {top_str}")

    return "\n".join(lines)


def format_json(profile: dict) -> str:
    """Render a profile dict as indented JSON."""
    return json.dumps(profile, indent=2)
