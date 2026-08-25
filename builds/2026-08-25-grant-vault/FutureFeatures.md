# Future Features — Grant Vault

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **`--json` output for `search`/`stats`** — a `--json` flag on both commands that prints machine-readable output instead of the human-formatted terminal report, so the CLI can be piped into other scripts (e.g. a "paste the top 3 Broader Impacts chunks into my draft" helper).
2. **Full-chunk `show <id>`** — a `show <chunk-id>` subcommand that prints one chunk's complete, un-truncated text plus all metadata, since `search` currently only shows a 150-character preview.
3. **`.gitignore`-style ignore file for `ingest`** — an optional `.grantvaultignore` in the ingested folder to skip specific files (drafts-in-progress, non-grant notes that happen to live in the same folder) without moving them elsewhere.

## Medium Effort (roughly one nightly build session)

4. **PDF ingestion** — extract text from `.pdf` grant exports (a common format for downloaded past submissions) using a lightweight pure-Python PDF text extractor, feeding the same chunking/classification/scoring pipeline. This was explicitly deferred tonight to keep scope to plain text/Markdown.
5. **Near-duplicate detection across documents** — flag when two stored chunks are highly similar (e.g. the same Broader Impacts paragraph reused verbatim across three past grants), so the library surfaces one canonical version instead of near-identical duplicates cluttering search results.
6. **Reusability score explanation** — a `--why` flag on `search` results that prints which specific rule fired (length band, which specificity signal, generic-bonus keyword) for a chunk's score, turning the scorer from a black box into a teaching tool for what makes grant prose portable.

## Ambitious Extensions (multi-session effort)

7. **Draft assembly mode** — given a target section type and a rough outline, retrieve the top-N highest-reuse chunks for that section and AI-stitch them into a first-draft paragraph (clearly marked as a draft requiring the user's own editing), turning Grant Vault from a retrieval tool into a genuine first-draft accelerator. This is the natural next step beyond tonight's explicitly-scoped "retrieval, not generation" boundary.
8. **Funder-specific tagging** — cross-reference ingested documents against GrantScope's (2026-07-14) NIH RePORTER data or manually-tagged funder/mechanism metadata, so search can filter by "language that worked for an R01" vs. "language that worked for a foundation letter of intent."

---

## Possible Integration Points

- **GrantScope** (2026-07-14, Category F) discovers external funding opportunities; Grant Vault could surface its own most-relevant chunks alongside a GrantScope funding hit ("you found a matching NIH RePORTER grant — here's your best prior Significance language for this topic").
- **Effort Ledger** (2026-08-19, Category F) audits budget-compliance math; Grant Vault's Budget Justification chunks are narrative language, not the numbers themselves, so the two are complementary rather than overlapping — a future integration could link a Budget Justification chunk to the Effort Ledger run that validated its underlying numbers.
- **Deadline Guardian** (2026-07-17, Category I) tracks submission deadlines; a future version could prompt "your R01 resubmission is due in 3 weeks — here are your highest-reuse chunks for that mechanism" at the right moment instead of requiring the user to remember to run `search`.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Plain text/Markdown only — most real grant archives are `.docx`/`.pdf` | Add a PDF/DOCX text-extraction step ahead of the existing chunking pipeline (see Future Feature #4) |
| The reusability scorer is a heuristic, not a learned model — it can misjudge unusual prose styles | Add the `--why` explanation flag (#6) so misjudgments are at least transparent and correctable by hand-editing the stored tier |
| Search ranking is simple token-overlap counting, not semantic similarity | A future version could add an optional local embedding-based re-ranker, keeping the current approach as the zero-dependency default |
| No way to edit or delete an individual chunk once ingested (only whole-document re-ingest) | Add `edit <chunk-id>` and `delete <chunk-id>` subcommands for manual curation |
