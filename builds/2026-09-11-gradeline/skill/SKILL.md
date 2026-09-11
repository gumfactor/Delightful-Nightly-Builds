---
name: gradeline
description: Batch-grade a folder of student written submissions against a rubric — deterministic compliance checks (word count, required sections, citation count, keyword coverage) plus near-duplicate detection, with an optional grounded AI feedback draft per criterion. Use when the user asks to grade, check, or QC a batch of student papers/essays/reflections against a rubric.
---

# GradeLine

Copy this file into `.claude/skills/gradeline/SKILL.md` in a project (or point Claude Code at this build folder directly) to grade student submissions on request — e.g. "grade this batch of reflection papers" or "check these essays for missing citations and near-duplicates."

## What it does

1. Reads an instructor-authored rubric JSON (document-level requirements: word count range, required section headings, minimum citation count; plus scored criteria, each either keyword-coverage-scored or `manual_only`).
2. Loads a batch of submissions — either a folder of one `.txt`/`.md` file per student, or a single file with `=== NAME ===` delimited sections.
3. Runs every submission through the same deterministic compliance and keyword-coverage checks, and flags any pair of submissions above a similarity threshold for manual review.
4. Persists the graded batch to a local SQLite database and can render it as a self-contained HTML report.

## Running it

```bash
# One-time: scaffold a rubric, then edit it
python3 main.py init-rubric my_rubric.json

# Grade a folder of submissions
python3 main.py grade /path/to/submissions --rubric my_rubric.json

# Grade with optional AI-drafted feedback (requires ANTHROPIC_API_KEY)
ANTHROPIC_API_KEY=sk-... python3 main.py grade /path/to/submissions --rubric my_rubric.json --ai

# List past batches, render the newest as HTML
python3 main.py list --db gradeline.db
python3 main.py render <batch_id> --db gradeline.db --out report.html
```

## Privacy note

When `--ai` is used, only the rubric criterion's own name/description and the submission's own text are sent to the Anthropic API — the student's identifier/filename is never included in the prompt, by construction (the AI module has no parameter for it).

See `../Manual.md` for the full command reference.
