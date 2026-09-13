# PRD — Preprint Pulse

> **Build date:** 2026-09-13
> **Category:** D — Creative / Generative
> **Complexity:** Ambitious Project
> **Day of week:** Sunday → Ambitious Project

---

## Goal

A Python CLI that turns a live arXiv search on a research topic into a fact-grounded, ready-to-publish research-digest article draft — a deterministic trend/fact-extraction engine does the analysis, and an optional Claude Haiku pass turns the extracted facts into polished prose, with an always-available deterministic fallback when no AI key is present.

## User Story

As an Associate Professor who writes public-facing articles and blog posts, follows research trends across neuroscience/AI, and named "Blog writing and editing" as a manual task worth automating, I want to point a tool at a research topic and get back a real, source-grounded draft — which papers are trending, what keywords are rising, and what concrete facts (sample sizes, effect sizes, p-values) those papers report — so that I can turn "I should write about X" into a usable first draft in minutes instead of an afternoon of manual literature scanning.

## Scope

### In Scope
- `arxiv_client`: query arXiv's public Atom API (`export.arxiv.org/api/query`, free, no auth) by topic keywords + optional category codes + a trailing time window; paginate for `max_results`; parse into structured `Paper` records (id, title, authors, abstract, published date, categories); polite rate-limiting (arXiv's documented 3-second courtesy delay between paged requests); optional local JSON cache (per-query hash, TTL-based) so repeated runs during drafting don't re-hit the API.
- `trend_engine`: bucket papers by month across the window; compute a least-squares trend slope and classify direction (rising / declining / flat); compute first-half-vs-second-half paper count and percent change; detect "rising keywords" — terms whose per-paper mention count grew from the first half of the window to the second half, with a minimum-support floor to suppress noise.
- `fact_extractor`: regex-based extraction of concrete reported statistics from abstracts — sample sizes (`N = 123`), p-values (`p < .05`), correlations (`r = .34`), effect sizes (`d = 0.5`) — each tagged with its source paper and a short context snippet.
- `outline_builder`: assembles topic, trend result, rising keywords, top papers, and notable facts into a single deterministic `DigestOutline`, including a computed hook-stat sentence.
- `ai_writer`: optional Claude Haiku drafting pass, called via `urllib.request` (no SDK dependency) using `ANTHROPIC_API_KEY` from the environment, with a system prompt that restricts the model to only the facts contained in the outline (no external knowledge, no invented statistics/papers). Falls back unconditionally, with zero network calls attempted, to a deterministic template renderer when no key is set or the API call fails for any reason.
- `report`: renders a Markdown draft (paste-ready for a blog CMS) and a self-contained dark-mode HTML report (Chart.js 4.4.4 paper-count-over-time chart with a DOM-table fallback, source paper list with links, rising-keyword chips, notable-facts list) — every externally-sourced or user-supplied string is HTML-escaped, and chart data is embedded as an escaped JSON `<script type="application/json">` block read via `JSON.parse(...textContent)`, never string-built into executable JS.
- CLI (`main.py`, argparse): `digest` (full pipeline: fetch → analyze → extract → outline → draft → render) and `trend` (quick terminal-only trend check, no draft/report). Flags: `--topic` (required), `--categories`, `--months` (default 18), `--max-results` (default 150), `--ai` (attempt the Claude pass), `--out` (output directory, default `./output`), `--no-cache`.
- Path-safety: topic-derived output filenames are slugified through an allowlist (`[a-z0-9-]`), never built from raw user input, to prevent path traversal.
- A committed `sample_output/` demonstrating a full run (fixture-backed, no live network call baked in) so the user can see the shape of the deliverable without running it first.

### Out of Scope
- Multi-topic batch runs or a persistent history/tracking database across runs (this is a single-topic drafting tool, not a feed or tracker — Paper Lens and Throughline already cover the feed/tracker shape for arXiv/Semantic Scholar).
- Cross-referencing citation counts (would require a second API dependency; kept to arXiv-only for reliability, matching Paper Lens's precedent).
- Any auto-publishing/posting integration (out of scope per "self-contained, no external hosting/services" build rules) — the output is a local file the user pastes wherever they publish.
- Non-English abstract handling / translation.

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** None
- **Dependencies:** stdlib only (`urllib.request`, `xml.etree.ElementTree`, `re`, `json`, `argparse`, `dataclasses`, `hashlib`, `datetime`) — Chart.js 4.4.4 via pinned CDN URL inside the generated HTML only (no build-time/test-time dependency on it)
- **Runtime requirement:** `python3 src/main.py digest --topic "..."` — no install step required beyond a Python 3.11+ interpreter

## Data Structure

No database — each run is a self-contained, stateless pipeline over one topic query.

```python
@dataclass
class Paper:
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    published: date
    categories: list[str]
    pdf_url: str

@dataclass
class TrendBucket:
    period_label: str   # "2025-03"
    count: int

@dataclass
class TrendResult:
    buckets: list[TrendBucket]
    slope: float
    direction: str        # "rising" | "declining" | "flat"
    first_half_count: int
    second_half_count: int
    pct_change: float | None   # None when first_half_count == 0

@dataclass
class Fact:
    arxiv_id: str
    paper_title: str
    fact_type: str    # "sample_size" | "p_value" | "correlation" | "effect_size"
    raw_text: str
    context: str

@dataclass
class DigestOutline:
    topic: str
    window_months: int
    total_papers: int
    trend: TrendResult
    rising_keywords: list[str]
    top_papers: list[Paper]
    notable_facts: list[Fact]
    hook_stat: str
    generated_at: str   # ISO 8601, injectable for testability

@dataclass
class DigestDraft:
    intro: str
    trend_section: str
    facts_section: str
    takeaway: str
    source: str   # "ai" | "template"
```

Optional on-disk cache: `<out>/cache/<sha256-of-query>.json` — raw fetched paper list plus a fetch timestamp; ignored if older than `--cache-ttl-hours` (default 24) or `--no-cache` is passed.

## Folder Structure

```
builds/2026-09-13-preprint-pulse/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── arxiv_client.py
│   ├── trend_engine.py
│   ├── fact_extractor.py
│   ├── outline_builder.py
│   ├── ai_writer.py
│   └── report.py
├── tests/
│   ├── __init__.py
│   ├── fixtures/
│   │   └── sample_arxiv_response.xml
│   ├── test_arxiv_client.py
│   ├── test_trend_engine.py
│   ├── test_fact_extractor.py
│   ├── test_outline_builder.py
│   ├── test_ai_writer.py
│   ├── test_report.py
│   └── test_cli.py
└── sample_output/
    ├── digest.md
    └── digest.html
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v` (run from the build folder)
- **What will be tested:**
  - arXiv Atom XML parsing into `Paper` records (fixture file), including missing/optional fields
  - Query URL construction (topic + category filter + date range encode correctly)
  - Pagination across multiple mocked pages, combined without duplicates
  - Network-error handling in the client (raises a clean, catchable exception; no crash)
  - Cache write/read round-trip and TTL expiry (via `tmp_path` and an injectable clock)
  - Trend bucketing correctness against a hand-worked fixture
  - Least-squares slope sign correctness for rising / declining / flat hand-worked cases, including the n<2-bucket edge case
  - Rising-keyword detection against a fixture corpus with a known keyword shift, and the empty/low-support edge case
  - Fact-extractor regexes against crafted abstract text with known expected matches (sample size, p-value, r, d) and a no-match case
  - Outline assembly: hook-stat sentence correctness for both a defined and an undefined (`first_half_count == 0`) percent-change case
  - AI writer: falls back to the template renderer with zero network calls when no API key is set (verified via a monkeypatched `urlopen` that raises if called at all)
  - AI writer: falls back gracefully to the template renderer when the (mocked) API call raises or returns malformed data
  - AI writer: the outbound request payload contains only outline-derived facts (snapshot-style check of the constructed prompt)
  - HTML report: malicious topic/title input (`<script>` payload) is rendered escaped, never executable, and JSON chart data is safely embedded (`</script>` sequences neutralized)
  - Output-path slugification rejects/normalizes path-traversal-shaped topic input (`../../etc/passwd`-style)
  - End-to-end CLI `digest` run with the arXiv client mocked and no API key: produces valid, non-empty Markdown and HTML files with expected sections present

## Success Criteria

1. All tests pass (zero failures)
2. Given a mocked arXiv response, `digest` produces a Markdown draft and an HTML report containing a hook-stat sentence, a trend direction, at least one rising keyword (when the fixture supports it), and at least one extracted fact — all traceable to the mocked input data
3. With no `ANTHROPIC_API_KEY` set, the full pipeline runs end-to-end with zero network calls beyond arXiv and produces a complete, readable draft (`source: "template"`)
4. The generated HTML report renders safely with arbitrary/hostile topic and paper-title text (verified via escaping tests) and includes a working Chart.js visualization with a table fallback
5. `trend_engine` and `fact_extractor` outputs match hand-computed values for at least one fixture corpus each, verifying the deterministic core is correct, not just "runs without crashing"

---

## Scope Changes

None — the build proceeded as scoped above. (See BUILD_LOG.md for any implementation-level adjustments.)
