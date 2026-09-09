# Manual — Headroom: RRSP/TFSA Contribution Room & Deadline Tracker

> **Version:** 1.0 (built 2026-09-09)
> **Complexity:** Ambitious Project

---

## What This Is

Headroom tracks exactly how much RRSP and TFSA contribution room you have left, whether you're at risk of a CRA overcontribution penalty, and when the next contribution deadline lands — computed from the real, published annual limit history (2009–2026) and the actual carryforward, withdrawal-timing, and penalty rules, not a rough estimate. It's a local CLI plus a self-contained HTML dashboard: your financial data never leaves your machine unless you explicitly turn on the optional AI briefing, and even then only aggregate room figures (never individual transactions) are sent.

---

## Quick Start

1. `python3 main.py init --birth-year 1990` (creates `data/headroom.json`; add `--resident-since-year YYYY` if you became a Canadian resident after turning 18)
2. `python3 main.py add-contribution --account tfsa --date 2024-03-01 --amount 3000`
3. `python3 main.py add-income --year 2024 --amount 95000` (RRSP room for 2025 is based on 2024's earned income)
4. `python3 main.py status` for a quick terminal summary, or `python3 main.py report` to generate `headroom_report.html` and open it in any browser

---

## How to Use It

### Recording activity

- `add-contribution --account tfsa|rrsp --date YYYY-MM-DD --amount X` — for RRSP, add `--tax-year YYYY` if the contribution should count toward a different tax year than the calendar date it was made in (e.g. a contribution made in January 2025 that you're applying to your 2024 tax year). Defaults to the transaction date's own year if omitted.
- `add-withdrawal --date YYYY-MM-DD --amount X` — TFSA withdrawals only. The withdrawn amount is correctly added back to your room the *following* January 1, not immediately (that's the real CRA rule — re-contributing in the same calendar year you withdrew is the single most common accidental overcontribution).
- `add-income --year YYYY --amount X [--pension-adjustment P]` — your RRSP-eligible earned income for that year; this generates new RRSP room *the following year*.

### Bulk import

`import-csv --file path.csv --type contributions-tfsa|contributions-rrsp|income` — column headers are matched case-insensitively. Contribution files need `date` and `amount` columns; income files need `year` and `earned_income` (an optional `pension_adjustment` column is used if present, otherwise assumed zero).

### Seeding real RRSP history

If you've been contributing to an RRSP for years before you started using this tool, Headroom has no way to know your true carryforward from income history alone. Open `data/headroom.json` and set:
```json
"rrsp_opening_balance": {"year": 2024, "amount": 42000}
```
using the deduction limit shown on your actual CRA Notice of Assessment as of the start of that year. The engine then computes forward from there instead of from scratch.

### Checking your standing

- `status` — a quick terminal summary: available room for both accounts, or an OVER-CONTRIBUTED warning, plus the next RRSP deadline and TFSA room-opening date.
- `report [--out path.html] [--use-ai]` — generates the full HTML dashboard: room cards, a chart of your balance history for both accounts, a deadline countdown, and a contribution history table. Pass `--use-ai` with `ANTHROPIC_API_KEY` set in your environment for a Claude-written plain-English summary; without a key (or without the flag), a clear deterministic summary sentence is used instead — no functionality is lost.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `--data` | `data/headroom.json` | Path to your local data file. Pass a different path to track a second profile. |
| `--out` (report only) | `headroom_report.html` | Where the dashboard HTML is written. |
| `--use-ai` (report only) | off | Calls the Anthropic API for a written briefing; requires `ANTHROPIC_API_KEY` in your environment. |
| `ANTHROPIC_API_KEY` | not set | Environment variable read only when `--use-ai` is passed. |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `No data file at data/headroom.json. Run init first.` | You haven't run `init` yet, or you're running from a different directory. | Run `python3 main.py init --birth-year YYYY`, or pass `--data /full/path/to/headroom.json` to every command. |
| RRSP room looks too low compared to your CRA Notice of Assessment | Headroom only knows about income years you've explicitly entered with `add-income`; it has no visibility into your pre-tracking history by default. | Set `rrsp_opening_balance` in `data/headroom.json` — see "Seeding real RRSP history" above. |
| Dashboard chart doesn't render, but a table appears instead | The Chart.js CDN is unreachable (e.g. no internet, or a restrictive network). | This is the intended fallback — the table shows the same year-by-year data. Nothing is broken. |
| `report --use-ai` still shows the deterministic summary | `ANTHROPIC_API_KEY` isn't set, or the API call failed and Headroom fell back gracefully rather than showing an error. | Check that the environment variable is exported in the shell you're running from. |
| `import-csv` fails with "missing required column(s)" | Your CSV's headers don't include `date`/`amount` (contributions) or `year`/`earned_income` (income), even case-insensitively. | Rename the relevant column headers in the CSV, or export again with those exact names. |

---

## Known Limitations

- No FHSA (First Home Savings Account) support — only RRSP and TFSA are modeled. See FutureFeatures.md.
- No spousal RRSP attribution or Home Buyers' Plan / Lifelong Learning Plan repayment tracking.
- RRSP room computed purely from income history (without an `opening_balance`) only starts the year after your earliest recorded income year — carryforward from before that isn't visible to the tool unless you seed `rrsp_opening_balance`.
- The annual limit tables run through 2026 and need a manual update in `src/limits.py` once CRA publishes new figures each year.
- Does not connect to any brokerage or bank automatically — all contribution/income data is entered manually or via CSV import, matching how any Canadian tracking multiple institutions' registered accounts would need to reconcile them anyway.
