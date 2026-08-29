// Loads the pure-logic source files (no DOM) into a fresh V8 context so
// solver/generator/formatter tests can run directly under Node, without a browser.
const fs = require('fs');
const path = require('path');
const vm = require('vm');

function loadLogic() {
  const ctx = {};
  vm.createContext(ctx);
  ['data.js', 'logic.js'].forEach(function (file) {
    const code = fs.readFileSync(path.join(__dirname, '..', '..', 'src', file), 'utf8');
    vm.runInContext(code, ctx, { filename: file });
  });
  return ctx;
}

module.exports = { loadLogic };
