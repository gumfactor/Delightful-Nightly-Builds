# Manual — Qualtrics Survey Data Inspector

## What It Does

Takes a Qualtrics CSV export and produces a research-quality data quality report that flags problems a researcher should address before statistical analysis:

- Incomplete responses (Progress < 100%)
- Fast responses (below a configurable timing threshold)
- Straight-lining (same answer given to all items in a scale)
- Duplicate IP addresses (potential duplicate submissions)
- Per-column missing data rates
- Cronbach's alpha for automatically detected scale groups

Output: formatted text report to stdout, optional self-contained HTML report, and a filtered "clean" CSV with a QI_Flags column.

---

## Quick Start

```bash
# Text report to terminal
python3 main.py inspect my_survey.csv

# Text report + HTML file
python3 main.py inspect my_survey.csv --html report.html

# Clean CSV (removes incomplete, fast, and straight-lining respondents)
python3 main.py clean my_survey.csv --output cleaned.csv

# Keep incomplete respondents but still flag them
python3 main.py clean my_survey.csv --keep-incomplete --output cleaned.csv
```

---

## Qualtrics CSV Format

The tool auto-detects Qualtrics exports from their 3-row header structure:

| Row | Contents |
|-----|----------|
| 0 | Column names (`ResponseId`, `Q1`, `Q2_1`, etc.) |
| 1 | Full question text for each column |
| 2 | ImportId values (`{"ImportId":"responseId"}`, ...) |
| 3+ | Respondent data |

Standard single-header CSVs also work — the tool falls back to basic column-name parsing automatically.

---

## `inspect` Subcommand

```
python3 main.py inspect FILE [--html OUTPUT.html] [--threshold SECONDS] [--scales SCALES.json]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--html` | — | Write a self-contained HTML report to this path |
| `--threshold` | 60 | Flag responses shorter than this many seconds as fast |
| `--scales` | auto | JSON file mapping scale names to column lists (see below) |

**Example output:**
```
==============================================================
  QUALTRICS SURVEY DATA QUALITY REPORT
  Source : mystudydata.csv
  Generated: 2026-06-17 14:30 UTC
==============================================================

OVERVIEW
  Total respondents  : 147
  Completed (100%)   : 143  (97.3%)
  Fast responses     : 3  (< 60s)
  Straight-liners    : 2
  Duplicate IPs      : 1

TIMING (seconds)
  Mean   : 312.4
  Median : 289.0
  Min    : 24.0
  Max    : 1891.0
  Fast   : 3 respondents (< 60s)

MISSING DATA (columns with any missing)
  Q5                                   ███░░░░░░░░░░░░░░░░░ 12.9%

SCALE RELIABILITY (Cronbach's α)
  PSS10                  α = 0.872  [good]
  STAI                   α = 0.913  [excellent]
==============================================================
```

---

## `clean` Subcommand

```
python3 main.py clean FILE [--output OUTPUT.csv] [--threshold SECONDS]
                          [--keep-incomplete] [--keep-fast] [--keep-straight-liners]
```

Produces a CSV with a `QI_Flags` column appended. Flagged rows are removed unless the corresponding `--keep-*` flag is set.

**Flag values in `QI_Flags` column:**

| Flag | Meaning |
|------|---------|
| `incomplete` | Progress < 100% |
| `fast_response` | Duration below threshold |
| `straight_liner` | Same response across all scale items |
| `duplicate_ip` | IP address appears in multiple rows |

Multiple flags are pipe-separated: `fast_response|straight_liner`.

---

## Scale Groups (`--scales`)

By default, the inspector auto-detects scales from column naming patterns. Columns named `Q2_1`, `Q2_2`, `Q2_3` are grouped as scale `Q2`. This works well for default Qualtrics naming.

For custom scale names, provide a JSON file:

```json
{
  "PSS10": ["Q3_1", "Q3_2", "Q3_3", "Q3_4", "Q3_5", "Q3_6", "Q3_7", "Q3_8", "Q3_9", "Q3_10"],
  "STAI":  ["Q4_1", "Q4_2", "Q4_3", "Q4_4", "Q4_5"]
}
```

```bash
python3 main.py inspect data.csv --scales scales.json --html report.html
```

---

## Running Tests

```bash
python3 -m pytest tests/ -v
```

Expected: 61 tests, 0 failures.

---

## No Dependencies

The tool uses Python 3.10+ standard library only (`csv`, `html`, `argparse`, `json`, `re`, `math`, `pathlib`). No pip install required.

---

## Interpreting Cronbach's Alpha

| α value | Interpretation |
|---------|---------------|
| ≥ 0.90 | Excellent |
| ≥ 0.80 | Good |
| ≥ 0.70 | Acceptable |
| ≥ 0.60 | Questionable |
| ≥ 0.50 | Poor |
| < 0.50 | Unacceptable |

Alpha is computed using listwise deletion: respondents with any missing item in a scale are excluded from that scale's alpha calculation.

---

## Known Limitations

- Straight-lining detection requires a scale with ≥ 3 non-missing items per respondent
- Cronbach's alpha requires ≥ 2 respondents with complete data on the scale
- IP duplicate detection is a heuristic — shared IPs (lab computers, university networks, VPNs) may be legitimate
- Very large files (> 100,000 rows) may be slower due to pure-Python implementation; no functional limit exists
