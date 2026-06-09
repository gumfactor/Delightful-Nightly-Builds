# PRD — Quick Data Profiler

> **Build date:** 2026-06-08
> **Category:** F — Data Explorer
> **Complexity:** Focused Utility
> **Day of week:** Monday → Focused Utility

---

## Goal

A Python CLI that reads a CSV or JSON/JSONL file and outputs a column-by-column statistical profile: types, null rates, value ranges, distributions, and top frequencies — all in a single command.

## User Story

As a researcher and The Canada List operator who regularly receives raw CSV and JSON data files and needs to quickly understand their structure and quality, I want to run `python3 main.py mydata.csv` and immediately see column types, null counts, value distributions, and anomalies, so that I can make fast QC decisions without writing one-off pandas exploration code.

## Scope

### In Scope
- Accept one file path as input (CSV or JSON array / JSONL — auto-detected by extension)
- Detect column data types: integer, float, date, boolean, string
- Per-column output: inferred type, null count + %, unique value count, sample values
- Numeric columns add: min, max, mean, median, standard deviation
- Low-cardinality string/boolean columns (≤ 20 unique values): top-N frequency table
- Global summary: file format, total rows, total columns
- `--top N` flag: number of top values to show (default 5)
- `--sample N` flag: number of sample values to show (default 3)
- `--format text|json` flag: output as human-readable text (default) or JSON
- Graceful error handling: file not found, empty file, malformed CSV/JSON

### Out of Scope
- Writing output to a file (stdout only)
- Multi-file comparison or diffing
- Modifying, filtering, or transforming input data
- Pandas or any third-party data libraries
- Support for Excel, Parquet, or other binary formats
- Interactive TUI or web interface

## Tech Stack

- **Language:** Python 3.10+
- **Framework:** None
- **Dependencies:** stdlib only (`csv`, `json`, `statistics`, `datetime`, `argparse`, `pathlib`); `pytest` for tests
- **Runtime requirement:** `python3 main.py <path> [--top N] [--sample N] [--format text|json]`

## Data Structure

The profiler reads all rows into memory as lists of strings (from CSV) or converted to strings (from JSON). It builds a per-column `dict` structure:

```python
{
  "name": str,
  "type": "integer" | "float" | "date" | "boolean" | "string",
  "total": int,
  "null_count": int,
  "null_pct": float,
  "unique_count": int,
  "sample": list[str],
  # numeric only:
  "min": float,
  "max": float,
  "mean": float,
  "median": float,
  "std": float,
  # low-cardinality only:
  "top_values": list[{"value": str, "count": int}]
}
```

Global profile dict:
```python
{
  "file": str,
  "format": "CSV" | "JSON" | "JSONL",
  "rows": int,
  "columns": list[column_dict]
}
```

## Folder Structure

```
builds/2026-06-08/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── main.py                     ← CLI entry point (argparse, calls profiler)
├── requirements.txt            ← pytest only
├── src/
│   ├── __init__.py
│   └── profiler.py             ← Core logic: type inference, column profiling, file reading, formatting
└── tests/
    ├── test_profiler.py        ← Unit tests for type inference, column stats, file parsing
    └── fixtures/
        ├── sample.csv          ← Mixed-type CSV with nulls
        ├── sample.json         ← JSON array
        └── sample.jsonl        ← JSONL format
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_profiler.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - `infer_type()` correctly identifies integer, float, date, boolean, and string columns
  - `profile_column()` calculates null count/pct, unique count, and sample values correctly
  - `profile_column()` computes min/max/mean/median/std for numeric columns
  - `profile_column()` builds top-values frequency table for low-cardinality string columns
  - `profile_column()` handles a column of all nulls (no crash)
  - `read_csv()` parses the fixture CSV and returns correct header + row count
  - `read_json()` parses a JSON array and a JSONL file correctly
  - `format_text()` produces output containing column names and type labels
  - Edge case: column with a single distinct value
  - Edge case: column where every value is null

## Success Criteria

1. All tests pass (zero failures)
2. `python3 main.py tests/fixtures/sample.csv` produces a profile with correct column names, types, and row count without error
3. `python3 main.py tests/fixtures/sample.json --format json` produces valid JSON output that can be parsed back without error
4. `python3 main.py /nonexistent/file.csv` exits with a clear error message (non-zero exit code, no traceback)
5. Numeric columns show min, max, mean, median, and std; string columns with ≤ 20 unique values show a top-values frequency table

---

## Scope Changes

<!-- Leave this section blank. -->
