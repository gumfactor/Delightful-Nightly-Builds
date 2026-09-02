# Future Features — CiteForge

1. **NLM/journal-abbreviation database.** Ship a lookup table (or fetch NLM's public journal-title-abbreviation list once and cache it locally) so AMA/Vancouver output uses real abbreviated journal names instead of the full name, closing the biggest documented limitation.

2. **Manuscript-aware in-text citation numbering.** Scan an actual manuscript file for citation-key markers (e.g. `[@smith2020]`) and number AMA/Vancouver in-text citations by first-appearance order in that manuscript, rather than by library-import order.

3. **A proper-noun-aware sentence-case converter.** Ship a small curated list of common proper nouns (country names, major cities, common scientific terms like "COVID-19") that sentence-case should preserve, reducing the "United States" → "united states" class of miscasing without needing a full NLP pipeline.

4. **Reference-type coverage beyond journal-article/book/webpage.** Add real templates for conference proceedings, datasets, and reports/theses instead of falling back to a generic template for those BibTeX types.

5. **Duplicate/near-duplicate detection across the whole library** — not just exact-DOI or exact-author/year/title dedup, but a fuzzy title-similarity pass that flags likely duplicates (e.g. the same paper added once via BibTeX and once via DOI with a slightly different title string) for manual review.

6. **A `diff` command** that shows what changed in a formatted reference between two `render`/`format` runs — useful when iterating on a manuscript's reference list over multiple revisions.

7. **MLA and Harvard style modules**, using the same `styles/` plugin shape already established, to cover the two other citation styles most commonly requested outside STEM/medical/social-science journals.
