# Future Features — Regex Dojo

## 1. Regex Flag Support
Allow the player to set flags (`i` for case-insensitive, `m` for multiline, `g` for global) via toggle buttons next to the input. Several compelling puzzles depend on flags — e.g., "match 'hello' regardless of case" only makes sense with the `i` flag. This would also teach a practical skill: knowing when flags are required.

## 2. Free-Play / Custom Level Editor
A panel where the user can paste in their own test strings and iteratively build a regex to match them — essentially turning the game into a live regex workbench. Patterns and test sets could be saved to localStorage by name and loaded back. This converts the game from a tutorial into a daily-use tool.

## 3. Solution Reveal After N Attempts
After the player has typed 5+ distinct patterns on the same level without solving it, offer a "Show Solution" button that reveals the intended pattern with an explanation of why each component is needed. This prevents frustration without removing the challenge.

## 4. Timed Challenge Mode
A secondary mode that runs all 20 levels back-to-back with a cumulative timer. Each level has a par time; under-par earns a star. Scores are stored in localStorage as a personal leaderboard. Gives replay value to users who have already completed all levels once.

## 5. Additional Level Packs
The core 20 levels cover the fundamentals; a second pack could target more advanced concepts:
- Named capture groups `(?<name>...)`
- Non-greedy quantifiers `+?`, `*?`
- Negative lookahead `(?!...)`
- Lookbehind assertions `(?<=...)` and `(?<!...)`
- Unicode property escapes `\p{L}` (ES2018+)
- Atomic groups and possessive quantifiers (where supported)

A level pack selector on the home screen would let users choose between "Fundamentals" (current) and "Advanced."

## 6. Clipboard & Share
After completing a level, show the solution regex and a "Copy" button. Also generate a sharable URL fragment (e.g., `?level=1&pattern=hello`) that loads the game with a specific level and pre-filled pattern — useful for sharing puzzle solutions or interesting regexes with colleagues.

## 7. Accessibility Improvements
Currently relies on color (green/red) to communicate pass/fail. Add `aria-live` regions so screen readers announce feedback changes. Replace color-only indicators with a redundant text label (✓ PASS / ✗ FAIL). Ensure keyboard-only navigation through the level select grid.
