# Build Log — Protocol Forge

> **Date:** 2026-07-19
> This is a live log. Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:20 UTC] Session Start

- Checked for an interrupted prior build: `ls builds/` on this local branch only showed folders through 2026-06-18, but the local `builds/index.md` referenced builds through 2026-06-24. Investigated via `git ls-tree` on `origin/main` (confirmed same, stale) and found the real repo state is spread across many still-open build PRs (#41–#45), the most recent being PR #45 (`claude/cool-sagan-ikj2az`, 2026-07-18, "CanEcon Pulse"). Fetched that branch and confirmed its `BUILD_LOG.md` ends with "Build complete. Success criteria reviewed. All tests passing." — no resumption needed.
- Resynced orientation from `origin/claude/cool-sagan-ikj2az`'s `builds/index.md` and `builds/ideas.md` (38 total builds logged, last build 2026-07-18) rather than the stale local/main copies, per CLAUDE.md's resync instructions.
- Today's date (UTC): 2026-07-19. Day of year 200 → `(200-1) % 9 = 1` → **Category B — Productivity Utility**.
- Checked `builds/ideas.md` for pending Category B ideas: only two rows tagged B (#4 Cross-Agent Project Activity Workstreams, #7 Morning Briefing) and both are already marked `built`. Pending pool is empty → skipped the lottery, went straight to fresh-idea generation (Step 2d).
- Topic diversity check on the last 10 builds (2026-07-09 through 2026-07-18): repo/dev-tooling (Pipeline Pulse, Worklog, AgentLint), neuroscience/teaching (CircuitLab, Research Question Forge), research-feed (GrantScope, and earlier PubMed Research Radar/Connectome — already flagged as a recurring pattern), research-integrity game (Confound Hunter), admin (Deadline Guardian), econ dashboard (CanEcon Pulse). No investment/finance in the last 10. Avoided proposing another GitHub-analytics or external-research-feed build given repeated critique of that pattern in Rating Notes.
- Generated 3 fresh Category B candidates (see `WhyThis.md`): Protocol Forge (IRB/ethics protocol drafting + compliance checklist + reusable boilerplate library), GradeFlow (batch rubric-based grading/feedback assistant), and a Grant Budget Justification Builder. Chose **Protocol Forge** — it targets "Ethics application generation," a friction point named verbatim in PROFILE.md's "Things you do manually that you suspect could be automated" list, and has never been built. Full reasoning in `WhyThis.md`.
- Build folder created: `builds/2026-07-19-protocol-forge/`

### [08:35 UTC] PRD Written

- Goal: turn structured study parameters into a compliance-checked IRB/ethics protocol draft, with a local library of approved boilerplate that compounds in usefulness over repeated use.
- Scope: JSON study format, deterministic compliance-rule engine, SQLite protocol library with approve/reuse, tag-based deterministic similarity matcher (not fuzzy/embedding-based, so it works fully offline), 3-tier drafting fallback (reuse → AI → template), 6 canonical sections, full CLI.
- Notable decision: deliberately avoided fuzzy text similarity or embeddings for the boilerplate matcher — a deterministic tag-overlap score keeps the tool fully functional and testable with no network/model dependency, and is the direct mitigation for the "value depends entirely on what you write in" critique that scored the 2026-06-06 AI Session Context Bridge a 3/10.

### [09:10 UTC] Build Phase — Models & Checklist Engine

- `src/models.py`: `Study` dataclass with `from_dict`/`from_file`, explicit `ValueError` on missing required keys or malformed JSON (never silently defaults a required field).
- `src/checklist.py`: 7 deterministic rules, each returning zero or more `Finding(severity, code, message, field)` objects; `run_checklist(study) -> ChecklistReport` aggregates findings plus a 0-100 completeness score (100 minus a fixed point deduction per blocking/warning finding, floored at 0).

### [09:35 UTC] Build Phase — Library & Similarity Matcher

- `src/library.py`: SQLite-backed `ProtocolLibrary` — `save_protocol`, `list_protocols`, `get_protocol`, `approve`, and `find_reusable_section(study, section_key)` which scores every `approved` protocol's stored section of the same `section_key` by Jaccard overlap of a small deterministic tag set (vulnerable groups, `data_identifiable`, `deception`) and returns the best match above a 0.5 threshold, or `None`.
- Confirmed via test that a `draft`-status protocol is never returned as a match, even with a perfect tag overlap — only `approved` protocols contribute boilerplate.

### [10:05 UTC] Build Phase — Drafting Engine

- `src/drafting.py`: `draft_section(section_key, study, library)` implements the 3-tier fallback (reuse → Anthropic API via `urllib.request` → deterministic template). The Anthropic call is isolated in `_call_anthropic()` so tests can monkeypatch it directly; it is never invoked in this build session since no `ANTHROPIC_API_KEY` is set in the container.
- `assemble_markdown(...)` builds the full document: title/metadata header, the 5 always-present sections, the Vulnerable Populations Safeguards section only when `population.vulnerable_groups` is non-empty (excluding `"none"`), and a Compliance Check Summary appendix listing every finding with severity.

### [10:30 UTC] Build Phase — CLI

- `src/cli.py` / `protocol_forge.py`: `init`, `check`, `draft`, `approve`, `list`, `show`, each with clear stderr messages on bad input (missing file, malformed JSON, unknown protocol id) and non-zero exit codes on failure — never a silent no-op.

### [10:50 UTC] Tests Written & Run

- Wrote `tests/test_models.py`, `tests/test_checklist.py`, `tests/test_library.py`, `tests/test_drafting.py`, `tests/test_cli.py` — 66 tests total, covering every checklist rule individually (fires on a bad study, silent on a clean one), the similarity matcher's match/no-match/draft-excluded/multiple-candidates cases, all three drafting fallback tiers (including a mocked Anthropic success response, a mocked Anthropic network-error response, and a mocked malformed-response case, all falling through correctly), and full CLI round-trips (`init` → `check` → `draft` → `approve` → second tag-similar `draft` reuses text verbatim → `list`/`show`).
- Deliberately wrote the vulnerable-population safeguard rule to check both `procedures` and `consent_process` for safeguard keywords from the start (assent/parental-consent language is conventionally documented in the consent section, not the procedures section) — covered by two explicit tests (`test_vulnerable_population_safeguard_in_procedures_not_flagged` and `..._in_consent_process_not_flagged`) so a future edit can't silently narrow this back to one field.

[10:55 UTC] Tests: 66 passed, 0 failed. All passed on first run — no bugs found during test-writing.

### [11:00 UTC] Manual Verification Beyond Pytest

Ran the actual CLI end-to-end outside the test suite: `init` → filled in a realistic student-subject-pool stress study → `check` (clean, 100/100) → `draft` (produced a complete Markdown document via the template tier, no API key set) → `list` → `show 1` → `approve 1` → `draft` a second, tag-similar study → confirmed all 6 sections showed the `(reused from protocol #1)` marker in the output file. Also manually verified the checklist against a deliberately broken study (deception with no debrief, zero retention, no risks) via both `check` and `check --json` — all three seeded issues surfaced with correct severities and the completeness score matched the deduction math (100 − 20 − 8 − 8 = 64).

### [11:05 UTC] Verify — Step 7

Security checklist (STANDARDS.md):
- No `.env` files; no hardcoded credentials — `ANTHROPIC_API_KEY` read only via `os environ.get`, never written to source
- No `eval()`/`exec()` anywhere
- No `os.system()`/`subprocess` calls at all
- No file paths built from unsanitized user input — `--db`/study-file paths are operator-supplied CLI arguments, matching this repo's established pattern (Ledger Lens, Schema Sentinel, GrantScope, etc.)
- All Markdown/HTML text is built from structured fields the user explicitly authored about their own (not-yet-conducted) study design — no real participant PII exists at this stage; nothing is sent to a third party except the study-design fields themselves, and only when the user supplies their own `ANTHROPIC_API_KEY`
- All code and data reads/writes are confined to `builds/2026-07-19-protocol-forge/`

Success criteria review:
1. ✓ 66 tests pass, 0 failed
2. ✓ `check` on deliberately bad study fixtures (built via `tests/factories.py::make_study_dict` overrides) surfaces all 6 seeded issues with correct severities — `test_checklist.py`
3. ✓ `draft` with no `ANTHROPIC_API_KEY` set produces a complete Markdown document via the template fallback — `test_drafting.py::test_template_fallback_used_when_no_api_key_and_no_reuse`, `test_cli.py::test_draft_end_to_end_no_api_key`
4. ✓ Approve → similar second study → reused section text verified verbatim with a "(reused from protocol #N)" marker — `test_cli.py::test_approve_then_reuse_across_protocols`
5. ✓ Anthropic path only ever called through a monkeypatched `_call_anthropic` in tests; grepped the whole test suite and confirmed zero live `urllib`/`http` calls are made

### [11:10 UTC] Documentation Complete

- `FutureFeatures.md`: 8 concrete suggestions
- `Manual.md`: quick start, full command reference, study JSON field reference, configuration, troubleshooting, known limitations

Build complete. Success criteria reviewed. All tests passing.
