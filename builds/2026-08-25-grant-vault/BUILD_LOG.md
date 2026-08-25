# Build Log — Grant Vault

> **Date:** 2026-08-25
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [00:05 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- Step 0: checked `builds/` for an incomplete build. Local `main`/branch state only went up to 2026-06-18, so per CLAUDE.md's orientation instructions, fetched the most recent open PR branch (`claude/cool-sagan-4osa1m`, PR #80, 2026-08-24) and checked its latest build folder `builds/2026-08-24-lecture-loom/BUILD_LOG.md` — it ends with "Build complete. Success criteria reviewed. All tests passing." No resume needed. Today (2026-08-25) is a new date, so proceeding with tonight's new build.
- Synced local `builds/index.md` and `builds/ideas.md` from `origin/claude/cool-sagan-4osa1m` (the most recent open PR branch) so tonight's decision is based on the full, current catalog rather than the stale local copy.
- Category rotation: day-of-year 237 → `(237-1) % 9 = 2` → Category C — Personal Knowledge Tool.
- Lottery: 2 pending Category C backlog ideas (#15, #16), both unrated (R=0) → `lottery_chance = 25%`. Rolled 68/100 → fresh-idea path.
- Generated 3 fresh Category C candidates (Grant Vault, Highlight Vault, Supervision Notebook); reviewed the 8 existing Category C builds plus the last-10-builds topic-diversity check (only Trading Book, 2026-08-23, touches finance — not saturated). Picked **Grant Vault**: a personal, section-tagged, reusability-scored library of the user's own past grant prose. Full reasoning in `WhyThis.md`.
- Build folder created: `builds/2026-08-25-grant-vault/`.

### [00:20 UTC] PRD Written

- Goal: local knowledge base mining past grant documents into a searchable, section-organized, reusability-scored prose library.
- Scope: deterministic chunking → section classification → reusability scoring → corpus-wide tagging → optional AI enrichment → SQLite store → search/stats/render CLI. Out of scope: PDF/DOCX ingestion, cross-doc dedup, auto-composition of new drafts, multi-user sync.
- Notable decision: all core logic (classification, scoring, tagging) is deterministic and stdlib-only; Anthropic API integration is strictly additive/optional (`--ai` flag + `ANTHROPIC_API_KEY`), matching the pattern that scored well in prior builds (Qualtrics Inspector, PubMed Research Radar) — a tool that is fully useful with zero external dependencies, with AI as a bonus layer, not a requirement.

### [00:35 UTC] Build Phase — Core deterministic logic

- Implemented `src/chunking.py` (paragraph splitting on blank lines, whitespace normalization).
- Implemented `src/classifier.py` (heading-line override + keyword-signature scoring across 7 named section types + "Other" fallback).
- Implemented `src/scorer.py` (deterministic 0–10 reusability score: length band bonus, specificity-signal penalties for dollar amounts/years/capitalized-name-like phrases, generic-language bonus; tiered High ≥7 / Medium 4–6 / Low <4).
- Implemented `src/tagging.py` (stopword-filtered, corpus-wide rarity-weighted keyword extraction — same TF-IDF-style approach used in the 2026-07-11 Connectome build, reimplemented independently for this build's own folder per the "no importing from another build's folder" hard standard).

### [01:10 UTC] Build Phase — Storage, ingest, search, AI, render, CLI

- Implemented `src/store.py` (SQLite schema, content-hash-based incremental document tracking, chunk insert/query helpers).
- Implemented `src/ingest.py` (orchestrates chunk → classify → score → tag → optional AI enrich → store; skips unchanged files by content hash).
- Implemented `src/ai_enrich.py` (Claude Haiku call via `urllib.request` only, gated on `--ai` + `ANTHROPIC_API_KEY`; catches malformed responses and network errors and falls back to the deterministic tags/no-summary path without raising).
- Implemented `src/search.py` (token-overlap ranking with `--section`/`--tag`/`--min-reuse` filters).
- Implemented `src/render.py` (self-contained dark-mode HTML dashboard; all chunk data embedded as one JSON blob in a `<script type="application/json">` tag, client JS builds the DOM via `createElement`/`textContent` only — no `innerHTML` from chunk text, verified below).
- Implemented `src/cli.py` + `main.py` (argparse: `ingest`, `search`, `stats`, `render` subcommands; `--db` override on every subcommand).
- Authored two synthetic fixture grant documents (`fixtures/`) covering all 7 named section types with realistic but entirely invented content (no real names, institutions, or grant numbers) for tests and live verification.

### [01:40 UTC] Tests Written and Run

Wrote 10 test files covering chunking, classification, scoring (hand-computed reference values for every length/specificity/generic-bonus rule and each tier boundary), tagging, storage, incremental ingest, search ranking/filters, AI enrichment (fully mocked, including a zero-network-calls assertion), render/XSS-escaping, and CLI wiring.

Tests: 86 passed, 0 failed. (`pytest tests/ -v` — `python -m pytest` failed in this container with "No module named pytest" despite `requirements.txt` listing it; the `pytest` executable itself resolves correctly via a separate installed entry point. Documented as a container-specific quirk in `Manual.md`; not a build defect. A user running `pip install -r requirements.txt` and then `python -m pytest tests/ -v` or plain `pytest tests/ -v` from the build folder will not hit this.)

### [01:50 UTC] Manual Verification — render output

Ran `ingest` on both fixtures via the actual CLI (`--db grantvault.db ingest <fixture>`), confirmed the incremental skip by re-ingesting the first fixture unchanged (`skipped 1 unchanged, inserted 0 chunk(s)`), checked `stats` (2 documents, 15 chunks across all 7 section types, 5 High / 1 Medium / 9 Low reuse tiers) and `search "broadly applicable"` (correctly ranked the two most-generic Significance/Broader-Impacts chunks first). Then directly inserted one additional chunk via `store.insert_chunk` containing `harmless prefix </script><script>window.__xss_fired = true;</script> harmless suffix`, re-ran `render`, and opened the output in headless Chromium (`npx playwright`, an ad hoc verification script outside the build folder — not part of the committed pytest suite, matching the pattern used by prior Python-CLI-plus-HTML builds in this catalog). Verified: zero console errors, `window.__xss_fired` stayed `false` (the injected script never executed), `document.querySelectorAll('script').length` stayed at exactly 2 (the page's own two `<script>` tags — the JSON data block and the render logic — no third script node was created from chunk data), the payload rendered as plain visible text inside a `.chunk-text` element, and the live search box correctly filtered from 16 cards down to 1 for a real query. Re-ran `render` once more afterward against only the two legitimate fixtures for the version referenced by `Manual.md`'s walkthrough.

### [01:55 UTC] Verify — Step 7 Success Criteria Check

1. ✓ All 86 tests pass (zero failures) — confirmed above.
2. ✓ Ingesting both fixtures produces at least one chunk per section type, each with a section tag, reuse tier, and ≥1 keyword tag — confirmed via `stats` output and `test_ingest.py`.
3. ✓ Re-running `ingest` on unchanged fixtures inserts zero new chunks — content-hash skip covered by `test_ingest.py::test_reingest_unchanged_file_skips`.
4. ✓ `render` produces a self-contained HTML file that opens via `file://` with zero console errors and safely neutralizes injected `<script>` payloads — verified live above and by `test_render.py`'s XSS regression test.
5. ✓ With no `ANTHROPIC_API_KEY` set and `--ai` omitted, zero network calls occur — verified by `test_ai_enrich.py`'s monkeypatched-`urlopen`-raises-if-called test, and by the fact that `ingest`/`search`/`render`/`stats` never construct a `urllib` request outside `ai_enrich.py`.

Security checklist (STANDARDS.md):
- No `.env` files committed.
- No hardcoded credentials/API keys/passwords — `ANTHROPIC_API_KEY` is read only from the environment at runtime.
- No real personal data — fixture documents are entirely synthetic.
- No `eval()`/`exec()` anywhere.
- No `innerHTML` assignment from stored chunk text — the render page builds all chunk-derived DOM via `createElement`/`textContent`; verified live and by `test_render.py`.
- No `os.system()`/`subprocess` calls.
- No file-path traversal — `ingest`'s path argument is the tool's documented purpose (a local CLI reading files the user points it at, same pattern as every prior Python-CLI build in this catalog); no path is built from data stored *inside* the app.
- All code lives under this build's own folder; no reads/writes outside it.
- AI enrichment is opt-in only (`--ai` flag), sends only the chunk text itself (the user's own already-written grant prose, never third-party personal data) to the Anthropic API, and is documented in `Manual.md`.

### [01:58 UTC] Note — generated artifacts not committed

Running the CLI locally during verification produced `grantvault.db` and `grant_vault_dashboard.html` in the build folder. This is an autonomous, unattended session with no user present to approve destructive shell commands, so these scratch artifacts (including the temporary XSS-test chunk inserted directly into the database for the render verification above) could not be `rm`'d. They are intentionally left untracked and are not staged in the commit — only the source files listed in `PRD.md`'s Folder Structure are committed. A user running the tool locally will generate their own `grantvault.db`/dashboard from their own data on first `ingest`/`render`.

### [02:00 UTC] Documentation

- `FutureFeatures.md`: 7 concrete suggestions across quick-wins/medium/ambitious tiers.
- `Manual.md`: quick start, all 4 commands, configuration table, AI-enrichment privacy note, troubleshooting, known limitations.

Build complete. Success criteria reviewed. All tests passing.
