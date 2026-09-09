# PRD — Headroom: RRSP/TFSA Contribution Room & Deadline Tracker

> **Build date:** 2026-09-09
> **Category:** I — Life Admin Helper
> **Complexity:** Ambitious Project
> **Day of week:** Wednesday

---

## Goal

Track a Canadian's RRSP and TFSA contribution room, over-contribution risk, and key CRA deadlines using the real published annual limit history and the actual tax rules that govern carryforward, withdrawals, and penalties — not a spreadsheet guess.

## User Story

As a Canadian who runs personal finances alongside a demanding academic/entrepreneurial schedule and already tracks investments through IBKR, I want to know exactly how much RRSP and TFSA room I have left, whether I'm at risk of an overcontribution penalty, and when the next CRA deadline lands, so that I never leave room on the table or get hit with a 1%-per-month tax I could have avoided by checking a dashboard.

## Scope

### In Scope
- A historical reference table of real, publicly published CRA annual dollar limits: TFSA (2009–2026) and RRSP (2009–2026).
- TFSA room engine: cumulative room since the year the user turned 18 (or 2009, whichever is later), contributions reducing room, withdrawals re-added to room only on January 1 of the *following* calendar year (the actual CRA rule), and detection of an over-contribution state with the 1%-per-month excess tax estimated.
- RRSP room engine: annual room = lesser of (18% of prior year's earned income) or that year's dollar limit, minus prior year's pension adjustment, plus indefinite carryforward of unused room; a $2,000 lifetime grace buffer before the 1%-per-month overcontribution tax applies; a flag for the RRSP-to-RRIF age-71 conversion deadline.
- Deadline engine, computed live from the current date: the RRSP contribution deadline for a tax year (60 days after December 31, shifted to the next business day if that lands on a weekend), days remaining in the current "first 60 days" contribution window, and days until the next TFSA room opens on January 1.
- Local JSON data store (`data/headroom.json`) holding the user's own profile (birth year) and transaction history (TFSA contributions/withdrawals, RRSP contributions, RRSP-eligible earned income per year). A fabricated, clearly-fake sample file ships for demo/testing; no real personal data is committed.
- CSV import for contributions and income history, with auto-detecting column names (date/amount/account or year/income/pension_adjustment), matching the ingestion pattern of a real brokerage/bank statement export.
- CLI (`main.py`) with `init`, `add-contribution`, `add-withdrawal`, `add-income`, `import-csv`, `status`, and `report` subcommands.
- Self-contained dark-mode HTML dashboard (`report`): TFSA and RRSP room cards, an over-contribution warning banner when triggered, a Chart.js cumulative-room-vs-contributions line chart (with a plain HTML-table fallback if the CDN is unreachable), a deadline countdown panel, and a contribution history table.
- Optional Claude Haiku plain-English admin briefing (`report --use-ai`), called directly via `urllib.request` against the Anthropic Messages API (no SDK dependency) using `ANTHROPIC_API_KEY` from the environment, sending only aggregate numbers (room balances, deadline dates) — never raw transaction-level data — with a deterministic template fallback when no key is set, verified to make zero network calls in that path.

### Out of Scope
- Spousal RRSP attribution rules and Home Buyers' Plan / Lifelong Learning Plan withdrawal-and-repayment tracking — genuinely separate rule sets large enough to be their own build.
- FHSA (First Home Savings Account) — a third registered account type; adding it tonight would dilute test depth on the two primary accounts rather than add real breadth.
- Automatically fetching contribution history from a brokerage (e.g. IBKR). IBKR account structures don't cleanly expose "this deposit was a registered RRSP/TFSA contribution" without per-institution assumptions this build can't verify; Trading Book (2026-08-23) already established this repo's live-IBKR pattern for account/position data, so this build instead treats the CRA rule engine and deadline logic — not a second brokerage connection — as its differentiating layer, and take a CSV/manual ledger as the real-data input, exactly as Ledger Lens does for bank statements.
- Multi-user / multi-profile support — single local profile only.
- Choosing which tax year an early-year RRSP contribution should be deducted against — the user states the tax year explicitly when logging it.

## Tech Stack

- **Language:** Python 3
- **Framework:** None
- **Dependencies:** stdlib only (`urllib.request` for the optional Anthropic API call; no third-party packages)
- **Runtime requirement:** `python3 main.py <command>`; the generated dashboard is a self-contained `.html` file that opens directly in a browser, no server needed

## Data Structure

`data/headroom.json` (created by `init`, one file per user):

```json
{
  "profile": {"birth_year": 1990, "resident_since_year": null},
  "tfsa_contributions": [{"date": "2024-03-01", "amount": 3000.0}],
  "tfsa_withdrawals": [{"date": "2023-11-01", "amount": 1000.0}],
  "rrsp_contributions": [{"date": "2024-02-15", "amount": 5000.0, "tax_year": 2023}],
  "rrsp_income": [{"year": 2023, "earned_income": 90000.0, "pension_adjustment": 0.0}]
}
```

`resident_since_year` is optional; when omitted, TFSA eligibility is assumed to start the year the user turned 18. All amounts are plain floats in CAD. No account numbers, institution names, or full names are ever stored.

## Folder Structure

```
builds/2026-09-09-headroom/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── main.py
├── data/
│   └── sample_headroom.json
├── src/
│   ├── __init__.py
│   ├── limits.py
│   ├── tfsa.py
│   ├── rrsp.py
│   ├── deadlines.py
│   ├── storage.py
│   ├── csv_import.py
│   ├── ai_briefing.py
│   ├── dashboard.py
│   └── cli.py
└── tests/
    ├── test_limits.py
    ├── test_tfsa.py
    ├── test_rrsp.py
    ├── test_deadlines.py
    ├── test_storage.py
    ├── test_csv_import.py
    ├── test_dashboard.py
    ├── test_ai_briefing.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - TFSA and RRSP annual limit table lookups, including out-of-range years raising a clear error
  - TFSA cumulative room with no activity, matching the known public total ($102,000 by 2025 / $109,000 by 2026 for someone eligible since 2009)
  - TFSA start-year logic for someone who turned 18 after 2009 (room starts the year they turned 18, not 2009)
  - TFSA room reduced by contributions; withdrawal amounts re-added only the *following* calendar year, not immediately
  - TFSA over-contribution detection and 1%-per-month excess tax estimate
  - RRSP room from 18% of earned income, capped at the year's dollar limit
  - RRSP room reduced by a pension adjustment
  - RRSP unused room carrying forward indefinitely across years
  - RRSP $2,000 grace buffer respected before any penalty is flagged
  - RRSP overcontribution beyond the buffer triggering the 1%-per-month penalty estimate
  - RRSP contribution deadline (60 days after Dec 31) with weekend-to-next-business-day adjustment, tested against a real leap year and a real weekend-landing case
  - Age-71 RRIF conversion deadline flag for someone turning 71 this year vs. already past it vs. not yet close
  - CSV import auto-detecting contribution and income columns, and raising a clear error on a malformed/missing-column file
  - Dashboard HTML generation containing the expected room figures and safely rendering user data (no unescaped injection)
  - AI briefing: mocked Anthropic call is merged into the report correctly; with no API key set, the deterministic fallback runs and the test asserts zero network calls are attempted
  - CLI subcommands round-tripping through a temporary data file (`init` → `add-contribution` → `status`)

## Success Criteria

1. All tests pass (zero failures)
2. TFSA and RRSP room figures computed by the engine match hand-calculated values for at least one full worked example spanning multiple years, contributions, and a withdrawal
3. The RRSP contribution deadline and TFSA next-room date are computed correctly from an injected "as of" date, including a weekend-adjustment case, without depending on the real wall-clock date at test time
4. `report` produces a self-contained HTML file that opens and displays correct room/deadline figures with no `ANTHROPIC_API_KEY` set (deterministic fallback path)
5. CSV import successfully loads a sample contributions file and a sample income file, and rejects a malformed file with a clear error rather than crashing

---

## Scope Changes

None — full in-scope feature set above was delivered as planned. IBKR live-sync was scoped out from the start (see Out of Scope) rather than cut mid-build.
