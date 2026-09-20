# Build Log — Counterpoint

> **Date:** 2026-09-20
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:10 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- Step 0: checked `builds/` for an interrupted build. Most recent dated folder (2026-06-18-regex-dojo) ends with "Build complete. Success criteria reviewed. All tests passing." — nothing to resume.
- Resynced `builds/index.md` from the most recent open PR branch (`claude/cool-sagan-strfyn`, PR #103) per Step 1 — local `main` copy was over 70 builds behind (last local date 2026-06-24 vs. actual last build date 2026-09-19).
- Day of year for 2026-09-20 is 263 → `category_index = (263-1) % 9 = 1` → **Category B — Productivity Utility**.
- Filtered `builds/ideas.md` to pending Category B rows: #39, #40, #53, #54, all blank rating → R=0 → lottery_chance = 25%. Random roll: 97 → above threshold → fresh idea generation.
- Decided to build: **Counterpoint** — a Response-to-Reviewers letter generator with a deterministic completeness gate and an optional AI prose-polishing layer.
- Build folder created: `builds/2026-09-20-counterpoint/`

### [08:22 UTC] PRD Written

- Goal: parse raw reviewer comments + author response notes, guarantee every comment has a response, render a complete point-by-point letter (Markdown/HTML/plaintext), with an optional AI polish layer that never invents new claims.
- Scope: `check` and `build` CLI subcommands; deterministic parsers for both input files; completeness engine; AI/fallback boundary with injectable client factory for testing; HTML escaping.
- Notable decision: ruled out an IRB/ethics-application angle because Protocol Forge (2026-07-19) already owns that niche — see `WhyThis.md` for the full reasoning.

### [08:30 UTC] Build Phase — Parsing and Matching

- Wrote `src/parser.py`: line-scanning state machine for reviewer headers (`Reviewer N`, `## Reviewer #N`, case-insensitive) and numbered comments (`1.` / `1)`), with multi-line continuation until the next comment/header/EOF. Falls back to "Reviewer 1" when no header precedes the first numbered item (single-reviewer letters). Raises `ParseError` on zero comments found or duplicate comment IDs.
- Wrote the response-file parser in the same module: `[R1C1]`-style block markers, case/whitespace-normalized keys, `ParseError` on zero keys or duplicate keys.
- Wrote `src/response_matcher.py`: `CompletenessReport` dataclass (`total`, `addressed`, `missing`, `orphaned`, computed `percentage`) and the set-difference matching logic.

### [08:45 UTC] Build Phase — AI Polish and Reporting

- Wrote `src/ai_polish.py`: `fallback_format()` deterministic cleanup, and `polish_response()` which takes an injectable `client_factory` so tests never need the real `anthropic` package installed or a network path. `use_ai=False` (the default) never calls the factory at all — this is asserted directly in tests via call-count checks, the same pattern this repo's Snipvault build used for its own zero-network-calls guarantee.
- The AI prompt in `ai_polish.py` explicitly instructs the model to rephrase only — never add claims, data, or justifications beyond what the author's own response text contains.
- Wrote `src/report.py`: Markdown, self-contained dark-mode HTML (with a completeness dashboard bar), and plain-text renderers. All user-controlled text passed through `html.escape()` before HTML embedding.
- Wrote `src/main.py`: `check` and `build` argparse subcommands, exit codes wired to completeness state, `--force` override for `build` that still visibly flags missing comments rather than silently omitting them.

### [09:05 UTC] Tests Written and Run

Wrote 43 tests across 5 files covering parser edge cases (header/number-style variants, multi-line continuation, single-reviewer fallback, no-comments-found, duplicate IDs), response-file parsing failure modes, completeness matching (missing/orphaned/percentage edge cases, numeric vs. lexicographic ID sorting), the AI/fallback boundary (zero-call proof via a raising fake factory, mocked success with prompt-content assertions, mocked-exception graceful fallback, empty-model-output fallback), HTML escaping/XSS safety (both comment and response text), and full CLI integration (`check`/`build` exit codes, `--force` behavior, output file contents, a spy proving `--ai` is never implicitly enabled even when `ANTHROPIC_API_KEY` is present in the environment).

Ran with `/root/.local/bin/pytest tests/ -v` (the environment has no writable location for `pip install`/`venv create`, so the pre-existing `uv`-installed pytest binary was used instead of a project-local install).

Tests: 43 passed, 0 failed.

Also manually ran `python3 -m src.main check` and `build` against `sample_data/` outside pytest to confirm the CLI works end-to-end, not just through test harnesses — output matched expectations (5/5 addressed, all three output files written with correct content).

### [09:20 UTC] Verify — Step 7

Success criteria review:
1. ✓ All tests pass, zero failures, 43 tests (nearly 3x the 15 minimum), each tied to a real failure mode.
2. ✓ `check` against `sample_data/` correctly reports 5/5 addressed with zero missing/orphaned and exits 0 (manually verified); a deliberately incomplete responses file in tests correctly reports missing IDs and exits 1.
3. ✓ `build` (no `--ai`) against `sample_data/` produces `letter.md`, `letter.html`, `letter.txt`, all complete and correctly ordered, with zero network calls (verified via the injected client factory never being invoked, and via a CLI-level spy proving `use_ai=False` on every call even with a fake key present in the environment).
4. ✓ HTML escaping test confirms a `<script>`-bearing comment is rendered as inert escaped text, not live markup; the dashboard bar and missing-comment flag both render correctly.
5. ✓ AI-polish success and failure branches are both exercised via a mocked client factory; no real Anthropic call is ever made during build or test.

Security checklist (STANDARDS.md):
- No `.env` files committed.
- No hardcoded credentials — `ANTHROPIC_API_KEY` is read only from `os.environ`.
- No `eval()`/`exec()`.
- No `innerHTML`-equivalent unescaped injection — all HTML output goes through `html.escape()`.
- No `subprocess`/`os.system()` calls anywhere in the build.
- No file paths built from unsanitized user input beyond the `--out-dir`/`--comments`/`--responses` CLI arguments the user themselves supplies (same trust boundary as any CLI tool).
- All files confined to `builds/2026-09-20-counterpoint/`.

### [09:22 UTC] Note — Build Environment Constraint

`python3 -m venv` and `pip install` were both denied by this session's sandbox permissions. Worked around it by using the pre-existing `pytest` binary already installed via `uv` at `/root/.local/bin/pytest` (found via `find`), which is on this container regardless of project-local installs. This has no effect on the user's own environment — `requirements.txt` still lists `pytest` and `anthropic` for a normal `pip install -r requirements.txt` locally. Also added a `.gitignore` in this build folder (`__pycache__/`, `.pytest_cache/`, `.venv/`, `output/`) since `rm -rf` on those generated directories was likewise denied by the sandbox; staging respects the ignore file so none of them are committed.

### [09:25 UTC] Documentation — Step 8

- `FutureFeatures.md`: 8 concrete suggestions across quick wins, medium effort, and ambitious extensions.
- `Manual.md`: quick start, full usage guide for both input file formats, `check`/`build` command reference, troubleshooting table.

Build complete. Success criteria reviewed. All tests passing.
