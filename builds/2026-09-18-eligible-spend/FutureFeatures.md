# Future Features — Eligible Spend

> Ideas for extending this build. The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Per-category subtotal breakdown** — Add a second bar chart or table section grouping flagged $ by `category` (not just by verdict), so a user with many small hospitality line items can see the category driving the flags, not just the aggregate.
2. **`--strict` mode** — A flag that also flags any line item with a justification shorter than N words as `requires_justification`, for users who want a harder bar than "any text at all."
3. **Markdown export** — A `--format markdown` option that writes the flagged-items summary as a Markdown table, ready to paste into a grant-office email or a lab wiki page.

## Medium Effort (roughly one nightly build session)

4. **Institution overhead-rate layer (opt-in, separate module)** — A second, clearly-labeled module where the user supplies their own institution's negotiated overhead percentage (never assumed or looked up), so the tool can also flag budgets that don't correctly separate direct vs. indirect costs — kept as an explicit add-on so the core tool's public-data-only guarantee stays intact.
5. **Historical run comparison** — Persist each run's verdict counts to local SQLite (same pattern as Rotation Radar/Headroom) so re-running against a revised budget shows "3 fewer ineligible items than last run," useful across the multiple budget-revision passes a real grant application goes through.
6. **CIHR/SSHRC-specific directive variants** — The three agencies share TAGFA but each publishes agency-specific program notices with additional rules (e.g. CIHR's specific rules on participant compensation). A per-agency rule pack, selected with `--agency nserc|cihr|sshrc`, would sharpen accuracy for a specific competition.

## Ambitious Extensions (multi-session effort)

7. **Grant application budget-builder integration** — Instead of checking a finished CSV, let the user build the budget interactively in the dashboard (add/edit line items in the browser, re-check live), turning this from a post-hoc checker into the actual budget-drafting tool.
8. **Multi-institution comparison mode** — For collaborative grants spanning institutions, accept multiple budgets tagged by institution and flag items that would need different institutional-overhead treatment at each site, without ever computing the overhead numbers itself.

---

## Possible Integration Points

- **Headroom** (2026-09-09) established the pattern this build reuses (hand-encoded, web-search-verified Canadian public rules tables + optional AI layer with a deterministic fallback) — a future "Canadian Research Admin Suite" could share a common rules-table format between the two.
- **GradeLine** (2026-09-11) ships a companion Claude Code Skill for a repeated workflow; if grant budget checks become a recurring per-application task, a `/budget-check` Skill wrapping this CLI would fit the same pattern.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Keyword rules can't catch every phrasing of an ineligible expense | Add the optional `--ai` layer as the primary classifier (not just a review note) once the deterministic rules are proven against more real budgets |
| No overhead-rate math at all | Ship as the separate opt-in module described in Quick Win #4, never folded into the core public-data-only engine |
| No persistence across runs | Add the SQLite run-history layer described in Medium Effort #5 |
