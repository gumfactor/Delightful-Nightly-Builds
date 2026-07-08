# PRD — Ledger Lens

> **Build date:** 2026-07-08
> **Category:** I — Life Admin Helper
> **Complexity:** Ambitious Project
> **Day of week:** Wednesday

---

## Goal

A Python CLI that turns a raw bank/credit-card CSV export into a categorized, budget-aware spending dashboard — auto-detecting columns, classifying every transaction (rule-based, with optional Claude enrichment for ambiguous merchants), flagging recurring subscriptions, and rendering a self-contained dark-mode HTML report.

## User Story

As an Associate Professor and solo founder who runs multiple ventures and explicitly has no dedicated budgeting tool in his daily stack (Interactive Brokers covers investing, not spending), I want to drop in a bank CSV export and instantly get a categorized, visual picture of where my money went — including which recurring charges are quietly draining my accounts — so that I can catch subscription creep and see spending patterns without manually building a spreadsheet every month.

## Scope

### In Scope
- CSV ingestion with auto-detected column mapping: handles `Date`/`Description`/`Amount` naming variants, plus split `Debit`/`Credit` column exports (common with Canadian banks)
- Multiple date format parsing (ISO, `MM/DD/YYYY`, `DD-Mon-YYYY`)
- `--invert-sign` flag for exports where charges are positive (e.g. some card issuers) instead of the negative-for-debit convention
- Deterministic keyword-based categorizer across 14 fixed categories (Groceries, Dining, Transport, Travel, Shopping, Subscriptions, Utilities, Health, Housing, Entertainment, Fees & Charges, Income, Transfers, Other)
- Optional Claude Haiku enrichment (via `urllib`, no SDK) for transactions the rule-based pass can't confidently classify — batched, with long digit sequences (reference/account numbers) redacted from descriptions before they leave the machine, and a deterministic fallback (stays in the rule-based/"Other" bucket) if no `ANTHROPIC_API_KEY` is set or the call fails
- Recurring/subscription detection: same normalized merchant + similar amount (±5%) appearing in ≥2 distinct months
- Monthly aggregation: income, expenses, net, category breakdown, top merchants, average daily spend
- Optional budget comparison via `--budgets budgets.json` (category → monthly cap), flags over/under
- Optional plain-English "Spending Insights" paragraph via Claude, with a deterministic template fallback (top categories + biggest month-over-month category change)
- Three output modes: colored terminal summary (default), `--json` machine-readable output, `--html report.html` self-contained dark-mode dashboard (hero stats, category donut chart, monthly income/expense trend line, recurring-charges list, budget-vs-actual bars, sortable/searchable transaction table)
- `--out-csv cleaned.csv` — original data plus `Category` and `Recurring` columns
- Bundled synthetic demo CSV (`sample_transactions.csv`) so the tool is usable immediately without the user's real bank export
- `budgets.example.json` as a starting template

### Out of Scope
- Live bank account integration (no aggregator credentials available; user must export CSV manually)
- Multi-currency conversion (single currency per run, symbol configurable via `--currency-symbol`)
- Persistent multi-run history/trend-over-time storage (each run is a snapshot of one CSV; no database)
- Editing/re-categorizing transactions interactively in the HTML report (view-only; re-run CLI with corrected rules to change categorization)

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** None
- **Dependencies:** stdlib only (`csv`, `json`, `argparse`, `datetime`, `re`, `urllib.request` for the optional Anthropic call). Chart.js 4.4.4 loaded via pinned CDN URL inside the generated HTML only (not a Python dependency).
- **Runtime requirement:** `python3 src/main.py analyze <input.csv> [options]` — no install step beyond stdlib Python 3.

## Data Structure

**Input:** a transaction CSV with (in any of several recognized header spellings):
- A date column (`Date`, `Transaction Date`, `Posting Date`, ...)
- A description column (`Description`, `Details`, `Memo`, `Merchant`, ...)
- Either one `Amount` column (negative = expense by default) or split `Debit`/`Credit` columns

**Internal transaction record** (per row, after parsing):
```
{date: date, description: str, amount: float, category: str,
 category_source: "rule" | "ai" | "existing", recurring: bool}
```

**Optional budgets file** (`budgets.json`): `{"Groceries": 600, "Dining": 300, ...}` — category name to monthly cap in the report's currency.

**Output (`--json`)**: `{summary: {...}, monthly: [...], categories: [...], top_merchants: [...], recurring: [...], budget_status: [...] | null, insights: str}`

## Folder Structure

```
builds/2026-07-08-ledger-lens/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── budgets.example.json
├── sample_transactions.csv
├── src/
│   ├── __init__.py
│   ├── parser.py          (CSV ingestion + column auto-detection)
│   ├── categorize.py       (rule-based categorizer + AI enrichment orchestration)
│   ├── ai_client.py        (Anthropic API call via urllib, deterministic fallback)
│   ├── analyze.py          (monthly aggregation, recurring detection, budget comparison)
│   ├── report_html.py      (self-contained dark-mode HTML dashboard renderer)
│   ├── report_terminal.py  (colored terminal summary)
│   └── main.py             (argparse CLI entry point, wires everything together)
└── tests/
    ├── conftest.py
    ├── test_parser.py
    ├── test_categorize.py
    ├── test_analyze.py
    ├── test_report_html.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Column auto-detection across header-naming variants and split Debit/Credit columns
  - Multiple date formats parse correctly; malformed rows are skipped and counted, not silently dropped
  - Missing required columns raise a clear error
  - `--invert-sign` flips expense/income interpretation correctly
  - Rule-based categorizer correctly classifies representative merchants per category and defaults unmatched ones to "Other"
  - Digit-sequence redaction strips reference/account numbers before any text would leave the machine
  - AI enrichment merges results correctly when the API call succeeds (mocked), and falls back cleanly to rule-based "Other" when no API key is set or the call raises/times out
  - Monthly aggregation totals and category breakdown sum consistently to overall totals
  - Recurring detection flags a merchant+amount pair repeating across ≥2 months and does not flag a genuine one-off charge
  - Budget comparison correctly flags over-budget categories and leaves under-budget ones unflagged
  - Generated HTML embeds transaction/report data as JSON (no external data file dependency), pins the Chart.js CDN version, and HTML-escapes transaction descriptions (XSS safety)
  - CLI end-to-end: `--json`, `--html`, and `--out-csv` all produce correct, well-formed output from the bundled sample CSV; a missing input file errors gracefully (no traceback)

## Success Criteria

1. All tests pass (zero failures)
2. Running the CLI against the bundled `sample_transactions.csv` with no flags produces a correct terminal summary; `--html` produces a self-contained dashboard that opens directly in a browser with charts, a searchable transaction table, and correct totals
3. Every transaction in the sample CSV is assigned a category from the fixed 14-category list — none silently dropped
4. Recurring charges present in the sample data (repeated same-merchant, same-amount, multi-month) are correctly flagged in both the terminal and HTML output
5. The tool runs to completion with no `ANTHROPIC_API_KEY` set (this session's actual condition), using the deterministic fallback path for both categorization and insights, with no crash or degraded output

---

## Scope Changes

None — full scope as planned was completed.
