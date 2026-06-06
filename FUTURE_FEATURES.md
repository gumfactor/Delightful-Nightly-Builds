# Future Features — Nightly Build System

> Ideas for improving the build system itself, not individual builds.
> Add notes here as you notice things worth revisiting.

---

## Decision Logic

- **Complexity eligibility rule for lottery draws** — The current rule (`focused` eligible any night; `solid` on solid/ambitious; `ambitious` on ambitious nights only) is elegant but has a structural bias: focused ideas accumulate lottery chances across all 7 nights while ambitious ideas are eligible only 2 nights per week. Over time this may cause the backlog to skew toward focused builds being drawn and ambitious ones aging out. Worth monitoring after a few months of use. Possible adjustments: (a) let ambitious ideas carry over bonus tickets when they miss eligible nights, (b) relax the rule to complexity ≤ one tier above tonight's target, or (c) keep it as-is if the builds in practice feel well-balanced.

## Scheduling & Routing

- **Dynamic category weighting** — Currently the category is chosen by rotation (avoid last 7). Could incorporate ratings more directly: if the user has rated 3+ builds in a category at 8+, that category gets a mild rotation bump.

## Discoverability

- **Build digest** — A weekly summary commit (or GitHub Action) that generates a `DIGEST.md` with the week's builds, ratings, and top backlog ideas. Easier to review than navigating branches.

## Ratings & Feedback

- **Granular rating dimensions** — Currently a single 1–10 rating per build. Could split into: Utility (did I use it?), Craft (was it well-built?), Surprise (did it spark something?). Would give Claude richer signal.
