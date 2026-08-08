# Future Features — Panel Prep

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **`diff` command** — Show what changed between two versions of the same project: which checklist items newly passed/failed and how each persona's score moved, so a revision's actual delta is explicit instead of implied by two separate `history` rows.
2. **`--strict` checklist mode** — An optional flag that adds a handful of harder checks (e.g. requiring the sample-size justification to include an actual number via regex, not just the phrase "power analysis") for users who want the tool to push back harder.
3. **Configurable persona weights via a JSON file** — Let the user tune how much each persona weighs Approach vs. Significance vs. Innovation, for fields where the standard NIH balance doesn't quite fit (e.g. a K-award emphasizes Investigator/Approach more than a typical R01).
4. **`export --format bibtex-style-citation-list`** — Not applicable here, but a `export --format markdown` command that dumps the latest full critique (checklist + personas + resume) as a single Markdown file the user can paste directly into a personal notes system would be a genuinely cheap add.

## Medium Effort (roughly one nightly build session)

5. **NSF-mode rubric** — A second, parallel scoring mode using NSF's Intellectual Merit / Broader Impacts criteria instead of NIH's Significance/Innovation/Approach, selectable with `--rubric nsf`, for the user's non-NIH submissions.
6. **Aggregate dashboard across all projects** — A `render-all` command producing one HTML page summarizing every project's latest score and trend, mirroring the multi-repo dashboards several prior builds in this catalog already do for GitHub data.
7. **Section-level AI rewrite suggestions** — Beyond scoring, an opt-in mode where Claude proposes a specific rewritten sentence or two for the single weakest-scoring section, always shown as a diff/suggestion the user accepts or rejects manually — never auto-applied.

## Ambitious Extensions (multi-session effort)

8. **Cross-reference against Protocol Forge and Citation Vault** — When a project shares a name/tag with an existing Protocol Forge ethics protocol or cites papers already logged in Citation Vault, surface those automatically in the critique (e.g. "your Significance section doesn't cite the 3 most relevant papers already logged as `read` for this topic in Citation Vault") — a genuinely new capability no single build in this catalog can provide alone.
9. **A real historical calibration set** — If the user is ever willing to manually log a handful of their own past proposals' actual study-section outcomes (funded/not funded, real percentile if disclosed), the deterministic scorer's weights could be tuned against real outcomes instead of hand-authored defaults, turning this from "plausible heuristic" into an evidence-calibrated tool.

---

## Possible Integration Points

- **Protocol Forge** (2026-07-19) already produces ethics/compliance-checked boilerplate for the same proposals this tool critiques for content — a shared project-name convention between the two tools (and eventually a shared SQLite file or cross-read) would let one proposal's full lifecycle, from ethics drafting through content critique, live in one place.
- **Citation Vault** (2026-07-29) already tracks which papers the user has read and tagged by topic — a natural extension (see Ambitious Extensions above) is cross-referencing a proposal's Significance section against relevant, already-logged reading.
- **Voiceprint** (2026-07-28) audits prose for AI-tells and readability; running a proposal draft through both tools (content critique here, prose-quality there) covers two genuinely different failure modes without overlap.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| The checklist can only detect whether relevant *language* appears, not whether the underlying claim is actually correct (e.g. a nonsensical power analysis still passes the check) | Add `--strict` numeric validation for a handful of checks where a real number can be regex-extracted and sanity-checked (see Quick Win #2) |
| Investigator and Environment NIH criteria are never scored, so the overall Impact estimate is necessarily partial compared to a real study section's five-criteria view | Document this clearly in `Manual.md` (done) rather than fabricate scores; a future build could accept an optional biosketch/facilities text file to legitimately extend scoring to those two criteria |
| The section parser is heuristic and can mis-split unusually formatted drafts (e.g. headers embedded mid-paragraph) | Ship a `--dry-run-parse` flag that prints just the detected sections before running the full review, so a user can catch a bad split before wasting an AI call |
| No way to mark a version as the one actually submitted vs. a rough intermediate draft | Add an optional `--tag submitted` flag on `submit` and surface it in `history`/the HTML report |
