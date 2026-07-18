# Future Features — CanEcon Pulse

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **`--json` export flag** — Add a `render --json output/snapshot.json` mode that dumps the same latest-value/delta data the HTML dashboard shows, so it can be piped into another script (e.g. a Canada List editorial workflow) without scraping the HTML.
2. **Configurable lookback window** — `sync --recent` already exists; expose it more visibly in `Manual.md` with concrete examples (e.g. `--recent 90` to backfill a deeper initial history in one call, since the Bank of Canada Valet API supports much longer `recent=` windows than the 30-day default used here).
3. **`--currencies` flag** — Let the user add more Bank of Canada FX series (e.g. `FXGBPCAD`, `FXCNYCAD`) via a CLI flag instead of editing `src/indicators.py` directly.

## Medium Effort (roughly one nightly build session)

4. **Routine wrapper** — Package `run` as a Claude Code Routine that runs on a daily or weekly schedule, so the local history genuinely compounds without the user remembering to invoke it. This is the single highest-leverage extension: the dashboard's trend charts are only as rich as accumulated `sync` history.
5. **Retail trade / GDP indicators** — Add StatsCan retail trade and GDP-by-industry vectors once the exact vector IDs used in this build (CPI: `v41690973`, unemployment: `v2062815`) have been confirmed correct by a live run, to avoid compounding unverified guesses.
6. **Canada List cost-basket view** — A second dashboard panel translating the CAD/USD movement into an illustrative "cost of a $100 imported basket vs. $100 Canadian-made basket" figure, tying the macro data more concretely to the Canada List mission the AI briefing already gestures at.

## Ambitious Extensions (multi-session effort)

7. **Regional breakdown** — StatsCan WDS supports provincial-level CPI and unemployment vectors; a province selector (especially Ontario, where the user is based) would make the dashboard materially more personally relevant than national aggregates alone.
8. **Historical event annotations** — Overlay Bank of Canada rate-decision dates (available from the Valet API's own rate-announcement series) on the interest-rate chart, turning a bare trend line into a narrative of policy decisions over time.

---

## Possible Integration Points

- **The Canada List** — the AI briefing's consumer-purchasing-power framing is a natural seed for editorial content; a `--for-editorial` output mode producing a publish-ready paragraph would connect this tool directly to that active project.
- **Deadline Guardian (2026-07-17)** — both builds share the "extract structured data via Claude with a deterministic fallback" pattern; if Deadline Guardian's capture module is ever generalized, CanEcon Pulse's briefing generation could share that code (once/if these two builds are ever consolidated into a shared local toolkit — not possible tonight since builds cannot import from each other's folders).

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| The two StatsCan WDS vector IDs (`v41690973` for CPI, `v2062815` for unemployment) could not be verified against live traffic during this build session (see BUILD_LOG.md) — if StatsCan has since renumbered either vector, that indicator will silently show "No data yet" until corrected. | Run `sync` once locally; if either StatsCan panel stays empty, look up the correct vector ID via StatsCan's table browser and update `src/indicators.py`. |
| History only grows from repeated `sync` calls — a fresh install has an empty dashboard until at least one sync, and useful week/month deltas need real elapsed time between syncs. | Ship the Quick Win `#2` deeper `--recent` backfill so a first run already has weeks of trend data instead of a single point. |
| The AI briefing is a single paragraph with no historical memory of prior briefings. | Persist each generated briefing alongside its date in the SQLite database so the dashboard can show "how the assessment has changed" over time. |
| No alerting — a large single-day CAD move requires the user to notice it by opening the dashboard. | Add a `--threshold` flag to `show` that exits non-zero (for cron/Routine use) when any indicator's day delta exceeds a configurable percentage. |
