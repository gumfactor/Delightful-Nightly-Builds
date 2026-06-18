# PRD — Qualtrics Survey Data Inspector

> **Build date:** 2026-06-17
> **Category:** F — Data Explorer
> **Complexity:** ambitious

---

## Goal

A Python CLI that ingests a Qualtrics CSV export and produces a research-quality data quality report — covering completion, timing, missing data, straight-lining, duplicate IPs, and Cronbach's alpha for detected scales.

## User Story

As a neuroscience lab director who runs Qualtrics surveys and must manually inspect every dataset before analysis, I want to run a single command on a raw CSV export and get a structured quality report (text + HTML) that flags problematic respondents and quantifies scale reliability, so that I can spend 2 minutes on QC instead of 30.

## Scope

### In Scope
- Auto-detection of Qualtrics 3-header-row format (column names / question text / ImportId)
- Graceful fallback to standard single-header CSV
- Completion rate (Progress == 100)
- Timing analysis: mean / median / min / max duration; fast-response flagging (< configurable threshold, default 60s)
- Per-column missing data rates
- Straight-lining detection: respondents who give the same answer across all items in a scale (≥ 3 items required)
- Duplicate IP address detection
- Cronbach's alpha for auto-detected scale groups (columns sharing a prefix like Q2_1, Q2_2, Q2_3)
- `inspect` subcommand: outputs text report to stdout; optionally writes HTML report to file
- `clean` subcommand: writes a filtered CSV with flagged respondents removed and a `QI_Flags` column added
- HTML report: self-contained, dark-themed, mobile-friendly; sections for overview, missing data table, response quality, scale reliability, timing

### Out of Scope
- GUI or web server
- Qualtrics API integration (no credentials needed — file-based only)
- Real-time monitoring
- Statistical significance tests beyond alpha
- Outlier detection (Mahalanobis distance) — deferred to FutureFeatures
- PDF export
- Batch processing of multiple files in one call

## Tech Stack

- **Language:** Python 3.10+
- **Framework:** None
- **Dependencies:** stdlib only (`csv`, `io`, `re`, `html`, `math`, `statistics`, `datetime`, `argparse`, `json`, `pathlib`, `dataclasses`, `typing`)
- **Test framework:** pytest
- **Runtime requirement:** `python3 main.py inspect survey.csv`

## Data Structure

### Qualtrics CSV Format
```
Row 0: Column names         (e.g. ResponseId, Progress, Duration (in seconds), Q1, Q2_1, Q2_2)
Row 1: Question text        (e.g. Response ID, Progress, ..., Rate your stress level:, Mood - Item 1, ...)
Row 2: ImportId values      (e.g. {"ImportId":"responseId"}, ..., {"ImportId":"QID1"}, ...)
Row 3+: Data rows
```

### Parsed Data Structures
```python
QualtricsColumn(name: str, question_text: str, import_id: Optional[str])
ParsedSurvey(columns: list[QualtricsColumn], rows: list[dict], is_qualtrics_format: bool, respondent_count: int)
QualityReport(respondent_count, completed_count, completion_rate, timing_stats,
              per_column_missing, straight_liner_ids, duplicate_ips,
              cronbach_results, fast_response_ids, timing_threshold_seconds, detected_scales)
```

### Scale Auto-Detection
Columns matching pattern `PREFIX_N` (where N is an integer) are grouped as a scale named `PREFIX`.
Example: `Q2_1, Q2_2, Q2_3` → scale `Q2`.

### Clean CSV Output
Original columns preserved. `QI_Flags` column appended: pipe-separated flag strings (`incomplete`, `fast_response`, `straight_liner`, `duplicate_ip`). Flagged rows can be excluded via CLI options.

## Folder Structure

```
builds/2026-06-17-qualtrics-data-inspector/
├── PRD.md                   ← This file
├── WhyThis.md               ← Decision rationale
├── BUILD_LOG.md             ← Session log
├── FutureFeatures.md        ← Post-build enhancements
├── Manual.md                ← Usage instructions
├── requirements.txt         ← Empty (stdlib only)
├── main.py                  ← CLI entry point (inspect / clean subcommands)
├── src/
│   ├── __init__.py          ← Package marker
│   ├── parser.py            ← CSV parsing; Qualtrics format detection
│   ├── quality.py           ← Quality metrics computation
│   └── report.py            ← Text report, HTML report, clean CSV export
└── tests/
    ├── test_parser.py       ← 12 tests
    ├── test_quality.py      ← 13 tests
    └── test_report.py       ← 10 tests
```

## Testing Strategy

All tests are unit tests using pytest. No file I/O or network calls in tests — CSV content is embedded as string constants. Tests cover:

- **parser.py**: Qualtrics format detection, column name / question text / ImportId parsing, missing value normalization, standard CSV fallback, edge cases (empty content)
- **quality.py**: Missing rate computation (0%, 50%, 100%), completion rate, timing stats (mean, median, fast count), straight-lining detection (positive and negative cases), Cronbach's alpha (perfect correlation, low correlation, edge cases), duplicate IP detection
- **report.py**: HTML structure (DOCTYPE, key sections present), XSS escaping of column names, text report content, clean CSV output (flag column, filtering)

Run: `python -m pytest tests/ -v`

## Success Criteria

1. All 35 tests pass with zero failures.
2. Running `python3 main.py inspect <file>` on a valid Qualtrics CSV produces a text report to stdout in under 2 seconds.
3. The `--html` flag writes a self-contained HTML report file with: respondent count, completion rate, timing stats, missing data per column, straight-liner count, duplicate IP list, and Cronbach's alpha for detected scales.
4. Running `python3 main.py clean <file>` writes a cleaned CSV with `QI_Flags` column added and flagged respondents removed.
5. The HTML report passes the security checklist: no user data in innerHTML, all strings escaped via `html.escape()`.
