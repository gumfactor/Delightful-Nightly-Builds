# PRD — Bridgework

## Goal

Generate, score, and permanently accumulate novel, structurally-grounded analogies that bridge the user's own stress/empathy/psychopathy neuroscience research to everyday domains, for direct reuse in the "Stress and Coping" book and public empathy/AI education talks named in PROFILE.md.

## User Story

As a researcher writing a public-facing book and giving public talks on stress, empathy, and related neuroscience, I want a tool that generates fresh, scientifically-honest analogies for my core concepts (rather than the same handful I've already used), keeps every analogy I've ever generated in a searchable local library so nothing is lost between sessions, and lets me export the ones I like as Markdown I can paste straight into a manuscript or slide deck.

## Scope

**In scope:**
- A hand-curated taxonomy of 20 neuroscience concepts across three subdomains (stress, empathy, psychopathy) and 12 everyday-domain analogs (kitchen stove, storm, thermostat, athletic training, traffic, garden, orchestra, stadium wave, computer network, smoke alarm, dam/reservoir, phone battery)
- A structural-mapping compatibility rule engine: each concept and domain is tagged with a "mechanism type" (threshold trigger, feedback loop, resource depletion, contagion/mirroring, calibration/regulation, dual pathway, learned pattern); a concept and domain are only ever paired if their mechanism types match, so analogies are structurally sound rather than arbitrary
- Three audience registers (undergrad lecture, public talk, book chapter), each with genuinely distinct deterministic phrasing
- Deterministic template generation that always works with no API key, built from structured trigger/mechanism/consequence fields per concept and matching trigger/process/outcome fields per domain
- Optional Claude Haiku polish (`ANTHROPIC_API_KEY` read at runtime, never during the build or in tests) that rewrites the hook/analogy/caveat in the requested audience register from the deterministic draft, with the deterministic version as an unconditional fallback on any missing key, network error, timeout, or malformed response
- Novelty scoring: candidate (concept, domain, audience) triples are ranked by how many times that exact triple has already been generated (ascending, so unexplored combinations surface first), and each generated entry is scored by Jaccard token-overlap against every previously stored analogy text
- A persistent local SQLite library (`data/bridgework.db`, created on first run inside the build folder) — every `generate` call inserts new rows; nothing is ever overwritten, so the library only grows and old entries stay browsable even after a triple is regenerated
- A CLI (`generate`, `list`, `show`, `export`, `render`, `stats`, `taxonomy`) for creating, browsing, and exporting analogies
- A self-contained dark-mode HTML viewer (`render`) — search, filter by concept/domain/audience/source, detail panel, "Copy as Markdown" button, all text inserted via safe DOM APIs (never `innerHTML` from generated text)

**Out of scope:**
- A live web server or hosted deployment (the HTML output is a static file opened locally, per the self-contained/no-persistent-infrastructure constraint)
- Editing or deleting library entries (the library is an append-only record by design, matching the "never overwritten" value proposition)
- Any external API beyond the optional Anthropic call — there is no live/public data source relevant to a hand-curated conceptual taxonomy, so none is claimed

## Idea Brief Traceability

No linked Idea Brief. This build overlaps closely with backlog idea #15 ("Metaphor Machine"), which is marked `built` in `builds/ideas.md` with a note pointing here; see `WhyThis.md` for the full reasoning and how tonight's build extends that concept (persistent library + novelty scoring against the exact "one Claude prompt" critique that scored 2026-06-24's AI Lecture Builder a 2/10).

## Tech Stack

Python 3, standard library only (`argparse`, `sqlite3`, `json`, `re`, `random`, `datetime`, `pathlib`, `urllib.request`, `html`). Optional runtime dependency on the Anthropic API via a direct `urllib` HTTPS POST (no `anthropic` SDK needed for a single Messages call) — never imported or called during the build or in tests. `pytest` for tests.

## Data Structure

**Taxonomy (in-code, `src/taxonomy.py`):**
- `Concept`: `id`, `name`, `subdomain` (stress/empathy/psychopathy), `mechanism_type`, `trigger`, `mechanism`, `consequence`, `caveat`, `description` — 20 concepts total
- `Domain`: `id`, `name`, `mechanism_types` (tuple, a domain may express more than one), `trigger_word`, `process_word`, `outcome_word`, `description` — 12 domains total
- Compatibility: `concept.mechanism_type in domain.mechanism_types` → 97 valid (concept, domain) pairs out of 240 possible (verified: every concept has ≥1 compatible domain, every domain has ≥1 compatible concept), × 3 audience registers = 291 valid (concept, domain, audience) triples

**Library (SQLite, `data/bridgework.db`):** one `analogies` table — `id`, `concept_id`, `concept_name`, `subdomain`, `domain_id`, `domain_name`, `audience`, `hook`, `analogy`, `caveat`, `source` (`ai`/`template`), `novelty_score`, `created_at`. Append-only; `id` is the only stable identifier for `show`/`export`.

## Folder Structure

```
builds/2026-07-21-bridgework/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── taxonomy.py     # concepts, domains, compatibility engine
│   ├── novelty.py       # Jaccard overlap + triple-usage ranking
│   ├── storage.py       # SQLite persistence
│   ├── ai_client.py     # optional Claude Haiku polish via urllib
│   ├── generator.py     # deterministic templates + orchestration
│   ├── render.py        # self-contained dark-mode HTML viewer
│   ├── cli.py            # argparse subcommands
│   └── main.py           # entry point, __main__ guard
├── tests/
│   ├── test_taxonomy.py
│   ├── test_novelty.py
│   ├── test_storage.py
│   ├── test_ai_client.py
│   ├── test_generator.py
│   ├── test_render.py
│   └── test_cli.py
└── data/                  # created at runtime; not committed
```

## Testing Strategy

- `test_taxonomy.py`: every concept's `mechanism_type` and `subdomain` are valid, every domain's `mechanism_types` are valid and non-empty, no duplicate IDs, no orphan concept/domain (every concept has ≥1 compatible domain and vice versa), `valid_pairs`/`valid_triples` filtering by concept/domain/audience works, incompatible pairs are correctly excluded.
- `test_novelty.py`: `jaccard_similarity` for identical/disjoint/partial-overlap/empty text pairs, `max_overlap` against an empty and non-empty corpus, `novelty_score` monotonicity (higher usage count or overlap → lower score) and input validation, `rank_triples_by_usage` orders ascending and is stable on ties.
- `test_storage.py`: schema creation on a fresh temp DB, insert/get round-trip, `list_analogies` filtering by concept/domain/audience/search and `limit`, entries are never overwritten (regenerating a triple adds a new row, both remain listed), `count_triple`/`usage_counts`/`all_analogy_texts`/`stats` correctness on a seeded DB.
- `test_ai_client.py`: no API key → returns `None` without attempting a network call (mocked to assert it's never invoked); successful mocked HTTP response is parsed into hook/analogy/caveat; malformed JSON, non-200 status, and a simulated `URLError`/timeout all fall back to `None` rather than raising.
- `test_generator.py`: deterministic template output differs across all three audiences for the same concept/domain, contains the concept name, domain name, and concept's caveat text, is well-formed (non-empty hook/analogy/caveat); `generate_entry` uses the AI client when `use_ai=True` and a key is present (mocked), and falls back to the template when `use_ai=False`, no key, or the AI client returns `None`; novelty score is computed against prior stored texts.
- `test_render.py`: rendered HTML contains every passed entry's hook/analogy text; a `<script>`-tag-bearing analogy string is escaped in the output (never appears as an executable tag); rendering an empty list still produces valid, non-crashing HTML; embedded JSON data does not break out of its `<script>` block even when source text contains `</script>`.
- `test_cli.py`: `generate` inserts the requested count into a temp DB and respects `--concept`/`--domain`/`--audience` filters; `list` filters correctly; `show` returns the right entry and a clean error for a missing ID; `export --all` and `export <id>` produce valid Markdown containing the analogy text; `stats` reports correct totals; invalid `--concept`/`--domain` IDs produce a clear CLI error rather than a traceback.

Run with `python -m pytest tests/ -v` from the build folder.

## Success Criteria

1. `bridgework generate --count 5` inserts 5 new, valid rows into the library, each respecting mechanism-type compatibility, with distinct phrasing per audience register when audiences differ.
2. Regenerating the same (concept, domain, audience) triple never overwrites a prior entry — both remain in `list`/`render` output, and the library only grows.
3. With no `ANTHROPIC_API_KEY` set, every command still works end-to-end and produces complete, well-formed analogy text (template fallback is fully functional, not a stub).
4. `bridgework render` produces a self-contained HTML file that opens directly (no server) and correctly escapes all generated text against script injection, verified live in headless Chromium.
5. All tests in `tests/` pass (`python -m pytest tests/ -v`), with zero failures.
