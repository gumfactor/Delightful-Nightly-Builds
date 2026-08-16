# PRD — Curriculum Atlas

> **Build date:** 2026-08-16
> **Category:** C — Personal Knowledge Tool
> **Complexity:** Ambitious Project
> **Day of week:** Sunday

---

## Goal

A local, versioned knowledge base that extracts teaching concepts and learning objectives from a professor's own syllabi and lecture materials, then answers two questions no single course file can: which concepts repeat across different courses (intentional reinforcement or accidental redundancy), and which stated learning objectives are not actually backed by any concept in the materials.

## User Story

As an Associate Professor who teaches multiple courses (Stress and Coping, Social Affective Neuroscience, AI Applications for Psychologists) and is actively developing new AI-focused courses and updating neuroscience curriculum, I want to ingest my syllabi and lecture outlines into one searchable local knowledge base, so that I can see cross-course concept overlap, catch objectives my materials don't actually cover, and track how a course's concept set changes term over term — without re-reading every document by hand.

## Scope

### In Scope
- `add-course` — register a course (name, term/semester label)
- `ingest` — parse a plain-text/markdown syllabus or lecture file into concepts + objectives for a course+term, store in local SQLite (append-only per ingest — re-ingesting the same file path within the same term updates that document's concepts, never silently duplicates)
- Deterministic concept extraction (always works, zero network calls):
  - Explicit `[[Concept Name]]` wiki-style markers anywhere in the text (highest-confidence source)
  - Heading-as-concept: any heading line (`# `/`## `/`### ` or `Week N:` / `Session N:` / `Unit N:` / `Module N:` / `Lecture N:` style) that contains a colon or dash separator contributes its topic portion as a concept
  - Heuristic capitalized-phrase extraction from body text (2–4 consecutive capitalized words, mid-sentence only, filtered against a stopword/common-word list) as a lower-confidence source
  - All three sources are deduplicated against each other by a shared normalization (lowercase, strip punctuation, naive singularize)
- Deterministic objective extraction: lines matching common syllabus objective phrasing ("Students will...", "By the end of...", "Learners will...", "Objective N:") captured as objective text tied to the course+term
- Deterministic gap analysis (`gaps` command): for each objective in a course+term, Jaccard token-overlap against every concept extracted for that same course+term; objectives below a configurable threshold (default 0.15) are flagged as "not clearly covered by any extracted concept"
- Deterministic cross-course overlap analysis (`overlap` command): concepts whose normalized name appears in more than one course, listing every course/term/document where each shared concept appears
- Deterministic term-over-term diff (`diff` command): for one course, compares the concept set of two terms and reports concepts added/removed/kept
- Optional AI concept auto-marking (`ingest --ai-mark`, requires `ANTHROPIC_API_KEY`): when a document contains zero `[[...]]` markers, Claude Haiku is asked to insert `[[...]]` markers around concept phrases in a copy of the text; the marked-up text is then run back through the exact same deterministic parser used for hand-marked text — the AI never invents a concept the deterministic parser doesn't also see and re-verify. Unconditional fallback to unmarked deterministic extraction (headings + heuristic phrases) when no key is set or the API call fails.
- Optional AI concept notes (`concepts --ai-notes`, requires `ANTHROPIC_API_KEY`): one-sentence plain-English gloss per concept name, generated in a single batched call, cached in SQLite so it is only ever generated once per concept. Falls back to no notes (blank) when no key is set.
- `render` — self-contained dark-mode HTML dashboard: per-course concept list with source badges, a cross-course overlap table, a gap-analysis panel per course/term, a term-over-term diff view, and full-text concept search — all data delivered as an escaped JSON payload and rendered via `createElement`/`textContent`, never `innerHTML`
- `list-courses`, `concepts` (list/search), all read-only inspection commands
- Companion Claude Code Skill (`skill/SKILL.md`) so `ingest`/`concepts`/`overlap`/`gaps` can be invoked by name from within a Claude Code session while working on course materials

### Out of Scope
- PDF/DOCX parsing — plain text or Markdown files only (a professor can paste/export to text; documented as a known limitation)
- Automatic import from an LMS (Canvas, Blackboard) — no such API is listed in PROFILE.md's Data Sources
- Any storage of student names, grades, or enrollment data — this tool only ever touches instructor-authored course content
- Real NLP/embedding-based concept similarity — overlap and gap matching are deterministic token/name-based, not semantic, and this is stated plainly in the dashboard and Manual.md
- Multi-user/collaboration features

## Tech Stack

- **Language:** Python 3
- **Framework:** None
- **Dependencies:** stdlib only (`sqlite3`, `argparse`, `json`, `re`, `html`, `urllib` for the optional Anthropic call)
- **Runtime requirement:** `python3 -m src.cli <command> ...` from the build folder; `render` produces a self-contained `.html` file that opens directly via `file://`

## Data Structure

SQLite database at `curriculum_atlas.db` (gitignored, created on first `add-course`):

```sql
CREATE TABLE courses (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    UNIQUE(name)
);

CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES courses(id),
    term TEXT NOT NULL,
    source_path TEXT NOT NULL,
    ingested_at TEXT NOT NULL,       -- ISO8601, injected by caller (no datetime.now() at import time issues)
    raw_char_count INTEGER NOT NULL,
    UNIQUE(course_id, term, source_path)
);

CREATE TABLE concepts (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    display_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    source TEXT NOT NULL             -- 'marker' | 'heading' | 'heuristic'
);

CREATE TABLE objectives (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    text TEXT NOT NULL
);

CREATE TABLE concept_notes (
    normalized_name TEXT PRIMARY KEY,
    note TEXT NOT NULL,
    generated_at TEXT NOT NULL
);
```

Re-ingesting the same `(course_id, term, source_path)` deletes and replaces that document's concepts/objectives (via `INSERT OR REPLACE` on `documents` + cascade delete of old rows keyed to the old document id) rather than duplicating — verified by a dedicated test.

## Folder Structure

```
builds/2026-08-16-curriculum-atlas/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── store.py        (SQLite schema + CRUD)
│   ├── parser.py        (deterministic concept + objective extraction)
│   ├── analysis.py      (overlap, gaps, term diff — pure functions over parsed data)
│   ├── ai_enrich.py     (optional Claude Haiku auto-marking + concept notes, via urllib)
│   ├── report.py        (HTML dashboard renderer)
│   └── cli.py            (argparse entry point)
├── skill/
│   └── SKILL.md
└── tests/
    ├── __init__.py
    ├── fixtures/
    │   ├── stress_coping_w3.md
    │   ├── social_affective_w1.md
    │   └── ai_apps_w2.md
    ├── test_store.py
    ├── test_parser.py
    ├── test_analysis.py
    ├── test_ai_enrich.py
    ├── test_report.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest, `tests/test_*.py`, run with `python -m pytest tests/ -v`
- **test_parser.py:** each concept source (marker, heading, heuristic) tested independently on hand-written fixture strings with known expected output; normalization/dedup collapsing "HPA Axis" (marker) and "hpa axis" (heuristic) into one concept; objective-phrase detection across all supported patterns; a document with zero concepts/objectives returns empty lists, not an error; a heading without a separator does not produce a bogus concept
- **test_analysis.py:** overlap correctly finds a concept in 2 of 3 courses and correctly excludes a concept unique to one course; Jaccard gap-scoring cross-checked by hand on a worked example (objective text vs. concept set) at both above- and below-threshold; term diff correctly reports added/removed/kept sets between two ingests of the same course with different concepts; empty-course edge cases (no documents yet) return empty results, not exceptions
- **test_store.py:** course creation is idempotent (`add_course` called twice with the same name does not create a duplicate row); re-ingesting the same course+term+path replaces rather than duplicates concepts/objectives (row counts asserted before/after); querying an unknown course returns an empty result, not a crash
- **test_ai_enrich.py:** every Anthropic call is mocked (`urllib.request.urlopen` patched) — never a live network call; auto-marking with no `ANTHROPIC_API_KEY` set makes zero network calls and returns the original unmarked text; a malformed/error API response falls back to the original text without raising; concept-notes batching only requests notes for names not already cached
- **test_report.py:** rendered HTML contains no unescaped injected payload when a concept/objective/course name contains `</script><script>alert(1)</script>` or `<img onerror=...>` — asserted by string search on the output, not just "it didn't crash"; JSON payload round-trips through `json.loads` on the embedded script content
- **test_cli.py:** end-to-end smoke test through the real CLI over a temp SQLite DB using the fixture files — `add-course` → `ingest` (2 courses sharing one concept, one course with an uncovered objective) → `overlap` reports the shared concept → `gaps` flags the uncovered objective → `render` produces a file that exists and is non-empty; unknown command and missing-file arguments produce a clean non-zero exit with a message, not a traceback
- **Minimum 15 tests, target ~30**, all must pass before commit

## Success Criteria

1. Ingesting two fixture documents from two different courses that intentionally share one concept name (e.g. "HPA Axis") causes `overlap` to report that concept against both courses.
2. Ingesting a fixture document containing an objective sentence with no matching concept anywhere in that document causes `gaps` to flag it (Jaccard score below threshold), verified against a hand-computed reference score.
3. Re-ingesting the same course+term+file path a second time does not create duplicate concept or objective rows (row count is identical before and after the second ingest).
4. With no `ANTHROPIC_API_KEY` set, `ingest --ai-mark` and `concepts --ai-notes` make zero network calls (verified via a mock call-count assertion) and the tool still produces correct deterministic concept/objective output.
5. `render` produces a self-contained HTML file in which a deliberately injected `<script>`/`onerror` payload in a course, concept, or objective name is present in the underlying JSON data but never executes or appears as live markup — verified by string inspection of the rendered output.
