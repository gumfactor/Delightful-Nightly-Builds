# Manual — Throughline

A personal knowledge base of your own publications: live citation counts, deterministic thematic clusters, citation-growth tracking, and a grant/CV-ready research narrative per theme.

## Setup

Python 3.9+, no third-party packages required to run the tool itself (only `pytest` is needed to run the tests). No API key is required for `lookup`, `sync`, `cluster`, `growth`, or `render`. `narrative --ai` requires `ANTHROPIC_API_KEY` in your environment; without it, `narrative` still works and produces a deterministic summary.

```bash
cd builds/2026-09-12-throughline
```

## Step 1 — Find your author id

Semantic Scholar author-name search is ambiguous (many people share a name), so this is always a manual, human-confirmed step:

```bash
python3 main.py lookup "Your Name"
```

This prints every matching author with their id, affiliations, paper count, citation count, and a few sample titles. Pick the row that is actually you.

## Step 2 — Sync your publication record

```bash
python3 main.py sync --author-id <id-from-step-1> --name "Your Name"
```

This fetches your full paper list (title, year, venue, abstract, citation count) and stores it in a local SQLite database (`throughline.db` by default — pass `--db path/to/file.db` to use a different location). Every citation count is also appended as a timestamped snapshot, so re-running `sync` later (e.g. monthly) builds a citation-growth history. Re-running `sync` never duplicates a paper — it updates the existing row in place.

## Step 3 — Cluster your papers by theme

```bash
python3 main.py cluster
```

Groups your papers into thematic clusters using a fully deterministic, stdlib-only algorithm (corpus-wide keyword scoring + keyword-overlap grouping — no external ML libraries, no network calls). Re-running `cluster` after a `sync` recomputes clusters from the current corpus.

## Step 4 — Generate a research narrative per cluster

```bash
python3 main.py narrative
# or, for an AI-written version:
ANTHROPIC_API_KEY=sk-... python3 main.py narrative --ai
```

Without `--ai` (or without an API key set), each cluster gets a deterministic summary (top keywords, year range, paper count, total citations, titles) — useful on its own, and always the safety net. With `--ai`, each cluster's titles/abstracts/keywords are sent to Claude Haiku for a one-paragraph "research narrative" synthesizing the throughline — a good starting draft for a grant biosketch or manuscript introduction. If the AI call fails for any reason, the deterministic summary is used instead automatically.

## Step 5 — See citation growth

```bash
python3 main.py growth
```

Prints every paper's citation count at first sync vs. most recent sync, sorted by biggest gain first. Requires at least two `sync` runs to show a nonzero delta.

## Step 6 — Render the dashboard

```bash
python3 main.py render --output dashboard.html
```

Writes a self-contained HTML file (no server needed — open it directly in a browser) with:
- Cluster cards showing each theme's narrative and member papers
- A sortable table of every paper (click a column header to sort; click again to reverse)
- A live search box filtering the paper table by title or venue
- A citation-growth chart (falls back to a plain table if Chart.js can't load, e.g. offline)

## Other commands

```bash
python3 main.py papers          # list all locally stored papers
python3 main.py --db other.db sync ...   # use a different database file
```

## Running the tests

```bash
python -m pytest tests/ -v
```

60 tests, all mocking the Semantic Scholar and Anthropic HTTP calls — no live network access is required to run the test suite.

## As a Claude Code Skill

See `skill/SKILL.md` — copy it to `.claude/skills/throughline/SKILL.md` in a project to trigger a sync/narrative refresh on request from within a coding session.
