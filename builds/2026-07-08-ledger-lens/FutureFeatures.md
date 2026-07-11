# Future Features — Ledger Lens

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Multi-file merge** — Accept multiple `--input` CSVs (e.g. one per credit card) in a single run and merge them into one report, deduplicating by date+description+amount to handle overlapping statement periods.
2. **Category override rules file** — A `rules.json` the user can edit to add their own merchant → category keyword mappings without touching `categorize.py`, loaded and merged with the built-in `KEYWORD_RULES` at runtime.
3. **CSV export of the category breakdown alone** — A `--category-csv` flag for a compact category-totals-only export, useful for pasting straight into a spreadsheet.
4. **Configurable recurring sensitivity** — Expose `RECURRING_AMOUNT_TOLERANCE` and `RECURRING_MIN_MONTHS` as CLI flags instead of module constants, since a two-month minimum may be too aggressive or too lax depending on the export window.

## Medium Effort (roughly one nightly build session)

5. **Multi-run trend storage (SQLite)** — Persist each run's monthly totals to a local SQLite database keyed by month, so re-running the tool on a new export each month builds a true year-over-year spending history instead of each run being an isolated snapshot. This is the single biggest gap versus a "real" budgeting tool.
6. **Interactive category correction in the HTML report** — Add a small local-only edit mode (writes back to a sidecar JSON, not the original CSV) where clicking a category badge lets the user reassign it, and re-running the CLI respects prior corrections as high-priority rules.
7. **PDF statement support** — Many banks only offer PDF statements for older history; adding a `pdfplumber`-based extraction path (with the same auto-detect-columns logic re-applied to extracted table rows) would remove the CSV-export bottleneck entirely.

## Ambitious Extensions (multi-session effort)

8. **Cross-account net-worth view** — Combine Ledger Lens's spending data with the existing Investment Research Platform build's (2026-06-10) portfolio data into a single monthly financial position report — spending, investing, and net worth in one place, which is the natural endpoint of "life admin" for this user's specific multi-venture financial life.

---

## Possible Integration Points

- **Investment Research Platform (2026-06-10)** and **Investment Thesis Journal (2026-06-14)** — both already use `yfinance` for portfolio data; a future build could sit above all three and produce a single monthly "financial position" report combining spending (this build), investments, and thesis tracking.
- **Morning Briefing (2026-06-22)** — that build's daily digest pattern (GitHub + portfolio + weather + AI synthesis) is a natural home for a monthly "spending recap" section once multi-run history storage (#5 above) exists.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Each run is a standalone snapshot of one CSV — no memory of prior runs | Add SQLite-backed multi-run history (#5 above) |
| Rule-based categorizer only recognizes merchants common in Canadian/US retail; a different country's bank export will fall through to "Other" more often | Ship a locale-specific keyword pack, or lean more heavily on the AI enrichment pass when a key is available |
| Recurring detection requires the exact same normalized merchant string across months; a subscription that changes its billing descriptor (e.g. "NETFLIX.COM" → "NETFLIX INC") will be missed | Add fuzzy string matching (e.g. Levenshtein distance) as a second pass on top of the exact-normalized-key grouping |
| Budget comparison only supports a flat monthly cap per category, no seasonal or rolling budgets | Support a `budgets.json` schema with per-month overrides |
