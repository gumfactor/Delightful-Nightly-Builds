# FutureFeatures — Investment Research Notes

These are enhancements to a working, usable tool — not prerequisites for it.

---

## Quick Wins

**1. Tags / Custom Labels**
Let users add arbitrary tags to an entry (e.g., "dividend", "growth", "speculative", "catalyst-Q3"). Rendered as small chips on the card. Search already works; tags would extend the filtering surface.

**2. Thesis Last-Updated Indicator**
Show a visual indicator (e.g., amber dot or "stale" label) on cards that haven't been updated in > 90 days. Encourages keeping notes current as positions evolve.

**3. Sort Options**
Currently entries appear in add order. Add a sort control: by date added, last updated, symbol (A–Z), conviction (high → low), and status group. Store the preference in localStorage.

**4. Bulk Status Change**
Checkbox-select multiple cards and change their status in one action — useful when cleaning up a watchlist after earnings or a market event.

**5. Print / PDF Export**
A print-friendly stylesheet (or `window.print()` trigger) that renders all entries in a clean, two-column table layout for paper review or sharing.

---

## Medium Effort

**6. Entry History / Thesis Changelog**
Store up to N versions of thesis notes per entry with timestamps, so you can look back at how your thinking evolved over time. Would require a small schema migration for existing entries.

**7. Linked Price Annotations**
Optionally record the price at time of note-taking (manually entered) alongside conviction. Over time this builds a record of entry price awareness without requiring API access.

---

## More Ambitious

**8. Optional Price Fetch via Open APIs**
Hook into a free, no-auth market data API (e.g., Polygon free tier or Alpha Vantage) to display a current price alongside the symbol — purely additive, with a toggle and graceful failure if offline.

**9. CSV Export**
Export the current filtered view as a CSV file (symbol, name, sector, status, conviction, thesis first line, dates). Useful for pasting into a spreadsheet for further analysis.

**10. Browser Extension Clip**
A small browser extension that adds a "Research Note" button on financial sites (e.g., Seeking Alpha, IBKR). Clicking it pre-fills the symbol field in the app if it's open in another tab.
