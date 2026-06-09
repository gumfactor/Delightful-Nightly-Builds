# Future Features — Quick Data Profiler

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **`--output FILE` flag** — Write the profile report to a file (`.txt` or `.json`) instead of stdout. Useful for saving profiles alongside source data files during QC runs.

2. **Column-name filtering (`--columns col1,col2`)** — Profile only the specified columns, skipping the rest. Useful for large CSVs with 50+ columns when you only care about a few fields.

3. **Duplicate row detection** — Add a global summary line: "X duplicate rows detected (Y%)." Uses a hash of all column values per row. Directly useful for Canada List deduplication QC.

4. **`--delimiter` flag for CSV** — Support tab-separated and pipe-separated files in addition to comma-separated. Many data exports use `\t` or `|` as the delimiter.

5. **Date range summary for date columns** — Instead of only showing sample values, show "Earliest: 2022-01-01 | Latest: 2024-12-31 | Span: 2 years, 11 months." More useful than raw samples for temporal data.

---

## Medium Effort (roughly one nightly build session)

6. **Anomaly flagging** — Highlight suspicious patterns automatically: columns where null rate suddenly exceeds 50%, columns with only one unique value, numeric columns where std > 3× mean, IDs with duplicate values. Print a `⚠ Warnings` section at the end of the text report. This is the core value-add for the Canada List QC use case.

7. **Multi-file comparison mode (`python3 main.py file1.csv file2.csv --diff`)** — Profile two files and highlight structural differences: columns present in one but not the other, type mismatches, significant changes in null rates or row counts. Useful for checking pipeline output consistency across ingestion runs.

---

## Ambitious Extensions (multi-session effort)

8. **HTML report output (`--format html`)** — A single self-contained HTML file with a visual column summary: type badges, null rate bar, histogram for numeric columns, frequency bar chart for categorical columns. Readable on mobile. Would make the profiler shareable and much more visually scannable.

9. **Schema inference and enforcement** — After profiling, export a `schema.json` that defines expected types, null tolerances, and value ranges. On subsequent runs, pass `--schema schema.json` to validate the new file against the expected schema and report any violations. Turns the profiler into a data contract enforcer — directly useful for the Canada List ingestion pipeline.

---

## Possible Integration Points

- **2026-06-07 Git Standup Reporter** — No direct integration, but both are Python CLI tools that could be packaged together into a personal dev toolkit.
- **Backlog Idea #1: Canada List CSV Quality Inspector** — This profiler is the foundation for that idea. The QC Inspector would add Canada-List-specific validation rules (required columns, province code validation, URL format checks) on top of the general profiling layer already built here.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Reads entire file into memory — will be slow on very large files (1M+ rows) | Stream-process rows for stats instead of loading all at once; track running min/max/mean using Welford's algorithm |
| Type inference uses 80% threshold — a column that's 79% integers and 21% strings is called "string" even if the non-integers are all data errors | Add a "mixed type" warning for columns just below threshold |
| Top-values table is not shown for high-cardinality numeric columns (> 20 unique) — can miss important integer IDs with duplicates | Add separate duplicate-ID detection logic that doesn't use the cardinality cutoff |
| No support for Excel (.xlsx) or Parquet files | Add openpyxl / pyarrow as optional deps with a try/import guard |
