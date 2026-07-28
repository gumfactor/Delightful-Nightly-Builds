# Manual — Voiceprint

Voiceprint audits a Markdown/plain-text draft for the lexical and structural patterns that make
prose read as AI-generated or formulaic, scores it 0–100, and tracks that score across revisions
of the same file.

## Setup

```bash
cd builds/2026-07-28-voiceprint
pip install -r requirements.txt   # only needed to run the tests locally
```

No setup is required to run the tool itself — it's stdlib-only. `pip install` is only for `pytest`.

## Commands

### Analyze a single file

```bash
python3 main.py analyze path/to/draft.md
```

Prints a colored terminal report: Human Voice Score, penalty breakdown, and every flagged
AI-tell phrase with its line number and surrounding text.

Options:
- `--ai` — also request a Claude Haiku second opinion on the three worst paragraphs. Requires
  `ANTHROPIC_API_KEY` to be set in your environment; without it, a deterministic template-based
  second opinion is used instead (still fully functional, no network call attempted).
- `--json` — print a JSON report instead of the terminal report (for piping into other tools).
- `--html OUTFILE` — also write a self-contained dark-mode HTML report to `OUTFILE`. Open it in
  any browser; it's readable on a phone.
- `--db PATH` — history database path (default: `voiceprint.db` in the current directory).

Example with everything on:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 main.py analyze my-book/chapter-3.md --ai --html chapter-3-report.html --db my-book/voiceprint.db
```

### Batch mode

```bash
python3 main.py batch path/to/drafts-directory/
```

Runs `analyze` against every `.md` and `.txt` file directly inside the directory. Options:
`--ai`, `--db`, and `--html-dir DIR` (writes one HTML report per file, named after the source file).

### History

```bash
python3 main.py history path/to/draft.md
```

Shows every prior score for that exact file path, in order, with the delta from the previous run
and a simple terminal bar. Re-run `analyze` on the same file path as you revise it — each run adds
a new history point (this is the main way to use Voiceprint across a long-running project like a
book chapter you're revising over several sessions).

## What the score means

- **80–100 — reads natural.** Few or no flagged patterns.
- **60–79 — some formulaic patterns.** Worth a pass before publishing.
- **Below 60 — heavily flagged.** Multiple AI-tell phrases, mechanical rhythm, or repeated
  structure; read the penalty breakdown to see which.

The score is 100 minus a set of capped, documented penalties (see `src/scoring.py` for the exact
weights) — it is not a machine-learning classifier and makes no claim about whether text was
literally written by an AI. It flags the specific lexical/structural habits that make prose read
as formulaic, whatever the source.

## Running the tests

```bash
cd builds/2026-07-28-voiceprint
pytest tests/ -v
```

(This container's `python3` doesn't have `pytest` importable as a module and `pip install` is
blocked by sandbox policy, so this build was tested with the standalone `pytest` launcher already
on `PATH`. On your own machine, `pip install -r requirements.txt` first and either `pytest tests/ -v`
or `python -m pytest tests/ -v` will work — a `conftest.py` at the build root makes the `src`
imports resolve correctly either way.)

## Known limitations

- Passive-voice and rule-of-three detection are regex heuristics, not a real parser — they will
  miss irregular verbs and can occasionally flag an intentional stylistic triad. Treat every flag
  as a nudge to re-read, not an automatic rewrite instruction.
- Only `.md`/`.txt` input is supported (see FutureFeatures.md for `.docx`).
- The AI-tell phrase list is a fixed, hand-curated set of ~65 phrases — it won't catch every
  formulaic pattern, and language trends change; expect to extend the list over time.
