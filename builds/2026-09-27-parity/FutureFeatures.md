# Future Features — Parity

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Per-project drift breakdown** — Group the `teamwork_only` and `status_conflict` buckets by `project_id` on the dashboard so a multi-project setup shows which specific project is drifting, not just an aggregate number.
2. **`--threshold` CLI override** — Expose `match_threshold` as a `sync` flag in addition to `config.json`, so a noisy match rate can be tuned without editing the config file.
3. **CSV export of the latest run** — A `parity export --out gaps.csv` subcommand mirroring Ledger Lens/Eligible Spend's CSV-export pattern, for pasting gap items directly into an email or a Coda table.

## Medium Effort (roughly one nightly build session)

4. **"Stale coda-only" aging view** — Track how many consecutive sync runs a `coda_only` item has persisted unmatched, and surface a dedicated "aging" list (e.g. "planned in Coda 4 syncs ago, still not in Teamwork") — the single most actionable signal this tool could add, since a one-sync gap is normal but a persistent one is the real problem.
5. **Routine wrapper** — Package `parity sync && parity render` as a Claude Code Routine that runs on a schedule (e.g. weekly) and only surfaces a notification when the gap count grows, rather than requiring the user to remember to run it. This is the natural "pull tool" upgrade path CLAUDE.md recommends for productivity tools.
6. **Multi-doc / multi-table Coda support** — Currently one Coda doc/table per sync. Real usage across The Canada List, Kwyeter, and the lab likely spans several Coda docs; support a list of `{doc_id, table_id}` pairs in config and tag each row with its source doc.

## Ambitious Extensions (multi-session effort)

7. **Guarded write-back** — An explicit, confirmation-gated `parity apply` command that can create a missing Teamwork task from a `coda_only` row (or vice versa) or fix a `status_conflict` — turning Parity from a read-only auditor into an active synchronization tool. This is real scope creep and was deliberately kept out of tonight's build (see PRD.md's Out of Scope) because write access to two live production tools is a materially different risk profile than read-only reconciliation.
8. **Semantic-similarity matching** — Replace or supplement the Jaccard token-set matcher with an embedding-based similarity (e.g. a small local sentence-embedding model) to catch matches with zero shared tokens but the same meaning ("Fix login bug" vs "Resolve authentication issue") — the matcher's current design explicitly isolates similarity scoring in one function, so swapping the scoring function later is a contained change.

---

## Possible Integration Points

- **Project Pulse** (2026-06-29) already syncs GitHub commit activity into a project-context dashboard; a future build could feed Parity's drift counts into Project Pulse's staleness scoring as a fourth signal (alongside commit recency) for "is this project actually moving."
- **Renewal Radar** (2026-08-22) established the pattern of a self-contained dashboard tracking multiple live sources with graceful per-source degradation on failure — Parity's dashboard and briefing modules follow the same shape and could share a common "Category I dashboard shell" if a future build wants to formalize that.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Matching is title-only; two genuinely different tasks with coincidentally similar wording could false-match | Add a secondary signal (due date proximity, project/table tag matching) to the greedy matcher's tie-breaking before falling back to pure title similarity |
| A single Coda table and a fixed list of Teamwork project IDs per sync — no auto-discovery | Add a `parity discover` command that lists available Teamwork projects and Coda docs/tables the configured API key can see, so config.json can be built without hand-copying IDs from each tool's UI |
| No alerting — the user has to remember to run `parity sync` and check the dashboard | Quick Win #5 above (Routine wrapper) is the direct fix |
| The Jaccard matcher has no memory across syncs — a manually-confirmed "these are actually different tasks" pair will be re-evaluated identically next time | Persist a small "ignore this pairing" list keyed on the two titles' normalized token sets, checked before the matcher proposes it again |
| `TeamworkClient.fetch_tasks` now fetches every task ever created in a project (both completed and open), since the matcher needs both sides' done/open state to catch status conflicts — on a project with years of history this could mean many pages per sync | Add an optional `updated_after`/`created_after` cutoff (Teamwork's API supports date filtering) so only recently-touched tasks are considered, trading a small chance of missing a very old status conflict for materially faster syncs |
