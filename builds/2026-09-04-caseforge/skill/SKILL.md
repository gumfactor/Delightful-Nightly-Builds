---
name: caseforge
description: Generate real-literature-grounded teaching case vignettes with discussion questions from live PubMed research, for use in course prep. Use when the user asks to build, generate, or prepare teaching cases, discussion cases, or class examples on a research topic.
---

# CaseForge

Generates classroom-ready teaching cases from real, live PubMed abstracts — each case includes a real citation, deterministically extracted methodological facts (sample size, effect size, p-value, methodology, population), and deterministic discussion questions grounded in those facts. An optional AI polish pass smooths the prose without ever being allowed to drop or invent a number.

## When to use this skill

The user asks something like:
- "Build me 3 discussion cases on stress and cortisol for my undergrad seminar"
- "Generate teaching cases on empathy and psychopathy for Social Affective Neuroscience"
- "Pull some real research on AI and mental health I can use in class"

## How to use it

This build lives in `builds/2026-09-04-caseforge/`. Run its CLI from that directory:

```bash
cd builds/2026-09-04-caseforge
python -m src.main generate --course "<course name>" --query "<PubMed search terms>" --n <count>
```

- `--course` — any course or unit name the user gives, used to tag and later filter the cases (e.g. `"Stress and Coping"`).
- `--query` — the PubMed search terms. Translate the user's natural-language topic into a few good keyword terms (e.g. "cortisol reactivity chronic stress adults").
- `--n` — how many cases to generate (default 3, max 50).
- `--ai-polish` — optional; requires `ANTHROPIC_API_KEY` set in the environment. Rewrites each vignette into smoother prose for `--register undergrad|graduate|public` (default `undergrad`) while a built-in safety check guarantees every extracted number still appears verbatim.
- `--force` — re-fetch and overwrite cases already in the library for the same PMIDs (normally skipped to avoid duplicates).

After generating, show the user the cases:

```bash
python -m src.main list --course "<course name>"
python -m src.main show <pmid>
python -m src.main export markdown --course "<course name>" --out cases.md
python -m src.main render --out cases.html
```

`render` produces a self-contained HTML dashboard (`cases.html`) the user can open directly in a browser — offer to open or share it after generating a batch.

## Notes

- PubMed's API requires outbound internet access; if the session's network is restricted, tell the user to run the command from their own machine.
- Never invent facts on the user's behalf — this skill only reports what the CLI actually extracted from real PubMed abstracts.
