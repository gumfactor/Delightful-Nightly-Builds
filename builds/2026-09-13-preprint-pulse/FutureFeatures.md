# Future Features — Preprint Pulse

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Author watchlist filter** — Add `--authors "Name A, Name B"` to `digest`/`trend` so a run can be narrowed to papers by specific researchers within the matched topic, useful for tracking a known lab's output alongside the broader field trend.
2. **`--min-facts` gate** — Skip (or warn on) topics where `extract_facts` finds fewer than N structured statistics, since a digest built from zero notable figures is weaker; surfacing this before drafting saves a wasted read.
3. **Export to plain-text clipboard-ready format** — A `--format text` output mode that strips Markdown syntax entirely, for pasting directly into an email or Slack message rather than a CMS that renders Markdown.
4. **Configurable rising-keyword stopword list** — Let the user pass a `--extra-stopwords` file to suppress domain-generic terms (e.g. "model," "data") that show up as "rising" simply because a subfield is growing overall, not because that specific term is newly trending.

## Medium Effort (roughly one nightly build session)

5. **Multi-topic comparison mode** — A `compare --topics "A,B,C"` command that runs the trend engine across several topics in one pass and renders a single HTML report ranking them by growth rate, useful for deciding which of several candidate blog topics is actually the timeliest one right now.
6. **Persistent history via local SQLite** — Track each topic's trend numbers across repeated runs over weeks, so a re-run doesn't just show "current state" but "how this has moved since I last checked" (the tracker shape this build deliberately left out of scope, since Paper Lens and Throughline already cover it for other purposes — but a *topic-trend* history specifically doesn't exist anywhere in the catalog yet).
7. **Second data source for citation-weighted "importance," not just recency** — Cross-reference Semantic Scholar (already free/no-auth, used by Throughline) to weight `top_papers` and `notable_facts` by citation count as well as publication date, so a highly-cited paper from earlier in the window doesn't get crowded out by ten low-signal recent preprints.

## Ambitious Extensions (multi-session effort)

8. **Full draft revision loop** — After the first AI draft, let the user reply with edits/feedback and have a second Claude call revise the draft while still being checked against the same fact set (never allowing a revision to introduce a new, unverified claim) — turning this from a one-shot draft generator into a lightweight editorial back-and-forth tool.
9. **Direct integration with a Canada List / lab blog publishing target** — If the user has a specific CMS or static-site generator for their public-facing writing, a `--publish-draft` mode that drops the Markdown into that repo's posts directory in the right front-matter format, closing the loop from "trend detected" to "draft sitting in my blog's drafts folder" with zero copy-paste.

---

## Possible Integration Points

- **Paper Lens** (2026-06-23) already indexes arXiv papers with AI relevance scoring into a personal inbox; Preprint Pulse could read Paper Lens's SQLite database as an alternative paper source for topics the user has already been triaging there, instead of re-querying arXiv from scratch.
- **Voiceprint** (2026-07-28) audits a draft for AI-generated writing patterns; running a Preprint Pulse AI draft through Voiceprint before publishing would directly test whether the fact-constrained AI layer still produces the kind of writing the user dislikes, and could inform prompt tuning.
- **Throughline** (2026-09-12) already implements a from-scratch TF-IDF-style clustering engine over the user's own papers; a future build could apply that same clustering approach *within* a single Preprint Pulse digest to auto-group the matched papers into 2-3 named sub-themes instead of one flat list.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Single-source (arXiv only) — misses journal-published work with no preprint, and non-CS/physics/q-bio fields with lower arXiv adoption | Add a PubMed fallback query (already used by CaseForge/Throughline in this catalog) for biomedical topics specifically |
| Rising-keyword detection uses simple presence-per-half counting, not statistical significance testing | Add a proper two-proportion z-test or Fisher's exact test per keyword so "rising" carries a real p-value, not just a raw count delta |
| The AI drafting prompt sends the full fact set in one shot with no length cap | Add a token-budget-aware truncation step (e.g. top 15 facts by relevance) before building very large prompts on broad topics with hundreds of matched papers |
| No handling for arXiv API's occasional empty-page-then-more-results quirk (a known documented API inconsistency) | Add a one-retry-with-backoff on an unexpectedly empty page before concluding pagination is finished |
| `sample_output/` is a single hand-authored demo corpus, not generated from a real historical arXiv snapshot | Once run locally with real network access, regenerate `sample_output/` from an actual `digest` run and commit that instead |
