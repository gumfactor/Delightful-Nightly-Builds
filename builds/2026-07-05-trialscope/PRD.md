# PRD — TrialScope: Behavioral & Reaction-Time Data QC Explorer

> **Build date:** 2026-07-05
> **Category:** F — Data Explorer
> **Complexity:** Ambitious Project
> **Day of week:** Sunday

---

## Goal

Given a trial-level behavioral/reaction-time data export from a cognitive or behavioral experiment, TrialScope computes rigorous per-subject and per-condition data-quality diagnostics, flags common contamination patterns (guessing, attention lapses, anticipatory responses, excessive missing data), and renders an interactive dark-mode HTML report with an AI-drafted participant-exclusion paragraph ready to paste into a methods section.

## User Story

As a neuroscience/psychology researcher who runs behavioral and neuroimaging studies and regularly has to decide which participants and trials to exclude before analysis, I want to drop in a raw trial-level CSV export and immediately see which subjects and trials are contaminated by guessing, fatigue, or technical failure — with the reasoning already written up — so that I stop manually eyeballing spreadsheets and second-guessing exclusion criteria before every analysis.

## Scope

### In Scope
- CSV ingestion for generic trial-level data (one row per trial) with configurable or auto-detected column roles: subject/participant ID, condition, block, trial number, reaction time, accuracy/correct
- Auto-detection of column roles from common naming conventions (subject/subj/participant/id, condition/cond/group, rt/reaction_time/latency, accuracy/correct/acc, block, trial/trial_num), with explicit `--*-col` CLI overrides when auto-detection is ambiguous or wrong
- Graceful handling of malformed cells: non-numeric RT, blank cells, out-of-range values — coerced with a warning count, never a crash
- Per-subject summary: trial count, % correct, mean/median/SD reaction time (correct trials only)
- Per-condition summary: same statistics aggregated across subjects, for cross-condition comparison
- Configurable QC flags computed live from the data (no hardcoded per-dataset thresholds):
  - Anticipatory/fast-guess trials (RT below a floor, default 150ms)
  - Attention-lapse outliers (a modified z-score using each subject's own median/MAD of correct-trial RTs, default threshold 3.5 — chosen over a mean/SD z-score because a single outlier inflates its own reference SD, capping the achievable mean/SD z-score at `sqrt(n-1)` regardless of magnitude; median/MAD stays robust to a single extreme value — plus an absolute ceiling, default 5000ms)
  - Chance-level performance (binomial test of subject accuracy against a configurable chance rate, default 50%)
  - Excessive missing/incomplete trials (completed trials below a configurable fraction of expected trials)
  - Implausible ceiling performance (100% accuracy combined with implausibly fast mean RT — possible automated/bot-like responding)
- Subject-level exclusion recommendation: subjects meeting or exceeding a configurable flag-count threshold (default 2) are recommended for exclusion, each with a plain-English reason list
- Trial-level QC: a cleaned CSV export with a `QC_Flag` column added per trial (fast guess / outlier / none)
- Learning-curve view: accuracy and RT trend across binned trial blocks, per condition
- RT distribution view: histogram of correct-trial RTs per condition, hand-drawn SVG (no external chart library, no network dependency)
- Interactive dark-mode HTML report: summary header, sortable/searchable subject table with flag badges, condition comparison table, RT histograms, learning-curve charts, AI-generated (or template-generated) methods paragraph
- AI-drafted "Participants & Data Quality" paragraph via the Anthropic Messages API (called directly over HTTPS with the `requests` library — no `anthropic` SDK dependency) when `ANTHROPIC_API_KEY` is set; a deterministic, fully-computed template paragraph when it is not, so the report is always complete
- CLI entry point: `python src/trialscope.py <input.csv> [options] --out-dir <dir>`

### Out of Scope
- No GUI file picker or drag-and-drop upload — command-line input path only
- No support for wide-format data (one row per subject with repeated-measure columns) — long format (one row per trial) only
- No statistical inference beyond the binomial chance-level test (no ANOVA, mixed models, or between-condition significance testing)
- No live/network data source — this is a local file-processing tool by design (the domain has no meaningful "live API"; the same design choice as the Jun 17 Qualtrics Survey Data Inspector, the highest-rated build to date)
- No persistence/database — each run is stateless, operating on one input file at a time

## Tech Stack

- **Language:** Python 3.11
- **Framework:** None
- **Dependencies:** `requests` (already present in the environment; used only for the optional Anthropic API call — falls back to stdlib-only behavior with no network call when no API key is set)
- **Runtime requirement:** `python3 src/trialscope.py <input.csv> --out-dir <output_dir>` — produces a self-contained HTML report and a cleaned CSV; the HTML opens directly in any browser with no server or build step

## Data Structure

**Input:** a CSV file, one row per trial, with columns identifiable (by name or CLI flag) as:
- subject/participant ID (string or int)
- condition (string)
- block/trial-block (int, optional — falls back to a single implicit block if absent)
- trial number (int, optional — inferred from row order within subject if absent)
- reaction time in milliseconds (float)
- accuracy/correct (0/1, True/False, or "correct"/"incorrect")

**Internal representation:** a list of `Trial` dataclasses after parsing/coercion, grouped into per-subject and per-condition aggregate dataclasses (`SubjectSummary`, `ConditionSummary`) carrying computed stats and flags.

**Output:**
- `report.html` — self-contained interactive report (inline CSS/JS, hand-drawn SVG charts, no external requests)
- `cleaned_data.csv` — original columns plus a `QC_Flag` column
- `exclusions.csv` — recommended-exclusion subject IDs with reasons

## Folder Structure

```
builds/2026-07-05-trialscope/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── trialscope.py       (CLI entry point / argument parsing / orchestration)
│   ├── parsing.py          (CSV loading, column auto-detection, coercion)
│   ├── qc.py                (per-subject/condition stats, QC flag logic, exclusion logic)
│   ├── ai_summary.py        (Anthropic API call + deterministic fallback template)
│   └── report.py            (HTML report generation, SVG chart rendering)
└── tests/
    ├── fixtures/
    │   └── sample_trials.csv
    ├── test_parsing.py
    ├── test_qc.py
    ├── test_ai_summary.py
    └── test_report.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v` (run from `builds/2026-07-05-trialscope/`)
- **What will be tested:**
  - Column auto-detection across several common naming conventions
  - Explicit `--*-col` overrides taking precedence over auto-detection
  - Missing required column raises a clear, actionable error (no silent failure)
  - Malformed/non-numeric RT and blank cells are coerced with a warning, not a crash
  - Per-subject and per-condition aggregate statistics are numerically correct against hand-computed fixtures
  - Fast-guess (RT floor) flag triggers correctly at and around the threshold boundary
  - Outlier (SD + ceiling) flag triggers correctly, using each subject's own mean/SD
  - Chance-level binomial flag triggers for a subject performing at/below chance and not for one performing well above it
  - Excessive-missing-data flag triggers when completed trials fall below the configured completion fraction
  - Implausible-ceiling flag triggers on the 100%-accuracy + fast-RT combination
  - Exclusion recommendation logic respects the configurable flag-count threshold
  - Cleaned CSV output contains the added `QC_Flag` column with correct per-row values
  - AI summary falls back to the deterministic template when no API key is present (this environment's actual state)
  - AI summary call path is exercised with a mocked HTTP response to confirm correct request construction and response parsing
  - HTML report generation includes the computed subject count, flag counts, and condition names as literal text (structural content check)
  - Empty input file (header only, zero trials) is handled without crashing and produces a report stating there is no data
  - CLI argument parsing applies documented defaults when options are omitted

## Success Criteria

1. All tests pass (zero failures)
2. Running the CLI against `tests/fixtures/sample_trials.csv` produces `report.html`, `cleaned_data.csv`, and `exclusions.csv` in the specified output directory
3. The generated HTML report is fully self-contained (openable via `file://`, no external network requests) and correctly reflects the computed subject/condition statistics and QC flags for the sample fixture
4. Every QC flag is derived from a configurable, live-computed rule — no per-dataset hardcoded thresholds or fabricated results
5. The report includes a "Participants & Data Quality" paragraph, generated by the deterministic template in this environment (no Anthropic API key present), with the AI code path verified separately via a mocked test

---

## Scope Changes

None — the AI-layer design (direct HTTPS call via `requests` with a deterministic fallback) was decided during PRD writing after discovering the `anthropic` Python package cannot be installed in this session (`pip install` is denied by this session's permission policy) and that `ANTHROPIC_API_KEY` is not actually set in this environment despite CLAUDE.md/PROFILE.md describing it as always available. This is documented as a deviation in BUILD_LOG.md rather than a mid-build scope cut.
