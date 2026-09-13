# Build Log — Preprint Pulse

> **Date:** 2026-09-13
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:00 UTC] Session Start

- Read CLAUDE.md, STANDARDS.md, PROFILE.md in full.
- Step 0: confirmed `builds/2026-06-18-regex-dojo` (the most recent dated folder) ends with "Build complete. Success criteria reviewed." — no resume needed.
- Step 1: resynced `builds/index.md` and `builds/ideas.md` from the most recently opened PR branch (`claude/cool-sagan-83j15e`, PR #97, re-verified newest via `list_pull_requests` sorted by created desc) rather than the stale `main` copies.
- Day of year 256 → `(256-1) % 9 = 3` → Category D — Creative / Generative.
- Category D lottery: 3 pending backlog rows (#17, #42, #43), all unrated, R=0, lottery_chance=25%, rolled 39 → miss → fresh generation.
- Generated 3 fresh Category D candidates, picked Preprint Pulse (arXiv trend + fact-extraction research-digest drafter). Full reasoning in WhyThis.md. Non-winning candidates logged as ideas #57 and #58 in `builds/ideas.md`.
- Build folder created: `builds/2026-09-13-preprint-pulse/`.

### [08:20 UTC] PRD Written

- Goal: live arXiv search → deterministic trend/fact analysis → fact-grounded draft article, with an optional Claude Haiku prose pass and an always-available deterministic template fallback.
- Scope: `arxiv_client`, `trend_engine`, `fact_extractor`, `outline_builder`, `ai_writer`, `report`, CLI with `digest`/`trend` subcommands, path-safe slugification, committed `sample_output/`.
- Notable constraints/decisions: arXiv-only (no citation cross-reference) to keep the data dependency single and reliable, matching Paper Lens's precedent; no persistent database — each run is a stateless single-topic pipeline (a tracker/feed shape is already covered by Paper Lens and Throughline).

### [08:25 UTC] Build Phase — Core engine

- Implemented `arxiv_client.py`: Atom XML query construction/parsing, pagination with a courtesy delay between pages, JSON on-disk cache with TTL.
- Implemented `trend_engine.py`: month bucketing, least-squares slope + direction classification, first/second-half percent-change, rising-keyword detection (per-paper term presence, first-half vs second-half shift, minimum-support floor).
- Implemented `fact_extractor.py`: regex extraction of sample sizes, p-values, correlations, effect sizes, each with source paper + context snippet.
- Implemented `outline_builder.py`: assembles the deterministic `DigestOutline`, including the hook-stat sentence (handles the `first_half_count == 0` undefined-percent-change case explicitly).

### [08:45 UTC] Build Phase — AI layer, report, CLI

- Implemented `ai_writer.py`: Claude Haiku call via `urllib.request` (no SDK), model overridable via `ANTHROPIC_MODEL` env var, system prompt restricted to outline facts only. Unconditional deterministic-template fallback on missing key or any API failure — verified in tests that no network call is attempted at all when the key is absent.
- Implemented `report.py`: Markdown + self-contained dark-mode HTML rendering, Chart.js 4.4.4 (pinned CDN) with a DOM-table fallback, all external/user-derived strings passed through `html.escape`, chart data embedded as an escaped `<script type="application/json">` block (`</script>` sequences neutralized) parsed via `JSON.parse(...textContent)` rather than string-built into executable JS.
- Implemented `main.py` CLI (`digest`, `trend` subcommands) with topic-based output slugification restricted to an `[a-z0-9-]` allowlist (rejects path-traversal-shaped input).

### [09:05 UTC] Tests Written

- Wrote fixture `tests/fixtures/sample_arxiv_response.xml` (hand-authored, realistic Atom structure) and hand-computed expected trend/fact values (bucket counts, least-squares slope, first/second-half percent change, keyword-shift scores) before writing the corresponding assertions — see `test_trend_engine.py`'s module docstring.
- 7 test files covering: arXiv client parsing/pagination/dedup/cutoff/cache-TTL/errors, trend engine bucketing/slope-direction/keyword-shift, fact extractor regexes, outline assembly (including the `first_half_count == 0` undefined-percent-change branch), AI writer fallback behavior (network-call assertions via a raising-monkeypatched `urlopen`, malformed/incomplete-response handling, request-payload fact-containment), HTML/JSON escaping + path-traversal slugification, and 5 end-to-end mocked CLI runs.

### [09:15 UTC] Tests Run — first pass

Tests: 55 passed, 5 failed. All 5 failures were the same root cause: the hand-authored XML fixture had an unescaped `<` inside an abstract ("p < .001"), which is invalid XML — not a bug in `arxiv_client.py` itself (its `ET.ParseError` handling worked correctly and raised a clean `ArxivClientError`, exactly as designed). Fixed by escaping it to `&lt;` in the fixture.

### [09:20 UTC] Tests Run — after fixture fix

Tests: 60 passed, 0 failed.

### [09:25 UTC] Verification

- Ran `python3 src/main.py digest --help` and confirmed the CLI's argument parsing/help text is correct.
- Byte-compiled every `src/` and `tests/` file (`python3 -m py_compile`) to catch any syntax error tests wouldn't otherwise exercise.
- Generated `sample_output/digest.md` and `sample_output/digest.html` from a realistic 12-paper synthetic corpus ("large language model agents") via a one-off script that calls the real `build_outline`/`template_draft`/`render_*` functions directly — the deliverable is visible in the repo without the user needing to run it first. Confirmed the trend correctly came out "rising" (+167%, 3→8 papers) and 6 notable facts were extracted, matching what the hand-authored corpus was designed to produce.
- Checked all 5 PRD success criteria — see final entry.
- Ran the STANDARDS.md security checklist against every file in `src/` and `tests/`: no hardcoded credentials, no personal data (`grep -i` for password/api_key/secret/token/private_key patterns found only test placeholder strings like `"fake-key"`), no `eval`/`exec`, no unescaped interpolation into HTML (every external/user string passes through `html.escape`; chart JSON is embedded via `safe_json_for_script` with `</script>` neutralized), no `os.system`/`subprocess` calls anywhere, output filenames are built exclusively through `report.slugify`'s `[a-z0-9-]` allowlist (verified against `../../etc/passwd`-shaped input in both unit and CLI-level tests), no reads outside the build folder.

### [09:35 UTC] Documentation

- FutureFeatures.md: 9 concrete suggestions (4 quick wins, 3 medium-effort, 2 ambitious extensions) plus integration points and known limitations.
- Manual.md: quick start, `digest`/`trend` CLI reference, configuration table, troubleshooting, known limitations.

### [09:40 UTC] Success Criteria Review

1. All tests pass (zero failures) — 60 passed, 0 failed. ✅
2. Given mocked arXiv data, `digest` produces a Markdown + HTML draft containing a hook-stat sentence, trend direction, rising keywords, and extracted facts — verified by `test_cli.py`'s end-to-end tests and the committed `sample_output/` (trend "rising" +167%, 6 facts, 8 rising keywords, all traceable to the synthetic input corpus). ✅
3. With no `ANTHROPIC_API_KEY` set, the pipeline runs end-to-end with zero network calls beyond arXiv and produces a complete draft (`source: "template"`) — verified by `test_no_api_key_never_calls_network_and_uses_template` (asserts a call counter stays at 0) and `test_digest_command_reports_template_source_without_api_key`. ✅
4. The HTML report renders safely with hostile topic/title text and includes a working chart with a table fallback — verified by `test_render_html_escapes_hostile_topic_and_title`, `test_safe_json_for_script_neutralizes_script_close_tag`, and the report's own JS `try/catch` fallback to `#chart-fallback`. ✅
5. `trend_engine` and `fact_extractor` outputs match hand-computed values for a fixture corpus — verified by `test_compute_trend_rising_matches_hand_computed_slope` (slope = 4.5/17.5 exactly, cross-checked by hand before the test was written) and `test_extract_facts_from_text_finds_all_four_types`. ✅

All five PRD success criteria met. STANDARDS.md security checklist passed. No scope reductions were needed.

Build complete. Success criteria reviewed. All tests passing.
