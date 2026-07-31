# FutureFeatures.md

Enhancements to a working, valuable tool — not gaps required to make tonight's build usable.

1. **Google Scholar / Semantic Scholar cross-referencing.** PubMed covers indexed biomedical journals well but misses preprints and some conference proceedings. Semantic Scholar has a free public API (no auth) that could add citation counts and "cited by" tracking per article, surfacing which new papers are already getting picked up.

2. **Recurring Routine wrapper.** Ship a Claude Code Routine that runs `fetch` + `report` automatically every morning and only notifies if new high-relevance (≥8) articles were found, turning this from a pull tool into a genuine push digest — matching the "Routines" pattern PROFILE.md calls out for recurring tasks.

3. **Per-topic notification threshold and digest email.** Let each topic define its own relevance floor (e.g., "only tell me about Forensic Neuroscience hits above 8, but show everything for Empathy"), and generate a plain-text digest suitable for piping into an existing email workflow.

4. **Full-text PDF ingestion for open-access articles.** PubMed Central (PMC) hosts full text for open-access articles and is reachable through the same E-utilities family (`efetch` with `db=pmc`). Detecting PMC availability and pulling full text (not just the abstract) would let the AI summary quote actual methods/results details instead of working from the abstract alone.

5. **Server-persisted star/read state.** The `articles` table already has `starred`/`read_state` columns reserved for this; wiring up a tiny local Flask/http.server endpoint (or a `radar mark-read <pmid>` CLI command) would let star/read state survive a report regeneration instead of living only in browser `localStorage`.

6. **Topic-query assistant.** Use Claude to translate a plain-English research interest ("papers on how childhood trauma affects adult stress reactivity") into a well-formed PubMed query string automatically, instead of requiring the user to hand-write MeSH/tiab syntax via `topics add`.

7. **Weekly trend view.** Track relevance-score distribution and per-topic article volume over time (a small `trend` table keyed by ISO week) and chart it in the HTML report — useful for noticing when a topic goes quiet or suddenly heats up.
