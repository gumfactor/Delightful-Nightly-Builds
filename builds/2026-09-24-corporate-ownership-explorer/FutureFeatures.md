# Future Features — Corporate Ownership Chain Explorer

1. **Multi-parent display for joint ventures.** Right now the explorer collapses to one "primary" parent per hop (`choosePrimaryParent`) when Wikidata records more than one. A fuller view would show all recorded parents at a hop with their relative ownership share when Wikidata has it, rather than picking one deterministically and hiding the rest.

2. **Full downward subsidiary tree, not just one hop.** Subsidiaries currently expand lazily one click at a time. A "expand all" mode that walks the full subsidiary tree (with the same cycle/depth protection already built for the parent chain) would suit a full corporate-structure audit rather than a single-branch drill-down.

3. **Canada List integration: bulk verify mode.** Paste a list of company names (or Canada List product/business entries) and get a table of each one's top-level ultimate parent and country of that parent — the actual editorial workflow this tool was built for, batched instead of one search at a time.

4. **Country/flag context on each node.** Pull each entity's `country` (P17) alongside its label so "is this Canadian-owned?" is answerable from the chain itself at a glance, without opening the citation link.

5. **Export.** A "copy as Markdown" or "export JSON" button for the currently displayed chain, so a finding can be pasted straight into editorial notes with citations intact.

6. **Reference metadata inline, not just linked.** Wikidata statements sometimes carry structured reference data (`stated in`, `reference URL`, `retrieved`). Fetching and showing that inline (with a fallback to the current "source ↗" link when a statement has none) would save a click for the common case.

7. **Search result disambiguation hints.** When multiple Wikidata entities share a name (a common company name, or a company vs. its holding company sharing a near-identical label), show `instance of` (business/organization type) in the dropdown so the right entity is easier to pick on the first try.

8. **Cache SPARQL responses in-session.** Drilling into a company and then back currently re-fetches from Wikidata every time rather than reusing what was just fetched. An in-memory cache keyed by entity id would make repeated back-and-forth navigation feel instant and reduce load on the public endpoint.
