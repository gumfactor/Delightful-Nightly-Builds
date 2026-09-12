# Future Features — Throughline

1. **Co-author network graph.** Semantic Scholar's paper detail endpoint includes co-author lists; a simple force-directed or table view of frequent collaborators would surface patterns (e.g. which lab members appear across which thematic clusters) useful for supervision and mentorship tracking.

2. **Multi-source enrichment (PubMed/ORCID cross-reference).** Semantic Scholar's coverage of some journals/venues is incomplete. Cross-referencing against PubMed E-utilities (already used by this catalog's PubMed Research Radar build) or an ORCID id could catch papers Semantic Scholar misses and merge them into the same local corpus.

3. **Grant-cycle diffing.** A `throughline diff --since <date>` command comparing the corpus/clusters at two points in time would answer "what's new in my research program since my last grant renewal" directly, rather than requiring the user to eyeball citation-growth output.

4. **Per-cluster "gap" flagging.** Cross-reference cluster themes against a target list of keywords from a specific funding call or journal scope, and flag which of the user's existing themes are the best fit — turning the corpus into a grant-matching tool, not just a descriptive one.

5. **Export to BibTeX/biosketch format.** A `throughline export --format bibtex` (or a structured NIH biosketch-style text block per cluster) would let the narrative output be pasted directly into a grant application rather than requiring manual reformatting.

6. **Configurable clustering granularity.** Expose `--similarity-threshold` and `--top-n` as CLI flags (they are already parameters on `cluster_papers`, just not yet wired to argparse) so a user with a very large or very small corpus can tune cluster granularity without editing source.
