# Future Features — Ingest Gate

Concrete enhancements deliberately left out of tonight's build.

1. **Fuzzy near-duplicate matching.** Tonight's dedupe is exact-normalized-key only ("Tim Hortons" vs "Tim Hortons " vs "https://timhortons.ca/" all catch correctly, but "Tim Hortons" vs "Tim Horton's" does not). A Levenshtein-distance or token-Jaccard-similarity pass over the `unique` columns, with a configurable similarity threshold, would catch these — surfaced as a lower-confidence "possible duplicate" warning rather than a hard error, since fuzzy matches need human judgment.

2. **Multi-file diff mode.** Compare two CSV exports (e.g. this week's vs. last week's) to show which rows are new, which were removed, and which changed field values — useful for auditing what a pipeline run actually did before trusting it.

3. **Per-column value distribution view.** For `enum` and low-cardinality `text` columns, show a quick bar chart of value frequency in the Schema tab — useful for spotting a category that should have been in the enum whitelist but wasn't (currently these only show up individually as `invalid_enum` rows in the issues table, not aggregated).

4. **Saved schema profiles.** The current schema is a single localStorage slot. If the operator manages more than one CSV pipeline (e.g. businesses vs. products) they need distinct schemas — named, switchable profiles would remove the need to re-import a JSON file every time.

5. **Batch validation via folder drop.** Accept multiple CSV files at once (drag a folder or select multiple files) and produce one summary table across all of them, so a whole week's worth of incremental exports can be checked in one pass instead of one file at a time.

6. **Configurable severity overrides.** Some operators may want `unexpected_column` or `whitespace` promoted to a blocking error (stricter pipelines), or `invalid_date` demoted to a warning (looser pipelines). A per-code severity override in the Schema tab would let the tool match house rules instead of the fixed error/warning split shipped tonight.
