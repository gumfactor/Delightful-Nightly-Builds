# Build Log — CaseForge

> **Date:** 2026-09-04
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:10 UTC] Session Start

- Checked Step 0: most recent dated build folder (2026-06-18-regex-dojo, local branch) already carries "Build complete. Success criteria reviewed." — nothing to resume. Fetched the most recent open PR branch (`claude/cool-sagan-dlvwei`, PR #88, 2026-09-03 Promptbook) and resynced `builds/index.md`/`builds/ideas.md` from it, since local `main` is stale (last merge 2026-06-18; all 88 nightly PRs since then remain open/unmerged).
- Read PROFILE.md, builds/index.md (81 completed builds), STANDARDS.md, builds/ideas.md.
- Day of year 247 → category_index = 3 → Category D — Creative/Generative.
- Category D backlog: one pending row (#17, Workshop Architect, unrated). Lottery: R=0, lottery_chance=25%, roll=44 → miss → fresh generation.
- Generated 3 candidate ideas; selected CaseForge (PubMed-grounded teaching case generator) over an investment pre-mortem generator and a Kwyeter noise-card generator. Full reasoning in WhyThis.md. Logged the two non-winning ideas to `builds/ideas.md` as #42/#43.
- Build folder created: builds/2026-09-04-caseforge/

### [08:25 UTC] PRD Written

- Goal: generate classroom-ready teaching cases (real citation, extracted facts, deterministic discussion questions) from live PubMed abstracts.
- Scope: PubMed E-utilities client, deterministic fact extraction, deterministic discussion-question rule engine, deterministic vignette assembly, optional AI polish with a fact-presence safety net, SQLite library, CLI (generate/list/show/search/export/render), self-contained HTML dashboard, companion Skill.
- Notable constraint: this build container's egress proxy is expected to block `eutils.ncbi.nlm.nih.gov` (per PROFILE.md's documented network policy) — the tool is designed for the user's local runtime where PubMed is freely reachable, and every test mocks the network layer per CLAUDE.md's API-access guidance.

### [08:50 UTC] Build Phase

Built in this order: `extraction.py` (deterministic regex/keyword fact extraction) → `questions.py` (discussion-question rule engine over extracted facts) → `ai_client.py` (Anthropic Messages API via urllib, mirroring this repo's established runtime-credential pattern) → `vignette.py` (deterministic assembly + AI-polish with a fact-presence safety net) → `pubmed_client.py` (esearch/efetch via urllib, XML parsing via stdlib `xml.etree.ElementTree`) → `db.py` (SQLite, PMID as primary key so re-`generate` over an overlapping query never duplicates) → `render.py` (self-contained dark-mode HTML dashboard, JSON-in-`<script>` delivery with `</` escaped, DOM built via `createElement`/`textContent` only) → `main.py` (argparse CLI: generate/list/show/search/export/render) → `skill/SKILL.md` companion wrapper.

Wrote all 8 test files alongside each module (99 tests total). Full suite passed on the first run (`python -m pytest tests/ -v` → 99 passed, 0 failed).

Confirmed live this session that this build container's egress proxy genuinely blocks PubMed (`esearch failed: <urlopen error Tunnel connection failed: 403 Forbidden>`), matching PROFILE.md's documented network policy — expected, and not a reason to change the design; every test already mocks `pubmed_client`/`ai_client` at the `urlopen` boundary, so none of them depend on that access.

Ran a full manual end-to-end walkthrough (not just pytest mocks) by monkeypatching `pubmed_client.search_pmids`/`fetch_articles` with realistic fixture data — including a script-injection payload embedded directly in a fetched article's title (`</script><script>window.__xss=1</script>`) — through the real `main.main()` CLI dispatch: `generate` → `list` → `show` → `export markdown` → `render`, all producing correct output. The rendered `cases.html` correctly contains the payload only as an escaped, inert JSON string (verified: the raw `</script>` sequence never appears un-escaped in the case-data script block, and `payload[0]["title"]` round-trips to the exact original malicious string when JSON-parsed).

**Real bug found and fixed during manual QA** (not caught by the initial 99 tests, since none of them checked grammar): the deterministic vignette and the population-based discussion question both hardcoded the indefinite article "a" — e.g. "studying a undergraduate sample" and "This study samples a undergraduate sample," both wrong since "undergraduate" and "incarcerated/forensic sample" start with vowel sounds. Added `extraction.indefinite_article()` and wired it into both `vignette.py`'s method-bits assembly and `questions.py`'s population-question template (via a `population_article` key added to the format dict at question-generation time, not stored in the extracted-facts dict itself, since it's a presentation concern, not an extracted fact). Re-ran the manual walkthrough and confirmed "studying an undergraduate sample" / "samples an undergraduate sample" now render correctly. Full suite re-run: 99 passed, 0 failed.

Ran the STANDARDS.md security checklist via grep: no `.env` files, no hardcoded credential-like values, no `eval()`/`exec()`/`os.system()`/`subprocess`, and `innerHTML` appears exactly once in the whole `src/` tree — in a code comment in `render.py` explaining why it's *not* used, not an actual usage.

### [09:05 UTC] Tests Run

Tests: 99 passed, 0 failed. (`python -m pytest tests/ -v`)

### [09:10 UTC] Verify — Step 7

PRD success criteria reviewed against the manual walkthrough and test suite:
1. ✓ All 99 tests pass, zero failures
2. ✓ `generate` against mocked PubMed data produced a case per fetched PMID with a non-empty deterministic vignette and 6–7 discussion questions each (always ≥3 by construction); zero network calls made without `--ai-polish` (verified by `test_generate_with_ai_polish_makes_zero_network_calls_without_key`, which asserts against a `urlopen` stub that raises if ever called, and by the fact `ai_client.call_claude` is structurally only invoked inside the `--ai-polish` branch)
3. ✓ Re-`generate` over the same query does not duplicate PMIDs (`test_generate_skips_already_seen_pmids`; also confirmed manually — a second identical `generate` call correctly reported "No new articles found")
4. ✓ `render` produces a self-contained HTML file opening via plain file read, zero `innerHTML` in the whole template, verified live against a script-injection payload carried through the real CLI path end-to-end (not just a synthetic render.py-only test)
5. ✓ The AI-polish safety net rejects a mocked response that drops a required fact (`test_polish_with_ai_rejects_response_dropping_a_fact`) and falls back to the deterministic vignette

STANDARDS.md security checklist: no `.env` files, no hardcoded credential values, no `eval`/`exec`/`os.system`/`subprocess`, no real `innerHTML` usage (one mention only, inside an explanatory code comment), no personal data hardcoded, no calls to any API without PROFILE.md-listed credentials (PubMed is free/no-auth; Anthropic is optional/runtime-only).

Hard standard for Category D (not in STANDARDS.md's visual-interface-required list, unlike A/E/F/G/I) — CaseForge ships a UI anyway (the `render` HTML dashboard) since the prior Category D builds established that pattern and it materially improves usability for browsing a growing case library.

### [09:15 UTC] Documentation — Step 8

- `FutureFeatures.md`: 9 concrete suggestions (4 quick wins, 3 medium-effort, 2 ambitious extensions) plus integration points and known limitations
- `Manual.md`: quick start, full command reference, configuration table, troubleshooting table, known limitations — written for the user reading this cold in six months

Build complete. Success criteria reviewed. All tests passing.
