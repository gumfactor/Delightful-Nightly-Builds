// Default shipped data — no real market data until you run fetch_data.py.
//
// The `typeof` guard means this file only sets PORTFOLIO_DATA to null when
// nothing else has already defined it (e.g. a test harness injecting a
// fixture via page.addInitScript before this script runs, or a real
// fetch_data.py run overwriting this exact file with real data — in which
// case that generated file's own unconditional assignment simply replaces
// this one on disk).
if (typeof window.PORTFOLIO_DATA === 'undefined') {
  window.PORTFOLIO_DATA = null;
}
