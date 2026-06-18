# Manual — Qualtrics Survey Data Inspector

## What It Does

Takes a Qualtrics CSV export and produces a research-quality data quality report. Covers the full pre-analysis checklist a careful researcher would run:

| Check | What it detects |
|-------|----------------|
| Completion | Responses with Progress < 100% |
| Timing | Fast responses below a configurable threshold |
| Straight-lining | Same answer given to every item in a scale |
| Duplicate IPs | Potential duplicate submissions |
| High missing (respondents) | Respondents who skipped > threshold of items |
| Missing data (columns) | Per-column missing rates with severity flags |
| Outliers | Z-score and IQR (Tukey fence) per numeric column |
| Floor/ceiling effects | > 80% of responses at the scale endpoint |
| Normality | D'Agostino–Pearson K² test per numeric column |
| Scale reliability | Cronbach's alpha + corrected item-total correlations |
| Correlation matrices | Pairwise complete-observations matrix per scale |
| Between-group tests | Mann-Whitney U (2 groups) or Kruskal-Wallis (3+) |
| Attention checks | Auto-detected or explicitly named; pass/fail per respondent |
| Careless responding | Composite 0–1 index from all signal sources |

Output: formatted text report to stdout, optional self-contained HTML report, optional Excel workbook (multi-sheet), and a filtered "clean" CSV with a `QI_Flags` column.

---

## Requirements

- Python 3.11+ (uses `tomllib` from the standard library)
- `openpyxl` — only for `--excel` output: `pip install openpyxl`
- No other dependencies

---

## Quick Start

```bash
# Text report to terminal
python3 main.py inspect my_survey.csv

# Text + HTML report
python3 main.py inspect my_survey.csv --html report.html

# Text + HTML + Excel
python3 main.py inspect my_survey.csv --html report.html --excel report.xlsx

# Clean CSV (removes incomplete, fast, and straight-lining respondents)
python3 main.py clean my_survey.csv --output cleaned.csv
```

---

## Config File (`qi.toml`)

If `qi.toml` exists in the current directory it is loaded automatically. CLI flags always override config values. Use `--config PATH` to specify a different file.

**Full example:**

```toml
# qi.toml — Qualtrics Data Inspector project config

[thresholds]
fast_response_seconds  = 90     # default: 60
missing_column_warn    = 0.05   # default: 0.05
missing_column_flag    = 0.20   # default: 0.20
missing_respondent_flag = 0.20  # default: 0.20
outlier_z              = 3.0    # default: 3.0
low_item_total_r       = 0.20   # default: 0.20

# Inline scale definitions — avoids needing a separate scales.json
[scales]
PSS10 = ["Q3_1","Q3_2","Q3_3","Q3_4","Q3_5","Q3_6","Q3_7","Q3_8","Q3_9","Q3_10"]
STAI  = ["Q4_1","Q4_2","Q4_3","Q4_4","Q4_5","Q4_6","Q4_7","Q4_8","Q4_9","Q4_10"]

# Attention check expected answers — avoids needing a separate answers.json
[attention]
Q_attn_check = "4"
Q_trap       = "Strongly Agree"

[inspect]
no_conditions = false   # set true to skip between-group tests

[clean]
keep_incomplete      = false
keep_fast            = false
keep_straight_liners = false
exclude_high_missing = false
```

Priority order for any setting: **CLI flag > qi.toml > built-in default**.

---

## Qualtrics CSV Format

The tool auto-detects Qualtrics exports from their 3-row header structure:

| Row | Contents |
|-----|----------|
| 0 | Column names (`ResponseId`, `Q1`, `Q2_1`, …) |
| 1 | Full question text for each column |
| 2 | ImportId values (`{"ImportId":"responseId"}`, …) |
| 3+ | Respondent data |

Standard single-header CSVs also work — the tool falls back automatically.

---

## `inspect` Subcommand

```
python3 main.py inspect FILE [options]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--html OUTPUT.html` | — | Write a self-contained HTML report |
| `--excel OUTPUT.xlsx` | — | Write a multi-sheet Excel workbook (needs openpyxl) |
| `--config qi.toml` | qi.toml | Config file path |
| `--threshold SECONDS` | 60 | Fast-response cutoff |
| `--scales SCALES.json` | auto | JSON mapping scale names to column lists |
| `--attention-answers ANSWERS.json` | — | JSON mapping column names to expected answers |
| `--no-conditions` | off | Skip condition/group auto-detection |
| `--missing-warn RATE` | 0.05 | Column missing rate for a warning flag |
| `--missing-flag RATE` | 0.20 | Column missing rate for a serious flag |
| `--missing-respondent RATE` | 0.20 | Per-respondent missing item rate flag |
| `--outlier-z THRESHOLD` | 3.0 | Z-score outlier threshold |
| `--low-r R` | 0.20 | Item-total correlation below which items are flagged |

### Report sections

1. **Overview** — respondent count, completion, fast/straight-liner/duplicate-IP/high-missing counts
2. **Timing** — mean, median, min, max, fast count
3. **Missing Data** — per-column bar chart with severity flags (·= ≥5%, != ≥20%)
4. **Straight-liners** — list of response IDs
5. **Duplicate IPs** — list of IP addresses
6. **Outliers** — z-score and IQR flag counts; multi-column outlier list
7. **Floor/Ceiling Effects** — columns where > 80% of responses are at the endpoint
8. **Normality** — D'Agostino–Pearson K² table; non-normal columns starred
9. **Scale Reliability** — Cronbach's α with quality label + corrected item-total r
10. **Correlation Matrices** — one matrix per detected scale
11. **Between-Group Tests** — Mann-Whitney U or Kruskal-Wallis p-values per scale
12. **Attention Checks** — pass rate and failed respondent IDs per check item
13. **Careless Responding Index** — composite score distribution and top scorers

---

## `clean` Subcommand

```
python3 main.py clean FILE [options]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--output FILE` / `-o` | stdout | Output CSV path |
| `--config qi.toml` | qi.toml | Config file path |
| `--threshold SECONDS` | 60 | Fast-response cutoff |
| `--scales SCALES.json` | auto | JSON mapping scale names to column lists |
| `--keep-incomplete` | off | Retain incomplete responses |
| `--keep-fast` | off | Retain fast responses |
| `--keep-straight-liners` | off | Retain straight-liners |
| `--exclude-high-missing` | off | Also remove high-missing respondents |
| `--missing-warn RATE` | 0.05 | Column missing rate warning threshold |
| `--missing-flag RATE` | 0.20 | Column missing rate serious threshold |
| `--missing-respondent RATE` | 0.20 | Per-respondent missing rate |
| `--outlier-z THRESHOLD` | 3.0 | Z-score outlier threshold |
| `--low-r R` | 0.20 | Item-total r flag threshold |

Produces a CSV with a `QI_Flags` column appended. Rows matching exclusion criteria are removed; remaining rows are flagged but retained.

**`QI_Flags` values:**

| Flag | Meaning |
|------|---------|
| `incomplete` | Progress < 100% |
| `fast_response` | Duration below threshold |
| `straight_liner` | Same response across all scale items |
| `duplicate_ip` | IP appears in multiple rows |
| `high_missing` | > threshold of items blank |

Multiple flags are pipe-separated: `fast_response|straight_liner`.

---

## Scale Groups

By default scales are auto-detected from column naming: `Q2_1`, `Q2_2`, `Q2_3` → scale `Q2`. Works for standard Qualtrics naming.

For custom scale names, provide them inline in `qi.toml` **or** via a separate JSON file:

```json
{
  "PSS10": ["Q3_1","Q3_2","Q3_3","Q3_4","Q3_5","Q3_6","Q3_7","Q3_8","Q3_9","Q3_10"],
  "STAI":  ["Q4_1","Q4_2","Q4_3","Q4_4","Q4_5","Q4_6","Q4_7","Q4_8","Q4_9","Q4_10"]
}
```

```bash
python3 main.py inspect data.csv --scales scales.json
```

---

## Attention Checks

Attention check columns are detected automatically if their name contains any of: `attn`, `attention`, `catch`, `check`, `manipulation`, `instructed`, `infreq`, `bot`, `trap`, `vigilance`.

Expected answers are extracted from the column's question text when the text matches patterns like "Please select '4'" or "Please choose 'Strongly Agree'". If auto-extraction fails, provide them explicitly:

In `qi.toml`:
```toml
[attention]
Q_attn_1 = "4"
Q_catch   = "Strongly Agree"
```

Or via JSON file:
```json
{ "Q_attn_1": "4", "Q_catch": "Strongly Agree" }
```

```bash
python3 main.py inspect data.csv --attention-answers answers.json
```

Comparison is case-insensitive and whitespace-stripped.

---

## Careless Responding Index

A composite 0–1 score per flagged respondent, averaged across up to five components:

| Component | Score | Condition |
|-----------|-------|-----------|
| `fast_response` | 1.0 | Below timing threshold |
| `straight_liner` | 1.0 | Same value across all scale items |
| `high_missing` | 1.0 | > threshold of items blank |
| `outlier_breadth` | min(1, n/3) | n = number of columns flagged as outlier |
| `attention_fail_rate` | n_failed / n_checks | Only if attention checks are scored |

Score of 0.0 = no flags. Score of 1.0 = fired every signal. The default flagging threshold is ≥ 0.40.

---

## Excel Export

Requires `pip install openpyxl`.

```bash
python3 main.py inspect data.csv --excel report.xlsx
```

Sheets produced:
- **Overview** — summary stats
- **Respondents** — per-respondent flag summary
- **Missing Data** — per-column missing rates
- **Scale Reliability** — Cronbach's α and item-total r
- **Normality** — K² statistics and p-values
- **Outliers** — z-score and IQR flags (if any)
- **Attention Checks** — pass rates and failed IDs (if any)
- **Careless Index** — composite scores and flags (if any)
- **Group Tests** — between-group p-values (if conditions detected)
- **Corr {scale}** — one correlation matrix sheet per scale

---

## Running Tests

```bash
python3 -m pytest tests/ -v
```

Expected: 220 tests, 0 failures.

---

## Interpreting Cronbach's Alpha

| α | Interpretation |
|---|---------------|
| ≥ 0.90 | Excellent |
| ≥ 0.80 | Good |
| ≥ 0.70 | Acceptable |
| ≥ 0.60 | Questionable |
| ≥ 0.50 | Poor |
| < 0.50 | Unacceptable |

Alpha uses listwise deletion: respondents with any missing item on a scale are excluded from that scale's calculation.

---

## Known Limitations

- Straight-lining detection requires ≥ 3 non-missing items per respondent
- Cronbach's alpha requires ≥ 2 respondents with complete data on a scale
- Normality test (D'Agostino–Pearson K²) requires n ≥ 8 per column
- IP duplicate detection is a heuristic — shared IPs (labs, VPNs) may be legitimate
- Between-group tests use non-parametric methods; parametric tests (t-test, ANOVA) not yet supported
- Reverse coding is not supported without user-specified item lists and scale range
- Excel export requires openpyxl (`pip install openpyxl`)
