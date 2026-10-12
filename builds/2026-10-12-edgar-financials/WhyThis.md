# WhyThis

**Source:** lottery draw. Category F (day 285, (285-1) % 9 = 5). Pending F pool: 2 ideas (#1 Canada List CSV Quality Inspector, rated 7; #10 SEC EDGAR Financial History Extractor, unrated). One rated idea gives lottery_chance = min(75, 25 + 2) = 27%. Roll 21, so a draw. Tickets: #1 = 7, #10 = 5. Weighted pick landed on #10.

**Idea Brief:** none linked. No deviations from the backlog row; scope extended (cash flow, derived metrics, optional AI commentary).

**Why it earns a place:**
- Real data, no manual entry. SEC EDGAR needs no credentials, and the ratings history says mock/manual-entry builds score badly.
- Fixes a real annoyance: XBRL tags differ between companies and across years (revenue alone has five common tags, and ASC 606 changed which one is used). The tool normalises per year, so series do not have gaps where a company switched tags.
- Has a view layer (HTML report with comparison chart, sortable table, statements), which earlier CLI-only builds lacked.
- Topic diversity: finance has appeared in 5 of the last 10 builds, which is saturated. This build is justified as a data-engineering tool over a different source (filings, not prices), and no thesis/watchlist overlap. It is the only F-category candidate besides #1, which was not drawn.
- Not duplicated by the user's stack: yfinance gives prices and thin fundamentals; this gives audited 10-K history with restatement handling.

**Honest limits:** USD-only, annual-only, US-GAAP tag set; companies with unusual tags will show gaps rather than wrong numbers.
