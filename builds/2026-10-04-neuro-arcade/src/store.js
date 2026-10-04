(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./tasks.js'));
  else root.NAStore = factory(root.NATasks);
})(typeof self !== 'undefined' ? self : this, function (Tasks) {
  const KEY = 'neuro-arcade.sessions.v1';
  const LABEL_KEY = 'neuro-arcade.label.v1';
  const HEADER = ['session_id', 'task', 'timestamp', 'label', 'seed', 'trial', 'condition', 'stimulus', 'response', 'correct', 'rt_ms'];
  const KNOWN_TASKS = ['stroop', 'nback', 'gonogo', 'ultimatum'];

  function storage() {
    try { return typeof localStorage !== 'undefined' ? localStorage : null; } catch (e) { return null; }
  }

  function load() {
    const store = storage();
    if (!store) return [];
    try {
      const parsed = JSON.parse(store.getItem(KEY) || '[]');
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      return [];
    }
  }

  function save(sessions) {
    const store = storage();
    if (!store) return false;
    try { store.setItem(KEY, JSON.stringify(sessions)); return true; } catch (e) { return false; }
  }

  function add(session) {
    const sessions = load();
    sessions.push(session);
    save(sessions);
    return sessions;
  }

  function clear() {
    const store = storage();
    if (store) { try { store.removeItem(KEY); } catch (e) { /* storage unavailable */ } }
  }

  function getLabel() {
    const store = storage();
    try { return (store && store.getItem(LABEL_KEY)) || 'me'; } catch (e) { return 'me'; }
  }

  function setLabel(label) {
    const store = storage();
    try { if (store) store.setItem(LABEL_KEY, label); } catch (e) { /* storage unavailable */ }
  }

  function escapeCell(value) {
    const text = value === null || value === undefined ? '' : String(value);
    return /[",\n\r]/.test(text) ? '"' + text.replace(/"/g, '""') + '"' : text;
  }

  function toCsv(sessions) {
    const rows = [HEADER.join(',')];
    sessions.forEach((s) => {
      s.trials.forEach((t) => {
        rows.push([s.id, s.task, s.ts, s.label, s.seed, t.n, t.condition, t.stimulus, t.response,
          t.correct === null || t.correct === undefined ? '' : t.correct, t.rt === null || t.rt === undefined ? '' : t.rt]
          .map(escapeCell).join(','));
      });
    });
    return rows.join('\n') + '\n';
  }

  function parseCsvRows(text) {
    const rows = [];
    let row = [];
    let cell = '';
    let inQuotes = false;
    for (let i = 0; i < text.length; i++) {
      const ch = text[i];
      if (inQuotes) {
        if (ch === '"' && text[i + 1] === '"') { cell += '"'; i++; }
        else if (ch === '"') inQuotes = false;
        else cell += ch;
      } else if (ch === '"') inQuotes = true;
      else if (ch === ',') { row.push(cell); cell = ''; }
      else if (ch === '\n' || ch === '\r') {
        if (ch === '\r' && text[i + 1] === '\n') i++;
        row.push(cell); cell = '';
        if (row.some((c) => c !== '')) rows.push(row);
        row = [];
      } else cell += ch;
    }
    if (inQuotes) throw new Error('Unterminated quoted field');
    row.push(cell);
    if (row.some((c) => c !== '')) rows.push(row);
    return rows;
  }

  // Rebuild sessions from trial rows; metrics are recomputed so the CSV is the source of truth.
  function fromCsv(text) {
    const rows = parseCsvRows(String(text));
    if (!rows.length || HEADER.some((name, i) => rows[0][i] !== name)) {
      throw new Error('Not a Neuro Arcade CSV: header does not match');
    }
    const sessions = new Map();
    rows.slice(1).forEach((cells, index) => {
      if (cells.length !== HEADER.length) throw new Error('Row ' + (index + 2) + ' has ' + cells.length + ' columns, expected ' + HEADER.length);
      const [id, task, ts, label, seed, n, condition, stimulus, response, correct, rt] = cells;
      if (!KNOWN_TASKS.includes(task)) throw new Error('Row ' + (index + 2) + ': unknown task "' + task + '"');
      if (!sessions.has(id)) sessions.set(id, { id, task, ts: Number(ts), label, seed: Number(seed), trials: [] });
      sessions.get(id).trials.push({
        n: Number(n), condition, stimulus,
        response: response === '' ? null : response,
        correct: correct === '' ? null : correct === 'true',
        rt: rt === '' ? null : Number(rt),
      });
    });
    return Array.from(sessions.values()).map((s) => Object.assign(s, { metrics: Tasks.score(s.task, s.trials) }));
  }

  // Add imported sessions whose id is not already present; returns counts
  function merge(existing, incoming) {
    const known = new Set(existing.map((s) => s.id));
    const fresh = incoming.filter((s) => !known.has(s.id));
    return { sessions: existing.concat(fresh), added: fresh.length, skipped: incoming.length - fresh.length };
  }

  return { KEY, HEADER, load, save, add, clear, getLabel, setLabel, toCsv, fromCsv, merge };
});
