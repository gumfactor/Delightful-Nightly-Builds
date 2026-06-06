# Nightly Builds — Catalog

> **Claude:** Append one row to the Full Catalog table each night. Update the Stats block and Last 7 Builds section.
> Never delete or rewrite existing rows — this is an append-only record.
> **You:** Add `Your Rating` (1–10) and `Rating Notes` after reviewing a build. Both feed future build decisions.

---

## Stats

- **Total builds:** 0
- **Completed:** 0
- **Partial:** 0
- **Aborted:** 0
- **Last build date:** —
- **Categories used (all time):** —

---

## Last 7 Builds (Quick Reference for Decision-Making)

_No builds yet. Claude: after your first build, replace this line with a bullet list of the last 7 builds
in format: `YYYY-MM-DD — [Category ID] — [Title] ([Status])`_

---

## Full Catalog

| Date | Category | Complexity | Title | Short Description | Tech | Status | Your Rating | Rating Notes |
|------|----------|------------|-------|-------------------|------|--------|-------------|--------------|
| — | — | — | — | *No builds yet — this row is a placeholder* | — | — | — | — |

---

## Category Key

| ID | Category |
|----|----------|
| A  | Dashboard / Visualizer |
| B  | Productivity Utility |
| C  | Personal Knowledge Tool |
| D  | Creative / Generative |
| E  | Learning Aid |
| F  | Data Explorer |
| G  | Game / Puzzle |
| H  | Developer Tool |
| I  | Life Admin Helper |

## Status Key

| Value | Meaning |
|-------|---------|
| `complete` | All hard standards met, committed and pushed |
| `partial` | Build works but scope was reduced; documented in BUILD_LOG |
| `aborted` | Could not complete safely; see ABORTED.md in the dated folder |
