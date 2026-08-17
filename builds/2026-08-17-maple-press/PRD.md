# PRD — Maple Press

> **Build date:** 2026-08-17
> **Category:** D — Creative / Generative
> **Complexity:** Ambitious
> **Day of week:** Monday

---

## Goal

Turn a CSV of Canadian businesses (optionally pre-verified by Provenance/CanFile) into ready-to-publish editorial copy — spotlights, gift guides, "Canadian swap" pieces, and local roundups — via a deterministic content-structure engine with an optional AI prose-polish layer.

## User Story

As the founder of The Canada List, who currently writes editorial content for the site by hand, I want to turn a structured list of Canadian businesses into structurally-sound, non-duplicate first-draft articles, so that publishing a gift guide or business spotlight takes minutes instead of a from-scratch writing session.

## Scope

### In Scope
- CSV ingestion for business records: `name`, `category` required; `description`, `city`, `province`, `website` optional; optional Provenance-style `verdict`/`confidence`/`evidence` columns consumed when present
- Verdict-aware filtering: defaults to `verdict == canadian` when the column exists; `--include-unverified` includes everything, with an "unverified — confirm before publishing" disclaimer inserted into generated copy for any business lacking a canadian verdict
- Four piece types, each with real, checkable eligibility requirements against the filtered business set:
  - `spotlight` — 1 business
  - `gift_guide` — ≥3 businesses sharing one category
  - `swap_it` — ≥2 businesses sharing one category, framed as Canadian alternatives to reach for
  - `local_spotlight` — ≥2 businesses sharing one province
- Three tones (`consumer`, `editorial`, `social`) with a compatibility rule: `social` (short-form) is only valid for `spotlight`/`gift_guide`; `swap_it`/`local_spotlight` need the longer explanatory forms and reject `social`
- Optional `--occasion` (`general`, `holiday`, `canada-day`, `back-to-school`) swaps in occasion-specific headline formulas and CTA copy from a fixed lookup table — fully deterministic, no reliance on the system clock
- Deterministic headline selection from a per-piece-type formula bank, with a Jaccard-token-overlap novelty scorer that compares a candidate piece's body against every previously generated piece of the same type in the local library and prefers the least-overlapping formula, so repeat runs on similar inputs don't keep producing the same draft
- Deterministic body assembly: intro hook, per-business card (name, one-line pitch built from category/city/description with word-boundary truncation, "why it's Canadian" line drawn from `evidence` when present), and a closing CTA — all built from real input data, no invented facts
- Local SQLite library (`pieces` table) — every `generate` call inserts a new, permanently versioned row; nothing is ever overwritten
- CLI commands: `generate`, `list`, `show`, `export` (Markdown or HTML file), `render` (self-contained dark-mode HTML library dashboard: search/filter by type/tone, click-to-expand, copy-as-Markdown)
- Optional `--ai-polish`: sends only the deterministically-assembled draft text (never raw CSV rows or personal data) to Claude Haiku for a prose rewrite that preserves every fact; unconditional fallback to the deterministic draft on missing key, network error, or malformed response
- Companion Claude Code Skill (`skill/SKILL.md`) wrapping `generate`/`list`/`export` for in-session use

### Out of Scope
- Automatic sourcing of business data from the web (CSV input only — data comes from the user's own Canada List pipeline, e.g. Provenance's output)
- Image generation or selection (text copy only)
- Publishing/CMS integration — export produces a file, not a live post
- Multi-language (French) output

## Tech Stack

- **Language:** Python 3.x
- **Framework:** None
- **Dependencies:** stdlib only (`urllib` for the optional Anthropic API call)
- **Runtime requirement:** `python3 src/main.py <command> ...` — no install needed beyond stdlib

## Data Structure

**Input CSV** (business records), one row per business:

| Column | Required | Notes |
|---|---|---|
| `name` | yes | |
| `category` | yes | |
| `description` | no | free text, used for the card pitch |
| `city` | no | |
| `province` | no | used for `local_spotlight` grouping |
| `website` | no | |
| `verdict` | no | `canadian` / `foreign` / `uncertain` — Provenance/CanFile-compatible |
| `confidence` | no | 0–1 float |
| `evidence` | no | free text — feeds the "why it's Canadian" line |

**SQLite** (`maple_press.db`, created in the build folder):

```sql
CREATE TABLE pieces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    piece_type TEXT NOT NULL,
    tone TEXT NOT NULL,
    occasion TEXT NOT NULL,
    headline TEXT NOT NULL,
    body_markdown TEXT NOT NULL,
    businesses_json TEXT NOT NULL,
    novelty_score REAL NOT NULL,
    ai_polished INTEGER NOT NULL DEFAULT 0
);
```

## Folder Structure

```
builds/2026-08-17-maple-press/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── main.py            (CLI entry point / argparse)
│   ├── csv_ingest.py       (business CSV parsing + validation)
│   ├── taxonomy.py         (piece types, tones, occasions, compatibility rules)
│   ├── headlines.py        (formula bank + novelty-driven selection)
│   ├── novelty.py          (Jaccard token-overlap scorer)
│   ├── body.py             (deterministic body assembly, truncation)
│   ├── ai_polish.py        (optional Claude Haiku polish + fallback)
│   ├── store.py            (SQLite persistence)
│   └── render.py           (self-contained HTML library dashboard)
├── skill/
│   └── SKILL.md
├── tests/
│   ├── test_csv_ingest.py
│   ├── test_taxonomy.py
│   ├── test_headlines.py
│   ├── test_novelty.py
│   ├── test_body.py
│   ├── test_store.py
│   ├── test_ai_polish.py
│   └── test_render.py
└── fixtures/
    ├── businesses_valid.csv
    ├── businesses_missing_column.csv
    └── businesses_no_verdict.csv
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - CSV ingestion: valid file parses correctly; missing required column raises a clear error, not a crash
  - Verdict filtering: default-canadian filtering, `--include-unverified` behavior, and the disclaimer text when verdict is absent entirely
  - Piece-type eligibility: `gift_guide` rejects a 2-business category; `local_spotlight` rejects a single-province set; `spotlight`/`swap_it` accept valid minimal sets
  - Tone/piece-type compatibility: `social` + `swap_it` rejected; `social` + `spotlight` accepted
  - Headline selection is deterministic for identical inputs with no history, and shifts to a different formula on a second, near-duplicate generation via the novelty scorer
  - Novelty scorer: hand-computed Jaccard overlap reference example
  - Body assembly: word-boundary truncation never cuts mid-word and never exceeds the configured length
  - Occasion flag changes headline/CTA content versus `general`
  - SQLite persistence: `generate` inserts a new versioned row every call (never overwrites); `show` retrieves the exact stored body; a nonexistent id raises a clear error
  - AI polish: zero network calls with no `ANTHROPIC_API_KEY` (mocked `urlopen` assertion), draft-preserving fallback on a mocked network error, and a mocked-success path that stores the polished text
  - HTML render: a `<script>`/`<img onerror>` payload in a business name/description is present in the escaped JSON payload but never appears as unescaped, executable markup in the surrounding HTML

## Success Criteria

1. All tests pass (zero failures)
2. Given a realistic 8-business fixture CSV, `generate` produces all four piece types with at least one valid tone each, and every generated body contains only facts traceable to the input CSV (verified by a live run, not just fixtures)
3. Re-running `generate` with the same category twice produces two different headlines (novelty scoring measurably changes selection), verified live against the real SQLite history
4. With no `ANTHROPIC_API_KEY` set, `--ai-polish` makes zero network calls and the CLI still produces complete, publishable copy
5. `render` produces a self-contained HTML file that opens correctly and renders an XSS payload embedded in a business name as inert text, verified live in headless Chromium

---

## Scope Changes

(none — filled in during the build if scope changes)
