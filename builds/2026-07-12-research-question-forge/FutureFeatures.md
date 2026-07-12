# Future Features — Research Question Forge

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **`--dry-run` flag on `generate`** — preview a batch without writing it to the library, so you can sample a few batches before committing to a save.
2. **Markdown/CSV export command** — `forge export --tag R01-empathy-aim2` dumps every question with that tag straight to a `.md` file formatted for pasting into a grant document, instead of copying items one at a time from the HTML viewer.
3. **`forge stats`** — a one-line CLI summary (total questions, count by testability, most-used tags, average novelty of the last batch) for a quick pulse-check without opening the HTML.

## Medium Effort (roughly one nightly build session)

4. **Taxonomy editor UI** — an in-browser form (backed by a small local write-back endpoint or a `forge taxonomy add` CLI command) to add new populations/constructs/outcomes/methods/frames without hand-editing `taxonomy.json`, so the tool grows with new research directions without needing a code change.
5. **Batch AI polish backfill** — `forge polish --unpolished` to run the Claude enrichment pass over every previously-saved template-sourced question in one go, for when a user generates a large batch without a key and later adds one.

## Ambitious Extensions (multi-session effort)

6. **Cross-reference against Paper Lens / PubMed Research Radar** — the 2026-06-23 and 2026-07-02 builds already pull and score real literature. A shared SQLite join (or a light API between the two tools) could flag when a generated question skeleton closely resembles work already surfaced by those tools, turning "is this novel against my own past generations" into "is this novel against the literature I've actually been reading" — a much stronger signal for grant writing.
7. **Grant-aim assembler** — group several starred, same-tag questions into a structured "Specific Aims" draft (aim statement, sub-questions, timeline placeholder), building on the existing tag field as the grouping key, and exporting a single formatted document instead of one question at a time.

---

## Possible Integration Points

- **2026-07-02 PubMed Research Radar** — could feed real recent-literature terms back into the novelty scorer as an additional negative signal (a "well-covered in the literature" flag alongside "already generated before").
- **2026-07-10 Worklog** — a generated-and-used question could be logged as a workstream checkpoint decision ("chose this research question for Aim 2"), giving the correlation engine a concrete artifact to point to.
- Future Category C (Personal Knowledge Tool) builds that index the user's own writing (in the spirit of 2026-07-11 Connectome) could use the same taxonomy file as a shared vocabulary for tagging notes by research construct.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Taxonomy is fixed at 10×10×10×7×7 dimensions, hand-authored once; it will feel repetitive well before the 6,928 valid combinations are exhausted in practice, because many combinations share the same population or construct | Add the taxonomy editor (Future Feature #4) so the library grows with the user's actual evolving research interests instead of staying static |
| Novelty scoring is a transparent Jaccard token-overlap heuristic, not a semantic similarity measure — two questions using different wording for the same idea won't be flagged as duplicates | Swap in a lightweight local embedding or synonym-normalization pass if scikit-learn/numpy become an acceptable dependency in a future build |
| AI polish calls the Anthropic API once per question with no batching, so a large `--polish` batch makes many sequential HTTP requests | Batch multiple skeletons into a single Claude call with a structured multi-question prompt when `--count` is large |
| No taxonomy validation on load — a hand-edited `taxonomy.json` with a malformed entry (missing `tags` key, etc.) will raise an unhandled `KeyError` rather than a clear error message | Add schema validation with a friendly error message pointing at the offending entry |
