# Future Features — Marginal Gains

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Custom budget/project count** — a small form on the Practice difficulty screen letting the player type an exact hour budget and project count instead of only the 3 fixed tiers, reusing `Engine.drawProjects` directly (it already accepts an arbitrary count).
2. **"Show me the optimal curve" toggle mid-round** — an optional overlay on each project card's value trend (a tiny sparkline) so a player who wants a learning aid, not just a challenge, can see the shape they're optimizing against before locking in.
3. **Copy-to-clipboard for the Daily Challenge share text** — a single button next to `#share-text` calling `navigator.clipboard.writeText`, since right now the player has to select the text manually.
4. **Keyboard support for the steppers** — arrow-key increment/decrement while a project card is focused, for players who'd rather not click five times.

## Medium Effort (roughly one nightly build session)

5. **A real weekly-planner import mode** — let the player paste their own actual task list (name + rough hours-needed + a 1-5 priority) instead of the flavor-text pool, and have the DP solver compute a genuinely personal optimal allocation. This is the natural bridge from "puzzle about a fictional week" to "tool for planning your actual week," and was explicitly left out of tonight's scope to keep the game self-contained and avoid needing any real personal data.
6. **Difficulty that varies threshold/weight distributions**, not just project count — e.g. a "crunch week" mode where every project has a high startup threshold (lots of low-value setup hours), which changes the optimal strategy meaningfully and would teach a different lesson than the current uniform distribution.
7. **Persisted allocation history export** — a "Download my history as JSON/CSV" button on the Dashboard, so results aren't locked inside one browser's localStorage.

## Ambitious Extensions (multi-session effort)

8. **Multi-week campaigns** — chain several rounds together where an under-invested project from last week carries a "debt" penalty into this week's value curves (e.g. its threshold rises), modeling the real cost of chronic under-investment in one area — a genuinely deeper simulation than any single round can teach.
9. **A real Teamwork.com / Coda import** — pull the user's actual open tasks (titles, due dates, rough size) via API where credentials exist, letting the DP solver run against genuinely live data rather than flavor text. This is the most direct path from "puzzle" to "the actual tool PROFILE.md's friction points call for," but needs those credentials added to repo secrets first and was out of scope for a self-contained game build.

---

## Possible Integration Points

- **Worklog** (2026-07-10) and **Waymark** (2026-08-07) already track real project/commit activity — a future build could feed their output into Marginal Gains' project pool as *real* projects with *real* estimated remaining effort, closing the loop between "what did I actually work on" and "what should I work on next."
- **Deadline Guardian** (2026-07-17) tracks real recurring deadlines; its data could set the `threshold`/urgency weighting of a matching project card automatically instead of a random draw.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| The project pool is flavor text, not the user's real tasks — the game teaches the *skill* but doesn't yet plan the user's *actual* week. | Quick Win #5 / Ambitious #9 above. |
| The DP solver's `O(projects × budget × maxHours)` table is trivial at today's scale (≤8 projects, ≤56 hours) but would need memory optimization (rolling array instead of a full `n × budget` table) if a future difficulty tier scaled budget into the hundreds. | Switch `dp`/`choice` to a single rolling row plus a separate reconstruction pass, or cap future tiers well below where this matters. |
| Daily Challenge streak logic only checks for exact 1-day gaps in UTC; a player in a very different timezone could see their "day" boundary fall mid-session. | Document the UTC reset time more prominently, or let the player see a local-time countdown to the next UTC midnight. |
| The AI Advisor's coaching note is single-shot — there's no way to ask a follow-up question. | Add a small free-text follow-up input that re-sends the same computed numbers plus the player's question. |
| No sound or animation on lock-in — the moment of finding out your grade is purely textual. | A small CSS transition or Canvas confetti-style flourish for S/A grades would add polish without adding a dependency. |
