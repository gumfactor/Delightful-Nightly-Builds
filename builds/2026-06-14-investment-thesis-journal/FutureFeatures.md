# Future Features — Investment Thesis Journal

These are concrete enhancements to a working tool, not prerequisites for its usefulness.

---

## 1. Price history at a glance (Solid complexity)

When running `show TICKER`, display the price on the date of each note alongside the current price, so you can see at a glance how the stock has moved since each thesis was written. `yfinance` supports historical OHLCV data, so this is a straightforward extension: for each note, look up the closing price on the note date and compute the return since then.

```
  [1] 2026-01-15 — entry: $850.00 → today: $1102.50 (+29.7%)
  Bought on rate-cut thesis.
```

---

## 2. Tags per note (Focused)

Add an optional `--tags` flag to `add` so notes can be tagged by theme: `--tags ai semiconductor value`. Search could then filter by tag with `search --tag ai`. Tags are stored as a string list in the JSON entry. No schema migration needed — existing entries without tags are treated as untagged.

---

## 3. Export to Markdown or CSV (Focused)

A new `export` command that writes all notes to a structured Markdown file (suitable for pasting into Obsidian, Notion, or a blog) or a CSV (suitable for a spreadsheet). Useful for quarterly reviews. No new dependencies — just formatted `write()` calls.

---

## 4. Thesis status tracking (Solid complexity)

Add a `status` field to each thesis entry: `open`, `closed`, `watching`. Closing a position adds an exit price and date. A summary view could then show open positions vs. closed ones, with realized vs. unrealized returns. This turns the journal from a note-taking tool into a lightweight position journal.

---

## 5. Bulk import from a CSV watchlist (Focused)

A command like `python main.py import watchlist.csv` that reads a CSV with columns `ticker,note` and adds each row as a note. Useful for migrating existing research notes into the journal. Validates columns before writing anything.

---

## 6. Sector and market context enrichment (Solid complexity)

When adding a note, also capture the sector, P/E ratio, 52-week range, and analyst consensus from Yahoo Finance's `info` dict. Store these alongside the price. Reviewing a thesis years later with full market context (not just the price) would significantly improve the quality of the review.

---

## 7. `review` command for a periodic thesis audit (Ambitious)

A scheduled `review` command (runnable as a Claude Code Routine) that finds all open theses older than N days, prints the current price vs. the price at note, and prompts for a brief update note. Designed to run as part of a weekly investment routine so theses don't sit unexamined.

