# PRD — CaseForge

> **Build date:** 2026-09-04
> **Category:** D — Creative / Generative
> **Complexity:** Ambitious Project
> **Day of week:** Friday

---

## Goal

Generate classroom-ready teaching case vignettes — each with a real citation, extracted methodological facts, and deterministic discussion questions — from real, live PubMed research findings in any course topic the user specifies.

## User Story

As a professor who teaches Stress and Coping, Social Affective Neuroscience, and AI Applications for Psychologists and who currently builds discussion cases by manually searching the literature and writing them up by hand, I want to generate a batch of real-literature-grounded teaching cases for a course topic in one command, so that lecture and seminar prep stops competing with grant writing, research, and lab administration for the same hours.

## Scope

### In Scope
- `generate` command: given a course name and a PubMed search query, fetch N real articles via the free NCBI E-utilities API (`esearch` for PMIDs, `efetch` for abstracts — no auth, no key required), skipping PMIDs already in the local library
- Deterministic fact extraction from each real abstract: sample size, effect-size statistic, p-value, methodology tag (survey/RCT/fMRI/EEG/meta-analysis/correlational/longitudinal/case-study/etc.), population descriptor — all via tested regex/keyword functions, no AI required
- Deterministic discussion-question rule engine: a bank of question templates gated by boolean predicates over the extracted facts (small sample → power/generalizability question; correlational design → causality question; neuroimaging methodology → multiple-comparisons question; no comparison/control language found → confound question; an effect size present → statistical-vs-practical-significance question), with two always-included generic fallback questions so every case has at least 3 discussion questions even when extraction is sparse
- Deterministic vignette assembly: a template-based narrative built entirely from the extracted facts and article metadata — works with zero configuration, zero API key, zero network calls beyond PubMed
- Optional Claude Haiku polish (`--ai-polish`, requires `ANTHROPIC_API_KEY` at runtime): rewrites the deterministic vignette into smoother prose for a chosen audience register (undergrad/graduate/public), sent only the extracted facts and title — never the full raw abstract verbatim is required for the rewrite to succeed. A safety-net check re-confirms every originally-extracted fact string (sample size digits, p-value text, effect-size text) still appears in the AI output; if any fact is dropped or the call fails, it silently falls back to the deterministic vignette
- Local SQLite library, keyed by PMID, so the same article is never re-fetched or duplicated across `generate` runs (unless `--force`)
- `list`, `show`, `search`, `export markdown` CLI commands
- `render` command: self-contained dark-mode HTML dashboard — per-course tabs, live client-side search, case detail cards (citation, extracted-fact badges, vignette, discussion questions), a print-friendly stylesheet for handouts, all data delivered as an escaped JSON payload and rendered via `createElement`/`textContent` only
- Companion Claude Code Skill (`skill/SKILL.md`) so a course-prep session can request "/build cases on cortisol and coping for undergrads" without leaving the coding session

### Out of Scope
- Full-text article retrieval (PubMed E-utilities only exposes abstracts for most records; this build works from abstracts only, and says so explicitly)
- Automatic mapping from arbitrary free text to a PubMed query (the user supplies the search query directly, same pattern as PubMed Research Radar/GrantScope)
- LMS/Canvas export (no such credential exists in PROFILE.md's Data Sources)
- Author names in generated cases (only journal, year, and citation-style reference are stored/shown — the case content is what matters for teaching, not personal-name display)

## Tech Stack

- **Language:** Python 3
- **Framework:** None
- **Dependencies:** stdlib only (`urllib`, `sqlite3`, `re`, `json`, `argparse`, `xml.etree.ElementTree`, `html`); `pytest` for tests (dev only)
- **Runtime requirement:** `python -m src.main <command>` run from the build folder; no install step for end use beyond a Python 3 interpreter

## Data Structure

Single local SQLite database (`caseforge.db`, created on first run, git-ignored, never committed) with one table:

```sql
CREATE TABLE cases (
    pmid TEXT PRIMARY KEY,
    course TEXT NOT NULL,
    topic_query TEXT NOT NULL,
    title TEXT NOT NULL,
    journal TEXT,
    pub_year INTEGER,
    citation TEXT NOT NULL,
    abstract_text TEXT NOT NULL,
    sample_size INTEGER,
    population TEXT,
    methodology TEXT,
    effect_size_text TEXT,
    p_value_text TEXT,
    vignette_text TEXT NOT NULL,
    vignette_source TEXT NOT NULL,   -- 'deterministic' or 'ai'
    discussion_questions TEXT NOT NULL,  -- JSON array of strings
    created_at TEXT NOT NULL         -- ISO 8601 UTC
);
```

Extracted-fact fields are nullable — an abstract that mentions no explicit sample size or p-value still produces a valid case with the fallback discussion questions.

## Folder Structure

```
builds/2026-09-04-caseforge/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── main.py             (CLI entry point, argparse, command dispatch)
│   ├── pubmed_client.py    (esearch/efetch HTTP calls + XML/JSON parsing)
│   ├── extraction.py       (deterministic fact-extraction functions)
│   ├── questions.py        (discussion-question rule engine)
│   ├── vignette.py         (deterministic assembly + AI polish + fact safety-net)
│   ├── ai_client.py        (Anthropic API call via urllib)
│   ├── db.py               (SQLite schema, insert/query helpers)
│   └── render.py           (self-contained HTML dashboard generator)
├── skill/
│   └── SKILL.md
└── tests/
    ├── test_extraction.py
    ├── test_questions.py
    ├── test_vignette.py
    ├── test_pubmed_client.py
    ├── test_ai_client.py
    ├── test_db.py
    ├── test_render.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Fact extraction: sample size, p-value, effect size, methodology tag, population descriptor — happy path and no-match cases for each
  - Discussion-question rule engine: every predicate fires on a fact set built to trigger it, the always-included fallback questions appear even on an empty fact set, question count is always ≥3
  - Deterministic vignette assembly: produces valid, non-empty text embedding the real extracted facts; handles an abstract with zero extracted facts without crashing
  - AI polish safety net: a mocked Anthropic response that drops a required fact string is rejected and falls back to the deterministic vignette; a mocked response that preserves all facts is accepted; zero network calls are made when no `ANTHROPIC_API_KEY` is set
  - PubMed client: mocked `urlopen` responses — `esearch` JSON → PMID list, `efetch` XML → title/abstract/journal/year, an article with no `AbstractText` element is skipped rather than crashing, network/HTTP errors are handled gracefully
  - SQLite persistence: insert, re-`generate` over an overlapping PMID set does not duplicate or overwrite rows unless `--force`, `list`/`search`/`show` return correct rows
  - HTML rendering: case data with an embedded `</script><script>` and `<img onerror>` payload is JSON-escaped safely for `<script>`-tag delivery and never appears as an executable tag in the raw HTML output
  - CLI: argument validation (missing `--course`, invalid `--n`), end-to-end `generate` → `list` → `show` → `export markdown` → `render` flow against a fully mocked PubMed client

## Success Criteria

1. All tests pass (zero failures)
2. `generate` against a mocked PubMed response produces a case per fetched PMID with a non-empty deterministic vignette and at least 3 discussion questions, with zero external network calls made when `--ai-polish` is not passed
3. Re-running `generate` with the same query does not duplicate already-fetched PMIDs in the database
4. `render` produces a self-contained HTML file that opens directly (`file://`) with zero `innerHTML` use on case data, verified against a live script-injection payload
5. The AI-polish safety net demonstrably rejects a mocked response missing a required extracted fact and falls back to the deterministic vignette, proven by a dedicated test

---

## Scope Changes

None — built as scoped.
