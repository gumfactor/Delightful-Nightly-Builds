# Future Features — Star Atlas

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **`--export csv` on `list`/`search`** — dump matching repos as CSV for pasting into a spreadsheet or another tool, reusing the same query/filter logic already in `store.py`.
2. **Archived-repo flag** — GitHub's star API response includes `archived`; store it and let `list --exclude-archived` filter out repos that are no longer maintained, since a stale-but-starred repo is exactly the kind of noise this tool is meant to cut through.
3. **`stats --stale`** — surface repos starred over N days ago in a tag with only one member, as candidates for un-starring or re-review, using data already captured at sync time.

## Medium Effort (roughly one nightly build session)

4. **README-aware AI notes** — when `--ai` is set, optionally fetch each repo's README (already accessible via the same `GITHUB_TOKEN`) and include a short excerpt in the enrichment prompt, producing a much more specific "why useful" note than description/topics alone can support.
5. **Claude Code Skill wrapper** — ship a `/star-atlas-search` skill (same pattern as Promptbook's companion skill) so the library is searchable from inside a coding session without leaving the terminal.

## Ambitious Extensions (multi-session effort)

6. **Cross-reference with Promptbook and Throughline** — when a starred repo's name/topics match tools referenced in Promptbook's session-prompt corpus or Throughline's publication keywords, surface that link automatically, turning three separate personal-knowledge tools into one connected graph of "what I've built, what I've read, and what I've found."
7. **Duplicate/superseded detection** — many stars are forks or alternatives of the same underlying project; an AI pass that clusters near-duplicate stars (same purpose, different repo) would make the library meaningfully more useful than a flat list.

---

## Possible Integration Points

- **Promptbook (2026-09-03)** and **Throughline (2026-09-12)** are the two closest prior Category C builds — all three follow the same "mine a real personal data trail into a local SQLite knowledge base with optional AI enrichment" shape. A shared `render` theme/CSS module across all three (currently each ships its own copy) would be a good refactor if a future build touches this pattern again.
- **GitHub Repository Health Scorecard (2026-06-21)** already uses `GITHUB_TOKEN` for the user's own repos; Star Atlas is the same auth pattern applied to starred repos instead of owned ones. A future build could unify token/auth handling into a small shared helper if a fourth GitHub-API build is planned.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Rule-based tagging is keyword-only and can mis-tag ambiguous repos (e.g. a testing tool written to test AI models could match either "AI/ML" or "Testing & QA" depending on keyword order) | Run `--ai` enrichment as the default rather than opt-in once a user has confirmed their `ANTHROPIC_API_KEY` works, or let the ordered rule list be overridden per-project |
| No un-star / two-way sync — if a repo is un-starred on GitHub it stays in the local library forever | Add a `--prune` flag to `sync --full` that removes local rows not present in a full re-fetch |
| `search` uses `LIKE` substring matching, not real full-text ranking | Migrate to SQLite FTS5 if the library grows past a few hundred repos and ranking quality starts to matter |
| Organization-owned stars aren't included | Add an optional `--include-orgs` flag that also walks `GET /orgs/{org}/repos` combined with a manual "starred by me at org X" marker, since GitHub has no single starred-across-orgs endpoint |
