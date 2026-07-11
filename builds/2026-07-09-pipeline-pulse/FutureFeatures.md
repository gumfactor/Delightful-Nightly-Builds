# Future Features — Pipeline Pulse

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **PR number in the "Needs attention" links** — Once GitHub API access works reliably from wherever this is run, resolve the compare link to the actual PR number/URL instead of the generic `/compare/main...branch` redirect, so the link opens the existing PR directly rather than requiring GitHub to redirect it.
2. **`--json` output mode** — Emit the `Summary` dict as JSON to stdout (in addition to, or instead of, the HTML file) so the numbers can be piped into another tool or a future "Morning Briefing"-style build.
3. **Configurable attention list length** — Expose `attention_limit` as a `--top N` CLI flag instead of hardcoding 10.
4. **Merge-age warning threshold** — Color the "backlog" badge orange vs. red based on a configurable day threshold (e.g. >14 days = red) instead of a flat red for any backlog item.

## Medium Effort (roughly one nightly build session)

5. **Historical snapshots** — Write each run's summary stats to a small local JSON/SQLite log (inside this build's own folder) so a future run can show a "backlog size over time" trend line, not just a point-in-time snapshot.
6. **Idea backlog integration** — Cross-reference `builds/ideas.md` alongside `builds/index.md`: show pending-idea pool size per category, and flag categories whose pending pool has gone stale (no draws in N rotations). This is the "Idea Backlog Visualizer" idea logged in `builds/ideas.md` tonight — natural to fold into this dashboard rather than build standalone.
7. **Real GitHub PR metadata when available** — When run somewhere with genuine `GITHUB_TOKEN`/`gh` access (e.g. the user's own machine, or a GitHub Actions job), optionally enrich each backlog row with actual PR state (draft/open/has-reviews, CI status) instead of relying solely on git ancestry. Should stay optional/best-effort so the tool keeps working with zero token access, as verified tonight.

## Ambitious Extensions (multi-session effort)

8. **One-click merge helper** — A `--merge-oldest` flag that (after an explicit confirmation prompt) fast-forwards/merges the oldest clean, conflict-free backlog branch into `main` locally, turning the dashboard from purely observational into an active pipeline-clearing tool.
9. **Rating nudge loop** — Combine the rating-coverage stat with an interactive terminal prompt (or a generated checklist file) that walks the user through rating the N oldest unrated-but-merged builds in one sitting, closing the loop between "what needs attention" and actually acting on it.

---

## Possible Integration Points

- **Morning Briefing** (2026-06-22) already combines GitHub/portfolio/weather signals into one daily digest — Pipeline Pulse's summary numbers (backlog count, oldest unmerged) would be a natural additional section there once both tools can assume the same GitHub access.
- **Project Pulse: Multi-Project Context Manager** (2026-06-29) tracks staleness across multiple projects generically — this build is effectively a Project Pulse view specialized for the nightly-build system itself; the staleness-badge visual language from Project Pulse could be reused directly for the backlog age buckets here.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Branch-to-build-folder matching assumes each branch introduces at most one new dated folder; a branch that touches multiple build folders (e.g. a batch fix) could misattribute one folder's origin. | Match on exact date-prefixed folder path rather than "first branch found," and warn (rather than silently pick one) when more than one branch introduces the same folder. |
| No GitHub PR review/CI state — only "merged into default branch or not," derived from git alone. | See Future Feature 7 above — add real API enrichment as an optional, best-effort layer once reliable token access is confirmed in the target environment. |
| Chart.js is loaded from a CDN; charts silently degrade to a text fallback if that CDN is blocked (verified tonight, since this session's own sandbox blocks it) — the numbers are all still visible in the hero tiles and table, but the visual charts are lost in that scenario. | Vendor a local copy of Chart.js inside the build folder as a fallback `<script>` source, or accept the CDN dependency as intentional (consistent with the rest of this repo's Chart.js-based builds) and just document it. |
