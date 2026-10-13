# BUILD_LOG
- [08:20 UTC] Step 0: no incomplete builds. Day of year 286 → index 6 → category G. Lottery: pool of 2 finance ideas (#11, #12), R=0 → 25% chance, roll 46 → fresh ideas.
- [08:25 UTC] PRD, WhyThis written. Idea: Reviewer 2 flaw-spotting game.
- [08:35 UTC] Wrote cases.js (32 cases, 12 flaws), game.js, index.html, style.css, tests.
- Obstacle: `mkdir -p dir/{tests}` created a literal `{tests}` dir (empty, untracked, harmless); spec rewritten. A cleanup command with rm was blocked by the sandbox, left in place.
- Decision: Anthropic called directly from browser (anthropic-dangerous-direct-browser-access header) because the page has no backend; key kept in sessionStorage only.
- [08:50 UTC] Tests: 23 passed, 0 failed.
- Scope: PubMed ingestion cut (future).
Build complete. Success criteria reviewed. All tests passing.
