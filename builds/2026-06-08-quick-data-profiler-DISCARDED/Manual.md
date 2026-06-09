# Manual — Quick Data Profiler

> Profile any CSV or JSON/JSONL file in a single command. Outputs column types, null rates, distributions, and top frequencies.

---

## Requirements

- Python 3.10 or later (stdlib only — no pip install needed to run)
- pytest (for tests only): already available in this environment

---

## Quick Start

```bash
# From the builds/2026-06-08/ folder:
python3 main.py your_file.csv
python3 main.py your_file.json
python3 main.py your_file.jsonl
```

---

## Command Reference

```
python3 main.py <file> [--top N] [--sample N] [--format text|json]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `file` | *(required)* | Path to a `.csv`, `.json`, or `.jsonl` file |
| `--top N` | 5 | Top N most-frequent values to show for low-cardinality columns |
| `--sample N` | 3 | Number of sample values to show per column |
| `--format text\|json` | text | Output format: human-readable text or machine-parseable JSON |

---

## Example Output

### Text format (default)

```
=== Data Profile: businesses.csv ===
Format: CSV  |  Rows: 12,483  |  Columns: 6

Column 1: "business_name"
  Type: string  |  Nulls: 0 (0.0%)  |  Unique: 12,480
  Sample: "Maple Ridge Bakery", "Toronto Tech Co", "Pacific Coast Realty"

Column 2: "province"
  Type: string  |  Nulls: 12 (0.1%)  |  Unique: 13
  Sample: "ON", "QC", "BC"
  Top values: "ON" (4,102)  |  "QC" (2,981)  |  "BC" (1,834)  |  "AB" (1,440)  |  "MB" (721)

Column 3: "revenue_cad"
  Type: float  |  Nulls: 3,421 (27.4%)  |  Unique: 8,941
  Range: 0–9,847,221  |  Mean: 284,102.3  |  Median: 52,000  |  Std: 621,445.8
```

### JSON format (--format json)

```json
{
  "file": "businesses.csv",
  "format": "CSV",
  "rows": 12483,
  "columns": [
    {
      "name": "business_name",
      "type": "string",
      "total": 12483,
      "null_count": 0,
      "null_pct": 0.0,
      "unique_count": 12480,
      "sample": ["Maple Ridge Bakery", "Toronto Tech Co", "Pacific Coast Realty"]
    },
    ...
  ]
}
```

---

## Supported File Formats

| Extension | Format | Notes |
|-----------|--------|-------|
| `.csv` | Comma-separated values | UTF-8 or UTF-8-BOM; header row required |
| `.json` | JSON array | Array of objects at the top level |
| `.jsonl` | JSON Lines | One JSON object per line |

---

## Null Handling

- Empty strings (`""`) and whitespace-only values are counted as nulls
- JSON `null` values are treated as nulls
- Null rows are excluded from type inference and numeric stats, but included in counts

---

## Type Inference Rules

| Detected Type | Condition |
|---------------|-----------|
| `boolean` | ≥ 80% of values are: `true/false`, `yes/no`, `1/0`, `t/f`, `y/n` |
| `date` | ≥ 80% match ISO 8601 (`2024-01-15`), datetime (`2024-01-15T09:00`), or `MM/DD/YYYY` |
| `integer` | ≥ 80% parse as whole numbers |
| `float` | ≥ 80% parse as decimal numbers (integers also count) |
| `string` | Everything else |

---

## Running Tests

From the `builds/2026-06-08/` folder:

```bash
python3 -m pytest tests/ -v
```

Expected output: **37 tests passed, 0 failed**.

The test suite covers:
- Type inference for all 5 types + edge cases
- Null counting and whitespace detection
- Numeric stats (min, max, mean, median, std)
- Top-values frequency table
- CSV and JSON/JSONL file parsing
- Error handling (missing file, unsupported extension)
- Text and JSON formatters
