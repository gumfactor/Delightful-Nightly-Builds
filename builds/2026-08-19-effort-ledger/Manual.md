# Manual — Effort Ledger

> **Version:** 1.0 (built 2026-08-19)
> **Complexity:** Ambitious

---

## What This Is

Effort Ledger audits two spreadsheets you already have to produce for grants administration — a budget line-item list and an effort-commitment list — and catches the two error classes that most often surface late: indirect-cost (F&A) math that doesn't add up, and a person certifying more combined effort across simultaneous grants than they actually have. It's a batch tool: point it at your CSVs, get back an HTML dashboard, a terminal summary, and two annotated copies of your input files with a `Flags` column appended.

---

## Quick Start

1. Have Python 3.11+ installed (no other dependencies required — stdlib only)
2. From this build folder, run it against the bundled sample data:
   ```bash
   python3 src/main.py --budget sample_data/budget.csv --effort sample_data/effort.csv --far-rate 0.55 --output report.html
   ```
3. Open `report.html` in any browser
4. To audit your own data, replace `--budget`/`--effort` with paths to your own CSVs in the same column format (see Configuration below)
5. Add `--ai` and set `ANTHROPIC_API_KEY` in your environment for a short narrative briefing (optional — the tool is fully functional without it)

---

## How to Use It

### Preparing `budget.csv`

One row per budget line item, columns: `grant_id, grant_name, fiscal_year, category, description, direct_cost`. Valid `category` values: `Personnel`, `Fringe Benefits`, `Equipment`, `Travel`, `Supplies`, `Subcontract`, `Other`, `Indirect`. Put your award's *actual* stated F&A/indirect-cost dollar amount on an `Indirect` row if you want it cross-checked against the computed expected value — if you leave it out, the tool just reports what the expected indirect cost *would* be, informationally, with no mismatch to flag.

### Preparing `effort.csv`

One row per person/grant/period commitment, columns: `person_name, grant_id, grant_name, period_start, period_end, percent_effort`. Dates are `YYYY-MM-DD`, inclusive on both ends. If the same person has effort on the same grant across two non-adjacent periods, use two rows.

### Reading the Report

- **Hero stats** — grant count, total flags, and a break down by severity, plus how many distinct people have an overcommitment window
- **Effort Timeline** — one horizontal row per person; each colored segment is one grant commitment over its date range; a translucent red band with a red outline marks a period where that person's total commitment across all grants exceeded the cap
- **Budget Summary** — sortable/searchable table of Direct cost, MTDC (Modified Total Direct Cost — the indirect-cost calculation base), Expected Indirect, Stated Indirect (what you entered, if anything), and Total, per grant/fiscal-year
- **Flags** — every issue found, filterable by severity chip (error/warning/info) and searchable by text; click any column header to sort

### Command-Line Options

Run `python3 src/main.py --help` for the full list. The two annotated CSVs (`budget_flagged.csv`, `effort_flagged.csv`) are always written next to your `--output` HTML file.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `--far-rate` | *(required)* | Your F&A/indirect-cost rate as a decimal (e.g. `0.55` for 55%). No default — check your institution's current negotiated rate agreement rather than trusting a guessed number. |
| `--exempt-categories` | `Equipment` | Comma-separated budget categories fully excluded from the MTDC calculation base. |
| `--subcontract-threshold` | `25000` | Dollars of each Subcontract line item included in MTDC before the rest is excluded — the commonly used Uniform Guidance convention. Verify against your award terms; this is a configurable default, not a universal rule the tool asserts as fact. |
| `--effort-cap` | `100` | Percent-effort ceiling before an overcommitment window is flagged. |
| `--tolerance` | `1.00` | Dollar tolerance before a stated-vs-expected indirect cost mismatch is flagged. |
| `--ai` | off | Enables an optional one-paragraph narrative briefing via the Anthropic API (`ANTHROPIC_API_KEY` env var). The API only ever receives aggregate counts — never a name, dollar figure, or grant ID. Without a key set, `--ai` still produces a complete deterministic-template narrative and makes zero network calls. |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| "budget.csv is missing required column(s)" | Your CSV header doesn't exactly match the required column names | Check spelling/case against the columns listed in "Preparing budget.csv" above |
| A row is silently missing from the report | The loader flags malformed rows (bad number, bad date, empty required field) and skips them rather than crashing the whole run | Check the Flags panel and the `_flagged.csv` outputs — the skip reason is recorded there under codes like `malformed_direct_cost` or `malformed_date` |
| No overcommitment shown even though I expect one | The cap check only counts periods that actually overlap in time — two 60% commitments on grants running in different months won't sum | Check the Effort Timeline visually; overlap is date-range-based, not a simple sum of all rows for a person |
| `--ai` flag produces the same generic sentence every time | No `ANTHROPIC_API_KEY` is set, so the deterministic template is used (by design — this is not a bug) | Set `ANTHROPIC_API_KEY` in your environment before running with `--ai` |

---

## Known Limitations

- No persistent history between runs — this audits whatever two CSVs you point it at, once, each time
- The indirect-cost model is a generic Uniform-Guidance-style calculation, not a specific agency's full rule set (it will not catch, for example, an NIH salary-cap violation on its own)
- Effort overcommitment uses one global percentage cap; it does not distinguish between sponsored-research effort and other institutional commitments (e.g. teaching load)
- Currency is not represented as a unit — every dollar figure is assumed to be in whatever single currency you entered
