# Future Features — Macro Kitchen

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Diff view between plans** — `macro-kitchen diff <id1> <id2>` showing which meals changed and how the day-by-day macro totals moved, useful after re-running `generate` with a new Garmin import to see how much the training-load adjustment actually changed the week.
2. **CSV export of the grocery list** — `grocery <id> --csv out.csv` for pasting into a phone notes app or a grocery-delivery service's bulk-add field, instead of only terminal/HTML output.
3. **`--days N` flag on `generate`** — generate a 3-day or 14-day plan instead of a fixed 7, for people who shop more or less frequently.

## Medium Effort (roughly one nightly build session)

4. **Recipe favoriting and manual swap** — mark specific recipes as favorites so the planner weights them higher, and add a `swap <plan_id> <day> <slot> <new_recipe_id>` command to manually override a single generated meal without regenerating the whole week.
5. **Multi-week Garmin trend** — instead of only the most recent 7-day window, import a longer CSV export and track training load week-over-week, adjusting the calorie target on a rolling basis rather than a single-import snapshot.
6. **Grocery-list-to-pantry subtraction** — a simple `pantry add <item> <qty> <unit>` command that lets a user mark what they already have, so the generated grocery list only includes what's actually missing.

## Ambitious Extensions (multi-session effort)

7. **Recipe bank expansion with user-submitted recipes** — a `recipes add` command (with the same macro/ingredient schema as the curated bank) so a user's own go-to meals can enter the planner's rotation alongside the curated 54, closing the "only Claude's recipes" gap without needing a live recipe API (none is in PROFILE.md's Data Sources).
8. **Weekly review loop** — after a plan's week has passed, prompt for actual adherence (which meals were eaten vs. skipped/swapped) and feed that back into future portion-multiplier selection, so the planner learns which portion sizes this specific user tends to actually eat.

---

## Possible Integration Points

- **Run Planner** (2026-06-20) already computes weekly mileage from manually-logged runs; Macro Kitchen's Garmin CSV import is a second, independent source of the same kind of training-load signal. A future build could reconcile the two into one training-load service both tools read from — but per STANDARDS.md, that would need to be a new shared build, not an import from either existing build's folder.
- **Ledger Lens** (2026-07-08) already categorizes grocery-store spending from a bank CSV export. A future build could cross-reference Macro Kitchen's generated grocery list against Ledger Lens' "Groceries" category spend to show whether actual grocery spending tracks the planned list — again, as a new integration build, not a direct folder import.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Garmin CSV distance units aren't verified against the user's actual Garmin account unit setting (assumed km) | Add a `--units mi\|km` flag to `import-garmin`, or detect from a units column if Garmin's export includes one |
| Grocery aggregation keeps different units for the same ingredient as separate line items (e.g. "milk / ml" and "milk / cup" never merge) | Add a small hardcoded unit-conversion table for the ~10 units actually used in the recipe bank |
| Recipe bank is static — no live nutrition API backs it, so all macro figures are hand-estimated rather than lab-verified | Explore USDA FoodData Central once an API key can be added to PROFILE.md's Data Sources (currently not listed) |
| Portion multiplier is chosen purely to hit calorie/protein targets — it doesn't account for realistic serving-size ceilings (e.g. a 2x salad might be reasonable, a 2x steak may not be) | Add a per-recipe `max_multiplier` field so heavier dishes cap out lower than light ones |
| No handling for multi-person households (shopping/cooking for more than one person) | Add a `--servings N` global multiplier on top of the per-meal portion multiplier |
