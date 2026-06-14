# PRD — Investment Thesis Journal

> **Build date:** 2026-06-14
> **Category:** C — Personal Knowledge Tool
> **Complexity:** Focused Utility
> **Day of week:** Sunday → Focused Utility

---

## Goal

A command-line personal knowledge tool that stores investment research notes organized by ticker symbol, automatically capturing the live price from Yahoo Finance at the moment each note is written.

## User Story

As a researcher and investor who tracks multiple investment theses across different assets, I want a fast CLI to record my reasoning at the time of a decision and review it later alongside current price context, so that I can hold myself accountable to my original thesis and see how prices have moved since each note was written.

## Scope

### In Scope
- Add a research note for a ticker: records the note text, timestamp, and the live price at the time of writing (pulled from Yahoo Finance if available)
- Show all notes for a given ticker alongside the current live price, % change, and market cap
- List all tickers with a note count and last entry date
- Search all notes by keyword (case-insensitive)
- Delete a specific note by ticker and ID
- Graceful degradation when yfinance is unavailable or network call fails — all core operations still work

### Out of Scope
- Portfolio position tracking (quantities, cost basis, P&L)
- Price history charts or visualizations
- Export to PDF/CSV
- Tags or categorization within notes
- Any web or GUI interface
- Scheduled price alerts or notifications
- Multi-user or cloud storage

## Tech Stack

- **Language:** Python 3.10+
- **Framework:** None (stdlib + one optional dependency)
- **Dependencies:** `yfinance` (optional, for live price enrichment); `pytest` (tests)
- **Runtime requirement:** `python3 main.py <command>` from the build folder

## Data Structure

Local JSON file (`theses.json`) at the build folder root. Format:

```json
{
  "NVDA": [
    {
      "id": 1,
      "date": "2026-06-14T02:15:00+00:00",
      "note": "Strong GPU moat in AI training. Entering at peak valuation risk but thesis is multi-year.",
      "price_at_note": 1102.50
    }
  ],
  "AAPL": [...]
}
```

`theses.json` is a runtime data file and is not committed to the repository.

## Folder Structure

```
builds/2026-06-14-investment-thesis-journal/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── main.py               ← CLI entry point
├── requirements.txt      ← yfinance, pytest
└── tests/
    └── test_main.py      ← pytest tests (no network calls)
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_main.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Adding a note creates an entry with correct fields
  - Adding multiple notes to the same ticker increments IDs correctly
  - Getting notes for an unknown ticker returns empty list
  - Adding a note with a price records the price
  - Listing tickers returns all tickers sorted alphabetically with correct note counts
  - Search finds notes containing the keyword (case-insensitive)
  - Search returns empty when no notes match
  - Delete removes the correct entry by ID
  - Delete removes the ticker entirely when its last note is deleted
  - Delete a non-existent ID returns False
  - Data persists correctly across separate ThesisStore instances (file round-trip)
  - `format_market_cap` handles trillions, billions, millions, and None
  - `fetch_quote` returns None gracefully when yfinance raises an exception

## Success Criteria

1. All tests pass with zero failures
2. `python main.py add NVDA "test thesis"` creates a note and prints a confirmation with the ticker and note ID
3. `python main.py show NVDA` displays the stored note(s) and attempts to show live price
4. `python main.py list` produces a table of all tickers with note count and last entry date
5. `python main.py search moat` returns all notes containing the word "moat" regardless of case

---

## Scope Changes

<!-- No scope changes from original plan. -->
