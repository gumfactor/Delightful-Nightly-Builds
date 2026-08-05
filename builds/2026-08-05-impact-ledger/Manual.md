# Manual — Impact Ledger

> **Version:** 1.0 (built 2026-08-05)
> **Complexity:** Ambitious Project

---

## What This Is

Impact Ledger tracks how your own published research is being cited over time, using the free OpenAlex API. It's built for the moment you're drafting a grant progress report or a manuscript and need an up-to-date, evidence-backed answer to "what's my most-cited work, and is anything gaining momentum right now?" — without manually re-checking Google Scholar or OpenAlex. Every time you run it, it takes a dated snapshot of your citation counts, so over weeks and months you build a genuine history of your research's real-world impact, not just a single point-in-time number.

---

## Quick Start

1. Find your OpenAlex author ID: `python3 src/main.py search-author "Your Name"`
2. Pick the correct candidate from the printed list (checks affiliation, works count, citation count) and copy its ID (looks like `A5023888391`)
3. Fetch and snapshot your works: `python3 src/main.py sync --author-id A5023888391`
4. Render the dashboard: `python3 src/main.py render --author-id A5023888391 --out dashboard.html`
5. Open `dashboard.html` in any browser

Run `sync` again on a later date (weekly or monthly is plenty) to start seeing real citation-growth trends and "rising papers."

---

## How to Use It

### `search-author` — find your OpenAlex ID

```
python3 src/main.py search-author "Jane Doe"
```

Prints up to 5 candidates with affiliation, works count, and citation count so you can disambiguate a common name. No author ID is ever hardcoded in this tool — you always supply your own.

### `sync` — fetch and snapshot your citation data

```
python3 src/main.py sync --author-id A5023888391
```

Fetches your author profile (h-index, i10-index, total citations, works count) and every published work, then stores a dated snapshot in a local SQLite database. Running `sync` again on the **same UTC day** overwrites that day's snapshot (it never creates duplicate rows) — safe to re-run as many times as you like in one sitting. Running it on a **later day** adds a new snapshot, which is what builds the trend history.

Use `--mailto you@example.com` to opt into OpenAlex's "polite pool" for higher rate limits (entirely optional, and never set by default).

### `history` — see your citation trend in the terminal

```
python3 src/main.py history --author-id A5023888391
```

Shows total citations at each sync date, and which papers are rising since the previous sync. If you've only synced once, it tells you plainly that there isn't enough history yet.

### `render` — build the HTML dashboard

```
python3 src/main.py render --author-id A5023888391 --out dashboard.html --ai
```

Builds a self-contained dark-mode dashboard: hero stats, a citation-growth chart (once you have 2+ sync dates), a sortable/searchable paper table, and a "Rising Papers" panel. Add `--ai` to have Claude Haiku write a one-sentence note on why each rising paper might be gaining traction (requires `ANTHROPIC_API_KEY` to be set in your environment; without it, or if the call fails, a clear deterministic note is used instead — the dashboard never breaks either way).

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `--db-path` | `data/impact_ledger.db` (relative to the build folder) | SQLite database file location |
| `--mailto` (on `search-author`/`sync`) | none | Optional email for OpenAlex's polite pool (higher rate limits); never set automatically |
| `ANTHROPIC_API_KEY` (environment variable) | unset | Enables `render --ai`'s Claude Haiku commentary; without it, a deterministic template is used and zero network calls are made to Anthropic |

No credentials are required for the core tool — OpenAlex is free and requires no authentication.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `search-author` returns no candidates | Your name isn't indexed the way you typed it, or you have very few OpenAlex-tracked works | Try just your last name, or search directly at openalex.org to find your ID manually |
| `render` says "No data for author ..." | You haven't run `sync` for that author ID yet | Run `sync --author-id <ID>` first |
| Citation chart shows a plain table instead of a line chart | Either you have fewer than 2 distinct sync dates yet, or the Chart.js CDN was unreachable when the page loaded | Sync again on a later date for the chart to appear; the table fallback always shows the same data either way |
| "Rising Papers" panel is empty | You need at least 2 sync dates for velocity to be computable | Run `sync` again after some time has passed |
| AI notes don't appear even with `--ai` | `ANTHROPIC_API_KEY` isn't set, or the Anthropic call failed | Check the environment variable is exported in your shell; the dashboard still works fully without it |

---

## Known Limitations

- Author disambiguation is manual by design — `search-author` shows candidates, but you must confirm the correct one. This is deliberate: guessing wrong on a common name would silently track the wrong person's citations.
- Citation trend and rising-paper detection need at least two real `sync` runs on different UTC calendar days before they show anything — a single run only establishes the baseline.
- `render --ai` regenerates AI notes on every call rather than caching them, so repeated same-day renders with `--ai` will make repeated (small) Anthropic API calls if you re-run it multiple times in one day.
- This ships as a standalone CLI tonight, not yet wrapped as a scheduled Routine — see FutureFeatures.md for that extension.
