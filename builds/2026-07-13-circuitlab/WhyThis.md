# Why This? — CircuitLab: Affective & Forensic Neuroscience Circuit Trainer

> **Date:** 2026-07-13

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Day of year 194 → `category_index = (194-1) % 9 = 4` → Category E — Learning Aid. `builds/ideas.md` (resynced from the most recent open PR branch, `claude/cool-sagan-595da6`, PR #39) has no `pending` rows in Category E, so per Step 2c the lottery pool was empty and generation went straight to Step 2d (fresh ideas) without a dice roll.

## The Decision

Category E has been built three times before (Spaced Repetition Flashcards 06-16, Stats Coach 06-25, Power Lab 07-04), and the last two were both statistics/research-methods trainers. Repeating that exact subject would be a topic-diversity failure even though the category rotation forces category E again. The preference prior (`builds/index.md`) shows the highest-rated build to date, Qualtrics Survey Data Inspector (9/10), succeeded because it solved a problem tied directly to the user's actual research workflow with real domain specificity — not a generic tool. The lowest-rated builds (AI Lecture Builder 2/10, Quick Data Profiler 1/10) failed either by being trivially replicable with a single Claude prompt or by duplicating existing tools. CircuitLab is built to land on the "domain-specific, hard to replicate in one prompt, genuinely testable recall tool" side of that pattern: a clickable, mastery-tracked brain diagram scoped to the exact regions and circuits the user's own research (empathy, psychopathy, stress) and teaching (Social Affective Neuroscience) cover, which a single chat message cannot produce.

## Connection to User Context

PROFILE.md names "Social Affective Neuroscience" and "forensic and affective neuroscience lab" directly, and lists "Empathy, psychopathy, and stress research" as a specific rabbit-hole topic. CircuitLab's region set (amygdala, vmPFC, insula, ACC, hippocampus, hypothalamus, OFC, STS, TPJ, ventral striatum, etc.) and its 6 named circuits (fear conditioning, cognitive reappraisal, empathy for pain, reward-based decision making, HPA-axis stress response, mentalizing) are drawn directly from the constructs those courses and that research program actually use, not a generic neuroscience-101 set.

## Why Tonight

Purely category-rotation driven (day 194 → E), with the specific idea chosen fresh because the Category E backlog was empty and the last two E builds (Stats Coach, Power Lab) had already covered general research-methods statistics — CircuitLab deliberately moves into neuroanatomy/circuit content instead, which no prior build has touched.

## What I Hope the User Gets From This

1. A genuinely useful drilling tool for the specific neuroanatomy and circuits their own lectures and research already center on — not a generic quiz.
2. A visible, persistent sense of mastery (color-coded diagram, per-region levels) that a static slide deck or flashcard app can't give.
3. An extensible base — the vignette engine and circuit-trace format could later absorb real case material from the forensic lab or course exams (see FutureFeatures.md).

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| AI Concepts for Psychologists — interactive lesson/quiz on LLM concepts (tokens, embeddings, agents) framed for the "AI Applications for Psychologists" course | E | Strong PROFILE.md fit, but closer to generic AI-literacy content available in many existing courses/tools; less differentiated than a tool built around the user's own specific, less-commonly-covered research domain. |
| Forensic Assessment Reasoning Trainer — branching scenario trainer for competency-to-stand-trial / risk-assessment style reasoning | E | Genuinely strong idea but scoped closer to a full clinical-training curriculum than one session can responsibly build with correct, defensible content; risks shipping oversimplified or misleading forensic-assessment logic. CircuitLab's vignette mode captures a lighter-weight version of the same "apply concept to case" value without that risk. |
| A third statistics/research-methods trainer (e.g. deeper power-analysis or multilevel-model explainer) | E | Would be the third Category E build in a row on statistics content; fails the topic-diversity intent even though it's a different specific tool from Stats Coach/Power Lab. |
