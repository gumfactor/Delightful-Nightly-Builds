---
name: curriculum-atlas
description: Ingest course syllabi/lecture text into a local knowledge base, then check which concepts overlap across courses and which stated learning objectives aren't backed by any concept in the materials. Use when the user is preparing or reviewing course materials and asks something like "add this syllabus to my curriculum atlas," "does this course share any concepts with my other courses," or "check my syllabus for uncovered objectives."
---

# Curriculum Atlas — Cross-Course Concept & Objective Knowledge Base

Wraps the `curriculum-atlas` CLI (from `builds/2026-08-16-curriculum-atlas/` in the Delightful-Nightly-Builds repo) so a coding session can ingest and query course materials without leaving the session.

## When to use this

The user is working on a syllabus, lecture outline, or course-prep material and wants to either (a) add it to their running curriculum knowledge base, or (b) ask a cross-course question about it — "have I taught this concept before," "is this objective actually covered by what I wrote," "how has this course changed since last term."

## How to run it

All commands run from `builds/2026-08-16-curriculum-atlas/`:

1. **Register a course** (once, idempotent to re-run):
   ```bash
   python3 -m src.cli add-course --name "<Course Name>"
   ```
2. **Ingest a document.** For best concept detection, suggest the user wrap key terms in `[[double brackets]]` in their source text before ingesting — or pass `--ai-mark` if `ANTHROPIC_API_KEY` is set to have Claude Haiku suggest markers automatically (the deterministic parser always re-verifies whatever gets marked, so this is safe even unattended):
   ```bash
   python3 -m src.cli ingest --course "<Course Name>" --term "<Term Label>" --file <path.md> [--ai-mark]
   ```
   Re-ingesting the same file path for the same course+term replaces that document's data — it never duplicates.
3. **Answer a cross-course question:**
   ```bash
   python3 -m src.cli overlap                                            # concepts shared across courses
   python3 -m src.cli gaps --course "<Course Name>" --term "<Term Label>"  # objectives not backed by any concept
   python3 -m src.cli diff --course "<Course Name>" --term-a <T1> --term-b <T2>  # concept drift between terms
   ```
4. **If the user wants a browsable view**, run `python3 -m src.cli render --out report.html` and point them to the file — it's self-contained and safe to open via `file://`.

## Notes

- Everything runs against a local SQLite file (`curriculum_atlas.db` by default in the CLI's working directory, override with `--db`) — no network access is required for the core workflow.
- `--ai-mark` and `concepts --ai-notes`/`render --ai-notes` are optional and make zero network calls when `ANTHROPIC_API_KEY` is unset — report the deterministic result either way, and mention the flag exists if the user has a key and wants richer output.
- Concept matching is exact-normalized-name matching, not semantic — if the user expects two differently-worded mentions of the same idea to be recognized as one concept, tell them to use the same `[[marker]]` text in both places.
- This tool never stores or transmits student names, grades, or enrollment data — only instructor-authored course content.
