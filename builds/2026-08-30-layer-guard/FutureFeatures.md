# Future Features — Layer Guard

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **`--fail-on violations` / `--fail-on cycles` CLI flags** — right now any cycle forces exit code 2 unconditionally; a configurable gate (matching Schema Sentinel's and dep-check's `--fail-on`/`--exit-on-outdated` convention) would let a pre-commit hook or CI job choose to fail only on violations, only on cycles, or on structural-risk modules, rather than an all-or-nothing check.
2. **`--min-instability` / `--min-afferent` flags to tune the structural-risk thresholds** — the 0.8/2 thresholds are reasonable defaults but are currently hardcoded constants; exposing them as CLI flags would let the tool adapt to a much larger or smaller codebase without a code change.
3. **A `--diff` mode against a second directory or git ref** — run the analysis twice (working tree vs. a given git ref via `git show <ref>:<path>` piped through the same `ast.parse` path, no new machinery needed) and report only newly introduced cycles/violations, so a pre-commit hook can complain about regressions without re-litigating pre-existing debt.

## Medium Effort (roughly one nightly build session)

4. **Auto-suggested layer ordering** — deliberately left out of tonight's scope because it's a genuine judgment call, but a *suggested* (not enforced) ordering derived from the graph's own topology (e.g., a topological sort of the SCC-condensation DAG, breaking remaining ties by afferent coupling) could be offered as a starting point the user edits rather than accepts blindly — clearly labeled as a suggestion, never auto-applied.
5. **A `.layerguardignore` file format** (mirroring `.gitignore` syntax) instead of only `--exclude` CLI flags, so a project's exclusion rules travel with the repo rather than living only in whatever command line invoked the tool.
6. **HTML report drill-down**: click a module in the dependency graph to highlight only its direct edges and open its metrics row — currently the graph and table are both static/independent views; wiring them together would make investigating one specific module in a large codebase much faster than scrolling the table.

## Ambitious Extensions (multi-session effort)

7. **Multi-package / monorepo mode** — analyze several independent Python packages in one run (e.g., this whole `Delightful-Nightly-Builds` repo's every build folder at once) and report cross-package coupling separately from intra-package coupling, which would need a notion of "package boundary" beyond the single-root assumption this build makes.
8. **A pre-commit / Claude Code hook wrapper** — package the core `analyze()` function (already decoupled from the CLI in `src/cli.py`) as a Claude Code Hook that runs on file save or pre-commit and posts a one-line summary ("2 new violations introduced by this change") rather than requiring the user to remember to run the CLI manually, following CLAUDE.md's own guidance that a recurring check is usually a better fit as a Hook than a standalone script.

---

## Possible Integration Points

- **Snipvault (2026-08-12)** and **Provenance (2026-08-15)** both shipped a companion Claude Code Skill (`skill/SKILL.md`) so a coding session can invoke the tool on request ("check this repo for import cycles") rather than requiring a manual terminal command — Layer Guard's `analyze()` function is already CLI-independent and would wrap into a Skill with minimal glue code.
- **AgentLint (2026-07-16)** audits `CLAUDE.md`/`AGENTS.md`-style instruction files for structural issues; Layer Guard audits Python import structure. Both are "static structural health checks for a project" in different domains — a future build could unify them under one `project-health` umbrella CLI that runs whichever checks apply to a given repo.
- **Landing Pattern (2026-08-03)** already builds a changed-file overlap graph across this repo's own open PRs to recommend a merge order; Layer Guard's import graph could feed that tool a "does this PR touch a structurally risky module?" signal to help prioritize which PRs deserve closer review, if the two were ever combined.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Only Python is supported (`ast`-based parsing) — the user's stack also includes JavaScript/TypeScript and Dart | A JS/TS variant would need a real parser (e.g. via a Node-based AST library) rather than a from-scratch regex approach, which is a substantial enough undertaking to be its own future build rather than a quick extension |
| A star import (`from pkg import *`) collapses to a single edge on the package itself, losing which specific names were actually pulled in — technically correct for graph/cycle purposes, but coarser than a real import in rare cases | Track the actual imported names alongside the edge for informational display, without changing how cycles/metrics are computed |
| `_extract_one_cycle` reports one concrete cycle per strongly-connected component, not necessarily every node in a large SCC if the component isn't Hamiltonian | For SCCs beyond a handful of modules (rare in practice, but possible in a very tangled legacy codebase), report the full SCC membership alongside the one illustrative cycle chain, so nothing is silently hidden |
| Dynamic imports (`importlib.import_module("pkg.sub")`, `__import__`, or imports inside `if TYPE_CHECKING:` blocks) are invisible to a static `ast`-only scan | Document this explicitly as a known blind spot (already noted in Manual.md); a heuristic string-literal scan for `import_module(...)` calls could catch the common case without executing anything |
