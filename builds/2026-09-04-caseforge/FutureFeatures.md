# Future Features — CaseForge

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Course presets** — a small `--course "Stress and Coping"` → default `--query` lookup table seeded from PROFILE.md's three named courses, so the user can run `generate --course "Stress and Coping"` without typing a search query every time, while still allowing `--query` to override it.
2. **`export bibtex`** — reuse Citation Vault's (2026-07-29) BibTeX export shape so a case's source article can be dropped straight into a syllabus reference list, not just read as a case.
3. **`delete <pmid>`** — a CLI command to remove a case from the library, useful when a generated case turns out to be a poor fit for a particular lecture.
4. **`--sort recent|relevance`** on `generate`'s PubMed search (currently hardcoded to `sort=relevance`), so a user preparing a "what's new" seminar section can pull the most recently published matches instead.

## Medium Effort (roughly one nightly build session)

5. **Difficulty/readability scoring** — compute a Flesch-Kincaid grade level on the rendered vignette and surface it as a badge, so the `--register public` vs `--register undergrad` distinction becomes independently verifiable rather than just an AI-prompt instruction.
6. **Cross-case thematic clustering** — once a course's library grows past a handful of cases, a lightweight keyword-overlap pass (the same Jaccard approach used by Research Question Forge and Bridgework) could group cases into thematic units for a syllabus, not just a flat per-course list.
7. **PDF handout export** — a `render --print` mode already exists via the dashboard's print stylesheet, but a dedicated one-case-per-page PDF export (reusing a stdlib-only or already-approved PDF library) would be more directly classroom-usable than "open in browser, then print."

## Ambitious Extensions (multi-session effort)

8. **OpenAlex-sourced case generation** — extend `pubmed_client.py`'s interface to a second, interchangeable backend hitting the free OpenAlex API (already used by Impact Ledger, 2026-08-05), which would pull in non-PubMed-indexed venues relevant to the AI Applications for Psychologists course and give broader topic coverage than PubMed alone offers.
9. **Semester syllabus assembly** — a mode that takes a full course outline (e.g. Curriculum Atlas's, 2026-08-16, extracted concept list) and auto-generates one case per week/unit, closing the loop between "what I'm teaching" and "what real literature backs it up."

---

## Possible Integration Points

- **Curriculum Atlas** (2026-08-16) already extracts per-course concepts from the user's own syllabi/lecture text — its concept list would be a natural `--query` source for CaseForge, replacing manually typed search terms with concepts the user has already taught.
- **Citation Vault** (2026-07-29) already tracks a to-read → cited reading workflow with BibTeX export; a shared export format would let a CaseForge case graduate into a citable reference once actually used in a course.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Fact extraction is regex/keyword-based and will miss statistics reported in unconventional phrasing (e.g. "the correlation was moderate" with no numeric value stated) | Would need either a broader pattern library or an AI-assisted extraction pass with the same fact-presence safety net already used for vignette polishing |
| The methodology tag only reports a single best match per abstract, even when a study genuinely combines methods (e.g. an fMRI study that is also longitudinal) | Extend `extract_methodology` to return a list of all matching tags instead of the first match |
| PubMed E-utilities' abstract-only access means the tool cannot ground cases in results, figures, or discussion sections beyond what the abstract itself reports | Out of scope without a full-text API; document clearly in the case UI when a claim is abstract-only |
| No de-duplication across similar/overlapping queries for the same course (e.g. "cortisol stress" and "cortisol reactivity" could pull overlapping PMIDs, which is handled, but conceptually near-duplicate studies are not flagged) | Add a title-similarity check at generation time and warn on near-duplicate cases within the same course |
