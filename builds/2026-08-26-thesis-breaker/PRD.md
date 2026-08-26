# PRD — Thesis Breaker

> **Build date:** 2026-08-26
> **Category:** D — Creative / Generative
> **Complexity:** Ambitious
> **Day of week:** Wednesday

---

## Goal

Given a stock ticker and the user's own stated bull thesis, generate a real-data-grounded adversarial "bear case" critique from three fixed critic personas, so the user gets honest, evidence-backed pushback on their own investment reasoning instead of an echo chamber.

## User Story

As a psychology professor and solo founder who does personal quantitative investing research and explicitly values "honest pushback over agreement for its own sake," I want to paste in an investment thesis I've written for a ticker and get it stress-tested against real financial data by a panel of skeptical personas, so that I catch valuation stretch, decelerating growth, balance-sheet risk, insider selling, and unverifiable narrative claims before I act on my own thesis rather than after.

## Scope

### In Scope
- `check` command: fetch real fundamentals for a ticker via `yfinance` (trailing/forward P/E, P/S, sector, quarterly revenue by quarter, operating margin by quarter, total debt/equity, insider transactions table), run a deterministic 5-category bear-case rule engine against that data plus the pasted thesis text, score 3 fixed critic personas (Value Skeptic, Macro Bear, Governance Hawk), persist the run as a new versioned row in local SQLite (never overwritten), and render a self-contained dark-mode HTML report
- `demo` command: runs the identical pipeline against a bundled hand-crafted realistic fixture (no network) — lets the tool be exercised and verified without live market access, and gives the user an instant first look
- `history TICKER` command: prints every saved check for a ticker with overall bear-case score, so score drift over repeated runs is visible in the terminal
- `render --id ID` command: regenerates the HTML report for any saved run from SQLite without re-fetching
- `list` command: lists all saved checks across all tickers
- 5 deterministic rule categories, each computed from real fetched numbers (not from the thesis text): Valuation Stretch, Growth Deceleration, Margin/Debt Risk, Insider Selling Signal, Narrative Fragility (keyword-vs-data cross-check between the thesis text and what actually triggered/is available)
- 3 fixed critic personas with distinct category weightings, each producing a severity score (0–100) and a rationale that cites the specific triggered checks and real numbers, and explicitly names which checks did NOT trigger (so the critique is honest, not cherry-picked)
- Optional Claude Haiku narrative polish per persona (rephrases the deterministic findings into persona-voiced prose; never permitted to invent a fact/number beyond what the rule engine produced) with an unconditional deterministic-template fallback when `ANTHROPIC_API_KEY` is unset, the network call fails, or the response is malformed
- Self-contained dark-mode HTML report: persona cards, triggered-checklist matrix, real-data summary panel, Canvas 2D valuation-vs-threshold bar chart and quarterly revenue-growth trend line, and a bear-case-score-over-time chart once 2+ runs exist for the same ticker+thesis pair
- SQLite persistence (`thesisbreaker.db`) — every `check` run is a new row; history is append-only
- `requirements.txt` pinning `yfinance`

### Out of Scope
- Live SEC EDGAR Form 4 parsing (yfinance's own `insider_transactions` table is used instead — same underlying regulatory data, far simpler to integrate correctly in one session)
- A live-fetched sector-average P/E (would require a second data source with no stable free endpoint); a documented static per-sector valuation-threshold reference table is used instead, and is called out as a simplification in `FutureFeatures.md`
- Portfolio-wide or multi-ticker batch runs (one ticker per `check` call)
- Any brokerage/IBKR integration or trade execution
- Automatic thesis re-checking on a schedule (a Routine wrapper is listed as a future enhancement, not built tonight)

## Tech Stack

- **Language:** Python 3
- **Framework:** None
- **Dependencies:** `yfinance` (real market/fundamentals data); stdlib `sqlite3`, `json`, `argparse`, `html`, `urllib` (optional Anthropic call, no SDK dependency); `pytest` for tests (dev-only, not required at runtime)
- **Runtime requirement:** `python3 main.py check AAPL --thesis "..."` (or `demo`); opens the generated `report.html` directly in a browser, no server needed

## Data Structure

**Fetched fundamentals** (`FetchedData`, a plain dict returned by `src/fetch.py`):
```json
{
  "ticker": "AAPL",
  "sector": "Technology",
  "trailing_pe": 34.2,
  "forward_pe": 29.1,
  "price_to_sales": 8.4,
  "debt_to_equity": 1.8,
  "quarterly_revenue_yoy_growth": [0.12, 0.09, 0.07, 0.03],
  "quarterly_operating_margin": [0.31, 0.30, 0.295, 0.29],
  "insider_transactions": [
    {"insider": "Doe, Jane", "transaction": "Sale", "shares": 5000, "value": 850000},
    {"insider": "Smith, Bob", "transaction": "Purchase", "shares": 1000, "value": 170000}
  ]
}
```
Lists are ordered most-recent-quarter-first. Any field yfinance cannot supply is `None` and the rule engine treats an unavailable field as "cannot evaluate this check" rather than guessing.

**SQLite schema** (`thesisbreaker.db`, one table):
```sql
CREATE TABLE checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    thesis_text TEXT NOT NULL,
    run_timestamp TEXT NOT NULL,       -- ISO 8601, injected by caller (no datetime.now() inside library code)
    fetched_data_json TEXT NOT NULL,
    triggered_json TEXT NOT NULL,      -- which of the 5 categories fired, with rationale numbers
    persona_scores_json TEXT NOT NULL, -- {"value_skeptic": 62, "macro_bear": 40, "governance_hawk": 15}
    overall_score INTEGER NOT NULL,
    ai_polished INTEGER NOT NULL       -- 0/1, whether the Haiku layer produced this run's narrative text
);
```
Every `check` call inserts a new row; nothing is ever updated or deleted by the tool.

## Folder Structure

```
builds/2026-08-26-thesis-breaker/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── main.py
├── fixtures/
│   └── sample_aapl_fetch.json
├── src/
│   ├── __init__.py
│   ├── fetch.py          # yfinance wrapper, dependency-injected ticker factory
│   ├── rules.py          # 5 deterministic bear-case categories
│   ├── personas.py       # 3 persona weighting + scoring
│   ├── narrative.py      # deterministic template text + optional Haiku polish w/ fallback
│   ├── store.py          # SQLite persistence, append-only
│   ├── render.py         # self-contained dark-mode HTML report generator
│   └── cli.py            # argparse commands: check / demo / history / render / list
└── tests/
    ├── __init__.py
    ├── test_fetch.py
    ├── test_rules.py
    ├── test_personas.py
    ├── test_narrative.py
    ├── test_store.py
    ├── test_render.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Each of the 5 rule categories: fires correctly when the trigger condition is met, does not fire when it isn't, and reports "cannot evaluate" when the underlying data field is `None`
  - Persona scoring: correct weighting of triggered categories per persona, and that rationale text cites the actual triggered checks (not a static string)
  - Narrative fallback: with no `ANTHROPIC_API_KEY`, with a mocked network error, and with a mocked malformed API response — all three fall back to the deterministic template with zero real network calls (verified via a mocked `urlopen` that fails the test if actually invoked with a live host)
  - `fetch.py`: a mocked `yfinance.Ticker`-shaped fake object is used — no live network call is made in any test
  - `store.py`: two `check` runs for the same ticker+thesis produce two distinct rows (append-only, never overwritten); `history` returns rows in insertion order
  - `render.py`: the generated HTML escapes a `<script>` and an `<img onerror>` payload placed in `thesis_text` and `ticker` — confirmed to produce zero executable script tags in the output
  - `cli.py`: `demo`, `history`, `render`, and `list` commands run end-to-end against a temporary SQLite file and produce the expected exit codes and output
  - Edge case: a ticker whose fetched data has every optional field as `None` still produces a valid (all "cannot evaluate") report without crashing

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests
2. `python3 main.py demo` runs with zero network access and zero `ANTHROPIC_API_KEY`, producing a valid `report.html` that opens correctly in a browser and shows all 3 persona cards, the triggered-checklist matrix, and the real-data summary panel
3. Running `check` twice for the same ticker+thesis (mocked data) produces two independent, timestamped rows in SQLite, and `history` shows both with their overall scores
4. A `<script>` payload placed in `--thesis` text is present in the report only as escaped, inert text — never as an executable tag
5. With `ANTHROPIC_API_KEY` unset, `--ai-polish` silently falls back to the deterministic template text and makes zero network calls (verified via mock)

---

## Scope Changes

None during the build; scope was set at the level above before any code was written.
