# Why This? — GradeLine

> **Date:** 2026-09-11

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Category B (Productivity Utility) backlog held 2 pending rows (idea #39, SubmitCheck: journal formatting compliance checker; idea #40, Batch Release Notes Drafter), both unrated. `R=0` → `lottery_chance = min(75, 25 + 0*2) = 25%`. Rolled `random.randint(1,100)` → **41**. 41 > 25, so the lottery gate missed and generation moved to fresh ideas (Step 2d).

## The Decision

Both backlog rows were already own-noted as weaker candidates when logged (SubmitCheck needs hand-authored per-journal rules with no live, verifiable source inside this build container; Batch Release Notes Drafter would be an 11th build leaning on `GITHUB_TOKEN`, and GitHub-sourced tooling is already the single most repeated data source in this catalog). Rather than build either on a missed-lottery night, I generated fresh ideas targeting a PROFILE.md friction point with genuinely zero prior coverage: "Student evaluation workflows." The nearest existing build, ItemScope (2026-08-01), analyzes multiple-choice *item* psychometrics (p-values, discrimination) — it says nothing about grading written submissions, which is the far more time-consuming half of the same friction point for someone teaching courses like Stress and Coping and Social Affective Neuroscience.

## Connection to User Context

PROFILE.md names "Student evaluation workflows" verbatim under "Things you do manually that you suspect could be automated," alongside "Course material creation" (already covered by Lecture Loom and CaseForge) and "Grant writing" (covered by four prior builds). This is the specific friction point CLAUDE.md's category rotation happened to land on tonight that had not yet been built against, despite being named in the exact same profile section as those already-covered ones.

## Why Tonight

Day-of-year rotation (day 254 → `(254-1) % 9 = 1` → Category B). The lottery missing on both pending backlog rows freed this slot for a fresh idea rather than forcing a rebuild of a previously-deprioritized concept.

## What I Hope the User Gets From This

1. A faster, more consistent first pass on a stack of written student submissions — structural/citation compliance and near-duplicate flags surface before grading starts, not discovered mid-way through a stack.
2. A deterministic core the AI layer sits on top of rather than replaces — the failure mode CLAUDE.md's calibration note and several prior low-rated builds (AI Lecture Builder, 2/10; AI Session Context Bridge, 3/10) called out is a build whose only value is "prose a single Claude prompt could replicate." GradeLine's rubric-compliance scoring and TF-IDF similarity detection are real, independently verifiable algorithms with a value that exists with zero API key set.
3. A concrete, privacy-conscious pattern for handling student work with an optional AI layer (never sending the student's identity in the prompt) that could be reused by a future build touching any other named-student workflow (e.g. idea #29, Supervision Notebook, previously passed over for exactly the "requires manual entry" concern this design avoids by working off files the instructor already collects).

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Meeting Action Item Extractor — parses pasted lab/supervision meeting notes into tracked action items via a deterministic bullet/keyword rule engine, with an optional AI pass for ambiguous items | B | Real friction point ("Research administration," "Lab administration"), but its value depends entirely on the instructor manually pasting notes after every meeting — the same "requires manual entry to be useful" pattern that scored the 2026-06-06 AI Session Context Bridge build a 3/10 and that idea #29 (Supervision Notebook) was already passed over for on 2026-08-25. Logged to `builds/ideas.md` as a lower-priority candidate. |
| Course Accessibility Auditor — scans course materials (docx/pdf) for accessibility issues (missing alt text, heading structure, contrast) | B | Real, genuinely untouched angle, but would require adding third-party docx/pdf parsing dependencies for a first pass at something with less algorithmic depth than GradeLine's TF-IDF similarity engine and multi-check compliance scorer, and a narrower, more binary-checklist shape closer to a linter than a batch workflow tool. Logged to `builds/ideas.md` as a future Category B or H candidate. |
| SubmitCheck (backlog idea #39) | B | Passed over in its own 2026-09-02 note for needing hand-authored per-journal rules with no live, verifiable source inside this build container — that constraint hasn't changed tonight, and GradeLine's rubric format sidesteps it entirely by letting the instructor define their own compliance rules rather than the tool guessing a journal's. |
