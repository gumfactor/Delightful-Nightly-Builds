# Future Features — AgentLint

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **`--ignore` glob patterns** — let the user pass `--ignore "builds/YYYY-*-title-slug/*"` to suppress known-generic template placeholders (exactly the false-positive pattern found tonight running against this repo's own `CLAUDE.md`), instead of every bare filename mention being treated as a literal path.
2. **`--severity-override check_name=level`** — let a project downgrade a specific check (e.g. treat `possible_modal_contradiction` as `info` instead of `warning`) once a team has reviewed and accepted a given pattern, without disabling the check entirely.
3. **Config file support (`.agentlintrc.json`)** — persist `--require-sections`, `--ignore`, `--fail-on`, and `--ground-truth` per project instead of retyping CLI flags every run.

## Medium Effort (roughly one nightly build session)

4. **Multi-file mode** — audit every `CLAUDE.md`/`AGENTS.md` in a repo (or a list of them) in one run, with a combined HTML report and per-file summary table, instead of one file per invocation.
5. **Git-blame-aware staleness detection** — for each numeric/factual claim the AI review flags against a ground-truth file, look up when the referenced ground-truth data last changed (via `git log -1 --format=%ai <file>`) and report how long the instructions have been stale, not just that they are stale.

## Ambitious Extensions (multi-session effort)

6. **Pre-commit / CI gate mode** — a ready-made GitHub Actions workflow snippet (and matching pre-commit hook) that runs AgentLint against every tracked `CLAUDE.md`/`AGENTS.md` in a repo on every PR touching those files, blocking merge on new error-severity findings. This turns the tool from something the user has to remember to run into something that runs itself.
7. **Cross-file consistency mode** — when a project has several agent-facing docs (e.g. a root `CLAUDE.md` plus per-directory scoped instruction files, or multiple `SKILL.md` files), check for contradictions *between* files, not just within one — the natural next step once single-file auditing is trusted.

---

## Possible Integration Points

- This build's own `SKILL.md` is designed to be copied into any other repo's `.claude/skills/` directory — the most direct integration point is the user's other CLAUDE.md-governed projects (The Canada List, Kwyeter) once they exist as separate repos with their own instruction files.
- Pairs naturally with 2026-07-10's Worklog (Cross-Agent Project Activity Workstreams) — Worklog already ingests structured agent checkpoints; a future version could feed AgentLint findings into Worklog's event ledger so instruction-drift fixes show up in the same activity timeline as commits and PRs.
- The ground-truth cross-check pattern (compare a claim in doc A against real data in file B) is generic enough to extend to non-instruction documents too — e.g. auditing whether a project's README's stated feature list matches what's actually implemented — but that's a distinct enough use case to be its own future build rather than scope creep on this one.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Bare filename mentions in generic/templated prose (e.g. this very repo's `CLAUDE.md`, which describes what files *each future build* should contain) are flagged as broken references even when they were never meant to resolve from the audited file's own directory | Add `--ignore` glob support (Quick Win #1 above) so known-generic patterns can be suppressed per project |
| The modal-contradiction check is a keyword-overlap heuristic, not true semantic contradiction detection — it can miss contradictions phrased without "Always"/"Never," and can occasionally flag two statements about the same topic that aren't actually in conflict | Every such finding is explicitly labeled "possible contradiction — needs manual review" rather than a definitive verdict; a future version could route ambiguous heuristic matches through the AI-review pass for a second opinion before surfacing them |
| The AI-review path was validated in this session only through mocked API responses (no `ANTHROPIC_API_KEY` in the build container) — its real-world reliability at flagging ground-truth drift on arbitrary, longer documents hasn't been observed live | The user should try a real run (`ANTHROPIC_API_KEY=... python3 -m src.main audit CLAUDE.md --ground-truth builds/index.md`) and report back whether the flagged findings are accurate and worth the token cost |
| Single target-file + single ground-truth-file per run only | Multi-file mode (Medium Effort #4 above) |
| No persistence — every run is stateless, so there's no way to see whether a previously-flagged issue was fixed or is a repeat offender across runs | A lightweight local SQLite/JSON run history, similar to the pattern used in several of this repo's other Developer Tool builds (Schema Sentinel, dep-check), would let a future version show trend-over-time |
