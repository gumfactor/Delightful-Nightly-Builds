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
- [ ] No calls to paid or auth-required APIs unless credentials for that service are listed in PROFILE.md's Data Sources
- [ ] No sending user-entered or personal data to any third-party service
- [ ] Free, public, no-auth APIs may be used freely — prefer well-known services with stable, documented endpoints

### Completeness
- [ ] For categories A (Dashboard), E (Learning Aid), F (Data Explorer), G (Game), and I (Life Admin): the build includes a visual/interactive interface — a CLI that prints to stdout does not satisfy these categories
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
- [ ] Minimum 15 tests (every build is ambitious)
- [ ] All tests pass with zero failures (run the full test suite before committing)
- [ ] `BUILD_LOG.md` contains a test results entry: `Tests: X passed, Y failed`

### Documentation
- [ ] `Manual.md` exists for any build with a user interface

---

## Soft Standards (Deviations Must Be Documented in BUILD_LOG.md)

### Code Quality
- Use third-party packages freely when they raise quality or capability — pin versions in `requirements.txt` or `package.json`
- For builds using a bundler (Vite, webpack, etc.): install packages with `npm install` and declare them in `package.json` — do not mix CDN imports into a bundled project
- No unused imports, variables, or dead code
- Consistent indentation: 2 spaces for JS/HTML/CSS, 4 spaces for Python
- Meaningful variable names — no single-letter names except loop counters (`i`, `j`, `k`)
- No `console.log` or `print` debug statements in production code (use a `DEBUG` flag or structured logging)

### HTML/CSS/JS Builds
- CDN imports of well-known libraries are permitted and encouraged: Chart.js, D3.js, Plotly, Tailwind CSS, Alpine.js — no local fallback required
- CSS uses custom properties (variables) for colors and key spacing values
- Mobile-responsive: at minimum, does not break on narrow screens
- Accessible: semantic HTML elements, `alt` attributes on images, sufficient color contrast
- Dark/light mode considered even if only one is implemented
- Pin all dependency versions — exact version in CDN URLs (e.g. `chart.js@4.4.4`), exact or locked in `package.json`; commit `package-lock.json` when `npm install` is run
- If a build step is used, document the build command in `Manual.md`; `npm run build` must produce an artifact the user can open directly without a dev server

### Python Builds
- Type hints on all function signatures
- `if __name__ == "__main__":` guard in the entry point
- `requirements.txt` listing all third-party dependencies (leave empty only if truly stdlib-only)
- Common error cases handled gracefully (file not found, malformed input, wrong argument count)

### Node.js / React Builds
- `package.json` with accurate `name`, `version`, `description`, and `main` or `scripts.start`
- `.gitignore` note for `node_modules/` inside the build folder's README or PRD
- Lock file (`package-lock.json`) committed if `npm install` was actually run

### Testing
- Tests cover the happy path through the main user flow
- Edge case coverage reflects the actual complexity and risk of the logic — all meaningful failure modes have a test
- Test names are descriptive — reading them explains what the code does
- Tests are independent — each test sets up and tears down its own state
- Playwright tests use stable selectors (`data-testid` attributes preferred over CSS classes)
- No tests that `sleep` or use arbitrary timeouts — use proper async/await or Playwright's auto-waiting
- Python tests: use `pytest` fixtures for shared setup; avoid global state
- Tests live in `tests/` and can be run with a single command documented in `Manual.md`

### Scope Discipline
- If scope changed mid-build, document what was cut and why in a "Scope Changes" subsection of PRD.md
- Scope decisions must be deliberate. Push scope to the upper limit first; reduce only when necessary to ship something complete and genuinely useful rather than half-finished.
- Remove features that cannot be done correctly rather than shipping them broken
- FutureFeatures.md is for enhancements to a working, valuable thing — not for features required to make the build worth using. Those belong in tonight's scope
- Meeting the checklist is the floor. The goal is a build that is genuinely useful and well-executed

---

## Build Folder Structure Standard

```
builds/YYYY-MM-DD-title-slug/          ← Everything lives here
├── PRD.md                  ← Required always
├── WhyThis.md              ← Required always
├── BUILD_LOG.md            ← Required always
├── FutureFeatures.md       ← Required always
├── Manual.md               ← Required if any UI exists
├── package.json            ← React/Vite/Node builds
├── vite.config.js          ← If using Vite
├── playwright.config.js    ← If using Playwright (vanilla HTML/JS builds)
├── index.html              ← Entry point (vanilla builds at root; Vite builds at root too)
├── tests/                  ← All test files live here
│   ├── test_*.py           ← Python (pytest)
│   ├── *.spec.js           ← Playwright
│   └── *.test.js           ← Jest / Vitest
└── src/                    ← All source code lives here (components, modules, styles)
    ├── main.py             ← Python entry point
    ├── main.js / index.js  ← JS/Node entry point
    ├── App.jsx             ← React root component
    └── components/         ← React components, modules, etc.
```

Multi-file structure is the default for anything with meaningful complexity. Do not attempt to fit a React app or a multi-view dashboard into a single file.

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
7. The build delivers genuine value — the implementation is clean, real integrations are used where available, and tests verify meaningful behaviour
