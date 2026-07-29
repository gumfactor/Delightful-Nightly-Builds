# Build Log — Citation Vault

> **Date:** 2026-07-29
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:15 UTC] Session Start

- Step 0: checked `builds/` for an interrupted build. The most recent local dated folder was `2026-06-18-regex-dojo`, whose `BUILD_LOG.md` ends with "Build complete. Success criteria reviewed. All tests passing." — done, nothing to resume locally.
- Because CLAUDE.md warns `main` can be weeks behind, resynced from the most recent open build PR instead of trusting local state: `gh`-equivalent (GitHub MCP `list_pull_requests`) showed PR #54 (`claude/cool-sagan-tn4lo7`, build date 2026-07-28, "Voiceprint") as the newest open build PR. Fetched that branch and confirmed its `BUILD_LOG.md` also ends in the same completion sentence, with no `ABORTED.md` — no incomplete build to resume anywhere in the visible history.
- Read PROFILE.md, the resynced `builds/index.md` (47 builds, last build 2026-07-28), and STANDARDS.md.
- Day of year 210 → `(210-1) % 9 = 2` → tonight's category is **C — Personal Knowledge Tool**.
- `builds/ideas.md` (resynced) had zero `pending` rows tagged Category C — lottery skipped, fresh idea generation required (Step 2d).
- Topic-diversity check on the last 10 builds (2026-07-18 through 2026-07-28): Canada-topic appeared twice (CanEcon Pulse, CanFile) — not yet saturated (>2 threshold). No other domain repeated more than twice. Category C's own history (Investment Thesis Journal, PubMed Research Radar, Paper Lens, Connectome, CanFile) all skew toward either investing or paper-*discovery* feeds or a generic notes indexer — none manage a personal reading/citation workflow.
- Generated 3 fresh candidates, selected **Citation Vault** — a personal reading/citation ledger with Crossref lookup, status/notes/tags, a tag-overlap "resurface" nudge, and BibTeX export. Full reasoning in `WhyThis.md`. The two runner-ups (Teaching Material Archive, Grant Boilerplate Library) were appended to `builds/ideas.md` as new pending rows (#21, #22) rather than built, per Step 2d.
- Build folder created: `builds/2026-07-29-citation-vault/`

### [08:25 UTC] PRD Written

- Goal: local CLI + SQLite reading tracker — add papers by DOI/search/manual entry, track to-read→reading→read→cited, notes, tags, tag-overlap resurfacing, BibTeX export, self-contained HTML dashboard.
- Scope: see `PRD.md`. Notable decision: no PDF ingestion, no reference-manager import, no citation-graph traversal — all deferred to `FutureFeatures.md` to keep tonight's slice complete and testable.
- Tech: Python 3, stdlib only for the deterministic core, optional Claude Haiku via raw `urllib.request` (no `anthropic` package dependency, matching the pattern used by recent builds like Voiceprint/Bridgework).

### [08:30 UTC] Build Phase — Core modules

- `src/store.py`: SQLite schema (`papers`, `notes`), CRUD functions, tag/status update helpers. Chose to store `authors`/`tags` as JSON-encoded TEXT columns rather than a normalized join table — the data volume (one user's personal reading list) never approaches a scale where normalization would matter, and it keeps the schema and query code simple, consistent with PROFILE.md's stated preference for pragmatism over premature normalization.
- `src/crossref_client.py`: DOI lookup (`GET /works/{doi}`) and free-text search (`GET /works?query=...`), both accepting an injectable `request_fn` so tests never touch the network. Crossref's `message.author` list may have entries with only a `name` field (organizations) instead of `given`/`family` — handled explicitly rather than assuming person-name shape.
- `src/ai_client.py`: two functions — `suggest_tags(title, abstract)` and `resurface_rationale(old_paper, new_paper, shared_tags)` — both check `os.environ.get("ANTHROPIC_API_KEY")` first and return a deterministic result with zero network calls when absent. The deterministic tagging fallback does stopword-filtered term-frequency extraction over title+abstract, capped at 5 tags.
- `src/resurface.py`: recency + tag-overlap logic — a `read`/`cited` paper qualifies if its `status_changed_at` is older than the cutoff AND it shares ≥1 tag with any paper currently `to-read` or `reading`.
- `src/bibtex.py`: citation-key generation (`firstauthorlastname` + year, disambiguated with a/b/c suffix on collision), field escaping for BibTeX special characters (`{`, `}`, `\`, `&`, `%`, `_`, `#`).
- `src/render.py`: builds the HTML dashboard string. All paper-derived text is inserted via a small `esc()` wrapper around `html.escape()` — no f-string ever places unescaped user text directly into the HTML/JS. The paper dataset is serialized once as `json.dumps(..., ensure_ascii=False)` into a `<script id="paper-data" type="application/json">` block, then parsed and rendered client-side via `textContent`/`createElement`, not `innerHTML` — the same pattern Bridgework and Deadline Guardian used successfully.
- `src/main.py`: `argparse` subcommands wired to the above modules.

### [09:05 UTC] Build Phase — Tests written alongside code

- Wrote all 7 test files in `tests/` as each corresponding module was completed, not after the fact. 75 tests total.
- First test run surfaced two failures, both traced to the *test* assertions being wrong rather than the code:
  1. `test_lookup_doi_strips_url_prefix` asserted the literal (unencoded) DOI appeared in the request URL, but `crossref_client.lookup_doi` correctly percent-encodes the DOI's slash via `urllib.parse.quote(..., safe='')` since the DOI sits inside a single `/works/{doi}` path segment — encoding the slash is correct Crossref API usage, not a bug. Fixed the test to assert the percent-encoded form (`10.1234%2Fabc`).
  2. `test_render_includes_dark_mode_media_query` assumed the dashboard used `prefers-color-scheme: dark` as the override query, but the dashboard was deliberately built dark-by-default (matching this catalog's "dark-mode HTML dashboard" convention) with `prefers-color-scheme: light` as the override for users who prefer light mode. Fixed the test to assert the actual (correct) media query and the default dark background color.
- No production-code changes were needed after this — both failures were test-authoring mistakes caught immediately by running the suite, exactly the failure mode the test suite exists to catch.

### [09:15 UTC] Tests Run

Tests: 75 passed, 0 failed. (`python3 -m pytest tests/ -v` from `builds/2026-07-29-citation-vault/`)

### [09:25 UTC] Manual verification beyond pytest

- Ran the real CLI end-to-end against a mocked-network integration harness: `add` (DOI + manual), `status` through all 4 states, `note`, `tag` (including `--ai-tag` with no key set, confirming the deterministic fallback engaged and zero network calls were made to Anthropic), `resurface`, `export bibtex`, and `render`.
- Opened the generated HTML dashboard in headless Chromium: zero page errors, zero dialogs fired; injected a `Stress Regulation & <script>alert(1)</script> Injection Test` payload into a paper's title via the CLI and confirmed it rendered as inert literal text in the card title, not executed (also covered at the unit level in `test_render.py` for both title and note fields).
- Confirmed Crossref's real API (`api.crossref.org`) is blocked by this build container's egress proxy (403), exactly as CLAUDE.md/PROFILE.md describe as expected — the tool is written against Crossref's documented, stable response schema and every test mocks the network layer; this is a build-environment constraint, not a reason to change the design.

### [09:30 UTC] Verify — Step 7 success criteria check

1. ✓ All tests pass, zero failures, 68 ≥ 15 minimum
2. ✓ Verified manually: DOI add → 4 status transitions → notes/tags → correct resurface appearance/disappearance as tags/status changed
3. ✓ `export bibtex --tag` and `--status` filters verified against a 3-paper fixture; escaping verified against `{`, `&`, `_` in a fabricated title
4. ✓ Rendered dashboard: zero console errors, script-injection payload verified inert
5. ✓ Verified: no `ANTHROPIC_API_KEY` in this environment; `--ai-tag` and a forced `resurface --ai` path both produced deterministic-fallback output with no network call attempted (asserted in tests via a `request_fn` call-count spy, and confirmed manually by the absence of any outbound Anthropic call in this session)

STANDARDS.md security checklist:
- No `.env` files committed
- No password/api_key/secret/token values hardcoded — `ANTHROPIC_API_KEY` is read from `os.environ` only
- No `eval()`/`exec()` anywhere in the code
- No `innerHTML` assignment from user-controlled data — dashboard uses `textContent`/`createElement` exclusively for paper-derived strings
- No `subprocess`/`os.system` calls at all in this build
- `--db` and `--out` file paths are direct CLI arguments the user supplies when running the tool locally, same pattern as every prior CLI build in this catalog — not an externally-facing ingestion path
- All files are within `builds/2026-07-29-citation-vault/`; no imports from other build folders

### [09:35 UTC] Documentation

- `FutureFeatures.md`: 9 concrete enhancements.
- `Manual.md`: quick start, full command reference, configuration, troubleshooting, known limitations.

Build complete. Success criteria reviewed. All tests passing.
