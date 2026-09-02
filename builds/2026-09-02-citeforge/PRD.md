# PRD — CiteForge: Citation Style Converter & Batch Bibliography Formatter

> **Build date:** 2026-09-02
> **Category:** B — Productivity Utility
> **Complexity:** Ambitious Project
> **Day of week:** Wednesday

---

## Goal

A Python CLI that turns a bibliography (BibTeX file, a list of DOIs, or hand-entered references) into a correctly-formatted, submission-ready reference list in APA 7, AMA 11, Vancouver/ICMJE, or Chicago Author-Date 17 style, with a side-by-side comparison mode for preparing the same manuscript for multiple journals.

## User Story

As a researcher who writes grants and manuscripts and regularly submits to journals with different citation-style requirements, I want to convert one bibliography into any of the four major academic citation styles without hand-reformatting each reference, so that resubmitting a rejected manuscript to a different journal (or preparing a grant with a different style requirement) no longer means manually rewriting every reference.

## Scope

### In Scope
- A from-scratch BibTeX (`.bib`) parser (stdlib only) supporting `@article`, `@book`, `@inbook`, `@misc`/`@online` entry types, `{}`- and `""`-delimited fields, `and`-separated author lists, and `{Last, First}`/`Last, First` name forms
- DOI resolution via the free, no-auth Crossref API (`api.crossref.org/works/{doi}`), mapped into the same internal reference model as BibTeX entries
- A local SQLite reference library (deduplicated by DOI, or by normalized author+year+title when no DOI exists) so DOI lookups are never re-fetched and a `.bib`/DOI-list re-import is idempotent
- Free-text reference parsing (one reference per line) via a deterministic regex pre-pass (year-in-parens, DOI pattern, quoted title), with an optional Claude Haiku fallback (`--ai`, requires `ANTHROPIC_API_KEY`) for lines the regex pass cannot confidently structure — entries that still can't be structured are flagged `needs_review`, never silently guessed
- A from-scratch formatting engine implementing real style rules (not a template with blanks filled in) for reference-list entries in **APA 7th**, **AMA 11th**, **Vancouver/ICMJE**, and **Chicago Author-Date 17th** editions, across `journal-article`, `book`, and `webpage` reference types:
  - Per-style author-list formatting (initials vs. full given names, "&" vs. "and" vs. comma, "et al." thresholds that differ by style: APA 20/19, AMA/Vancouver 6, Chicago 10/7)
  - Sentence-case and title-case text converters (acronym-preserving) applied per style's title-casing rule
  - Style-specific punctuation, italics markers (rendered as Markdown `*emphasis*`), and DOI/URL formatting
  - ICMJE page-range truncation (e.g. `284-287` → `284-7`), cross-checked against a real published ICMJE sample citation
  - In-text citation formatting: author-date `(Author, Year)` for APA and Chicago; sequential numbered `[n]` markers (by library order) for AMA and Vancouver
- CLI commands: `add-bibtex`, `add-doi`, `add-text`, `list`, `remove`, `format --style <style>`, `compare` (all 4 styles side by side in the terminal), `render` (self-contained dark-mode HTML report)
- Self-contained dark-mode HTML report: side-by-side 4-style comparison per reference, live search/filter, copy-to-clipboard per formatted entry — all reference data delivered via an escaped JSON payload and built into the DOM with `createElement`/`textContent`, never `innerHTML`
- A companion Claude Code Skill (`skill/SKILL.md`) so a coding session can format a pasted reference list on request

### Out of Scope
- NLM/journal-specific abbreviated journal names (AMA/Vancouver technically require these; this build uses the full journal name and documents the limitation in `Manual.md` — a real journal-abbreviation database is a future feature)
- Reference types beyond `journal-article`, `book`, and `webpage` (e.g. conference proceedings, datasets, reports) — a `@inproceedings`/unrecognized BibTeX type falls back to a generic "other" template rather than crashing, clearly labeled less precise
- Scanning an actual manuscript file to detect real in-text citation order (AMA/Vancouver numbering uses library order as a documented stand-in, not manuscript-detected citation order)
- Style variants beyond the four listed (MLA, Harvard, ASA, etc.)
- Any network call other than Crossref (public, no-auth) and the optional, explicitly opt-in Anthropic API call

## Tech Stack

- **Language:** Python 3.11
- **Framework:** None
- **Dependencies:** stdlib only (`urllib`, `sqlite3`, `re`, `json`, `argparse`, `dataclasses`) — `pytest` is a test-only dependency
- **Runtime requirement:** `python3 main.py <command> [options]`; opens the rendered HTML report directly via `file://`, no server needed

## Data Structure

Internal reference model (one row per reference in SQLite, `references` table):

```
id                INTEGER PRIMARY KEY
ref_type          TEXT      -- 'journal-article' | 'book' | 'webpage' | 'other'
authors_json      TEXT      -- JSON list of {"family": str, "given": str}
year              TEXT      -- 4-digit year or "n.d."
title             TEXT      -- raw, as-supplied title (case-converted at format time, never stored pre-cased)
container_title   TEXT      -- journal name (articles) or publisher (books) or site name (webpages)
volume            TEXT
issue             TEXT
pages             TEXT
doi               TEXT
url               TEXT
source            TEXT      -- 'bibtex' | 'crossref' | 'manual' | 'ai-extract'
dedupe_key        TEXT UNIQUE  -- doi, else normalized "family|year|title" of first author
needs_review      INTEGER   -- 0/1, set when free-text parsing couldn't confidently fill required fields
created_at        TEXT      -- ISO8601 UTC
```

`crossref_cache` table: `doi TEXT PRIMARY KEY`, `raw_json TEXT`, `fetched_at TEXT` — avoids re-fetching a DOI already resolved in a prior run.

## Folder Structure

```
builds/2026-09-02-citeforge/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── main.py
├── skill/
│   └── SKILL.md
├── src/
│   ├── __init__.py
│   ├── models.py
│   ├── db.py
│   ├── bibtex_parser.py
│   ├── crossref.py
│   ├── ai_extract.py
│   ├── text_case.py
│   ├── names.py
│   ├── pages.py
│   ├── styles/
│   │   ├── __init__.py
│   │   ├── apa.py
│   │   ├── ama.py
│   │   ├── vancouver.py
│   │   └── chicago.py
│   ├── render_html.py
│   └── cli.py
└── tests/
    ├── __init__.py
    ├── test_bibtex_parser.py
    ├── test_text_case.py
    ├── test_names.py
    ├── test_pages.py
    ├── test_apa.py
    ├── test_ama.py
    ├── test_vancouver.py
    ├── test_chicago.py
    ├── test_crossref.py
    ├── test_ai_extract.py
    ├── test_db.py
    ├── test_render_html.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - BibTeX parser: `@article`/`@book`/`@misc` entries, `{}` and quoted fields, multi-author `and`-splitting, malformed-entry skip-not-crash, unsupported entry type falls back to `other`
  - Sentence-case / title-case converters: minor-word lowercasing, colon-segment capitalization, acronym preservation, single-word titles
  - Author-name formatting per style at exact "et al." boundary counts (APA 20/21, AMA/Vancouver 6/7, Chicago 10/11)
  - ICMJE page-range truncation against the real published ICMJE example (`284-287` → `284-7`) plus boundary cases (equal digit counts, differing digit counts, non-numeric pages left untouched)
  - Each of the 4 style modules against one hand-verified worked example per reference type (journal-article, book, webpage) — output compared to a literal expected string, not just "non-empty"
  - In-text citation formatting: 1/2/3+ authors for APA and Chicago; sequential numbering for AMA/Vancouver
  - Crossref client: successful mapping from a realistic fixture JSON payload, 404/not-found handling, cache-hit avoids a second network call (fake transport with a call counter)
  - AI free-text extractor: regex pre-pass succeeds without any network call; AI fallback invoked only when regex fails **and** `--ai` **and** a key is set (mocked transport, call-count assertions); unconditional `needs_review` flag with no key
  - SQLite dedupe: re-adding the same DOI/BibTeX entry upserts rather than duplicates
  - CLI end-to-end: `add-bibtex` → `format --style apa` on a real fixture `.bib` file produces the expected reference list
  - HTML render: reference data escaped safely against a script/`<img onerror>` injection payload in a title

## Success Criteria

1. All tests pass (zero failures)
2. `citeforge add-bibtex fixture.bib` parses every valid entry in a realistic multi-entry fixture file into the local SQLite library, skips malformed entries with a reported warning instead of crashing, and a second run does not duplicate rows
3. `citeforge format --style X` for each of APA/AMA/Vancouver/Chicago reproduces hand-verified worked examples (not just "produces some output") for at least one journal-article, one book, and one webpage reference
4. The ICMJE page-range truncation logic reproduces the real published ICMJE sample citation (`Halpern SD, Ubel PA, Caplan AL. ... N Engl J Med. 2002;347:284-7.`) and passes boundary-condition tests
5. `citeforge render` produces a self-contained HTML report that opens with zero page errors and renders an injected `<script>`/`<img onerror>` payload placed in a reference title as inert text, verified live in headless Chromium

---

## Scope Changes

None — full scope as planned was delivered. (If a scope reduction becomes necessary during the build, it will be recorded here with what was cut and why.)
