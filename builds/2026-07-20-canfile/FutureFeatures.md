# Future Features — CanFile: Canadian Ownership Knowledge Cards

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Ambiguous-match warning** — When `search_entity` returns more than one plausible candidate, `add` currently silently picks the top-ranked hit. Print the runner-up candidates (with their Wikidata descriptions) so the user can immediately spot a mismatch, and let `add --qid Q123` bypass search entirely when the user already knows the correct entity.
2. **Bulk `add` from a text file** — `canfile add-batch companies.txt`, one company name per line, looping over `add_company` with a short delay between requests to stay polite to the free Wikidata/Wikipedia APIs.
3. **CSV export** — A `export-csv` command alongside `export-html`, for pulling the latest verdict/confidence per company into a spreadsheet for The Canada List's own editorial workflow.

## Medium Effort (roughly one nightly build session)

4. **Scheduled re-check as a Claude Code Routine** — Wikidata facts change over time (acquisitions, HQ moves). A weekly Routine that re-runs `add` for every company already in `canfile.db` would build the version history this tool already supports into a genuine "did anything change" alert, rather than requiring the user to remember to re-run it.
5. **Confidence-aware review queue** — A `review` command that lists only `uncertain` and `insufficient-data` cards, prompting the user for a one-line manual override note that gets stored as a special "human-verified" version — closing the loop between the automated rule engine and editorial judgment for The Canada List.

## Ambitious Extensions (multi-session effort)

6. **Full ownership chain traversal** — Right now the tool resolves one hop of parent/owner. A recursive walk up the ownership graph (with cycle detection and a depth cap) would correctly handle multi-layer holding structures (e.g. a Canadian brand owned by a US private equity fund owned by a larger international group).
7. **MCP server wrapper** — Expose `add`/`show`/`search` as MCP tools so any Claude Code session (not just this CLI) can look up a company's ownership status inline while writing Canada List content — turning this from a build-then-run tool into something callable mid-conversation.

---

## Possible Integration Points

- **The Canada List CSV Quality Inspector** (`builds/ideas.md` #1, pending) — if built, CanFile's knowledge cards could become the ownership-verification step in that ingestion pipeline, flagging submissions whose claimed Canadian-ownership status disagrees with CanFile's Wikidata-derived verdict.
- **Connectome** (2026-07-11) — Connectome indexes the user's own Markdown notes; a future integration could let CanFile write each new knowledge card as a Connectome-indexable note, so ownership research surfaces alongside the user's other notes in one search.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Only resolves one hop of parent/owner ownership | Recursive multi-hop traversal (see Ambitious Extension #6) |
| No disambiguation UI when Wikidata search returns multiple strong candidates — top match is used silently | Quick Win #1 above |
| Wikidata's `country` (P17) property sometimes reflects legal incorporation jurisdiction rather than genuine "who benefits" ownership (e.g. a shell entity) | Document this caveat prominently in the HTML report itself, and treat `country`-only verdicts (no parent data at all) as one notch lower confidence than they currently are |
| No rate limiting on repeated `add` calls | Add a small delay / exponential backoff before Quick Win #2 (bulk `add`) ships, to stay within Wikidata/Wikipedia's fair-use expectations |
| Claude enrichment prompt does not ask for a citation count / structured output — it's free text | Move to a structured tool-call response if a future session wants machine-checkable citation verification |
