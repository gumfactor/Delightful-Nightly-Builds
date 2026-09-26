# Why This? — Shiplog

> **Date:** 2026-09-26

---

## How This Idea Was Selected

**Selection method:** Fresh generation

Category H (Developer Tool) had 5 pending backlog ideas, all unrated (blank = 5 tickets each, `R=0`), giving a 25% lottery gate (`min(75, 25 + 0*2)`). A `random.randint(1,100)` roll returned 38, which is above the 25% gate, so per CLAUDE.md Step 2c the draw is skipped and Step 2d (fresh generation) runs instead.

## The Decision

Every build in `builds/index.md` is now `ambitious`, so tonight's target was the upper end of what one session can deliver, not a scaled-down "focused" build. Category H already has 10 prior builds covering dependency auditing, CI performance, JSON/CSV schema diffing, agent-instruction-file linting, bug-pattern mining, PR merge-order planning, snippet storage, circular-import/coupling analysis, and secret scanning — a genuinely new angle was needed rather than a variation on any of those. Of three fresh candidates, Shiplog had the richest testable deterministic core (conventional-commit parsing, a keyword fallback classifier, revert/re-revert cancellation, semver-bump inference) and the clearest AI differentiator that isn't just a wrapper: Claude turns an already-correct classified structure into readable prose, with the classification itself carrying the real weight, following the lesson from the 2026-06-24 AI Lecture Builder (2/10 — "no deterministic core of comparable weight to the AI call").

## Connection to User Context

PROFILE.md names "building increasingly sophisticated software despite not being a full-time developer" as a recurring friction point, and lists The Canada List, Kwyeter, and this nightly-build repo itself as actively maintained codebases. All three accumulate commits between the user's own occasional review passes — exactly the situation where a generated changelog earns real value: reconstructing "what actually changed" without re-reading raw `git log` output. It also uses `GITHUB_TOKEN`, already confirmed available in PROFILE.md's Data Sources, and treats the Anthropic API as the optional differentiating layer PROFILE.md's "AI integration signal" calls for.

## Why Tonight

Day of year 269 → `category_index = 7` → Category H (Developer Tool) in the fixed 9-day rotation. No idea brief was linked — this is a same-night fresh pick, not a follow-up to a specific prior build, though it deliberately avoids re-treading any of the 10 existing Category H builds listed above.

## What I Hope the User Gets From This

1. A `git log`-to-changelog tool usable on any of the user's local repos (Canada List, Kwyeter, this repo) in seconds instead of manually skimming commit history before a release or a status update.
2. A concrete, testable example of turning noisy commit history into a structured, deduplicated record — the revert/re-revert cancellation and semver-bump inference are small but genuinely load-bearing pieces of logic, not filler.
3. An optional AI layer that stays honest about what it's for: Claude only ever sees the already-classified commit structure (type/scope/subject), never diffs or file contents, and everything works with a clean deterministic fallback if no API key is set.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Coverage Gap Radar — combine `coverage.py` output with git-churn (commit frequency per file) into a prioritized "what to test next" risk score and HTML heatmap | H | Real value, but the core logic (churn × uncovered-lines) is a single multiplication — thinner deterministic core than Shiplog's commit classification pipeline, and it depends on the target repo already having a coverage run configured, which not all of the user's repos do. Logged as backlog idea #73 for a night when that's less of a blocker. |
| Docs-Flag Drift Checker — parse a Python CLI's `argparse` definitions and diff them against the flags/examples documented in its `README.md`/`Manual.md`, flagging drift in either direction | H | Genuinely useful (this very repo's builds all ship a `Manual.md`), but narrower in scope than Shiplog and has no natural AI differentiator beyond a nice-to-have explanation of why a flag matters. Logged as backlog idea #74. |
| Config Drift Detector (backlog #50, pending) | H | Already in the backlog from a prior session's fresh-generation round; tonight's roll (38) sent this session to fresh generation rather than the backlog lottery, and re-proposing an existing pending idea under a new ID would be redundant rather than additive. Left untouched for a future lottery draw. |
