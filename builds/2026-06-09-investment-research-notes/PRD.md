# PRD — Investment Research Notes

## Goal
A local browser-based dashboard for capturing and organizing investment research notes — ticker by ticker — with status tracking, conviction ratings, sector tags, search, and JSON export/import.

## User Story
As someone actively researching individual stocks and other assets before deciding to buy or pass on IBKR, I want a single place to write thesis notes per ticker, tag my conviction level and watchlist/owned/passed status, and quickly surface notes when revisiting a name — without scattered documents or a subscription service.

## Scope

### In Scope
- Add, edit, and delete ticker entries with: symbol, company name, sector, status (watchlist / owned / passed), conviction rating (1–5), and free-text thesis notes
- Persist all data to `localStorage` — survives page reloads; no server required
- Filter entries by status (All / Watchlist / Owned / Passed)
- Live full-text search across symbol, company name, sector, and thesis
- Summary stats bar (total count + per-status counts)
- Export all entries as a dated JSON file for backup
- Import entries from a previously exported JSON file
- Responsive layout — works on mobile viewport

### Out of Scope
- Real-time price feeds or API calls to financial services
- Portfolio P&L tracking (IBKR handles this)
- Price history charts
- Multi-user sync or cloud storage
- Tags beyond sector and status

## Tech Stack
- Language: Vanilla HTML/CSS/JavaScript (ES2020)
- Framework: None — single self-contained `index.html`
- Storage: `localStorage`
- Tests: Playwright 1.x with Chromium
- Runtime requirement: Any modern browser (no build step)

## Data Structure
Each entry stored as a JSON object:
```json
{
  "id": "lk3abc9x2",
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "sector": "Technology",
  "status": "watchlist",
  "conviction": 4,
  "thesis": "Strong ecosystem ...",
  "dateAdded": "2026-06-09T08:00:00.000Z",
  "lastUpdated": "2026-06-09T08:00:00.000Z"
}
```
All entries stored as a JSON array at `localStorage` key `inv_research_entries`.

## Folder Structure
~~~
builds/2026-06-09-investment-research-notes/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── index.html                 ← single-file app with inlined CSS and JS
├── playwright.config.js
└── tests/
    └── research.spec.js       ← 15 Playwright tests
~~~

## Testing Strategy
- Framework: Playwright with Chromium
- Test file: `tests/research.spec.js`
- Approach: Each test navigates to `index.html` via a `file://` URL and clears `localStorage` via the `loadFreshPage()` helper for isolation
- Run command: `npx playwright test` (from build folder)
Tests cover:
1. Page loads with empty state message
2. Add modal opens
3. Can add an entry with all fields
4. Added entry appears in entry list
5. Stats update after adding entries
6. Filter by watchlist shows only watchlist entries
7. Filter by owned shows only owned entries
8. Search filters entries by symbol
9. Search filters entries by thesis text
10. Can edit an existing entry
11. Can delete an entry via confirm dialog
12. Export downloads the current entries as JSON
13. Import uploads JSON, confirms replacement, and updates the UI
14. Entry persists after page reload (localStorage)

## Success Criteria
1. All 15 Playwright tests pass with zero failures
2. Adding an entry saves it to `localStorage` and it survives a page reload
3. Filtering and search correctly show/hide cards without affecting stored data
4. Export produces a valid `.json` file containing all current entries
5. Import correctly restores entries from a previously exported file
