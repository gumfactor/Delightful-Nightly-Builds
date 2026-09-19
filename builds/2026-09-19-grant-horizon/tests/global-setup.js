// Regenerates the static dashboard HTML fixtures (via the real Python
// render.py) before the Playwright suite runs, so browser tests exercise
// the same template the CLI actually ships, never a hand-maintained copy.
const { execFileSync } = require('node:child_process');
const path = require('node:path');

module.exports = async function globalSetup() {
  execFileSync('python3', [path.join(__dirname, 'build_fixtures.py')], { stdio: 'inherit' });
};
