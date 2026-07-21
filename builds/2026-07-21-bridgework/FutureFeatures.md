# Future Features — Bridgework

1. **Course/chapter tagging.** Let a generated entry be tagged with the specific course (Stress and Coping, Social Affective Neuroscience, AI Applications for Psychologists) or book chapter it's intended for, and filter/export by that tag — turns the library into a real per-course or per-chapter working set instead of one flat pool.

2. **User curation (favorite/reject).** An append-only library is right for never losing an analogy, but there's no way yet to mark "this one is good, use it" versus "this one didn't land." A lightweight `favorite`/`reject` flag (a new column, still never deleting rows) would let `export` and `render` default to favorites only.

3. **Custom taxonomy extension.** The 20 concepts and 12 domains are hand-curated for tonight's scope. A `bridgework add-concept`/`add-domain` command (validated against the existing mechanism-type system) would let the taxonomy grow to cover new lecture topics or a wider set of everyday domains without a code change.

4. **Batch generation with an explicit coverage target.** `generate --until-coverage 50%` that keeps generating (subject to a hard cap) until a stated fraction of the 291 valid triples has at least one entry, rather than specifying a raw count.

5. **Analogy chains for a single talk.** A `bridgework outline <concept-list>` command that picks one strong analogy per concept in a specified sequence and exports them as a single ordered Markdown outline — closer to "build me the analogy section of Tuesday's talk" than one-at-a-time generation.

6. **Audience-specific reading level scoring.** A simple heuristic (e.g., average sentence length, syllable count) scored against each audience register's target, flagged in `list`/`render` output, so an "undergrad_lecture" entry that reads at book-chapter complexity is easy to spot and regenerate.

7. **A/B variant generation.** For a single (concept, domain, audience) triple, generate 2-3 AI-polished variants in one call and let the user pick a favorite, rather than only ever getting the one the AI returns.
