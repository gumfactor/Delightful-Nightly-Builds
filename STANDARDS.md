# STANDARDS.md — Build Quality Standards

> Every nightly build must pass ALL hard standards before being committed.
> Soft standards should be met; deviations must be documented in BUILD_LOG.md.
> Claude: treat this file as a checklist to execute, not documentation to absorb.

---

## Hard Standards (Violations Abort the Build)

### Safety & Reversibility
- [ ] All build output is entirely within `builds/YYYY-MM-DD-title-slug/`
- [ ] Files outside the build folder are limited to `builds/index.md` and, when the selection workflow requires it, `builds/ideas.md`
- [ ] No build file imports from, references, or modifies another build's folder
- [ ] No system-level operations (no `rm -rf`, no system file writes, no registry edits)
- [ ] No credentials, API keys, or passwords hardcoded in source files
- [ ] No personal data (real names, real emails, real addresses) hardcoded in code
- [ ] No external HTTP calls in the build scaffold itself (individual apps may make calls only to pre-configured services listed in PROFILE.md)

### Completeness
- [ ] `PRD.md` exists and all sections are filled — no `[YOUR ANSWER]` or `[TBD]` placeholders
- [ ] `WhyThis.md` exists, explains the specific rationale, and notes whether tonight's idea came from the lottery or fresh generation
- [ ] `BUILD_LOG.md` exists and has at least one entry per major phase
- [ ] `FutureFeatures.md` exists and has at least 5 concrete suggestions
- [ ] All code runs without modification (no broken imports, missing files, missing dependencies)
- [ ] `builds/index.md` has been updated with this build's entry (Category, Complexity, and blank `Your Rating` all filled)
- [ ] Non-winning fresh ideas have been appended to `builds/ideas.md` (fresh path only; not required for lottery draws)
- [ ] If the selected idea linked an Idea Brief, the brief was read before the build PRD and the PRD includes Idea Brief Traceability

### Tests
- [ ] At least one test file exists in a `tests/` subfolder
- [ ] Minimum test count met for complexity level (Focused: 5, Solid: 10, Ambitious: 15)
- [ ] All tests pass with zero failures (run the full test suite before committing)
- [ ] `BUILD_LOG.md` contains a test results entry: `Tests: X passed, Y failed`

### Documentation
- [ ] `Manual.md` exists for any build with a user interface
- [ ] Every function or class over 10 lines has a descriptive docstring or comment block

---

## Soft Standards (Deviations Must Be Documented in BUILD_LOG.md)

### Code Quality
- Prefer standard library over third-party dependencies
- No unused imports, variables, or dead code
- Consistent indentation: 2 spaces for JS/HTML/CSS, 4 spaces for Python
- Meaningful variable names — no single-letter names except loop counters (`i`, `j`, `k`)
- No `console.log` or `print` debug statements in production code (use a `DEBUG` flag or structured logging)

### HTML/CSS/JS Builds
- Must work in modern browsers without a build step (no compilation required)
- CSS uses custom properties (variables) for colors and key spacing values
- Mobile-responsive: at minimum, does not break on narrow screens
- No external CDN dependencies unless a local fallback is provided
- Accessible: semantic HTML elements, `alt` attributes on images, sufficient color contrast
- Dark/light mode considered even if only one is implemented

### Python Builds
- Type hints on all function signatures
- `if __name__ == "__main__":` guard in the entry point
- `requirements.txt` present even if empty (signals stdlib-only intent)
- Common error cases handled gracefully (file not found, malformed input, wrong argument count)

### Node.js / React Builds
- `package.json` with accurate `name`, `version`, `description`, and `main` or `scripts.start`
- `.gitignore` note for `node_modules/` inside the build folder's README or PRD
- Lock file (`package-lock.json`) committed if `npm install` was actually run

### Testing
- Tests cover the happy path through the main user flow
- Tests include at least one edge case (empty input, boundary values, invalid data)
- Test names are descriptive — reading them explains what the code does
- Tests are independent — each test sets up and tears down its own state
- Playwright tests use stable selectors (`data-testid` attributes preferred over CSS classes)
- No tests that `sleep` or use arbitrary timeouts — use proper async/await or Playwright's auto-waiting
- Python tests: use `pytest` fixtures for shared setup; avoid global state
- Tests live in `tests/` and can be run with a single command documented in `Manual.md`

### Scope Discipline
- If scope had to shrink mid-build, add a "Scope Changes" subsection to PRD.md explaining what was dropped and why
- A partial build done well is better than an ambitious build done poorly
- If a feature can't be done correctly, remove it rather than shipping it broken
- **Practical usefulness over theoretical usefulness** — FutureFeatures.md is for enhancements to a working, valuable thing. If a feature is required to make the build genuinely useful (not just interesting in concept), it must be part of the current build's scope. Ship something the user will actually open again, not something that requires a sequel to be worth using.

---

## Build Folder Structure Standard

```
builds/YYYY-MM-DD-title-slug/          ← Everything lives here
├── PRD.md                  ← Required always
├── WhyThis.md              ← Required always
├── BUILD_LOG.md            ← Required always
├── FutureFeatures.md       ← Required always
├── Manual.md               ← Required if any UI exists
├── index.html              ← Single-file web apps: place at folder root
├── playwright.config.js    ← If using Playwright (HTML/JS builds)
├── tests/                  ← All test files live here
│   ├── test_*.py           ← Python (pytest)
│   ├── *.spec.js           ← Playwright
│   └── *.test.js           ← Jest / Vitest
└── src/                    ← Multi-file builds: all code lives here
    ├── main.py             ← (or main.js, index.js, App.jsx, etc.)
    └── ...
```

For aborted builds:
```
builds/YYYY-MM-DD-title-slug/
└── ABORTED.md              ← This file only; no other files
```

---

## Security Checklist (Run Before Every Commit)

Search your own created files for these patterns before committing:

- [ ] No `.env` files committed
- [ ] No occurrences of: `password`, `api_key`, `secret`, `token`, `private_key` with real values assigned
- [ ] No `eval()` or `exec()` on user-controlled input
- [ ] No `innerHTML` assignments from user-controlled data (XSS vector)
- [ ] No `os.system()` or `subprocess` calls with user-controlled arguments (injection vector)
- [ ] No file path traversal: user input must never be used directly in file paths
- [ ] No code that reads from paths outside the build's own folder

---

## "Done" Definition

A build is complete when ALL of the following are true:

1. All hard standards pass (including tests)
2. The full test suite runs with zero failures
3. The code runs as described in `Manual.md` (or `PRD.md` if no Manual)
4. `BUILD_LOG.md` final entry reads: `Build complete. Success criteria reviewed. All tests passing.`
5. `builds/index.md` has been updated with this build's row
6. All changes are committed and pushed to the remote
