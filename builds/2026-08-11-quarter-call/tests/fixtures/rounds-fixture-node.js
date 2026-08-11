// Node-side accessor for the same fixture data the browser test harness loads,
// so test code can look up a round's real outcome by ticker without duplicating
// the dataset. Evaluates rounds-fixture.js (a classic `const ROUNDS_DATA = [...]`
// script) in an isolated VM context — it is never `require()`-able directly
// since it has no module.exports.
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const source = fs.readFileSync(path.join(__dirname, 'rounds-fixture.js'), 'utf8');
const sandbox = {};
vm.createContext(sandbox);
// Top-level `const` in a vm-executed script does not become a sandbox
// property (only `var`/function declarations do), so re-assign it onto
// the context's `this` (the global object of that context) explicitly,
// within the same script so the `const` is still in lexical scope.
vm.runInContext(source + '\nthis.ROUNDS_DATA = ROUNDS_DATA;', sandbox);

const ROUNDS_DATA = sandbox.ROUNDS_DATA;

module.exports = {
  all: ROUNDS_DATA,
  find(ticker) {
    const round = ROUNDS_DATA.find((r) => r.ticker === ticker);
    if (!round) throw new Error(`No fixture round found for ticker ${ticker}`);
    return round;
  },
};
