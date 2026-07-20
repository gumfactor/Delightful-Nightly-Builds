# PRD — CanFile: Canadian Ownership Knowledge Cards

> **Build date:** 2026-07-20
> **Category:** C — Personal Knowledge Tool
> **Complexity:** Ambitious Project
> **Day of week:** Monday

---

## Goal

A local CLI knowledge base that pulls structured ownership facts for any company from Wikidata and Wikipedia, applies a transparent rule engine (with optional Claude enrichment) to assess whether the company is likely Canadian-owned, and stores every assessment as a versioned, searchable knowledge card.

## User Story

As the founder of The Canada List — a directory that helps consumers identify Canadian-owned and Canadian-made businesses — I want to look up a company and get a sourced, confidence-rated ownership assessment pulled from public reference data, so that I can research candidate businesses for the directory faster and with a defensible evidence trail instead of manual Wikipedia digging.

## Scope

### In Scope
- Wikidata entity search + claims lookup for a company (country P17, headquarters location P159, parent organization P749, owned by P127, instance of P31)
- One level of parent/owner resolution: if a parent/owner organization exists, fetch *its* country too, since "owned by a Canadian holding company" and "owned by a US parent" are different conclusions
- Wikipedia REST API summary fetch (plain-English description) for the same entity
- Deterministic rule-engine assessment (Canadian HQ + no foreign parent → Canadian-owned; foreign parent/owner → foreign-owned; missing data → uncertain), always available with no API key
- Optional Claude Haiku enrichment: turns the structured facts into a 2–3 sentence plain-English assessment citing the same facts, when `ANTHROPIC_API_KEY` is set at runtime; falls back to the deterministic assessment text if the key is absent or the call fails
- Every `add` call for a company creates a **new version** of its knowledge card rather than overwriting — Wikidata facts change over time, and prior assessments stay auditable
- SQLite-backed local storage (`canfile.db`) of all card versions
- CLI commands: `add <company>`, `show <company>` (full version history), `list` (latest version per company), `search <term>` (company name or assessment text)
- Self-contained dark-mode HTML index export (`export-html`) — searchable/filterable card grid, confidence badges, source links, expandable version history per card, all user/API-derived text inserted safely (no `innerHTML` from untrusted data)
- Graceful handling of: entity not found on Wikidata, ambiguous search results (multiple candidates), network/API failures, missing Wikipedia page

### Out of Scope
- Bulk ingestion of The Canada List's actual product/business CSV export (no such dataset is available in this build environment — see `builds/ideas.md` idea #16 note); this build works one company at a time via CLI argument
- Automatic re-checking / scheduled refresh of existing cards (a future feature, not tonight)
- Multi-level full ownership chain traversal beyond one parent/owner hop
- A browser-based live search UI (the HTML export is a static, regenerate-on-demand report, not a live app)

## Tech Stack

- **Language:** Python 3
- **Framework:** None — stdlib only (`urllib.request` for HTTP, `sqlite3` for storage, `json`, `argparse`)
- **Dependencies:** None required. `anthropic` Python package used only if `ANTHROPIC_API_KEY` is set (imported lazily so the tool runs with zero third-party installs); listed in `requirements.txt` as optional
- **Runtime requirement:** `python3 src/main.py add "Company Name"` etc. No install step needed for core functionality.

## Data Structure

SQLite table `cards`:

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | autoincrement |
| `company_name` | TEXT | as typed by the user |
| `qid` | TEXT | Wikidata entity ID (e.g. `Q1524829`), nullable if not found |
| `wikidata_facts_json` | TEXT | JSON: country, headquarters, parent_organization, owned_by, parent_country, instance_of |
| `wikipedia_summary` | TEXT | plain-English extract, nullable |
| `assessment_text` | TEXT | Claude-enriched or deterministic-template text |
| `confidence` | TEXT | `high` / `medium` / `low` / `insufficient-data` |
| `verdict` | TEXT | `canadian` / `foreign` / `uncertain` |
| `source_urls_json` | TEXT | JSON list of the Wikidata/Wikipedia URLs used |
| `created_at` | TEXT | ISO-8601 UTC timestamp |
| `version` | INTEGER | 1, 2, 3… per `company_name`, computed at insert time |

## Folder Structure

```
builds/2026-07-20-canfile/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── main.py            (CLI entry point / argparse)
│   ├── wikidata_client.py  (search + entity + claims fetch, label resolution)
│   ├── wikipedia_client.py (summary fetch)
│   ├── assessment.py       (deterministic rule engine + optional Claude call)
│   ├── storage.py          (SQLite versioned card storage)
│   └── html_report.py      (HTML index renderer)
└── tests/
    ├── test_wikidata_client.py
    ├── test_wikipedia_client.py
    ├── test_assessment.py
    ├── test_storage.py
    ├── test_html_report.py
    └── test_main_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Wikidata search response parsing (single match, multiple matches, zero matches)
  - Wikidata claims parsing for each property (P17, P159, P749, P127, P31), including entities missing a given property
  - Label resolution batch call for referenced QIDs
  - Parent/owner one-hop country resolution
  - Wikipedia summary fetch success and 404/missing-page handling
  - Deterministic assessment rule engine: Canadian HQ + no parent → canadian/high; foreign parent → foreign/high; Canadian parent overriding foreign HQ registration → canadian/high; no country data at all → insufficient-data/low; parent exists but its country unknown → uncertain/medium
  - Claude enrichment path is mocked and falls back to deterministic text when the mocked call raises or when no API key is set
  - SQLite versioning: two `add` calls for the same company produce version 1 and version 2, `show` returns both, `list` returns only the latest
  - `search` matches on company name substring and on assessment text substring
  - HTML report escapes company names/assessment text against script injection (XSS safety)
  - CLI: `add`, `show`, `list`, `search`, `export-html` argument parsing and end-to-end flow with all network calls mocked
  - Network failure during `add` is caught and reported without crashing, and does not write a partial/corrupt card
  - All external API calls (Wikidata, Wikipedia, Anthropic) are mocked in every test — no live network calls in the test suite

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests
2. `add "<company>"` produces a stored, versioned knowledge card with a sourced Wikidata/Wikipedia fact set, a confidence-rated verdict, and cited source URLs — using real, documented public APIs (Wikidata, Wikipedia), not mock data
3. Re-running `add` on the same company creates a new version rather than overwriting, and `show` displays the full version history
4. The deterministic assessment path works correctly with zero API keys set — the tool never depends on `ANTHROPIC_API_KEY` to be usable, and adds a materially better plain-English write-up when the key is present
5. `export-html` produces a self-contained, searchable/filterable dark-mode HTML report with no unescaped user/API-derived text reaching the DOM

---

## Scope Changes

None — full scope as planned above was completed.
