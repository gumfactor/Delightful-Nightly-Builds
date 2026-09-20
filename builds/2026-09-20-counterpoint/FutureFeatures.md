# Future Features — Counterpoint

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **PDF export** — Render `letter.html` to PDF via a headless-print pass (e.g. `weasyprint` or a browser print-to-PDF), since many journal submission portals want a PDF attachment rather than HTML.
2. **`--diff` mode for `check`** — When re-running `check` after editing responses, show only what changed since the last run (which IDs newly became addressed/orphaned) instead of the full report every time.
3. **Word-count-per-response warning** — Flag any single response over a configurable length (e.g. 300 words) as a soft warning, since overly long individual responses are a common reviewer complaint.

## Medium Effort (roughly one nightly build session)

4. **DOCX manuscript line-number linking** — Parse a `.docx` manuscript with tracked changes and let a response reference `{{line:45}}` to auto-resolve to the actual current line number, so responses stay accurate even after further edits move content around.
5. **Journal-specific letter templates** — A small library of named-journal formatting conventions (heading style, reviewer numbering convention, required cover-letter boilerplate) selectable via `--template <journal>`, building on the same "check against a real standard" pattern used elsewhere in this catalog (Eligible Spend's Tri-Agency rules, Headroom's CRA tables).
6. **Multi-round history** — Track responses across multiple revision rounds (R1, R2, R3) in one project file, so a second-round response can reference "as noted in our first response to Comment 1.2" with the original text pulled in automatically.

## Ambitious Extensions (multi-session effort)

7. **Claude Code Skill wrapper** — Ship `skill/SKILL.md` so `/rebuttal-draft` can be invoked directly in a coding session against pasted reviewer comments, following the same "Skill as primary interface" pattern this catalog's Snipvault build (2026-08-12) established for developer tools — worth doing here since drafting a response letter is exactly the kind of occasional, high-friction task a Skill is meant to smooth over.
8. **Cross-reference with CiteForge** — When a response cites a new reference added during revision, validate that reference against CiteForge's (2026-09-02) formatting engine automatically, so citation-formatting and rebuttal-drafting share one pipeline instead of being separate manual steps.

---

## Possible Integration Points

- **CiteForge** (2026-09-02) — could validate any new references introduced in a response letter.
- **Voiceprint** (2026-07-28) — could run its AI-prose detector against `--ai`-polished responses before they're finalized, as a sanity check that the polish pass didn't drift into formulaic phrasing.
- **Panel Prep** (2026-08-08) — targets the pre-submission critique stage of the same publication pipeline; a future "Publication Pipeline" build could chain Panel Prep → submission → Counterpoint into one continuous tool.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| No manuscript cross-referencing | Add the DOCX line-linking feature above (#4) |
| Single revision round only | Add multi-round history tracking (#6) |
| Generic letter format only | Add journal-specific templates (#5) |
| CLI-only, no on-demand invocation inside a coding session | Ship the Skill wrapper (#7) |
