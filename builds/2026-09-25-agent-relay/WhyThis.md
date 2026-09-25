# Why This? — Agent Relay

> **Date:** 2026-09-25

---

## How This Idea Was Selected

**Selection method:** Fresh generation (after an overridden lottery draw)

Day of year 268 → `category_index = (268-1) % 9 = 6` → **Category G — Game / Puzzle**.

The Category G backlog had 7 pending rows (#11, #12, #23, #47, #48, #63, #64), all unrated (R=0), giving a 25% lottery gate. Rolled **23** → gate hit → ran a weighted draw (all 7 tied at 5 tickets each, roll 7/35) → drew **idea #12, "Stock Chart Direction Quiz."**

Idea #12 turned out to be a **verbatim duplicate** of the already-built 2026-08-11 build **Quarter Call** (`builds/index.md`): both are "show a real historical stock chart, guess whether price went Up/Down/Flat over the next quarter, using real Yahoo Finance data." This was caught before any code was written, while cross-checking the drawn idea against the current catalog. Per the same precedent set by the 2026-07-27 SiliconWatch correction (a lottery draw that hit a verbatim duplicate of GitHub Repository Health Scorecard), the draw was **overridden to fresh generation** rather than rebuilding something with zero differentiation. `builds/ideas.md` idea #12 was corrected to `skipped` with a note; idea #11 (Market Cap Higher or Lower — a different comparison mechanic but the same Yahoo Finance/guessing shape) was left `pending` with a note flagging it as adjacent enough to deprioritize for now.

Fresh generation produced three candidates (see Alternatives Considered). **Agent Relay** was selected.

## The Decision

Agent Relay is a resource-constrained parallel-scheduling puzzle: the player assigns a DAG of dependent tasks to a limited number of parallel "agent" lanes to minimize total completion time (makespan), scored against a from-scratch exact solver's provably optimal answer. The 10 prior Category G builds span regex-writing, trivia, category-sorting, vignette flaw-spotting (×2), word-guessing, stock-chart guessing, physics simulation, CSP logic-grid deduction, navigation math, and 0/1-knapsack optimization (Marginal Gains, 2026-09-16) — none of them do resource-constrained *scheduling* over a dependency graph, which is a genuinely different algorithm class from knapsack DP (no simple greedy/DP closed form; exact solving requires branch-and-bound over topological orderings). It also lands on the strongest hook in tonight's candidate pool: it is a game *about* the exact thing this repository itself does every night — orchestrating multiple agents against a dependency graph of tasks to finish faster.

## Connection to User Context

PROFILE.md names "Master AI agent workflows and orchestration" as an explicit learning goal and "Agentic AI systems and workflows" as a recurring rabbit-hole topic. No prior build in the 101-entry catalog turns multi-agent task orchestration itself into an interactive, played artifact — prior AI-agent-adjacent builds (AI Session Context Bridge, Cross-Agent Project Activity Workstreams) are productivity tooling, not something you *play* to build intuition for how parallelism, dependencies, and critical-path bottlenecks interact.

## Why Tonight

Category G is tonight's rotation slot. The lottery draw's duplicate-catch forced fresh generation, and among the three fresh candidates this was the most ambitious in algorithmic depth (an exact scheduling solver, not a single-dimension search or a single-lane allocator) while also being the freshest topic tie.

## What I Hope the User Gets From This

1. A few minutes of genuinely fun puzzle-solving with visible, provably-optimal feedback (gold/silver/bronze against the true optimum, not a guessed heuristic).
2. A concrete, hands-on intuition for *why* parallel agent orchestration is hard — dependency chains create unavoidable idle time on some lanes no matter how you shuffle the assignment, which is exactly the kind of thing that's abstract until you've had to solve it yourself.
3. A small, delightful bit of self-reference: a nightly build about scheduling agents, built by an agent, in a repo that runs a new agent build every night.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Bisect (git-bisect binary-search trainer) | G | Real mechanic and a direct "Git/GitHub proficiency" tie, but a single-dimension binary search is a lighter algorithmic lift for an ambitious slot, and GitHub-flavored builds are already heavily represented in the catalog (Fleet Drift, Layer Guard, Worklog, Waymark, ci-pulse, two Repo Health builds, Star Atlas). Logged to backlog as idea #71. |
| Lab Bench Triage (single-day lab resource scheduler) | G | Strong PROFILE.md tie ("lab administration"), but mechanically too close to Marginal Gains (2026-09-16, single-lane resource allocation under constraints), built only 9 nights ago in the same category. Logged to backlog as idea #72. |
| Stock Chart Direction Quiz (idea #12, drawn by lottery) | G | Verbatim duplicate of the already-built Quarter Call (2026-08-11); corrected to `skipped` in the backlog rather than rebuilt. |
