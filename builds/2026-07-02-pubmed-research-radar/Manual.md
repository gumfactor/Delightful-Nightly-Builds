# Manual — PubMed Research Radar

A personal literature-triage tool: it pulls new PubMed articles for your saved research topics, ranks them by relevance, and gives you an AI-written plain-English summary so you can decide in seconds what's worth reading.

## Setup

```bash
cd builds/2026-07-02-pubmed-research-radar
pip install -r requirements.txt
```

No API key is required to use the tool. If you export `ANTHROPIC_API_KEY` in your shell, `fetch` will use Claude Haiku to score relevance and write summaries; without it, `fetch` still works using a deterministic keyword-overlap fallback (no AI summary, just the raw abstract).

```bash
export ANTHROPIC_API_KEY="sk-ant-..."   # optional — enables AI scoring/summaries
```

## Everyday Use

**1. See (or edit) your saved topics.** Five are pre-seeded from a neuroscience/forensic-psychology research profile — affective neuroscience, psychopathy, empathy, stress & coping, forensic neuroscience:

```bash
python3 -m src.cli topics list
python3 -m src.cli topics add "Oxytocin & Trust" 'oxytocin[tiab] AND trust[tiab]'
python3 -m src.cli topics remove "Oxytocin & Trust"
```

**2. Pull new articles.** Queries PubMed for each topic's articles published in the last N days (default 14), stores them locally, and scores anything new:

```bash
python3 -m src.cli fetch                          # last 14 days, up to 20 per topic
python3 -m src.cli fetch --days 30 --max-per-topic 40
```

Re-running `fetch` never creates duplicate articles — it dedupes by PubMed ID.

**3. Generate the report.** A single self-contained dark-mode HTML file — open it in any browser, no server required:

```bash
python3 -m src.cli report --output report.html
open report.html   # or: xdg-open report.html
```

The report has one tab per topic, articles sorted by relevance (highest first), a live search box, and Star/Read buttons per article (state is saved in your browser's `localStorage`, so it persists across report regenerations on the same machine/browser).

**4. Search or check status from the terminal, without opening the report:**

```bash
python3 -m src.cli search "amygdala"
python3 -m src.cli stats
```

## Recommended Habit
Run `fetch` then `report` once a day (or wire it into a cron job / Claude Code Routine — see FutureFeatures.md), and open `report.html` as your literature-review starting point instead of manually re-running PubMed searches.

## Running the Tests

```bash
python -m pytest tests/ -v
```

All 56 tests run offline — every PubMed and Anthropic API call is mocked against fixture data in `tests/fixtures/`, so the suite passes with zero network access and no API key.

## A Note on This Build's Own Sandbox
This build was authored and tested inside a network-restricted autonomous session (see `BUILD_LOG.md`/`WhyThis.md` for the investigation). Live PubMed/Anthropic calls could not be exercised end-to-end from inside that sandbox — a real `fetch` there prints a graceful "Skipping '<topic>': ... 403 Forbidden" for each topic and exits cleanly rather than crashing, which was confirmed manually. On a normal machine with regular internet access, `fetch` will actually reach PubMed and (with a key set) Anthropic, and pull real results.
