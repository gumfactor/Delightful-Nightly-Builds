# Manual — Investment Thesis Journal

A command-line tool to record and review investment research notes, organized by ticker symbol. Notes are timestamped and automatically enriched with the live price from Yahoo Finance at the moment of writing.

---

## Setup

```bash
cd builds/2026-06-14-investment-thesis-journal
pip install -r requirements.txt
```

`yfinance` enables live price capture. If it's not installed, all commands still work — live price display is silently skipped.

---

## Commands

### Add a research note

```bash
python main.py add TICKER "note text"
```

Records the note with a UTC timestamp. If Yahoo Finance is reachable, also captures the current price alongside the note.

```
$ python main.py add NVDA "Strong GPU moat in AI training. Peak valuation risk but thesis is multi-year."
Added note #1 for NVDA.
Price at time of note: USD 1102.50 (+2.35%)
```

---

### Show all notes for a ticker

```bash
python main.py show TICKER
```

Displays stored notes with the price recorded at each note, plus the live current price for comparison.

```
$ python main.py show NVDA

============================================================
  NVDA
  Live: USD 1187.20  +7.68%  Market Cap: $2.9T
============================================================

  [1] 2026-06-14 02:15 UTC
  Price at note: 1102.50
  Strong GPU moat in AI training. Peak valuation risk but thesis is multi-year.
```

---

### List all tickers

```bash
python main.py list
```

Quick overview of every ticker that has notes.

```
$ python main.py list

Ticker        Notes  Last Entry
----------------------------------------
AAPL              2  2026-06-10
MSFT              1  2026-06-12
NVDA              3  2026-06-14
```

---

### Search notes by keyword

```bash
python main.py search QUERY
```

Case-insensitive search across all notes from all tickers.

```
$ python main.py search moat

Found 2 result(s) for "moat":

  [NVDA] #1 — 2026-06-14 02:15 UTC
  Price at note: 1102.50
  Strong GPU moat in AI training. Peak valuation risk but thesis is multi-year.

  [AAPL] #2 — 2026-06-10 14:22 UTC
  Ecosystem moat is defensible. Services growth continues.
```

---

### Delete a note

```bash
python main.py delete TICKER ID
```

The note ID is shown in brackets when you run `show` or `search`. Once the last note for a ticker is deleted, the ticker itself is removed from the list.

```
$ python main.py delete NVDA 1
Deleted note #1 for NVDA.
```

---

## Data file

Notes are stored in `theses.json` in the build folder. This file is not committed to the repository. Back it up manually or copy it to a location of your choosing if you want it preserved across reinstalls.

---

## Running tests

```bash
python -m pytest tests/ -v
```

28 tests. No network calls required — Yahoo Finance is fully mocked in tests.
