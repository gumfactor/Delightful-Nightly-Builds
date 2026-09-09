# Future Features — Headroom: RRSP/TFSA Contribution Room & Deadline Tracker

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Annual limit auto-refresh reminder** — `status` and `report` could print a one-line warning once the current date passes a point where next year's CRA limits are typically announced (usually November) but aren't yet in `src/limits.py`, so the tool never silently understates room for a new year.
2. **`--out-dir` flag on `report`** — write the dashboard with a date-stamped filename (`headroom_report_2026-09-09.html`) automatically so successive runs don't need `--out` re-typed and old reports aren't overwritten.
3. **CSV export of the year-by-year ledger** — a `headroom export-csv` command dumping both engines' `year_snapshots` (year, room added, contributions, ending balance) to a spreadsheet-friendly CSV for anyone who wants to double-check the math themselves.

## Medium Effort (roughly one nightly build session)

4. **FHSA (First Home Savings Account) support** — a third registered-account engine with its own rules ($8,000/year, $40,000 lifetime cap, 15-year or age-71 expiry, one-time carryforward of unused room by one year only) — deliberately scoped out of tonight's build to keep the two existing engines' test depth high.
5. **Spousal RRSP attribution tracking** — a second profile (spouse's birth year + income) so contributions made to a spousal RRSP correctly reduce the *contributor's* own room while being attributed to the spouse for withdrawal-timing (attribution) rules.
6. **Home Buyers' Plan / Lifelong Learning Plan withdrawal tracking** — these RRSP withdrawal types don't count as income and must be repaid over a fixed schedule (15 years / 10 years) or become taxable; a repayment-schedule tracker with a missed-payment warning would close a real gap in the current RRSP model, which only handles net new contributions.

## Ambitious Extensions (multi-session effort)

7. **Automated IBKR deposit-tagging assist** — rather than a full live sync (deliberately scoped out tonight, see PRD.md's Out of Scope), a lighter-weight `headroom suggest-from-ibkr` command that reads Trading Book's existing local SQLite snapshot history (2026-08-23) for deposit-shaped net-liquidation jumps and *suggests* them as candidate TFSA/RRSP contributions for the user to confirm — reusing an existing build's data instead of a second live brokerage connection.
8. **Multi-year tax-year optimization advisor** — given a target retirement date and current marginal tax bracket estimate, suggest which years to prioritize RRSP contributions (higher-income years) vs. carry room forward (lower-income years), turning the tracker from a passive ledger into an active planning tool.

---

## Possible Integration Points

- **Trading Book (2026-08-23)** — its local SQLite account-snapshot history is the most natural real-data bridge for the IBKR deposit-suggestion feature above, without duplicating its live-connection code.
- **CanEcon Pulse (2026-07-18)** — already pulls Bank of Canada Valet API data; a future version of Headroom's AI briefing could reference the current policy interest rate when suggesting whether unused RRSP room is worth contributing now vs. carrying forward (a rate-sensitive decision), without adding a new API integration.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| RRSP room computed from income history alone (no `opening_balance`) only starts the year *after* the earliest income record — any real carryforward from before that is invisible to the tool. | Prompt the user during `init` to optionally enter their actual CRA Notice-of-Assessment deduction limit as an `opening_balance`, which the engine already supports. |
| No FHSA support — a real third registered account this user may eventually want tracked. | See Medium Effort #4 above. |
| The annual limit tables stop at 2026 and must be manually updated in `src/limits.py` each year CRA publishes new figures (typically announced in the fall for the following year). | Add a `status` warning once `date.today()` is within ~60 days of the last tabulated year ending, so the gap is surfaced rather than silently hit. |
| `import-csv` only supports one contribution/income row format; a real brokerage or bank export may use different column names than `date`/`amount`/`year`/`earned_income`. | Extend `_normalize_headers` in `src/csv_import.py` with a small alias table (e.g. "transaction date" → "date", "value" → "amount") the way real-world exports vary. |
