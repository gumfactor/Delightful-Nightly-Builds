# Future Features — Effort Ledger

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **`--json summary.json` output** — dump the same data structure that feeds the HTML report (summaries, flags, windows) as a standalone JSON file, so the audit can be piped into another script or CI check without scraping the HTML.
2. **CSV export button in the dashboard** — a client-side "Download flagged CSV" button next to each table that re-serializes the already-loaded JSON data to CSV in the browser, so a user working only from the HTML report (without re-running the CLI) can still get a spreadsheet copy.
3. **Configurable severity-to-exit-code mapping** — `--fail-on error` making the CLI return a non-zero exit code when errors are present, so the tool can gate a pre-submission checklist or a CI step.
4. **Person-level effort total column in the timeline legend** — show each person's current maximum concurrent commitment percentage next to their name in the timeline, not just the highlighted red bands.

## Medium Effort (roughly one nightly build session)

5. **Multi-year budget rollup** — when the same `grant_id` appears across multiple `fiscal_year` values, add a "Project Period Total" view that sums direct/indirect/total across all years of one award, not just per-fiscal-year, matching how NIH/NSF budget justifications are usually reviewed as a whole project period.
6. **Institution rate-agreement presets** — a small local JSON file of named F&A-rate/exempt-category/subcontract-threshold presets ("On-Campus 2026", "Off-Campus 2026") the user maintains themselves, selectable via `--preset`, so the CLI flags don't need to be re-typed for every audit run of the same institution's rates.
7. **Salary-cap check as a pluggable, user-supplied rule** — rather than hardcoding any specific agency's numeric salary cap (which changes yearly and would go stale), accept an optional `--salary-cap-annual 221900` flag that flags any Personnel line whose implied annual salary rate exceeds it — the user supplies the current number, the tool does the check.

## Ambitious Extensions (multi-session effort)

8. **Local history across audit runs (SQLite)** — persist each `audit` run so a "same grant, different draft" comparison view can show how flags changed between budget revisions, similar to Panel Prep's version-over-version scoring.
9. **Direct import from NIH ASSIST / eRA Commons budget export formats** — a format-specific parser that maps the government's own multi-sheet budget export layout onto Effort Ledger's `budget.csv` schema, removing the manual CSV-authoring step entirely for NIH users.

---

## Possible Integration Points

- **Protocol Forge** (2026-07-19) already turns a study description into a compliance-checked IRB draft; a shared local "active grants" registry between Protocol Forge and Effort Ledger would let a new protocol automatically pull its effort/budget context instead of re-entering it.
- **Panel Prep** (2026-08-08) already tracks proposal-draft revisions over time in local SQLite; the "multi-year budget rollup" and "local history across runs" extensions above would let a future build pair Panel Prep's content critique with Effort Ledger's numeric budget critique into one pre-submission review pass.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| No persistent history — every run is a clean audit of whatever CSVs are passed in, with no memory of prior runs | Add local SQLite storage per the "Ambitious Extensions" item above |
| MTDC/exempt-category model is generic (Uniform-Guidance-style), not agency-specific — it will not catch every NIH- or NSF-specific budget rule (e.g. salary caps, specific equipment definitions) | Add the pluggable salary-cap check and, longer-term, agency-specific rule packs as separate opt-in modules rather than hardcoded defaults |
| The effort-overcommitment cap is a single global percentage; real institutional policy sometimes distinguishes between sponsored and non-sponsored (teaching, admin) effort commitments | Add an optional `commitment_type` column to `effort.csv` and let the cap check treat sponsored-only commitments separately from total commitments |
