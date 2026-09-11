# PRD — GradeLine

> **Build date:** 2026-09-11
> **Category:** B — Productivity Utility
> **Complexity:** Ambitious Project

---

## Goal

Batch-check a folder of students' written submissions against an instructor-defined rubric — deterministic structural/citation/keyword-coverage compliance checks, near-duplicate detection across the whole batch, and optional grounded AI feedback drafts — producing a consistent first-pass grading report in minutes instead of hours.

## User Story

As a professor who teaches multiple courses and has named "Student evaluation workflows" as a specific manual friction point, I want to run every student's submission for an assignment through the same rubric-compliance and near-duplicate check in one batch, so that I catch structural/citation gaps and possible over-similar submissions before I sit down to grade, and start every submission's feedback from a consistent, evidence-grounded draft rather than a blank page.

## Scope

### In Scope
- A JSON rubric format: overall document requirements (min/max word count, required section headings, minimum citation count) plus a list of scored criteria, each either keyword-coverage-scored (deterministic) or explicitly `manual_only` (flagged for the instructor's own judgment, never auto-scored)
- `init-rubric` — scaffolds a starter rubric JSON file the instructor edits
- Submission loading from either (a) a folder of one `.txt`/`.md` file per student, or (b) a single file with `=== NAME ===` delimited sections
- Deterministic checks per submission: word count in range, required-section presence (heading detection), citation count (Author-Year and numbered-bracket styles), per-criterion keyword-coverage scoring, Flesch Reading Ease (informational)
- From-scratch TF-IDF vectorization + cosine similarity across every submission pair in a batch; pairs above a configurable threshold (default 0.75) are flagged "review for possible over-similarity" — the tool never accuses, only flags for human review
- Local SQLite persistence of every graded batch (never overwritten), so re-grading a revised batch or comparing two assignments' class-level stats is possible via `history`/`compare`
- Optional Claude Haiku feedback drafting (`--ai`, requires the user's own `ANTHROPIC_API_KEY`) — one grounded paragraph per criterion per submission (including `manual_only` criteria, where the instructor's holistic judgment benefits most from a grounded starting draft), built strictly from the criterion's own name/description and the submission's own text; **the student's name/filename is never included in the AI prompt at all** — the AI feedback function has no parameter for it — and every auto-scored criterion's score is always the deterministic one (the AI drafts prose, it never re-scores)
- Unconditional deterministic-template fallback for feedback text when no API key is set or a call fails — zero network calls in that path
- Terminal summary, `--json` export, and a self-contained dark-mode HTML report (per-student cards, class-level per-criterion average chart, similarity-flags panel)
- Companion Claude Code Skill (`skill/SKILL.md`)
- pytest suite covering rubric validation, parsing (both submission formats), every deterministic check, the similarity engine (including hand-verified edge cases), SQLite persistence, the AI layer's transport-injected mock path and its zero-network fallback path, HTML rendering, and the CLI end-to-end

### Out of Scope
- OCR / PDF / DOCX ingestion (plain text/Markdown only tonight — a real, common workflow is already served by asking students to submit as text, and this keeps the parsing layer honest and fully testable)
- Multi-instructor / multi-grader agreement (inter-rater reliability) — single-instructor tool tonight
- Any network call to a plagiarism-detection service (Turnitin, etc.) — the similarity check is local-only, computed from the submissions the instructor already has on disk, and never leaves the machine
- Grade-book / LMS export integration (Canvas, etc.) — flagged in FutureFeatures.md

## Tech Stack

- **Language:** Python 3
- **Framework:** None
- **Dependencies:** stdlib only (`sqlite3`, `re`, `json`, `urllib.request`, `argparse`, `math`); Chart.js 4.4.4 via CDN in the rendered HTML only (with a verified DOM-table fallback when the CDN is unreachable)
- **Runtime requirement:** `python3 main.py <command> ...` — no install needed beyond stdlib Python 3

## Data Structure

**Rubric (JSON file, instructor-authored):**
```json
{
  "name": "Stress & Coping — Reflection Paper",
  "min_words": 800,
  "max_words": 1500,
  "min_citations": 3,
  "required_sections": ["Introduction", "Discussion", "Conclusion"],
  "criteria": [
    {"id": "thesis", "name": "Clear Thesis", "description": "States a clear, arguable thesis.",
     "max_points": 10, "keywords": ["thesis", "argue", "claim"], "min_keyword_hits": 1, "manual_only": false},
    {"id": "argument_quality", "name": "Argument Quality", "description": "Depth and coherence of reasoning.",
     "max_points": 15, "keywords": [], "min_keyword_hits": 0, "manual_only": true}
  ]
}
```

**Submissions:** plain text/Markdown, one per student (folder mode: filename stem is the identifier; single-file mode: `=== NAME ===` delimiter captures it). The identifier is used only for local display/storage — never passed into the AI prompt.

**SQLite (`gradeline.db`, created next to the rubric unless `--db` is given):**
- `batches(id, rubric_name, rubric_json, source_path, graded_at)`
- `submissions(id, batch_id, identifier, word_count, citation_count, flesch_score, compliance_json, criteria_json, ai_feedback_json)`
- `similarity_pairs(id, batch_id, submission_a_id, submission_b_id, score)`

## Folder Structure

```
builds/2026-09-11-gradeline/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── conftest.py
├── main.py
├── src/
│   ├── __init__.py
│   ├── rubric.py
│   ├── parser.py
│   ├── checks.py
│   ├── similarity.py
│   ├── storage.py
│   ├── ai.py
│   ├── render.py
│   └── cli.py
├── skill/
│   └── SKILL.md
├── sample_data/
│   ├── rubric_example.json
│   └── submissions/ (6 example student files, one planted near-duplicate pair)
└── tests/
    ├── test_rubric.py
    ├── test_parser.py
    ├── test_checks.py
    ├── test_similarity.py
    ├── test_storage.py
    ├── test_ai.py
    ├── test_render.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Rubric loading/validation (valid rubric loads; missing required key raises a clear error; a non-`manual_only` criterion with `min_keyword_hits: 0` raises a validation error)
  - Submission parsing in both modes, including empty-folder and malformed-delimiter edge cases
  - Word count, section detection (case-insensitive, Markdown-heading and ALL-CAPS-line variants), citation counting (both cited styles, zero-citation case), keyword-coverage scoring (0 hits, partial hits scaled proportionally, hits at/above the minimum capped at max_points)
  - Similarity engine: identical documents → 1.0; disjoint vocabularies → 0.0; a hand-computed partial-overlap pair matches to 4 decimal places; a batch of 1 submission returns zero pairs without error
  - SQLite persistence: a batch round-trips exactly; re-grading appends a new batch rather than overwriting; `compare` reads two real batches
  - AI layer: a mocked transport returns parsed feedback text; the student identifier is asserted absent from every call's payload; no `ANTHROPIC_API_KEY` and `--ai` unset both take the zero-network fallback path (asserted via a transport that raises if ever called)
  - HTML rendering: a script/img-tag injection payload in a submission identifier renders as inert text (string-level escape assertion, plus a live headless-Chromium check during manual verification)
  - CLI: `init-rubric`, `grade`, `list`, `show`, `render`, `compare` each exercised end-to-end against real fixture files

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests (target 45+ given the algorithmic surface area)
2. `python3 main.py grade sample_data/submissions --rubric sample_data/rubric_example.json` runs against the real sample batch and correctly flags the planted near-duplicate pair and the deliberately non-compliant submission
3. The TF-IDF similarity engine's output is verified against hand-computed reference values for at least 3 cases (identical, disjoint, partial-overlap), not just internal consistency
4. `render` produces a self-contained HTML report that opens directly (`file://`) with zero page errors and zero executed script from injected content in a submission identifier
5. With no `ANTHROPIC_API_KEY` set, every code path (including `--ai`) makes zero network requests, and the student identifier never appears in any AI transport payload when `--ai` is used with a key

---

## Scope Changes

None — full scope as planned above was completed as designed.
