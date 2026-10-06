# PRD — Recurring Charge Radar

> **Build date:** 2026-10-06
> **Category:** I — Life Admin Helper
> **Complexity:** Ambitious
> **Day of week:** Tuesday

---

## Goal

Read bank and credit-card CSV exports from Canadian banks, automatically detect every recurring charge (subscriptions, bills, annual renewals), and render a phone-friendly offline HTML report with monthly/annual cost, price hikes, zombie charges, and a forecast of upcoming charges plus an `.ics` calendar export.

## User Story

As a solo founder and professor who pays for many SaaS, AI, hosting, and domain subscriptions across several cards, I want to drop in my statement exports and see exactly what recurs, what has gone up in price, and what is about to renew, so that I can cancel waste and stop being surprised by annual renewals.

## Scope

### In Scope
- CSV parsing with auto-detection for RBC, TD, CIBC, Scotiabank, BMO and generic header-based exports; headered and header-less; debit/credit or signed amount columns; multiple date formats; preamble lines.
- Merchant normalisation (strip POS prefixes, payment-processor prefixes like `SQ *`/`PAYPAL *`, store/ref numbers, city/province tails).
- Recurrence detection: cadence classification (weekly, biweekly, monthly, quarterly, annual), confidence scoring, fixed vs variable amount, tolerance for date drift.
- Price-change detection (step changes, % and dollar delta, date).
- Lifecycle status: active / lapsed / zombie (still charging after a user-declared cancellation date).
- Cost roll-up: monthly-equivalent and annualised cost.
- Forecast of upcoming charges for the next N days (default 60).
- User rules file (JSON): ignore merchants, alias merchants, declare cancelled merchants.
- Self-contained HTML report (inline CSS/JS/SVG, no network, dark/light, mobile first): summary tiles, cost bars, sortable list, expandable history, upcoming timeline.
- `.ics` export of upcoming charges; JSON export; `--demo` mode with synthetic data.
- Fully local: no network calls; financial data never leaves the machine (deliberate).

### Out of Scope
- AI classification (would send transactions to a third party; local-only by design).
- Live bank connections, PDF statement parsing, multi-currency conversion.

## Tech Stack

- **Language:** Python 3.11+, HTML/CSS/vanilla JS (inline)
- **Framework:** None
- **Dependencies:** stdlib only (tests use stdlib `unittest`, collectable by pytest)
- **Runtime requirement:** `PYTHONPATH=src python -m recurring statements/*.csv --out report.html`

## Data Structure

`Transaction(date, description, amount, source)` — amount positive = money out.
`Series(merchant, cadence, period_days, typical_amount, variable, charges, confidence, status, price_changes, next_expected, monthly_cost, annual_cost)`.
Rules JSON: `{"ignore": ["..."], "aliases": {"raw substring": "Display Name"}, "cancelled": {"Display Name": "YYYY-MM-DD"}}`.

## Folder Structure

```
builds/2026-10-06-recurring-charge-radar/
├── PRD.md  WhyThis.md  BUILD_LOG.md  FutureFeatures.md  Manual.md
├── requirements.txt
├── src/recurring/
│   ├── __init__.py  __main__.py  cli.py
│   ├── models.py  parsers.py  normalize.py  detect.py
│   └── forecast.py  rules.py  report.py  demo.py
└── tests/
    ├── test_parsers.py  test_normalize.py  test_detect.py
    └── test_forecast_report.py
```

## Testing Strategy

- **Framework:** unittest (stdlib; the environment denied installing pytest, and pytest collects these too)
- **Location:** tests/test_*.py
- **Run command:** `PYTHONPATH=src python -m unittest discover -s tests -v` (or `python -m pytest tests/`)
- **Tested:** each bank format; date/amount parsing; merchant normalisation; cadence detection per period; irregular purchases rejected; price hike detection; variable bills; lapsed vs zombie; forecast dates; ICS validity; HTML escaping of hostile descriptions; malformed CSV errors; rules; end-to-end demo run.

## Success Criteria

1. All tests pass (zero failures)
2. Demo run detects every seeded subscription with correct cadence, flags the seeded price hike and zombie charge, and has no false positives from irregular merchants
3. HTML report is one offline file with a mobile viewport and no horizontal-scroll layout
4. ICS output contains one VEVENT per forecast charge
5. No network access or third-party packages at runtime
