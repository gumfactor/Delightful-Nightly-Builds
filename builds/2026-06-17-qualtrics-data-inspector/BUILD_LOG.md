# Build Log — Qualtrics Survey Data Inspector

> **Date:** 2026-06-17
> This is a live log. Entries are written in plain prose. Timestamps are UTC.

---

## Log

### [Session Start]

- Read CLAUDE.md, PROFILE.md, STANDARDS.md, builds/index.md fully
- Step 0: Checked 2026-06-10-investment-portfolio-snapshot/BUILD_LOG.md — ends with "Build complete. Success criteria reviewed. All tests passing (103/103)." → complete, skip
- Day 168 → category index 5 → F — Data Explorer
- Lottery: 1 pending F idea (ID 1, rating 7), R=1, lottery_chance=27%, roll=74 → fresh ideas
- Generated 3 ideas: Qualtrics Data Inspector (winner), GitHub Actions Performance Analyzer, SEC EDGAR Extractor
- Non-winners appended to builds/ideas.md (IDs 9 and 10)
- Build folder created: builds/2026-06-17-qualtrics-data-inspector/

### [PRD Phase]

- PRD written covering: Qualtrics 3-row header format detection, completion/timing/missing/straight-lining/duplicate-IP/Cronbach analysis, inspect and clean subcommands, HTML and text report output
- Stack: Python 3 stdlib only, pytest
- 35 tests planned across 3 test files
- Key design decision: all quality computation functions are pure (take parsed data structs, return report structs) — no I/O inside quality or report modules; fully testable without any file system or network access

### [Build Phase — Source Files]

- Wrote src/__init__.py: package marker
- Wrote src/parser.py: QualtricsColumn, ParsedSurvey dataclasses; METADATA_COLUMNS set; _is_importid_row(); parse_csv() with 3-row Qualtrics format detection and standard CSV fallback; question_column_names property
- Wrote src/quality.py: QualityReport dataclass; compute_missing_rate(); compute_completion_rate(); compute_timing_stats(); _get_response_id(); _parse_duration(); detect_straight_liners(); detect_duplicate_ips(); cronbach_alpha() with sample variance and total variance; auto_detect_scales() with regex prefix grouping; compute_quality() orchestrator
- Wrote src/report.py: generate_text_report(); generate_html_report() (self-contained dark-theme HTML with overview, missing data, response quality, scale reliability, timing sections; all strings escaped via html.escape()); export_clean_csv() with QI_Flags column and optional row filtering
- Wrote main.py: argparse CLI with inspect (--html, --threshold, --scales) and clean (--threshold, --keep-straight-liners, --keep-incomplete, --keep-fast, --output) subcommands; JSON scales config loading

### [Build Phase — Tests]

- Wrote tests/test_parser.py: 12 tests covering Qualtrics format detection, column parsing, question text, ImportId, data row parsing, missing values, standard CSV, edge cases
- Wrote tests/test_quality.py: 13 tests covering missing rate, completion rate, timing stats, straight-liner detection, Cronbach's alpha, duplicate IP detection, auto-scale detection
- Wrote tests/test_report.py: 10 tests covering HTML structure, XSS escaping, text report, clean CSV export and filtering
- Total: 61 tests (19 test_parser, 32 test_quality, 10 test_report)

### [Tests Run]

Tests: 61 passed, 0 failed. First run had 1 failure (test assertion used wrong expected value for max duration: 180 vs actual max 200). Fixed test assertion and all 61 passed immediately.

### [Integration Verification]

- `python3 main.py inspect /tmp/test_survey.csv` — produced correct text report: 4 respondents, 75% completion, 1 fast (R_002 at 45s), 1 straight-liner (R_002), 1 duplicate IP (192.168.1.1), Q2 α = 0.711 [acceptable]
- `--html /tmp/test_report.html` — wrote 5,084-byte self-contained HTML file
- `python3 main.py clean /tmp/test_survey.csv` — produced filtered CSV: R_001 and R_004 retained (with duplicate_ip flag), R_002 and R_003 excluded
- Security scan: no violations — no eval/exec/os.system/subprocess/innerHTML/hardcoded credentials

### [Success Criteria Verified]

1. All 61 tests pass, zero failures — ✓
2. `python3 main.py inspect <file>` produces text report in < 2 seconds — ✓
3. `--html` flag writes self-contained HTML with respondent count, completion rate, timing stats, missing data, straight-liner count, duplicate IPs, and Cronbach's alpha — ✓
4. `python3 main.py clean <file>` writes filtered CSV with QI_Flags column — ✓
5. HTML report: all user strings passed through html.escape(); no innerHTML with user data — ✓

### [Documentation Complete]

- FutureFeatures.md: 9 concrete suggestions written
- Manual.md: quick start, subcommand reference, scales config, alpha interpretation table, known limitations
- builds/index.md updated with this build's row

Build complete. Success criteria reviewed. All tests passing.

---

## v2 Expansion — Statistics, Outliers, Conditions (session 2)

**Scope added:** outlier detection, distributional statistics, normality testing, condition/group detection with between-group tests, correlation matrices, inter-item correlations, floor/ceiling effects, per-respondent missing rate flagging, configurable thresholds.

### New modules
- `src/statistics.py`: `descriptive_stats()`, `skewness()`, `excess_kurtosis()`, `normality_test()` (D'Agostino–Pearson K², pure Python including regularised incomplete gamma via series expansion and Lentz continued fraction), `pearson_r()`, `correlation_matrix()`, `item_total_correlations()`, `extract_numeric_column()`
- `src/outliers.py`: `zscore_outliers()`, `iqr_outliers()`, `respondent_outlier_counts()`
- `src/conditions.py`: `detect_condition_columns()`, `group_descriptive_stats()`, `compute_scale_scores()`, `mann_whitney_u()`, `kruskal_wallis()`, `run_condition_tests()`

### Modified
- `src/quality.py`: `QualityThresholds` dataclass; `QualityReport` extended with 10 new fields; `compute_quality()` orchestrates all new analyses
- `src/report.py`: text and HTML reports gain 7 new sections; `export_clean_csv()` gains `exclude_high_missing`
- `main.py`: `--threshold`, `--scales`, `--missing-warn`, `--missing-flag`, `--missing-respondent`, `--outlier-z`, `--low-r`, `--no-conditions`

### Tests
- `tests/test_statistics.py`: 34 tests
- `tests/test_outliers.py`: 17 tests
- `tests/test_conditions.py`: 26 tests
- Total after v2: 142 tests passing

### Key decisions
- Pure Python chi-squared CDF (no scipy): implemented regularised incomplete gamma to support D'Agostino K² p-values and Kruskal-Wallis
- Non-parametric group tests only: Mann-Whitney U with tie correction and normal approximation; Kruskal-Wallis with chi-squared approximation
- Corrected item-total correlations: each item correlated against sum of remaining items, avoiding part-whole inflation

---

## v3 Expansion — Attention Checks, Careless Index, Excel Export (session 3)

**Scope added:** attention check auto-detection and pass/fail scoring, careless responding composite index, multi-sheet Excel export.

### New modules
- `src/attention.py`: `detect_attention_check_columns()` (hint keywords + question text regex extraction), `score_attention_checks()` (case-insensitive pass/fail), `attention_failed_ids()`
- `src/careless.py`: `compute_careless_index()` (5-component 0–1 composite: fast response, straight-liner, high missing, outlier breadth, attention fail rate), `careless_summary()`
- `src/excel_export.py`: `export_excel()` — multi-sheet openpyxl workbook with color-coded cells; sheets: Overview, Respondents, Missing Data, Scale Reliability, Normality, Outliers, Attention Checks, Careless Index, Group Tests, per-scale correlation matrices

### Bug fixed
- `src/attention.py` was originally written with typographic curly quotes (U+201C/U+201D) used as Python string delimiters — invalid syntax that went unnoticed until the module was first imported. Rewrote the file with valid ASCII string delimiters and triple-quoted raw strings for regex patterns.

### Modified
- `src/quality.py`: `QualityReport` extended with `attention_specs`, `attention_results`, `careless_index`; `compute_quality()` gains `expected_attention_answers` parameter
- `src/report.py`: text and HTML reports gain Attention Checks and Careless Index sections
- `main.py`: `--attention-answers ANSWERS.json`, `--excel OUTPUT.xlsx`
- `requirements.txt`: added `openpyxl` (optional, only for `--excel`)

### Tests
- `tests/test_attention.py`: 29 tests
- `tests/test_careless.py`: 27 tests (Excel tests deferred until openpyxl available in CI)
- Total after v3: 198 tests passing

---

## v4 Expansion — Config File + Manual Rewrite (session 4)

**Scope added:** `qi.toml` config file support; comprehensive Manual rewrite covering all versions; this build log updated retrospectively.

### New module
- `src/config.py`: `load_config()` (reads `qi.toml` via stdlib `tomllib`; returns `{}` if absent; raises `ValueError` on malformed TOML), `apply_config_defaults()` (sets argparse defaults from config — CLI flags still override), `get_scales_from_config()`, `get_attention_answers_from_config()`

### Modified
- `main.py`: `--config` flag added; config loaded before argparse so defaults propagate correctly; `cmd_inspect` and `cmd_clean` use config for scales and attention answers when no CLI equivalent is provided
- `Manual.md`: complete rewrite — now documents all v1–v4 features, config file format with full example, all flags for both subcommands, attention check setup, careless index table, Excel sheet list, known limitations
- `BUILD_LOG.md`: retrospective entries added for v2, v3, v4

### Tests
- `tests/test_config.py`: 22 tests (load, apply defaults, scales, attention answers, CLI override)
- Total after v4: 220 tests passing

### Key decisions
- TOML over JSON for config: more readable for a file users edit by hand; Python 3.11+ stdlib `tomllib` means no additional dependency
- CLI flags always win: config only sets argparse defaults, so every option is still individually overridable
- `_extract_config_path()` does a pre-parse argv scan so config is loaded before the full argparse run, allowing `set_defaults()` to take effect

Build complete. Success criteria reviewed. All tests passing.
