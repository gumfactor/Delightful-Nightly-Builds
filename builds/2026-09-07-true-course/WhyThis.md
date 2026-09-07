# Why This? — True Course

> **Date:** 2026-09-07

---

## How This Idea Was Selected

**Selection method:** Fresh generation

Day-of-year rotation (day 250 → `(250-1) % 9 = 6` → Category G, Game/Puzzle). The Category G backlog held 5 pending ideas (#11 Market Cap Higher or Lower, #12 Stock Chart Direction Quiz, #23 Circuit Six, #32 Pace Strategy Simulator, #33 Boating/Marine Navigation Puzzle), none rated (R=0), so the lottery gate was `min(75, 25 + 0*2) = 25%`. Rolled 60 (1–100) — above the 25% threshold — so the lottery was skipped and fresh ideas were generated instead, per Step 2c/2d.

## The Decision

Backlog idea #33 (Boating/Marine Navigation Puzzle) had already been passed over twice, both times with the same note: it needed "a real tide/current calculation engine, not a trivia quiz" to be worth building. Since tonight's fresh-generation path let me design the mechanic properly rather than draw the under-specified backlog row as-is, I built exactly that — four independent, real deterministic navigation engines (vector-triangle current correction, cosine tide interpolation, COLREGS geometric classification, IALA buoyage rules) rather than a hand-authored vignette bank. This also directly answers the CLAUDE.md calibration note: every generated puzzle's correct answer comes from live computation against the same engine that validates the player's answer, never a hardcoded per-instance answer key.

## Connection to User Context

PROFILE.md names "boating" and "cottage life" explicitly under Personal interests and hobbies, and Category G alone has covered golf (Fairway Physics), running (implicitly via other categories), and markets (Quarter Call) — but zero of the 24 prior Game/Puzzle builds, and zero of the 92 builds catalog-wide, has touched boating. This is the first build in the catalog on that topic in any category.

## Why Tonight

Category G came up on tonight's 9-day rotation. Within G, the backlog's own rating notes on idea #33 (recorded 2026-08-20 and 2026-08-29) explicitly flagged this as "worth developing further into a concrete mechanic" — tonight's fresh-generation path (lottery missed) was the opportunity to do that properly instead of building the under-specified version.

## What I Hope the User Gets From This

1. Genuine, transferable seamanship skill — the set-and-drift correction-angle formula and the COLREGS give-way rules are real navigation content a boat owner would actually use, not flavor text wrapped around a generic quiz mechanic.
2. A puzzle game that never gets stale on replay — Voyage Mode and Practice Mode regenerate every round from the engines, unlike the catalog's five prior hand-authored-vignette-bank games (Confound Hunter, Heuristic Hunt, Synapse Sort, Neurofact, Lexicon), so there's no fixed content to memorize.
3. A daily 2-minute habit (Daily Challenge) tied to a hobby explicitly named in PROFILE.md that no prior build has served.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Data Detective — interactive statistical-anomaly-hunting game (click the outlier/Simpson's-paradox row in a live-manipulable dataset) | G | Genuinely different interaction model (data manipulation vs. multiple choice) but conceptually closer to Confound Hunter/Heuristic Hunt's "spot the methodological flaw" territory than a truly new domain; boating had a stronger, explicitly-named PROFILE.md tie with zero prior coverage anywhere in the catalog. |
| Diagnosis Duel — differential-diagnosis elimination game using classic lesion-symptom case literature (Phineas Gage-style cases), narrowing down a brain region via yes/no questions | G | Strong PROFILE.md tie to forensic/affective neuroscience, but CircuitLab (2026-07-13) already covers brain-region/circuit identification in the same Learning Aid space (different category, but same content domain), and an elimination-question mechanic is a lighter algorithmic lift than four real physics/geometry engines — less ambitious for a night with a clean 25%-miss fresh-generation slot. |
| Draw backlog idea #33 as originally scoped (generic boating trivia/navigation puzzle, no specified engine) | G | This is what tonight's build became once designed properly, but the original backlog row itself was explicitly under-specified per its own rating notes — building it required real design work, which fresh generation gave room to do rather than the lottery's as-written draw. |

Non-winning ideas (Data Detective, Diagnosis Duel) appended to `builds/ideas.md` as new pending rows.
