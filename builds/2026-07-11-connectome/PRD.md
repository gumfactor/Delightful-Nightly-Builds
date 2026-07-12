# PRD — Connectome: Personal Knowledge Graph Builder

> **Build date:** 2026-07-11
> **Category:** C — Personal Knowledge Tool
> **Complexity:** Ambitious

---

## Goal

Turn a folder of the user's own plain-text/markdown notes into a searchable, cross-linked local knowledge base — surfacing which notes are actually related to each other, something no flat notes folder shows on its own. (2026-07-11 same-day follow-up: extended so the same graph can span multiple *categories* of source material — Notes, Academic Papers, News Articles — not just notes, since the user's actual ask was "displaying the connectome," not the notes format specifically.)

## User Story

As a researcher and founder who accumulates notes across many separate contexts (lab research, course prep, investment theses, AI workflow ideas) and explicitly struggles with "context loss" and "keeping multiple data systems synchronized," I want to point a tool at a folder of my notes and get back a connected map of which notes share ideas, so that I can rediscover related thinking I've already done instead of re-deriving it or losing track of it across separate files. Extended user story (2026-07-11 follow-up): as that same user, I don't think about my own notes, the papers I've read, and the news I've seen as three separate silos — a paper I read last month and a note I wrote yesterday can be about the same idea. I want the graph to show that connection regardless of which "kind" of thing each item is, while still being able to filter down to just one category when I want to.

## Scope

### In Scope
- CLI `index` command: scan a directory of `.md`/`.txt` files, extract per-note concepts, compute cross-note links, store everything in a local SQLite database (incremental — unchanged files are skipped via content hash, matching mtime+hash change detection)
- Deterministic concept extraction: corpus-wide TF-IDF-style scoring (stdlib only) so extraction quality doesn't depend on any external service being reachable. Includes both single-word tokens and two-word phrases (`extraction.extract_bigrams()`, added 2026-07-11 same-day follow-up) — phrases are formed only from literally adjacent content words (a stopword between them blocks the join) and compete for ranking slots in the same TF-IDF space as single words, not a reserved quota.
- Optional AI enrichment layer: when `ANTHROPIC_API_KEY` is set, a note's concepts/one-line gist are refined by Claude Haiku via `urllib` (no SDK); deterministic extraction is always computed first and used as the fallback when no key is set or the call fails
- Note-to-note linking: score every pair of notes by shared-concept overlap weighted by how rare each concept is across the corpus (rarer shared concepts count for more than shared common words); store as a ranked edge list per note
- CLI `search <query>`: rank notes by matches across title/body/concepts
- CLI `related <note>`: show the top related notes for a given note with the shared concepts driving the score
- CLI `stats`: corpus summary (note/concept counts, most-connected "hub" notes, average links per note)
- CLI `build`: render a self-contained dark-mode HTML knowledge base into `output/index.html` — searchable note list, tag cloud of top concepts (click to filter), note detail view (rendered note body, related notes, concept tags), and a hand-drawn Canvas 2D concept graph (circular layout, no charting library/CDN dependency) with click-to-highlight neighbors
- A bundled `sample_notes/` folder of synthetic, thematically relevant demo notes (AI workflows, neuroscience research, investing, course prep) so the tool is immediately explorable without the user having a notes folder ready
- Safe HTML generation: note bodies are HTML-escaped before display; graph/search data is embedded as a `<script type="application/json">` block (not raw string interpolation into executable JS) to eliminate script-injection risk from note content

- CLI `backlinks` command (added 2026-07-11, same day, as a follow-up): writes a delimited `[[wiki-link]]` "See also" block into each note's own file, pointing at its top related notes. Dry-run by default (`--write` required to touch disk); `--write` additionally requires `--notes-dir` to be a git repository with a committed, clean working tree (checked via `git_baseline_problem()` in `backlinks.py`), so every edit is a reviewable, revertible `git diff`/`git checkout` away from undone — `--skip-git-check` is available as an explicit, documented override. A per-note content-hash check skips (rather than silently overwrites) any note edited on disk since the last `index` run. See `Manual.md` for full usage.

- **Multiple categories in one graph** (added 2026-07-11, same day, second follow-up): every note now belongs to a `category` (e.g. "Notes", "Academic Papers", "News Articles" — any string the user passes via `--category`, defaulting to "Notes"). `index` is run once per category/folder (`--notes-dir X --category Y`); indexing one category never touches or deletes another category's notes, but links, doc frequencies, and subcategories are always recomputed across the **whole** corpus, so a note, a paper, and a news article can link to each other. `search`/`stats` accept an optional `--category` filter; `related`/`backlinks` resolve related items across all categories even when scoped to writing into one category's files.
- **Subcategories** (added 2026-07-11, same day, second follow-up): a second, cross-cutting axis independent of category — a cluster of related items regardless of which category they're in. `clustering.py` computes this deterministically via connected components over the note-to-note links already produced by `linking.py` (threshold = median link score across the corpus, a rough heuristic like this build's other tuning constants), then names each cluster from its own aggregate top concepts (e.g. "Session / Context / Agent"). When `--ai` is passed to `index` and `ANTHROPIC_API_KEY` is set, an additional batched Claude call proposes a cleaner human-readable name per cluster; any cluster the response doesn't cover, or that the call fails on entirely, keeps its deterministic name — never all-or-nothing, never blocking on the network.
- Ingestion for Academic Papers and News Articles is intentionally **not** built tonight (see Out of Scope) — `sample_papers/` and `sample_news/` are synthetic demo content, same pattern as `sample_notes/`, chosen to deliberately share vocabulary with specific existing sample notes so the cross-category graph is populated and demoable immediately.

### Out of Scope
- Vector embeddings / semantic similarity (deliberately deterministic and offline; see `FutureFeatures.md`) — investigated and explicitly deferred: PyPI is reachable in this session but HuggingFace Hub (the standard source for pretrained model weights) returns 403, so a real embedding model can't be sourced here without either bundling weights permanently into the repo or accepting a much weaker hash-based substitute
- Real ingestion pipelines for Academic Papers or News Articles (PDF text extraction, live arXiv/PubMed/news-feed fetching) — the user explicitly scoped tonight's ask as "displaying the connectome," not building new data pipelines; `sample_papers/`/`sample_news/` are synthetic demo content instead
- Real-time file watching (index is run on demand via CLI)
- Syncing to any external service (Notion, Obsidian, Coda) — local files only
- Non-text formats (PDF, Word, images) — `.md`/`.txt` only tonight
- Multi-select category filtering in the HTML UI (single active category at a time, same interaction pattern as the existing tag-cloud filter, for consistency and to keep tonight's scope bounded)

## Tech Stack

- **Language:** Python 3
- **Framework:** None
- **Dependencies:** stdlib only (`sqlite3`, `hashlib`, `re`, `json`, `argparse`, `urllib.request`, `html`) — zero third-party runtime dependencies
- **Runtime requirement:** `python3 src/main.py index` / `search` / `related` / `stats` / `build`, then open `output/index.html` directly in a browser (no server needed)

## Data Structure

SQLite database (`connectome.db`, created in the build folder at runtime — not committed):

```sql
notes(id INTEGER PK, path TEXT, category TEXT DEFAULT 'Notes', subcategory TEXT, title TEXT, body TEXT, content_hash TEXT, indexed_at TEXT, UNIQUE(category, path))
concepts(id INTEGER PK, term TEXT UNIQUE, doc_freq INTEGER)
note_concepts(note_id INTEGER, concept_id INTEGER, weight REAL, PRIMARY KEY(note_id, concept_id))
links(note_a INTEGER, note_b INTEGER, score REAL, shared_concepts TEXT, PRIMARY KEY(note_a, note_b))
```

`note_a < note_b` always, so each unordered pair is stored once. `weight` is the concept's term frequency within that note. `doc_freq` on `concepts` is how many notes contain that concept — used both for extraction ranking (rarer terms score higher within a note) and for link scoring (shared rare concepts score higher than shared common ones). `category`/`subcategory` (added 2026-07-11 follow-up): uniqueness is scoped to `(category, path)`, not `path` alone, so the same relative filename can exist independently in two categories (e.g. an `overview.md` in both Notes and Academic Papers). A DB created before this change gets `category`/`subcategory` added via an in-place `ALTER TABLE` migration in `storage._migrate_schema()`; a migrated table keeps its old single-column `UNIQUE(path)` constraint (SQLite can't alter table constraints in place), so a migrated DB should be deleted and re-indexed rather than relied on for genuinely cross-category same-filename use — documented as a known limitation, not silently worked around.

Committed test fixtures live under `tests/fixtures/` (small, synthetic `.md` files, not the same as `sample_notes/`).

## Folder Structure

```
builds/2026-07-11-connectome/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── sample_notes/          # category "Notes" (original)
│   ├── ai-agent-handoffs.md
│   ├── lab-forensic-empathy-study.md
│   ├── canada-list-ownership-heuristics.md
│   ├── investment-thesis-semis.md
│   ├── course-stress-coping-outline.md
│   └── quant-screening-notes.md
├── sample_papers/         # category "Academic Papers" (2026-07-11 follow-up)
│   ├── agent-context-continuity.md
│   ├── semiconductor-capex-cycle.md
│   └── affective-empathy-recidivism.md
├── sample_news/           # category "News Articles" (2026-07-11 follow-up)
│   ├── agent-tooling-workflow-race.md
│   ├── hyperscaler-capex-guidance-raised.md
│   └── foreign-ownership-classification-scrutiny.md
├── src/
│   ├── main.py           # CLI entry point (argparse subcommands)
│   ├── extraction.py      # concept extraction (deterministic + optional AI enrichment)
│   ├── linking.py         # note-to-note link scoring
│   ├── storage.py         # SQLite schema + read/write helpers
│   ├── render.py          # HTML knowledge base generation
│   ├── backlinks.py       # writes [[wiki-link]] blocks into note files (dry-run + git-guarded)
│   └── clustering.py      # deterministic subcategory clustering + optional AI relabeling
└── tests/
    ├── fixtures/
    │   ├── note_a.md
    │   ├── note_b.md
    │   ├── note_c.md
    │   └── unrelated.md
    ├── test_extraction.py
    ├── test_linking.py
    ├── test_storage.py
    ├── test_cli.py
    ├── test_render.py
    ├── test_backlinks.py
    └── test_clustering.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Deterministic concept extraction: stopword filtering, minimum-length filtering, corpus-wide document-frequency weighting, empty-note handling; bigram phrases only join literally adjacent content words (a stopword between them blocks the join), are excluded when either word fails the length/stopword filter, and compete with single words in the same ranked `extract_concepts` output
  - Linking: symmetric scoring (order-independent), no self-links, rarer shared concepts outscore common shared concepts, notes with zero shared concepts produce no edge
  - Incremental indexing: unchanged file (same content hash) is skipped on re-index; changed file content triggers re-extraction; deleted file is removed from the index; non-`.md`/`.txt` files are ignored; empty notes directory handled without crashing
  - SQLite storage: schema creation is idempotent, re-indexing the same files does not duplicate rows, `search` matches are case-insensitive across title/body/concept
  - CLI: `search` with no matches returns a clean empty result (not a crash); `related` on a note with no links reports that clearly; `stats` computes correct aggregate counts
  - AI enrichment layer: mocked successful Claude response is used; missing `ANTHROPIC_API_KEY` falls back to deterministic extraction; a simulated API failure (timeout/HTTP error) falls back cleanly without crashing the index run
  - HTML rendering: generated HTML is valid and self-contained; a note body containing `<script>`, `</script>`, and raw quotes is escaped/embedded safely (does not break out of the embedded JSON block or execute)
  - Backlinks: block insert/replace/remove is idempotent (re-running against an already-written body is a no-op); the git-baseline guard correctly refuses a non-git directory, a git repo with no commits, and a git repo with a dirty working tree, and accepts a clean committed one; a note edited on disk after the last `index` but before `backlinks --write` is skipped, not silently overwritten; writing updates the note's stored body/hash so a subsequent `index` run doesn't re-flag it as changed
  - Categories: the same relative filename is allowed to exist independently in two categories; indexing one category never deletes or modifies another category's notes; `search`/`stats` correctly scope to one category or show everything; a pre-2026-07-11 database gets migrated in place with `category`/`subcategory` columns added
  - Subcategory clustering: union-find groups notes above the score threshold and keeps notes below it separate, is transitive through a shared strongly-linked member, and gives an isolated note its own singleton cluster; naming aggregates concept weights across a cluster's members; the optional Claude relabeling call falls back to the deterministic name per-cluster on a partial response and for the whole batch on total failure (no key, network error, bad status, malformed JSON)
  - End-to-end (CLI level, not just unit): indexing a "Notes" and an "Academic Papers" folder with deliberately overlapping vocabulary produces an actual cross-category link; `--ai` on `index` is confirmed (via mocked `urlopen`) to reach both the per-note concept-enrichment call and the batched subcategory-relabeling call

## Success Criteria

1. All tests pass (zero failures)
2. `index` on `sample_notes/` produces a populated SQLite DB with notes, concepts, and at least one cross-note link with a non-trivial shared-concept explanation
3. Re-running `index` on unchanged files is a no-op (no re-extraction, confirmed via a log/count check) — proves the incremental design actually works, not just in theory
4. `build` produces a self-contained `output/index.html` that opens directly in a browser (`file://`) and shows the note list, tag cloud, at least one note-detail page with related notes, and a rendered concept graph
5. A note body containing hostile characters (`<script>alert(1)</script>`, quotes, backticks) neither executes nor breaks the page when viewed in the generated HTML
6. Indexing `sample_notes/`, `sample_papers/`, and `sample_news/` under three different `--category` values into one database produces genuine cross-category links (verified by title, not just count) — e.g. a Notes item, an Academic Papers item, and a News Articles item about the same underlying topic all link to each other
7. The rendered HTML's category filter, when clicked in a real browser (Playwright/headless Chromium, not just JSON inspection), actually narrows the visible note list to that category with zero console/page errors

---

## Scope Changes

**Network access unavailable this session.** During idea selection, live connectivity checks (via Python `urllib`, matching how every recent build in this catalog talks to external APIs) showed this session's egress policy returns `403 Forbidden` from the agent proxy for `wikidata.org`, `en.wikipedia.org`, `query1.finance.yahoo.com`, `api.open-meteo.com`, `sec.gov`/`data.sec.gov`, `eutils.ncbi.nlm.nih.gov` (PubMed), and `export.arxiv.org` — every free public API listed in PROFILE.md's Data Sources except GitHub was unreachable tonight. `api.github.com` is reachable and `GITHUB_TOKEN` works, but GitHub-based tools already make up roughly a third of the existing catalog (Git Standup Reporter, GitHub Repository Health Scorecard, Morning Briefing, GitHub Developer Activity Explorer, ci-pulse, Project Pulse, GitHub Developer Analytics Dashboard, Pipeline Pulse, Worklog), so building another one risked exactly the redundancy criticism several of those already received. `ANTHROPIC_API_KEY` is also unset in this session (`api.anthropic.com` itself is reachable, connection-wise), despite PROFILE.md describing it as always available — consistent with several other recent builds in this catalog hitting the same gap.

Given this, the original plan (a Wikidata-backed Canadian company ownership knowledge base — see `WhyThis.md`) was replaced before any code was written with a design that needs no blocked external API: a local notes indexer that treats the user's own files as the real data source, with Claude enrichment wired in as a genuinely optional, gracefully-degrading layer exactly like the majority of this catalog's recent builds already do. This is a scope substitution made during idea selection (Step 2d), not a mid-build reduction — the PRD above reflects the actual, complete plan that was built.
