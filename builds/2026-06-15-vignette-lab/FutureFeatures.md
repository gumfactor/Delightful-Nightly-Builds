# Future Features — Vignette Lab

## Quick Wins

1. **Difficulty / arousal scaling flag** (`--intensity low|medium|high`)
   Each theme has three tiers of event severity. Low = mild stressor / brief discomfort;
   high = severe / crisis-level. Flag filters events by tier so researchers can create
   within-subject manipulations with matched narrative structure.

2. **JSON/CSV export** (`--format json|csv`)
   Export the generated vignette set as JSON (for programmatic use) or CSV (for direct
   Qualtrics survey block import). Each row/object has: `id, theme, narrative, prompt,
   check_1, check_2, researcher_note`.

3. **Demographic targeting** (`--age-range 18-25 --roles student,employee`)
   Filter the character pool by age bracket and/or role type so all vignettes in a batch
   match a specific study population profile.

4. **Custom element bank loader** (`--bank path/to/custom.yaml`)
   Allow researchers to supply their own YAML-formatted element banks, keeping the
   generation engine and CLI while making the content domain entirely configurable.

5. **Duplicate-guard across multiple runs**
   Persist a session log of previously generated vignettes (keyed by theme + character +
   event) so consecutive `generate` calls don't recycle the same combinations even
   across terminal sessions.

## Medium Effort

6. **Fourth theme: Social Exclusion** (Category D extension)
   A theme specifically for Cyberball-style ostracism paradigms and in-group/out-group
   research. Scenarios involve explicit or implicit rejection in social, academic, or
   workplace contexts — distinct from the empathy theme in that the protagonist is the
   target rather than the observer.

7. **Randomised Latin-square counterbalancing output**
   For experiments requiring counterbalanced vignette-to-condition assignment, generate
   a Latin-square assignment table alongside the vignettes, ready to paste into a
   Qualtrics flow or SPSS data file.

## Ambitious

8. **Anthropic API enhancement mode** (`--enhance`)
   When `ANTHROPIC_API_KEY` is set, pass each template-generated vignette through a
   brief Claude rewrite call to add natural language variation, improve narrative flow,
   and produce two or three surface-structure variants of each scenario (same meaning,
   different phrasing) — useful for stimulus norming studies.

9. **Norming data integration**
   Add a lightweight SQLite store for pilot study ratings (stress level, relatability,
   clarity) collected via a companion HTML rating page. `generate` can filter for
   vignettes rated above a threshold on pilot data, making it a genuine stimulus
   selection pipeline rather than just a generator.
