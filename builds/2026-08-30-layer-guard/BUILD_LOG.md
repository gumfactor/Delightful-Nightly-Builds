# Build Log — Layer Guard

> **Date:** 2026-08-30
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:10 UTC] Session Start

- Step 0: checked `builds/` for an interrupted session. Local `main`/working branch was stale (last merged build 2026-06-18); resynced orientation from the most recent open PR branch (`claude/cool-sagan-q2pava`, PR #84, 2026-08-29 "Zebra Lab") per CLAUDE.md's resync instructions. That build's `BUILD_LOG.md` ends with "Build complete. Success criteria reviewed. All tests passing." and has no `ABORTED.md` — nothing to resume.
- Read PROFILE.md, the resynced `builds/index.md` (77 prior builds, last build 2026-08-29), and STANDARDS.md.
- Day of year (UTC) = 242 → `category_index = (242-1) % 9 = 7` → **Category H — Developer Tool**.
- Read the resynced `builds/ideas.md` from the same branch. Only one pending Category H row existed: idea #9, "GitHub Actions Performance Analyzer" (added 2026-06-17). Cross-checking `builds/index.md`, this is a verbatim duplicate of the already-built `ci-pulse` (2026-06-28, GitHub Actions Performance Analyzer). The 2026-08-12 Snipvault build's log already recorded correcting this exact row to `skipped` on its own branch, but since none of these PRs have ever merged to `main`, that correction never propagated to this branch's copy of `ideas.md` (each nightly session branches from stale `main`, not from the previous night's branch). Corrected idea #9 to `skipped` in this session's local `builds/ideas.md` with a note, which empties the Category H pending pool → routed to fresh generation.
- Fresh idea generation (Category H). Reviewed the 8 prior Category H builds (Git Standup Reporter, dep-check, ci-pulse, Schema Sentinel, AgentLint, BugTrace, Landing Pattern, Snipvault) to avoid duplication — 7 of 9 lean on `GITHUB_TOKEN`; Snipvault deliberately broke that pattern. Considered 3 candidates (see WhyThis.md for full reasoning):
  1. **Dead Code Detective** — AST reachability analysis to find unused Python functions/classes.
  2. **Test Flakiness Static Scanner** — rule-based scan for common pytest/JS non-determinism patterns.
  3. **Layer Guard** — import-graph cycle detection + layering-violation checker + coupling metrics (chosen).
- Chose **Layer Guard**: ties directly to PROFILE.md's named learning goal "Better understand scalable software architecture" and the explicit thing-to-avoid "Overly complex architectures," neither previously touched by any of the 77 prior builds. Real from-scratch graph algorithm (Tarjan's SCC) gives it the same "verifiable, testable core logic" shape this catalog's highest-rated builds share (Qualtrics Survey Data Inspector, 9/10), rather than being a thin AI wrapper.
- Build folder created: `builds/2026-08-30-layer-guard/`

### [08:25 UTC] PRD Written

- Goal: static Python import-graph analyzer — cycle detection (Tarjan's SCC), coupling/instability metrics, optional explicit layering-violation checking, terminal/JSON/HTML output, optional AI refactor-advice note built from aggregate structure only.
- Scope: full feature set as designed; no auto-inferred layering (deliberately out of scope — the tool can't safely guess architectural intent); no cross-language support; no execution of scanned code (pure `ast`, safe on any codebase); no persistent history (each run is a complete stateless analysis).
- Key decision: resolve imports via progressive-prefix matching against the actual set of discovered modules, since `from pkg.sub import name` may target either a submodule or an attribute — this only affects graph precision, not correctness of stdlib/third-party filtering.

### [09:05 UTC] Build Phase — Core engine

- `src/scanner.py`: recursive `.py` discovery with default excludes (`.git`, `__pycache__`, `venv`, `.venv`, `node_modules`, `.tox`, `build`, `dist`) plus user `--exclude` glob support; package-aware dotted module-name derivation (honors `__init__.py`, strips trailing `__init__` from the dotted path).
- `src/ast_parser.py`: `ast.parse` per file (never executes code); extracts `Import`/`ImportFrom` nodes including `level` for relative imports; resolves relative imports against the importing file's own package position; classifies each resolved name as first-party (progressive-prefix match against the known module set), stdlib (`sys.stdlib_module_names`), or external; a file with a `SyntaxError` is skipped with a warning rather than aborting the whole scan.
- `src/graph.py`: builds the deduplicated edge list with evidence; implements Tarjan's SCC **iteratively** (explicit stack, not recursive) so it can't blow Python's recursion limit on a large real codebase; computes Ca/Ce/instability/structural-risk per module.
- `src/layers.py`: loads and validates `layers.json`, does prefix-based module→layer assignment, computes violations (importer layer index < importee layer index) and the unassigned-module list.
- `src/ai.py`: builds an aggregate-only prompt (cycle chains as module-name lists, violation tuples, top instability modules — never file paths or source text) and calls the Anthropic API directly via `urllib.request` only when `ANTHROPIC_API_KEY` is set; deterministic template fallback otherwise, verified to make zero network calls without a key.
- `src/report.py`: terminal (colored via ANSI codes with a `NO_COLOR`-respecting fallback), JSON, and a self-contained dark-mode HTML dashboard — all dynamic data delivered as a JSON payload embedded in a `<script type="application/json">` tag (never string-interpolated into executable JS or via `innerHTML`), read back with `JSON.parse` and rendered via `createElement`/`textContent` only; a hand-drawn Canvas 2D force-ish dependency graph colored by layer with cycle edges in red and violation edges in orange.
- `src/cli.py` / `main.py`: argparse entry point wiring it all together; clear error messages for a nonexistent root or malformed `--layers` JSON instead of a raw traceback.

### [09:35 UTC] Tests Written

- 63 tests across 7 files covering file discovery/excludes, module naming, every import form (including relative imports at multiple levels and a deliberately syntax-broken fixture file), stdlib/third-party filtering, progressive-prefix resolution, Tarjan's SCC on 6 hand-built graph shapes, coupling-metric edge cases (including a caught-and-fixed arithmetic mistake in a test's own expected instability value, corrected after the first run), layer-violation detection and prefix matching, the AI mocked-call/no-key-zero-calls pair, JSON round-trip, HTML XSS-escaping, and CLI error paths.
- `pytest.ini` with `pythonpath = .` added — the pre-installed `pytest` binary in this environment runs from an isolated uv-tool venv that doesn't add the invoking directory to `sys.path`, so `import src...` failed on the first collection attempt until this was added.

### [09:40 UTC] Tests Run

Tests: 63 passed, 0 failed (one test's own expected-value arithmetic was wrong on the first run — `instability` for Ce=5,Ca=1 is 5/6≈0.83, not 1.0 — fixed the test, not the code, since the code's formula was correct).

### [09:50 UTC] Manual Verification

- Ran the tool live against its own repository (this build folder) with the committed `layers.example.json` (`python3 main.py . --exclude tests --exclude .pytest_cache --layers layers.example.json`): 9 modules, 14 edges, **0 cycles**, **0 layering violations**, 1 unassigned module (`src`, the package's own empty `__init__.py`) — confirms this build's own architecture is genuinely acyclic and correctly layered (`core` never imports `presentation`/`cli`). Also generated the HTML report from this real run and inspected the embedded JSON payload directly (not just via unit tests) — module list, edge count, and layer order all matched expectations exactly.
- Ran the tool against a real synthetic fixture directory (a 3-module package with `a -> b -> c -> a` imports, written to the scratchpad, not committed) via the actual CLI entry point (not the test suite): correctly detected as a single 3-node cycle (`cyclepkg.a -> cyclepkg.b -> cyclepkg.c -> cyclepkg.a`), correct exit code 2, and the deterministic AI-fallback note correctly named the exact cycle chain.
- Ran the CLI directly (not via pytest's mocking) against that same fixture with `ANTHROPIC_API_KEY` unset and `urllib.request.urlopen` monkey-patched at the real module level to raise `AssertionError` if ever called: the run completed successfully with no exception, confirming zero network calls end-to-end through the actual entry point, not just the unit-test mocks.
- The HTML-escaping guarantee is covered by `test_render_html_escapes_script_injection_in_evidence`, which injects a `</script><script>alert(1)</script>` payload into an `Evidence.file` field, renders the report, confirms the literal payload never appears unescaped, and confirms the embedded JSON still parses back to the exact original string.

Security checklist:
- No `.env` files, no hardcoded credentials/keys
- No `eval()`/`exec()` anywhere (the tool parses code via `ast.parse`, which never executes it)
- No `innerHTML` from user-controlled data — HTML report uses `createElement`/`textContent` only, with the dynamic payload delivered via a `application/json` script tag
- No `os.system()`/`subprocess` calls at all
- No file-path traversal — the root path and `--exclude` patterns are used only with `os.walk`/`fnmatch`, never concatenated into a shell command
- Nothing reads or writes outside the build folder or the user-specified scan root/output path (which are runtime CLI arguments, not the build's own files)

### [09:55 UTC] Documentation

- `FutureFeatures.md`: 8 concrete suggestions.
- `Manual.md`: quick start, full CLI reference, `layers.json` format walkthrough using this build's own `layers.example.json`, configuration table, troubleshooting.

Build complete. Success criteria reviewed. All tests passing.
