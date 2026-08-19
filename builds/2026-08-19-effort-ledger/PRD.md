# PRD — Effort Ledger

> **Build date:** 2026-08-19
> **Category:** F — Data Explorer
> **Complexity:** Ambitious (every nightly build targets ambitious scope per STANDARDS.md)
> **Day of week:** Wednesday

---

## Goal

Audit a research budget spreadsheet and an effort-commitment spreadsheet for the arithmetic and cross-grant errors that IRB/grants offices catch late (or don't catch at all), and render the results as an explorable dashboard.

## User Story

As a research lab director who writes grants, manages multiple simultaneous awards, and handles the associated budget justifications and effort certifications personally, I want to upload my own budget line items and per-person effort commitments and have a tool catch indirect-cost math errors and cross-grant effort overcommitment before I submit or certify them, so that I catch mistakes myself instead of during a compliance audit or a grants-office rejection.

## Scope

### In Scope
- CSV loader for two independent inputs: `budget.csv` (grant_id, grant_name, fiscal_year, category, description, direct_cost) and `effort.csv` (person_name, grant_id, grant_name, period_start, period_end, percent_effort)
- Row-level parse validation that never crashes the whole run — malformed rows become flags, not exceptions
- Deterministic budget audit per grant/fiscal-year group:
  - Modified Total Direct Cost (MTDC) computation with configurable fully-exempt categories (default: Equipment) and a configurable subcontract exemption threshold (default: first $25,000 of each subcontract line included, remainder excluded — the common Uniform Guidance convention, explicitly labeled as a default to verify against the user's actual negotiated rate agreement, never asserted as a fixed rule)
  - Expected indirect cost (MTDC × F&A rate) cross-checked against a stated `Indirect` category line, flagged beyond a configurable dollar tolerance
  - Missing-Fringe-Benefits-line check when a Personnel line exists
  - Zero/negative direct cost check
  - Duplicate line-item check within a grant/fiscal-year
  - Unknown category check
- Deterministic effort audit:
  - Per-line range/date validation (0 < percent_effort, period_end >= period_start)
  - Cross-grant, cross-time effort overcommitment detection via an interval-sweep algorithm: for each person, finds every contiguous date window where concurrently active grant commitments sum above a configurable cap (default 100%), and reports the window's date range, peak total percentage, and the contributing grants
  - Grant-name-mismatch check (same grant_id, different grant_name across rows — a data-entry safety net)
  - Orphan-grant check (effort row references a grant_id absent from the budget file — informational, not an error, since non-financial commitments are legitimate)
- Self-contained dark-mode HTML dashboard: hero stats, sortable/searchable per-grant budget table, sortable/searchable flags table (grouped by severity), and a Canvas 2D per-person effort timeline with overcommitment windows highlighted
- Terminal text summary always printed
- Two annotated CSV exports (`budget_flagged.csv`, `effort_flagged.csv`) — the original rows plus an appended `Flags` column
- Optional Claude Haiku narrative briefing, built exclusively from an aggregate-only summary object (counts of flags by type/severity, number of grants, number of people overcommitted — never a name, dollar figure, or grant identifier), with an unconditional deterministic-template fallback that makes zero network calls when `ANTHROPIC_API_KEY` is unset
- Bundled `sample_data/budget.csv` and `sample_data/effort.csv` so the tool is runnable immediately without the user's own data

### Out of Scope
- Persistent storage or run history (SQLite) — this is a single-run audit tool; the CSVs are the source of truth each time it runs
- Agency-specific rule packs (NIH vs. NSF vs. institution-specific MTDC base definitions) beyond the configurable exempt-category/threshold model — the tool encodes the general Uniform-Guidance-style pattern, not any specific agency's current numeric caps (e.g. NIH's salary cap), which change yearly and would go stale if hardcoded
- Multi-currency support — all figures are treated as a single currency the user chooses
- In-app data entry/editing UI — CSV in, report out, matching this category's established "batch processor" builds
- PDF export

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** None
- **Dependencies:** stdlib only (`csv`, `argparse`, `dataclasses`, `datetime`, `json`, `urllib.request` for the optional AI call, `html`)
- **Runtime requirement:** `python3 src/main.py --budget <file> --effort <file> --far-rate <rate> --output report.html`

## Data Structure

**`budget.csv`** (one row per budget line item):

| Column | Type | Notes |
|---|---|---|
| `grant_id` | str | Stable identifier grouping lines into one award |
| `grant_name` | str | Human-readable award title |
| `fiscal_year` | str | e.g. `"2026"` or `"Y1"` — grouping key, not parsed as a date |
| `category` | str | `Personnel`, `Fringe Benefits`, `Equipment`, `Travel`, `Supplies`, `Subcontract`, `Other`, or `Indirect` |
| `description` | str | Free text |
| `direct_cost` | float | Dollar amount for this line (the `Indirect` category's amount is the *stated* indirect cost, compared against the computed expected value) |

**`effort.csv`** (one row per person/grant/period commitment):

| Column | Type | Notes |
|---|---|---|
| `person_name` | str | |
| `grant_id` | str | |
| `grant_name` | str | |
| `period_start` | date (`YYYY-MM-DD`) | Inclusive |
| `period_end` | date (`YYYY-MM-DD`) | Inclusive |
| `percent_effort` | float | e.g. `25` for 25% |

**Config** (CLI flags, all optional with documented defaults except `--far-rate`, which has no default since institutional F&A rates vary and a wrong silent default would be worse than requiring it explicitly):

| Flag | Default | Meaning |
|---|---|---|
| `--far-rate` | *(required)* | F&A/indirect rate as a decimal, e.g. `0.55` |
| `--exempt-categories` | `Equipment` | Comma-separated categories fully excluded from MTDC |
| `--subcontract-threshold` | `25000` | Dollars of each subcontract line included in MTDC |
| `--effort-cap` | `100` | Percent effort ceiling before a window is flagged |
| `--tolerance` | `1.00` | Dollar tolerance before an indirect-cost mismatch is flagged |
| `--ai` | off | Enable the optional Claude Haiku aggregate-only narrative |

Internal audit result objects (`Flag`, `GrantBudgetSummary`, `OvercommitmentWindow`) are Python dataclasses defined in `src/models.py`; the report is a JSON blob of these (serialized via `dataclasses.asdict`) embedded in a `<script type="application/json">` tag and read client-side with `JSON.parse` — never string-interpolated into executable HTML.

## Folder Structure

```
builds/2026-08-19-effort-ledger/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── sample_data/
│   ├── budget.csv
│   └── effort.csv
├── src/
│   ├── __init__.py
│   ├── models.py
│   ├── loader.py
│   ├── budget_audit.py
│   ├── effort_audit.py
│   ├── ai_narrative.py
│   ├── report.py
│   └── main.py
└── tests/
    ├── __init__.py
    ├── test_loader.py
    ├── test_budget_audit.py
    ├── test_effort_audit.py
    ├── test_ai_narrative.py
    └── test_report.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - CSV loading: happy path, missing columns, malformed dates/numbers become flags rather than crashes, empty file
  - Budget audit: correct MTDC computation with an exempt category, correct subcontract-threshold partial exemption, indirect-cost mismatch detection within/beyond tolerance, missing-fringe detection, zero/negative-cost detection, duplicate-line detection, unknown-category detection, the case with no stated indirect line at all
  - Effort audit: two grants overlapping above the cap is flagged with the correct window and contributing grants; two grants at exactly the cap is *not* flagged; touching-but-not-overlapping periods are not flagged; partial overlap flags only the overlapping sub-window; a single line over 100% is flagged; grant-name mismatch and orphan-grant checks
  - AI narrative: deterministic fallback produces non-empty text with zero network calls when no API key is set; a mocked Anthropic response is used as the narrative when a key is set; the aggregate payload sent never contains a name, dollar figure, or grant identifier
  - Report rendering: a script/HTML-injection payload placed in a person/grant name is never emitted as executable markup; the report embeds the expected counts

## Success Criteria

1. All tests pass (zero failures)
2. Given a budget CSV with a deliberately wrong `Indirect` line, the tool flags the mismatch and reports the correct hand-computed expected value
3. Given an effort CSV with two grants whose overlapping-period percentages sum above the cap, the tool identifies the correct overlapping date range and both contributing grants — and does not flag a non-overlapping or exactly-at-cap case
4. The HTML dashboard renders real audit results and a script-injection payload in a name field is never present as executable markup in the generated file
5. Running with no `ANTHROPIC_API_KEY` set (and `--ai` on) produces a complete report via the deterministic template with zero network calls

---

## Scope Changes

None — full in-scope list above was delivered as planned.
