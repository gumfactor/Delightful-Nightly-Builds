# Manual — Paper Lens

## Overview

Paper Lens is a command-line tool and HTML viewer that fetches recent research papers from arXiv, scores their relevance to your research areas using Claude, and presents them in a searchable dark-mode inbox sorted by relevance. Run `fetch` each morning; open `output/inbox.html` in your browser.

## Requirements

- Python 3.8+
- `ANTHROPIC_API_KEY` environment variable (optional — falls back to relevance=5 and truncated abstract if absent)
- Network access to `export.arxiv.org`

## Commands

```bash
# From the builds/2026-06-23-paper-lens/ directory:

python src/main.py fetch              # Fetch new papers from arXiv + AI analysis
python src/main.py view               # Generate output/inbox.html
python src/main.py list               # List all papers (text, sorted by relevance)
python src/main.py search <query>     # Search by keyword across title, summary, authors
python src/main.py read <arxiv_id>    # Mark a paper as read in the database
```

## Workflow

1. **Daily fetch**: Run `fetch` each morning. New papers are downloaded from arXiv (4 topic queries), analyzed by Claude Haiku for relevance and plain-English summary, and stored in `data/papers.db`.

2. **Open viewer**: Run `view` to regenerate `output/inbox.html`. Open this file in any browser — no server required.

3. **Browse**: Use the filter tabs (All / Unread / Today / High Relevance) and the search bar to navigate your inbox. Papers are sorted by relevance score by default.

4. **Mark as read**: Click "Mark as read" on any card — read state persists in browser localStorage. Or use `python src/main.py read <arxiv_id>` to mark in the database.

## Relevance Score Guide

| Score | Meaning | Badge color |
|-------|---------|-------------|
| 8–10 | Directly in your research areas | Green |
| 4–7 | Relevant to related topics | Amber |
| 1–3 | Tangentially related | Grey |

Default relevance is 5 when `ANTHROPIC_API_KEY` is not set.

## Topic Queries

Default topics searched (configured in `src/fetcher.py`):

| Topic name | arXiv query |
|-----------|-------------|
| Affective Neuroscience | `cat:q-bio.NC` (15 results) |
| Psychopathy & Empathy | `ti:psychopathy OR ti:empathy` (10 results) |
| Stress & HPA | `ti:stress AND ti:neuroscience` (8 results) |
| AI Agents & LLMs | `cat:cs.AI AND (ti:agent OR ti:autonomous)` (12 results) |

To change topics, edit the `TOPICS` list in `src/fetcher.py`.

## Data Storage

All data is stored in `data/papers.db` (SQLite, inside the build folder). The database is created automatically on first `fetch`. Nothing is written outside this build folder.

## Running Tests

```bash
# From builds/2026-06-23-paper-lens/
python3 -m pytest tests/ -v
```

Tests: 43 (11 fetcher + 10 analyzer + 12 database + 10 renderer)

## Setting Up as a Daily Routine

To run Paper Lens automatically each morning via Claude Code:

1. Add a Claude Code Routine that runs `python src/main.py fetch && python src/main.py view` on a daily schedule.
2. The generated `output/inbox.html` will be updated each morning.
3. Open the HTML file in your browser to see the day's papers.

See [Claude Code Routines documentation](https://code.claude.com/docs/en/claude-code-on-the-web) for setup instructions.
