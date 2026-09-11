# Manual — GradeLine

> **Version:** 1.0 (built 2026-09-11)
> **Complexity:** Ambitious Project

---

## What This Is

GradeLine is a batch grading assistant for written student submissions (essays, reflection papers, short-answer assignments). Point it at a rubric and a folder of student text files, and it runs every submission through the same deterministic checks — word count, required-section presence, citation count, keyword-coverage scoring per criterion — and flags any pair of submissions that are suspiciously similar to each other, all before you sit down to grade. An optional AI layer can draft grounded per-criterion feedback text, but the scores and compliance flags are always computed the same deterministic way, with or without an API key.

---

## Quick Start

1. `python3 main.py init-rubric my_rubric.json` — scaffolds a starter rubric; open it and edit the criteria, keywords, and requirements for your assignment.
2. Put your students' submissions in a folder as one `.txt`/`.md` file per student (filename = that student's identifier), or as a single file with `=== Student Name ===` delimiters.
3. `python3 main.py grade path/to/submissions --rubric my_rubric.json` — grades the batch and prints a summary.
4. `python3 main.py render <batch_id> --db gradeline.db --out report.html` — opens the id printed by `grade`, and writes a browsable HTML report you can open directly.

Try it immediately against the bundled sample data:
```bash
python3 main.py grade sample_data/submissions --rubric sample_data/rubric_example.json
```

---

## How to Use It

### The Rubric File

A rubric is a JSON file with document-level requirements and a list of criteria:

```json
{
  "name": "My Assignment",
  "min_words": 800,
  "max_words": 1500,
  "min_citations": 3,
  "required_sections": ["Introduction", "Discussion", "Conclusion"],
  "criteria": [
    {"id": "thesis", "name": "Clear Thesis", "description": "...",
     "max_points": 10, "keywords": ["thesis", "argue"], "min_keyword_hits": 1, "manual_only": false},
    {"id": "depth", "name": "Argument Depth", "description": "...",
     "max_points": 20, "manual_only": true}
  ]
}
```

Every criterion is either:
- **Auto-scored**: give it `keywords` and a `min_keyword_hits` ≥ 1. GradeLine counts how many of those keywords appear in the submission and awards partial credit proportionally, capped at `max_points`.
- **`manual_only: true`**: reserved entirely for your own judgment. GradeLine never assigns it a score — it only (optionally) drafts AI feedback text for it, clearly labeled "needs manual score" everywhere it appears.

### Submission Formats

**Folder mode** (recommended for most classes): one `.txt` or `.md` file per student in a folder. The filename (without extension) becomes that student's identifier everywhere GradeLine displays it.

**Single-file mode**: one file with each student's submission introduced by a line like `=== Jane Doe ===`. Useful when you already have everything pasted into one document.

### Grading a Batch

```bash
python3 main.py grade path/to/submissions --rubric my_rubric.json [--db gradeline.db] [--threshold 0.75] [--ai] [--json]
```

- `--db` — where to store results (default: `gradeline.db` next to your rubric file). Every `grade` run creates a **new** batch; nothing is ever overwritten, so re-grading a revised batch or a follow-up assignment keeps full history.
- `--threshold` — the cosine-similarity score (0-1) above which two submissions are flagged for manual over-similarity review. Default 0.75.
- `--ai` — draft AI feedback text per criterion (see below). Requires `ANTHROPIC_API_KEY` to be set in your environment.
- `--json` — print the full batch result as JSON instead of a summary.

### Reviewing Past Batches

```bash
python3 main.py list --db gradeline.db
python3 main.py show <batch_id> --db gradeline.db
python3 main.py render <batch_id> --db gradeline.db --out report.html
python3 main.py compare <batch_id_a> <batch_id_b> --db gradeline.db
```

`render` produces a self-contained HTML file — per-student cards (compliance badges, per-criterion scores and feedback), a class-level average chart per criterion, and a panel listing every flagged similarity pair. Open it directly in a browser; no server needed.

### AI Feedback (optional)

Set `ANTHROPIC_API_KEY` in your environment and pass `--ai` to draft one short, grounded feedback paragraph per criterion per submission (including `manual_only` criteria — the AI can still draft a starting narrative even though it never sets the score). **Only the criterion's own name/description and the submission's own text are sent** — the student's name or filename is never included in the prompt; the AI drafting function has no parameter for it. Without `--ai`, or without an API key set, GradeLine makes zero network calls and uses a deterministic feedback template instead.

### Similarity Flags

GradeLine builds a TF-IDF vector for every submission in the batch and flags any pair above the similarity threshold. This is a **textual near-duplication detector**, not a plagiarism database lookup — it never leaves your machine, and it will not catch a paraphrased or AI-rewritten near-copy with substantially different wording. Treat every flag as "worth a manual look," never as a finding on its own.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `--db` | `gradeline.db` next to the rubric file | SQLite database path |
| `--threshold` | `0.75` | Cosine-similarity flag threshold (0-1) |
| `ANTHROPIC_API_KEY` (env var) | unset | Required for `--ai`; without it, `--ai` silently falls back to deterministic feedback |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `grade` fails with "Criterion '...' is not manual_only but has no keywords" | Your rubric has an auto-scored criterion with an empty `keywords` list | Add keywords and a `min_keyword_hits`, or set `manual_only: true` |
| A section you know is present shows as missing | The heading isn't alone on its own line, or uses different wording than the rubric | Put the heading on its own line (`Discussion` or `## Discussion`); GradeLine doesn't infer headings from prose |
| `--ai` produces no different output than without it | `ANTHROPIC_API_KEY` isn't set, or the API call failed | Check `echo $ANTHROPIC_API_KEY`; a failed call always falls back silently, by design |
| `render` command errors with "No batch with id ..." | The batch id doesn't exist in the `--db` you pointed at | Run `list --db <path>` to see valid batch ids for that database file |

---

## Known Limitations

- Plain text/Markdown submissions only — no DOCX or PDF ingestion yet (see FutureFeatures.md).
- Citation counting recognizes Author-Year parenthetical and numbered-bracket styles only; narrative citations ("Smith (2019) found...") are not counted.
- Section-heading detection requires the heading on its own line; a heading embedded mid-sentence or numbered ("1. Introduction") is not recognized.
- The similarity engine detects textual near-duplication, not paraphrased or semantically-similar plagiarism.
