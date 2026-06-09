# Manual — Investment Research Notes

## What it does
A local browser app for capturing investment thesis notes by ticker. Add a company, write your thesis, tag it as Watchlist / Owned / Passed, rate conviction 1–5, then filter and search later when you're revisiting a name.

All data lives in your browser's `localStorage`. No server, no account, no internet required.

---

## How to open it
1. Open `index.html` directly in any modern browser (Chrome, Firefox, Safari, Edge).
   - On Mac/Linux: `open index.html` or double-click in Finder/Files
   - On Windows: double-click `index.html`
2. Bookmark the local path for quick access.

---

## Adding an entry
1. Click **+ Add Entry**
2. Fill in Symbol (auto-uppercased) and Company Name — both required
3. Choose Sector, Status (Watchlist / Owned / Passed), and Conviction (1 = low, 5 = very high)
4. Write your thesis notes in the text area
5. Click **Save Entry**

---

## Filtering and searching
- **Filter chips** (All / Watchlist / Owned / Passed) at the top narrow entries by status. The count next to each label updates in real time.
- **Search bar** filters across symbol, company name, sector, and thesis text simultaneously as you type.
- Filters compose: you can filter by "Owned" and then search within those results.

---

## Editing an entry
Click **Edit** on any card. The same modal opens pre-filled. Change any field and click **Save Entry**.

## Deleting an entry
Click **Delete** on the card, then confirm the dialog. Deletion is permanent.

---

## Export (backup)
Click **↓ Export** to download all entries as a dated JSON file (e.g., `investment-research-2026-06-09.json`). Store the backup anywhere — email it to yourself, put it in Dropbox, keep it with your financial docs.

## Import (restore)
Click **↑ Import**, select a previously exported `.json` file, and confirm. **This replaces all current entries** with the contents of the file. Use export first if you want to merge rather than replace.

---

## Data storage
- Stored in: `localStorage` key `inv_research_entries`
- Format: JSON array of entry objects
- Limit: localStorage is typically 5–10 MB; the app will hold thousands of entries comfortably
- Clearing browser data will erase entries — export regularly if you accumulate notes

---

## Running the tests

Requires Node.js and the local `@playwright/test` package (installed in `node_modules/`).

```bash
# From the builds/2026-06-09-investment-research-notes/ folder:
PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers npx playwright test
```

Expected result: **13 passed, 0 failed**

To run a single test:
```bash
PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers npx playwright test --grep "persists"
```
