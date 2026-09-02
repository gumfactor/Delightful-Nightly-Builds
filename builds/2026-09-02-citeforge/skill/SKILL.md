---
name: cite-format
description: Format a bibliography or pasted reference list in APA 7, AMA 11, Vancouver/ICMJE, or Chicago Author-Date 17 style using CiteForge. Use when the user pastes references, a .bib file, or DOIs and asks to convert/format/reformat citations for a manuscript or grant.
---

# cite-format

Formats a reference list into one or more academic citation styles using the CiteForge CLI (`builds/2026-09-02-citeforge/`).

## When to use this skill

- The user pastes one or more references and asks for them in a specific style ("format these in AMA", "convert this bibliography to Vancouver").
- The user has a `.bib` file or a list of DOIs and wants a formatted reference list.
- The user is preparing the same manuscript/grant for submission under a different journal's citation style requirement.

## How to run it

From the repo root:

```bash
cd builds/2026-09-02-citeforge

# From a BibTeX file
python main.py --db /tmp/citeforge.db add-bibtex refs.bib

# From one or more DOIs (one per line in a file, or a single DOI)
python main.py --db /tmp/citeforge.db add-doi 10.1037/ppm0000185

# From pasted free-text references (one per line); --ai requires ANTHROPIC_API_KEY
python main.py --db /tmp/citeforge.db add-text references.txt --ai

# Format everything in the library in one style
python main.py --db /tmp/citeforge.db format --style apa
python main.py --db /tmp/citeforge.db format --style ama
python main.py --db /tmp/citeforge.db format --style vancouver
python main.py --db /tmp/citeforge.db format --style chicago

# Side-by-side all 4 styles
python main.py --db /tmp/citeforge.db compare

# Self-contained HTML report (opens directly in a browser, copy buttons per entry)
python main.py --db /tmp/citeforge.db render -o /tmp/citeforge_report.html
```

Use a fresh/temporary `--db` path per task unless the user wants a persistent personal bibliography — the SQLite file is the library, so reusing one path accumulates references across sessions.

## What to tell the user

- References flagged `NEEDS REVIEW` in `list`/`render` output could not be confidently parsed from free text — show the raw line back to the user and ask for the missing fields rather than guessing.
- AMA/Vancouver output uses full journal names, not NLM abbreviations (a documented limitation — see `Manual.md`).
- Chicago output omits place-of-publication and month (not tracked in the data model).
