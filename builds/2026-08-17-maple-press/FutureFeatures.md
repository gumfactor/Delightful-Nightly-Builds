# Future Features — Maple Press

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **`--seasonal-auto` occasion flag** — a thin wrapper that maps the current UTC month to an occasion (November/December → holiday, June 28–July 5 → canada-day, late August → back-to-school) so a daily-cron use doesn't require remembering to pass `--occasion` manually. Kept out of tonight's core engine deliberately, since the deterministic core needed to stay clock-independent for full test coverage — this would live as a thin CLI-only convenience layer on top.
2. **`delete <id>` / `archive <id>` command** — pieces are permanently versioned by design (never overwritten), but a soft "archived" flag would let old, superseded drafts stop cluttering `list` output without actually destroying the history.
3. **`--min-confidence` filter** — when the CSV has a `confidence` column, let the user require e.g. `--min-confidence 0.7` in addition to `verdict == canadian`, for stricter editorial standards on higher-stakes pieces like gift guides.

## Medium Effort (roughly one nightly build session)

4. **A fifth piece type: "Then & Now" business profile** — for businesses with a `founded_year` field, generate a piece framing a business's growth story (founding → today), a genuinely different narrative shape from the current four, which are all roundup/comparison-oriented.
5. **Direct Provenance → Maple Press pipeline command** — a `from-provenance <provenance.db>` subcommand that reads directly from a Provenance SQLite database (rather than requiring an intermediate CSV export) and offers to generate one piece per category that just crossed the gift_guide/swap_it eligibility threshold since the last run.

## Ambitious Extensions (multi-session effort)

6. **French-language output** — The Canada List serves a bilingual Canadian audience; a `--lang fr` flag with parallel headline/intro/CTA formula banks (not machine-translated at generation time, but hand-authored French formulas going through the same deterministic engine) would make this a genuinely bilingual editorial tool rather than an English-only one.
7. **Lightweight image-suggestion layer** — pull each business's `website` field and attempt an og:image or logo scrape (with graceful degradation when unreachable) to suggest — never auto-embed — a hero image alongside each generated piece, closing more of the gap to "ready to publish."

---

## Possible Integration Points

- **Provenance (2026-08-15)** and **CanFile (2026-07-20)** — Maple Press's CSV schema (`verdict`/`confidence`/`evidence`) is deliberately Provenance-output-compatible today; a future build could make that connection a single command instead of a manual CSV export/import step (see Future Feature 5).
- **Ingest Gate (2026-08-10)** — a business CSV destined for Maple Press could be run through Ingest Gate first to catch malformed rows/encoding issues before generation, closing the loop from raw data → QC → verification → editorial copy entirely within Canada List tooling built across this catalog.
- **Voiceprint (2026-07-28)** — Voiceprint's AI-tell/Human-Voice-Score auditor could be pointed at Maple Press's `--ai-polish` output specifically, to check whether the AI polish pass is introducing the kind of generic phrasing Voiceprint was built to catch.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Headline formula bank is fixed and hand-authored (a handful of formulas per piece type/occasion) — heavy repeat use on the same category will eventually exhaust genuinely novel headline options within one occasion. | Expand the formula bank per piece type, or add a formula-generation layer (e.g. combinatorial slot-filling like Bridgework/Research Question Forge) rather than a flat list. |
| `--ai-polish` sends the entire assembled draft in one call with no length cap; a very large `gift_guide` (many businesses selected) could produce a long prompt. | Add a business-count soft cap per piece type, or chunk the AI polish call per business card and reassemble. |
| Province/category matching is exact-string, case-insensitive only — "BC" and "British Columbia" are treated as different provinces. | Add a small Canadian province/territory name-and-abbreviation normalization table, matching the pattern Ingest Gate already uses for its own field normalization. |
