# WhyThis — Investment Research Notes

## Decision Path

**Tonight's complexity target:** Solid Feature (Tuesday)

**Category selected:** A — Dashboard / Visualizer

Categories used in the last 7 builds: B, H, F. Category A has not been used recently.

**Lottery result:**
- Filtered pool (Category A, compatible complexity): empty
  - Ideas #2 and #3 in `builds/ideas.md` are both Category A but Ambitious complexity — not eligible on a Solid Feature night
- Lottery skipped (empty pool)
- **Path: Fresh idea generation**

**Fresh ideas considered:**

| Idea | Decision |
|------|----------|
| Investment Research Notes Dashboard | WINNER — see below |
| Research Study Pipeline Tracker | Rejected — user already uses Teamwork.com for lab project tracking; prior build "Lab Research Project Tracker" rated 4 for this exact reason |
| Running Progress Dashboard | Rejected — Garmin Connect already covers this; redundant with tools in daily stack |

**Why Investment Research Notes won:**

The user does active personal investing research (IBKR mentioned in PROFILE.md, "personal quantitative investing research and automation" listed as an active project). IBKR handles order execution and portfolio tracking; it does not handle the research and thesis-writing phase — the part that happens before a decision is made.

Right now that research lives in scattered notes, documents, or memory. This dashboard gives it a home: one place to write down why you're watching a ticker, what your conviction level is, and whether you've passed on it or own it. It is immediately useful the first time you open it and add a name. There is no critical missing feature — filters, search, and export are all included so the delivered state is genuinely usable.

The tech stack (single HTML file, localStorage) matches the user's preference for tools that just work without infrastructure. Solid Feature complexity is appropriate: the app has multiple interacting components (CRUD, filtering, search, stats, import/export) and a meaningful data model, but is scoped tightly enough to complete well tonight.

**Non-winning ideas appended to `builds/ideas.md`:** IDs 4 and 5.
