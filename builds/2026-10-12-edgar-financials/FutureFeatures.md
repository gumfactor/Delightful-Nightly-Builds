# Future Features

1. **Quarterly data and TTM.** Use 10-Q facts to build trailing-twelve-month figures so the latest year is never 11 months stale.
2. **Join with prices.** Pull yfinance prices and add P/E, P/FCF and EV/EBIT per year, plus a link to the Investment Thesis Journal entries.
3. **Custom-tag mapping file.** A user-editable JSON that maps company-specific XBRL tags (banks, insurers, REITs) to normalised metrics, with a report listing which metrics are missing per company.
4. **Foreign filers.** Handle IFRS (`ifrs-full`) and non-USD currencies with a currency column and optional conversion.
5. **Insider and filing feed.** Add Form 4 insider transactions and a filings timeline using the same client.
6. **Peer groups by SIC code.** `--peers AAPL` fetches same-SIC companies and ranks the target against them.
7. **MCP server wrapper.** Expose `get_financials(ticker, years)` as an MCP tool so Claude sessions can query normalised fundamentals directly.
8. **Restatement diff.** Show which historical values changed between original and amended filings.
