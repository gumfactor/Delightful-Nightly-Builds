# Manual — Curriculum Atlas

> **Version:** 1.0 (built 2026-08-16)
> **Complexity:** Ambitious Project

---

## What This Is

Curriculum Atlas is a local knowledge base built from your own syllabi and lecture materials. Paste or export your course content to plain text/Markdown, ingest it per course and term, and the tool answers two things no single course file can: which concepts show up in more than one of your courses (on purpose, or by accident), and which of your stated learning objectives aren't actually backed by any concept you wrote down. Everything runs locally in a SQLite file — no data ever leaves your machine except an optional, explicitly-opted-into call to the Anthropic API.

---

## Quick Start

1. `cd` into this folder.
2. Register a course: `python3 -m src.cli add-course --name "Stress and Coping"`
3. Ingest a syllabus or lecture file: `python3 -m src.cli ingest --course "Stress and Coping" --term "Fall 2026" --file my_syllabus.md`
4. See what's shared across courses: `python3 -m src.cli overlap`
5. Render the dashboard: `python3 -m src.cli render --out report.html`, then open `report.html` in any browser.

---

## How to Use It

### Marking concepts in your source text

The most reliable way to get a concept recognized is to wrap it in double brackets: `the [[HPA axis]] regulates cortisol release`. This works with zero setup and zero API key.

If you don't hand-mark anything, the tool still extracts concepts two other ways:
- **Headings with a separator** — `## Week 3: Stress and the HPA Axis` contributes "Stress and the HPA Axis" as a concept. A bare document title (`# Stress and Coping — Fall 2026`) is deliberately *not* treated as a concept.
- **Capitalized phrase heuristic** — runs of 2–4 consecutive capitalized words in the body text (e.g. "Working Memory," "The Amygdala") are picked up automatically, filtered against a list of common capitalized sentence-starters.

### Marking objectives

Write objectives the way most syllabi already do — the tool recognizes several common phrasings automatically:
- `Students will explain...`
- `By the end of this course/week/session/unit/module/lecture, students will...`
- `Learners will...`
- `Objective 1: ...` / `Objective: ...`

An objective that wraps onto a second line (plain word-wrap) is still captured in full, as long as it isn't separated from its own start by a blank line.

### Commands

| Command | What it does |
|---|---|
| `add-course --name X` | Register a course (idempotent — safe to run again) |
| `list-courses` | List registered courses and how many documents/terms each has |
| `ingest --course X --term T --file PATH [--ai-mark]` | Parse a file into concepts + objectives for that course/term. Re-running on the same file replaces, never duplicates. |
| `concepts [--course X] [--term T] [--ai-notes]` | List extracted concepts, optionally scoped |
| `overlap` | Show every concept that appears in more than one course |
| `gaps --course X --term T [--threshold F]` | Flag objectives with no clearly-matching concept (default threshold 0.15) |
| `diff --course X --term-a T1 --term-b T2` | Compare a course's concept set between two terms |
| `render --out FILE [--ai-notes]` | Write the self-contained HTML dashboard |

### Optional AI enrichment

Set `ANTHROPIC_API_KEY` in your environment to unlock two optional features — both are pure add-ons, never required:
- `ingest --ai-mark`: if a document has zero `[[...]]` markers, Claude Haiku suggests where to add them. The marked-up text is then re-parsed by the exact same deterministic parser used for hand-marked input — the AI never adds a concept the code doesn't independently re-verify.
- `concepts --ai-notes` / `render --ai-notes`: generates a one-sentence plain-English gloss for each concept that doesn't have one yet, in a single batched call. Notes are cached, so a concept is only ever explained once.

With no key set, both flags are safe no-ops — zero network calls, and the deterministic output is unaffected.

### The dashboard

`render` produces a single self-contained HTML file with three tabs: **Courses** (per-course, per-term concept lists with source badges), **Cross-Course Overlap** (a table of every concept shared across more than one course), and **Objective Gaps** (a per-course/term table showing each objective's best-matching concept, its match score, and whether it's flagged). The search box at the top filters all three tabs live.

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `--db` | `curriculum_atlas.db` | Path to the SQLite database (create a separate one per semester if you like) |
| `--threshold` (on `gaps`) | `0.15` | Minimum Jaccard token-overlap score for an objective to count as "covered" |
| `ANTHROPIC_API_KEY` (env var) | unset | Enables `--ai-mark` and `--ai-notes`. Never required. |

---

## Known Limitations

- **Plain text/Markdown only.** PDF and Word syllabi need to be exported or pasted to text first.
- **Matching is deterministic token-overlap, not semantic.** "HPA axis" and "hypothalamic-pituitary-adrenal axis" will *not* be recognized as the same concept unless you mark them with the same `[[...]]` name, or hand-normalize the wording. This is a known, honest limitation, not a bug — the tool never guesses a semantic match it can't verify.
- **The heuristic capitalized-phrase extractor is imprecise.** It will occasionally pick up a real proper noun that isn't a concept (a person's name in a citation, for example). Hand-marking with `[[...]]` is always more reliable.
- **No student data is ever touched.** This tool only ever reads course/syllabus content you provide — it has no concept of grades, enrollment, or individual students, by design.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `error: no course named 'X'` | You tried to `ingest`/`concepts`/`gaps`/`diff` against a course that hasn't been registered | Run `add-course --name "X"` first |
| `error: could not read '...'` | Bad `--file` path | Check the path; the file must be plain text/Markdown |
| `overlap` shows nothing | No concept appears in more than one course yet | Expected if you've only ingested one course, or your courses genuinely don't share vocabulary |
| `--ai-mark`/`--ai-notes` seem to do nothing | `ANTHROPIC_API_KEY` isn't set | This is by design — set the env var to enable them; the tool still works fully without it |
| Dashboard shows a course with no concepts | The file had no `[[markers]]`, no headings with a separator, and no qualifying capitalized phrases | Add explicit `[[...]]` markers, or use `--ai-mark` with a key set |
