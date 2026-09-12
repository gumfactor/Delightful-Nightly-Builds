---
name: throughline
description: Build and refresh a local knowledge base of the user's own academic publications and citation growth from the free Semantic Scholar API, cluster them by theme, and draft a grant/CV-ready research narrative per theme. Use when the user asks to summarize their research program, update their publication record, or write the "prior work"/biosketch section of a grant or manuscript.
---

# Throughline

Copy this file into `.claude/skills/throughline/SKILL.md` in a project (or point Claude Code at this build folder directly) to refresh the user's personal research-corpus knowledge base on request — e.g. "pull my latest citation counts" or "give me a research narrative for my grant biosketch."

## What it does

1. Looks up the user's Semantic Scholar author id by name (a one-time, human-confirmed step — author-name search is ambiguous, so it never auto-selects).
2. Syncs the confirmed author's full paper list and current citation counts into a local SQLite database, appending a timestamped citation snapshot on every sync so growth is trackable across runs.
3. Deterministically clusters the corpus into themes (stdlib TF-IDF + Jaccard overlap — no ML libraries, no external calls).
4. Produces a one-paragraph narrative per theme — a deterministic template by default, or a Claude Haiku-written synthesis with `--ai` (requires `ANTHROPIC_API_KEY`).
5. Renders a self-contained HTML dashboard with cluster narratives, a sortable paper table, and a citation-growth chart.

## Running it

```bash
# One-time: confirm the correct author id
python3 main.py lookup "Jane Doe"

# Pull/refresh the publication record and citation counts
python3 main.py sync --author-id <id> --name "Jane Doe"

# Recompute thematic clusters
python3 main.py cluster

# Draft a research narrative per cluster (add --ai for a Claude Haiku-written version)
python3 main.py narrative --ai

# See citation growth since the last sync
python3 main.py growth

# Write the dashboard
python3 main.py render --output dashboard.html
```

## Privacy note

The only third-party data sent anywhere is what `sync` already pulled from the public Semantic Scholar API (paper titles/abstracts/keywords) — `narrative --ai` sends only that already-public text to Claude Haiku, never the user's name, email, or any other local file content.

See `../Manual.md` for the full command reference.
