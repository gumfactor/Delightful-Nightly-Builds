---
name: lecture-loom
description: Batch-convert a folder of raw lecture notes into a consistent slide outline + student handout, with a deterministic timing-budget and objective-completeness check. Use when the user asks to format, check, or prep lecture notes, or mentions turning course notes into slides/handouts.
---

# Lecture Loom

Turns raw, inconsistently-formatted lecture notes (Markdown or plain text) into
a consistent slide outline and student handout per lecture, with deterministic
checks that catch real problems before the professor walks into the room:
lectures likely to run over their time slot, lectures missing learning
objectives, and sections that are unbalanced relative to the rest of the
lecture.

## When to use this

The user wants to:
- Reformat one or more raw lecture-note files into a consistent structure
- Check whether a lecture will run long before presenting it
- Get a batch-wide view across a course folder of which lectures need attention

## How to invoke it

The tool lives at `../src/main.py` relative to this file (i.e.
`builds/2026-08-24-lecture-loom/src/main.py`). Run it with `python3`:

```bash
# Quick terminal check — no files written
python3 src/main.py check <path-to-file-or-folder>

# Write outline.md + handout.md for every lecture in a folder
python3 src/main.py format <path-to-folder> --output <output-dir>

# Build a batch HTML dashboard across a folder
python3 src/main.py render <path-to-folder> --output <output-dir>
```

Useful flags on every command:
- `--target-minutes N` — the class period length in minutes (default: 50)
- `--wpm N` — assumed instructional speaking pace in words/minute (default: 130)
- `--ai-polish` — sends only the extracted structure (headings + bullets, never
  raw file content) to Claude Haiku for presenter-phrasing cleanup and 2–3
  discussion questions. Requires `ANTHROPIC_API_KEY` in the environment;
  without it, a deterministic cleanup runs instead and no network call is made.

## What to tell the user

- The timing estimate is based on a configurable words-per-minute constant,
  not their own measured speaking rate — encourage them to pass `--wpm` if the
  default 130 doesn't match how they actually present.
- `format` never overwrites the input files — it only writes new
  `.outline.md`/`.handout.md` files into `--output`.
- If a lecture is flagged `missing` objectives, that just means neither an
  explicit "Objectives" heading nor a "By the end of this lecture, students
  will..." sentence was found — not that the lecture has no educational value.
