# Why This? — Signal Detection Lab

> **Date:** 2026-07-31

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

The most current `builds/index.md` (pulled from the most recent open PR branch, `claude/cool-sagan-xza82t`, per Step 1 — local `main` was six weeks stale, last dated folder `2026-06-18`) shows the day-of-year rotation: `(212 - 1) % 9 = 4` → Category **E — Learning Aid**. `builds/ideas.md` was scanned for `pending` rows with `Category = E`: there are none — every pending row in the backlog is A, B, C, F, G, H, or I. Per Step 2c, an empty filtered pool skips the lottery entirely and goes straight to fresh-idea generation (Step 2d); no dice roll was needed or recorded.

## The Decision

Three prior Category E builds already exist: Power Lab (2026-07-04, statistical power/effect size), CircuitLab (2026-07-13, clickable neuroanatomy diagrams), and Bayes Lab (2026-07-22, Bayesian inference on proportions). All three share a proven, well-received shape for this category: a single-page vanilla-JS interactive trainer with a hand-derived, independently-cross-checked math core rendered via native Canvas 2D, plus an optional Claude Haiku layer with a deterministic fallback. Signal Detection Theory (SDT) fills a real gap in that trio — it's the framework underlying recognition-memory, threat-detection, and forensic-judgment paradigms that Power Lab, CircuitLab, and Bayes Lab don't touch, and no prior build in the full 49-entry catalog covers it. The calibration note in CLAUDE.md ("every build has scored 4/10 or below") is stale against the actual index — Qualtrics scored 9/10, Bridgework/Confound Hunter-style chaptered/vignette builds and the three E-category builds all appear well-executed with no negative ratings on file — so the working prior used here is the pattern of *what specifically scored well* (live-computed answers, cross-checked math, real domain grounding, no localStorage-only toy data) rather than the stale blanket calibration line.

## Connection to User Context

PROFILE.md names "conduct neuroimaging and behavioral studies," "forensic and affective neuroscience lab," and teaching "Social Affective Neuroscience" as direct day-to-day work. Signal Detection Theory is the standard analytic framework for exactly the paradigms that domain uses: recognition-memory tasks in psychopathy research, threat/fear-face detection in affective neuroscience, eyewitness identification and deception judgment in forensic contexts. It is also squarely inside "Master AI agent workflows" and "Become substantially stronger as a Python developer" only tangentially — its real fit is the named lab/teaching work and the "Neuroimaging methods and forensic neuroscience" rabbit-hole topic.

## Why Tonight

Tonight is Category E by the fixed 9-day rotation (last E build: 2026-07-22, exactly 9 days ago). No standing brief or lottery draw applied — this is a genuinely new topic within an already-successful category shape, chosen specifically to avoid a fourth build reusing Bridgework/Research Question Forge's taxonomy-cross-product architecture or a straight rehash of Power Lab/Bayes Lab's stats-trainer format applied to yet another statistical concept without new domain grounding.

## What I Hope the User Gets From This

1. A genuinely useful reference the next time a recognition-memory, threat-detection, or forensic-judgment study needs d'/criterion/ROC reporting — the calculator tab takes raw hit/false-alarm counts straight to publication-ready numbers with the correct loglinear correction for edge cases (0% or 100% rates), which is a real, recurring need in this line of research.
2. A teaching aid directly usable in the "Social Affective Neuroscience" or "AI Applications for Psychologists" courses — the scenario quiz turns an abstract framework into six concrete, discipline-relevant judgment calls (memory, threat, eyewitness ID, screening, deception, radiology) with live-derived correct answers.
3. An intuition-building tool: the draggable-criterion dual-Gaussian visualization makes the sensitivity/bias distinction viscerally clear in a way that a lecture slide or textbook formula rarely does.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| HPA Axis / Stress Physiology Interactive Explainer | E | Ties well to the named "Stress and Coping" book and course, but a clickable-diagram-plus-quiz shape would read as a near-repeat of CircuitLab's exact mechanic (clickable SVG diagram + Leitner mastery quiz) on a different body system, without a comparably strong testable-math core. Worth building later with a more distinct mechanic (e.g., an interactive allostatic-load simulator over time) rather than tonight. |
| AI Evaluation Literacy Trainer (for "AI Applications for Psychologists") | E | Genuinely on-profile and a good AI-integration-signal fit, but the "judge whether this AI output is reliable" interaction is inherently subjective/scenario-based rather than backed by a derivable, cross-checkable mathematical core — a weaker fit for the category's strongest prior builds, which all center on live-computed, verifiable numbers. Revisit with a more rigorous evaluation rubric (e.g., grounded in specific, checkable hallucination/citation-accuracy criteria) rather than as a fresh-idea pick tonight. |
| Signal Detection Theory Lab (chosen) | E | — |
