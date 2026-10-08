# PRD — Lookalike

> **Build date:** 2026-10-08
> **Category:** B — Productivity Utility
> **Complexity:** Ambitious Project
> **Day of week:** Thursday

---

## Goal

Find and safely merge duplicate business records in a Canada List CSV batch (and against the existing directory) using explainable, deterministic matching, with a mobile-readable review page for the ambiguous cases.

## User Story

As the operator of The Canada List ingesting thousands of scraped and AI-classified business rows, I want near-duplicate listings detected, clustered and merged with per-field provenance — while legitimate multi-location branches are left alone — so that the directory stays clean without me eyeballing every row.

## Scope

### In Scope
- Flexible CSV intake (BOM, CRLF, quoted fields, header aliases such as `business_name`, `url`, `tel`, `postal`), row ids from an `id` column or row number.
- Normalization: name (accents, legal suffixes in English/French, `&`/`and`, punctuation), website registered domain (ignoring social/marketplace hosts), phone (NANP 10 digits), email, postal code, street address (abbreviation expansion, unit extraction).
- Candidate generation by blocking (domain, phone, email, postal code, name prefix + province) with fan-out caps.
- Explainable pair scoring: noisy-OR of positive evidence minus conflict penalties; every pair stores its reasons.
- Three outcomes per pair: `duplicate` (auto-merge), `review` (human decides), `branch` (same brand, different location — never merged), plus `distinct`.
- Union-find clustering with a weak-chain guard: a cluster containing any internal pair that scores below the review floor is downgraded to review rather than auto-merged.
- Field-level survivorship merge (most complete, then most frequent, then longest) with provenance recorded per field.
- `decisions.json` (same / different, by row id) persisted and honoured on re-runs.
- Self-contained dark/light `review.html` (side-by-side field diff, Same/Different buttons that build a downloadable decisions file, filters, works at phone width).
- Optional `--ai` adjudication of review-tier pairs via the Anthropic API (`ANTHROPIC_API_KEY` at runtime); advisory only, never auto-applied.
- `demo` command that writes a synthetic sample CSV (fictional businesses) and runs the whole pipeline.
- Outputs: `deduped.csv`, `clusters.csv`, `merge_report.json`, `review.html`.

### Out of Scope
- Writing to the live Canada List database or Firebase.
- Geocoding / map distance (only text address comparison).
- Fuzzy matching against the whole existing directory without an export CSV (use `--existing`, a second CSV, is in scope; direct DB access is not).

## Tech Stack

- **Language:** Python 3.11
- **Framework:** None
- **Dependencies:** stdlib only at runtime. Tests are `unittest.TestCase` classes (pytest-compatible; pytest could not be installed in the build container, see BUILD_LOG).
- **Runtime requirement:** `python3 lookalike.py ...`

## Data Structure

Input row → `Record(id, source, fields{name,website,phone,email,address,city,province,postal_code,category,description,...extra}, norm{name_key,tokens,domain,phone,email,postal,street,unit,province})`.
`PairResult(a, b, score, label, reasons[list of (signal, weight)])`.
`Cluster(id, members[ids], label, merged{field: value}, provenance{field: row id}, flags[])`.
`decisions.json`: `{"same": [["12","47"]], "different": [["3","9"]]}`.

## Folder Structure

```
builds/2026-10-08-lookalike/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── lookalike.py                 (launcher)
├── src/lookalike/__init__.py
├── src/lookalike/__main__.py
├── src/lookalike/normalize.py
├── src/lookalike/similarity.py
├── src/lookalike/schema.py      (CSV intake, header aliases)
├── src/lookalike/match.py       (blocking + scoring + labels)
├── src/lookalike/cluster.py     (union-find, survivorship, decisions)
├── src/lookalike/report.py      (HTML, CSV, JSON writers)
├── src/lookalike/ai.py          (optional Anthropic adjudication)
├── src/lookalike/demo.py        (synthetic sample data)
├── src/lookalike/cli.py
└── tests/test_*.py              (normalize, similarity, schema, match, cluster, report, ai, cli)
```

## Testing Strategy

`python -m unittest discover -s tests -v` (also runs under pytest). Normalization and similarity unit tests; scoring tests for each label including branch-vs-duplicate; cluster/weak-chain/decision tests; survivorship provenance; CSV edge cases (BOM, missing columns, empty file); HTML escaping (XSS) test; AI adjudication tested with a stub transport and malformed responses; end-to-end CLI test on the demo data with expected cluster counts. No live network calls.

## Success Criteria

1. The demo batch (seeded duplicates, typo variants, French/English legal-suffix variants, multi-location chains) yields the expected duplicate clusters and leaves chain branches unmerged.
2. Every merge is explainable: each pair lists its evidence and every merged field records its source row.
3. A `different` decision splits a would-be cluster and a `same` decision forces a merge, on re-run.
4. `review.html` renders self-contained, escapes untrusted CSV content, and works at 375px width.
5. Full test suite (≥15 tests) passes; AI step is opt-in and mocked in tests.
