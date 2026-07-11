# Future Features — TrialScope: Behavioral & Reaction-Time Data QC Explorer

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **JSON input support** — Accept a JSON array of trial records (the native export format of jsPsych) in addition to CSV, using the same column-role auto-detection logic against JSON keys instead of a CSV header.
2. **Export to XLSX** — Add an `--xlsx` flag that writes `cleaned_data.csv`'s content to an Excel workbook with the QC flags conditionally highlighted, since many collaborators expect Excel over CSV.
3. **Per-subject detail view** — Add a click-through from each subject table row to a per-subject mini-report (their own RT histogram and trial-by-trial flag timeline) within the same HTML file, using a simple show/hide toggle in the existing vanilla JS.

## Medium Effort (roughly one nightly build session)

4. **Multiple-file batch mode** — Point TrialScope at a directory of per-session CSVs (common when each participant's data is a separate file) and produce one combined report across all sessions, with a per-file parsing-error summary so a single malformed file doesn't block the whole batch.
5. **Configurable multi-alternative chance rate per condition** — Currently `--chance-rate` is a single global value; many studies mix a 2AFC block with a 4AFC block. Support a per-condition chance rate (e.g., a small config file or `--chance-rate condition:rate` repeated flag).

## Ambitious Extensions (multi-session effort)

6. **Pre-registration mode** — Let the user save a named QC configuration (thresholds + column mapping) as a small JSON file *before* seeing any data, then require the report to declare which named configuration produced it. This directly supports the "pre-registered exclusion criteria" framing already used in the generated methods paragraph, making the whole workflow more rigorous and audit-friendly.
7. **Longitudinal/multi-session subject tracking** — Extend beyond a single input file to track the same subject IDs across multiple experimental sessions over time, flagging subjects whose data quality is degrading across sessions (useful for multi-visit studies).

---

## Possible Integration Points

- The Jun 17 Qualtrics Survey Data Inspector and this build share the same "local research-data QC → dark-mode HTML report → AI-or-template summary paragraph" architecture. A shared internal library for that report shell (CSS, sortable-table JS, SVG chart helpers) would let future research-data-QC builds skip re-implementing the same report chrome — worth extracting if a third build in this family gets built.
- None of the existing builds process trial-level behavioral data, so there's no other integration point in the current catalog yet.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| No wide-format (one row per subject) input support | Add a `--format wide` mode with a melt/reshape step ahead of the existing long-format pipeline |
| Chance-level binomial test has low power at very small trial counts, which can flag high-accuracy subjects with few trials | Surface the achieved statistical power (or minimum accuracy needed to be conclusive at the current n) directly in the report next to the flag, so it reads as "inconclusive" rather than "chance-level" when n is small |
| Single global chance rate across all conditions | See Medium Effort item 5 above — per-condition chance rate support |
| No persistence between runs (each run is stateless) | Add an optional SQLite store keyed by subject ID to track QC history across repeated runs on updated data, if this becomes a tool used repeatedly on a growing dataset |
