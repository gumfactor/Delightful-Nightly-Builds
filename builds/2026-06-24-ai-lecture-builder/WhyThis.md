# WhyThis — AI Lecture Builder

## Category and Date
Category D — Creative / Generative | 2026-06-24

## Lottery or Fresh?
**Fresh ideas.** No Category D ideas were pending in `builds/ideas.md`. Lottery skipped; went directly to Step 2d.

## Roll and Pool
- Pool size: 0 (no Category D ideas in backlog)
- Lottery skipped (pool empty)

## 3 Candidates Generated

1. **AI Lecture Builder** (selected) — Python CLI + HTML generator that calls Anthropic API to produce a complete lecture package (objectives, timed outline, hook, discussion questions, MCQs, key concepts, homework) for any course topic in seconds.

2. **AI Research Hypothesis Generator** — CLI that accepts a domain, variables, and research design, then uses Anthropic API to generate 5–10 testable hypotheses with rationale, null/alternative form, and suggested analysis approach. Useful for brainstorming study ideas or teaching research methods.

3. **Canada List Product Description Writer** — CLI that reads a CSV of Canadian businesses and uses Anthropic API to generate editorial descriptions, "Why Canadian?" snippets, and social media captions per entry. Directly serves The Canada List operations workflow.

## Why AI Lecture Builder Won

The user teaches 3 courses: Stress and Coping, Social Affective Neuroscience, and AI Applications for Psychologists. PROFILE.md explicitly lists "Course material creation" as a manual task they suspect could be automated. This build directly attacks that friction.

The Hypothesis Generator is genuinely useful but narrower — it helps with research design, which the user does less frequently than teaching prep. The Canada List tool is useful but purely operational (content generation for one project), not generalizable.

AI Lecture Builder wins on:
- **Frequency of use:** Every lecture cycle, which is multiple times per week during term
- **Time saved:** Replaces 2–3 hours of manual prep per lecture
- **AI differentiation:** Without the Anthropic API call, this is just a template — the AI layer is what makes each output substantively useful
- **Visual output:** Self-contained HTML with tabs, copy buttons, and print support — not a bare CLI

## Pattern Comparison vs Previous D Build
The 2026-06-15 Vignette Lab (Category D) was a combinatorial generator using element banks — no AI, no live data, CLI output to markdown. AI Lecture Builder is differentiated: live Anthropic API call, structured JSON response, visual HTML viewer, and broader applicability (3 courses vs. scenario generation specifically).

## Why This Scores Better Than Average
The consistent 4/10-and-below pattern comes from (a) no visual interface, (b) mock data, (c) redundancy with existing tools. AI Lecture Builder addresses all three:
- Has a visual HTML output with navigation and copy/export features
- Uses real Anthropic API (not mock content)
- Is not replicated by any tool the user currently has — ChatGPT can do this on demand but there's no structured workflow, no output format, no direct-to-file delivery
