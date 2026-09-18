# PRD — Eligible Spend

> **Build date:** 2026-09-18
> **Category:** I — Life Admin Helper
> **Complexity:** Ambitious Project
> **Day of week:** Friday → Ambitious Project

---

## Goal

A deterministic rule engine (with an optional AI-assisted review layer) that checks a researcher's itemized grant budget CSV against the Canadian Tri-Agency (NSERC/CIHR/SSHRC) Guide on Financial Administration's principles and known ineligible-expenditure rules, flagging problem line items before submission.

## User Story

As a research lab director who writes Tri-Agency grant applications and manages post-award budgets, I want to run my itemized budget through a rules check grounded in the actual Tri-Agency Guide on Financial Administration, so that I catch expenditures that would be rejected or clawed back during a compliance audit before I submit the application or file an expense claim — not after.

## Scope

### In Scope
- CSV input: `item`, `category` (free text), `amount`, `date` (ISO `YYYY-MM-DD`), optional `justification`
- A `--grant-start` / `--grant-end` date range defining the eligible grant period
- Deterministic date-range check: any line item dated outside the grant period is flagged `ineligible`
- Deterministic keyword/category rule engine encoding the Tri-Agency Guide on Financial Administration's (TAGFA) principles-based framework, hand-verified via web search against multiple institutional summaries of the guide (documented per-rule with the specific principle/directive it comes from):
  - Always-ineligible categories: alcohol, tuition/thesis-related education costs, costs normally provided by the administering institution (general overhead — office space, utilities, basic IT/network infrastructure, general clerical/admin support), passport/immigration fees, international driver's licences, commuting between home and workplace, airfare reimbursed when purchased with frequent-flyer points, living expenses during sabbatical leave
  - Conditionally-eligible categories requiring justification text before being cleared: hospitality/non-alcoholic refreshments (eligible only when directly tied to a research-related gathering), equipment/travel/personnel/supplies with no justification text linking them to the funded research
  - Everything else: `no_blocking_rule_found` — still subject to the three general principles (direct cost & attributable to the grant, not normally institution-provided, effective/economical) — never presented as a guarantee of eligibility
- Optional AI-assisted review (`--ai`, Claude Haiku via `urllib.request`, no SDK): for items flagged `requires_justification` or `no_blocking_rule_found`, drafts a one-sentence plain-English note on whether the stated justification plausibly satisfies the "direct cost" and "not institution-provided" principles — grounded strictly in the item's own category/description/justification text, never inventing facts. Unconditional deterministic-template fallback when no `ANTHROPIC_API_KEY` is set (zero network calls attempted) or on any API error.
- Terminal summary report
- Self-contained dark-mode HTML dashboard: summary tiles (total budget, $ ineligible, $ requires justification, $ clean), a Chart.js bar chart of $ by verdict, a sortable/filterable line-item table with color-coded verdict badges and the cited principle/directive per flag, and a DOM-table fallback if the CDN chart script is blocked
- CSV export of only the flagged (ineligible + requires-justification) line items
- A prominent, unmissable disclaimer (terminal, dashboard, and Manual.md): this is a decision-support heuristic against the *general* Tri-Agency Guide, not a substitute for the institution's research grants/financial office, not legal or financial advice, and does not cover institution-negotiated indirect-cost/overhead rates

### Out of Scope
- Institution-negotiated overhead/indirect-cost-rate math (explicitly excluded per the backlog note that passed this idea over on 2026-09-09 — only the publicly documented eligible-expense-category rules are in scope)
- Any funding agency other than NSERC/CIHR/SSHRC (Tri-Agency only)
- Automatic categorization of completely free-text items via NLP beyond simple keyword matching (the optional AI layer assists judgment, it does not re-categorize)
- Multi-currency support (CAD only, no FX conversion)
- Direct submission or integration with any grant portal

## Tech Stack

- **Language:** Python 3.11
- **Framework:** None (stdlib CLI, `argparse`)
- **Dependencies:** stdlib only for the core engine and CLI; Anthropic API called via `urllib.request` (no SDK) for the optional `--ai` layer
- **Runtime requirement:** `python3 src/main.py budget.csv --grant-start 2026-04-01 --grant-end 2027-03-31` — writes a terminal report plus a self-contained `report.html` that opens directly via `file://`, no server needed

## Data Structure

**Input CSV** (`item`, `category`, `amount`, `date`, `justification` — last column optional):
```csv
item,category,amount,date,justification
Graduate student stipend - Q1,Personnel,12000,2026-05-01,RA salary for aim 2 data collection
Conference registration,Dissemination,650,2026-06-15,Presenting grant-funded findings
Lab holiday party wine,Hospitality,180,2026-12-10,
```

**Internal `Verdict`** (per line item): `{item, category, amount, date, justification, status, reason, principle, ai_note}` where `status ∈ {ineligible, requires_justification, no_blocking_rule_found, outside_grant_period}`.

**Rule table** (`src/rules.py`): a list of `Rule` objects — `{name, match_fn(item) -> bool, status, reason, principle_citation}` — evaluated in order; date-range check runs first and short-circuits, then always-ineligible keyword rules, then conditional rules, then the default no-blocking-rule verdict.

**Output**: terminal text report, `report.html` (self-contained, embeds all row data as an escaped `<script type="application/json">` block), `flagged_items.csv` (ineligible + requires-justification rows only).

## Folder Structure

```
builds/2026-09-18-eligible-spend/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── sample_data/
│   └── sample_budget.csv
├── src/
│   ├── main.py
│   ├── csv_io.py
│   ├── rules.py
│   ├── ai_review.py
│   └── report.py
└── tests/
    ├── test_csv_io.py
    ├── test_rules.py
    ├── test_ai_review.py
    ├── test_report.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v` (run from the build folder)
- **What will be tested:**
  - CSV parsing: valid file, missing required column, malformed amount, malformed date, empty file, extra whitespace/BOM handling
  - Date-range rule: item before grant start, item after grant end, item on exact start/end boundary (inclusive), item inside range
  - Every always-ineligible rule (alcohol, tuition, institution-overhead, passport/immigration, international driver's licence, commuting, frequent-flyer airfare, sabbatical living expenses) fires on a matching fixture row and does NOT fire on an unrelated row
  - Hospitality conditional rule: flagged `requires_justification` with empty justification, cleared to `no_blocking_rule_found` with a justification tying it to a research gathering
  - Unknown/unmatched category defaults to `no_blocking_rule_found`, never silently to "eligible"
  - Rule evaluation order: an item outside the grant period is flagged `outside_grant_period` even if it would also match an ineligible-category rule (period check short-circuits first)
  - AI review module: mocked successful Anthropic response is used verbatim; mocked malformed/error response falls back to the deterministic template; zero network calls made when `ANTHROPIC_API_KEY` is unset, verified by monkey-patching `urllib.request.urlopen` to raise if called
  - HTML report: correct verdict counts and total $ figures against a hand-computed fixture; a hostile `<script>`/`onerror` payload in an `item`/`justification` field renders as inert escaped text (no injected DOM nodes, exactly the page's own `<script>` tag count)
  - CLI: missing input file exits non-zero with a clear message; `--grant-start` after `--grant-end` exits non-zero; `flagged_items.csv` contains only flagged rows

## Success Criteria

1. All tests pass (zero failures)
2. Every always-ineligible and conditional rule is grounded in a specific, cited Tri-Agency Guide principle/directive and covered by a passing test that proves it fires correctly and does not over-fire on unrelated categories
3. Running the CLI against `sample_data/sample_budget.csv` produces a terminal report, `report.html`, and `flagged_items.csv` whose flagged-item count and total $ match a hand-computed expectation for that fixture
4. `report.html` opens directly via `file://`, renders correctly at both desktop and 375px mobile widths, and a hostile-payload fixture confirms zero script injection
5. The `--ai` path is fully optional: with no `ANTHROPIC_API_KEY` set, the tool runs end-to-end with zero network calls and produces a complete, useful report via the deterministic fallback alone

---

## Scope Changes

None — built as scoped.
