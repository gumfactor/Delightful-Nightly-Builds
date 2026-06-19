# WhyThis — Regex Dojo

## Selection Method

**Fresh ideas** (no pending Category G ideas in backlog).

- Lottery roll: N/A — backlog had zero pending Category G items, so the lottery was skipped per the rules.
- Pool size: 0
- Went directly to Step 2d.

---

## Tonight's Category

**G — Game / Puzzle** (day of year: 169, category index: (169 - 1) % 9 = 6).

---

## Ideas Considered

Three candidate ideas were generated for Category G:

1. **Regex Dojo** ← selected
   - 20-level browser puzzle game teaching regex through match/reject challenges
   - Completely self-contained (no external APIs or data)
   - Teaches a real skill the user uses daily in Python and JS
   - Terminal aesthetic fits the developer profile
   - Deterministic game logic makes tests thorough and reliable

2. **Market Cap Higher or Lower** ← rejected; added to ideas.md
   - "Higher or Lower" game using baked-in Yahoo Finance data
   - Rejected because the last 6+ builds heavily cover investment territory; another finance game would feel redundant even in a different format

3. **Stock Chart Direction Quiz** ← rejected; added to ideas.md
   - Show a historical stock chart, guess Up/Down/Flat for the next quarter
   - Rejected for the same reason — investment saturation in recent builds

---

## Why Regex Dojo Won

The user is an intermediate-to-advanced Python and JavaScript developer who uses regex regularly but likely reaches for reference material every time. A well-designed puzzle game that forces recall under light pressure — with 20 carefully ordered levels from literal matching to lookaheads — addresses a genuine skill gap in a fun, self-paced format.

Key strengths:
- **Novel**: nothing like it in the 11-build catalog so far
- **Genuinely useful**: regex proficiency pays off in Python data pipelines, JS validation, and shell scripting — all things the user does
- **Self-contained**: zero external dependencies, no credentials needed, works offline forever
- **Testable**: every level's pass/fail is deterministic, enabling comprehensive Playwright tests
- **Polished potential**: the terminal aesthetic and progressive reveal of regex concepts makes it feel cohesive

The game also fits the user's stated preference for "small polished things that just work" (priority #4) — and this can genuinely be that.

---

## Idea Brief

No linked Idea Brief — this was a fresh idea, not drawn from the backlog.
