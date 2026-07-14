# Future Features — GrantScope

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Custom topic editor** — Add a `topics add/remove` CLI command backed by a local JSON override file, so new saved topics (or edits to the default five) don't require touching source code.
2. **CSV/JSON export** — Add an `export --topic KEY --format csv` command that dumps a topic's stored projects for use in Excel or a grant-writing document, mirroring the export patterns already used in other builds (Ledger Lens, TrialScope).
3. **`--years` presets** — Add named shortcuts like `--recent` (last 2 fiscal years) and `--all` (widest available window) instead of requiring an explicit year list every time.

## Medium Effort (roughly one nightly build session)

4. **Similar-PI / potential-collaborator surfacing** — Cluster projects by overlapping keywords (using the existing `extract_keywords` groundwork) to surface researchers working on adjacent problems — a genuine "who should I reach out to" layer, not just a funding summary.
5. **Multi-source funding data** — Add NSF Award Search API (also free/no-auth) as a second data source alongside NIH RePORTER, with a `source` column distinguishing NIH vs. NSF projects in the same dashboard.
6. **Trend delta view** — Compare two `sync` snapshots over time (e.g., this quarter vs. last) to show which institutes/mechanisms are gaining or losing share, rather than only a point-in-time picture.

## Ambitious Extensions (multi-session effort)

7. **Grant deadline calendar integration** — Cross-reference the funding-mechanism/IC patterns this tool surfaces against NIH's published upcoming funding opportunity announcements (FOAs), and flag currently-open FOAs that match the user's strongest topic areas.
8. **Full proposal-positioning assistant** — Extend the AI briefing into an interactive mode: given a draft one-paragraph project summary, have Claude compare it against the current funding landscape data stored locally and suggest which IC/mechanism to target and how to frame the significance section.

---

## Possible Integration Points

- **Research Question Forge** (2026-07-12) generates novel, testability-scored research question skeletons for this same domain — a natural pairing would be cross-referencing a generated research question against GrantScope's funding landscape to flag which questions have active funding momentum behind them versus which are more speculative/underfunded.
- **Connectome** (2026-07-11) indexes the user's own notes into a local knowledge base with concept extraction — GrantScope's `extract_keywords` uses the same lightweight term-frequency approach, so a shared "concept vocabulary" between the two tools could eventually let a Connectome note about a research idea surface matching GrantScope funding data automatically.
- **PubMed Research Radar** (2026-07-02) already tracks the literature side of these same five research domains — GrantScope tracks the funding side. A future build could merge the two into a single "research landscape" view: what's being published vs. what's being funded, for the same topic set.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Only NIH RePORTER is queried; NSF, DoD, and private-foundation funding (all relevant to neuroscience research) are invisible to this tool | Add NSF Award Search API as a second source (see Medium Effort #5 above) |
| PI names are stored as a single string with no disambiguation — two different researchers who share a name would be conflated in any future collaborator-matching feature | Store NIH's `PiProfileId` (a stable numeric PI identifier the API already returns) alongside the display name |
| The keyword extractor is a simple stopword-filtered word-frequency count, not true TF-IDF — common domain words (e.g. "neural", "brain") can crowd out more specific, more useful terms | Weight terms by corpus-wide document frequency (rare-across-topics terms scored higher), same approach Connectome already uses for its concept extraction |
| `sync` re-fetches every project on every run rather than only fetching what changed since the last sync | Use NIH RePORTER's `fiscal_years` + a stored `last_synced_at` per topic to only pull recent award years on incremental syncs |
