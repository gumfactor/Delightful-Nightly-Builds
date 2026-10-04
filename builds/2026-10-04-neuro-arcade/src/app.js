(function () {
  const Stats = window.NAStats;
  const Tasks = window.NATasks;
  const Store = window.NAStore;

  const params = new URLSearchParams(window.location.search);
  const FAST = params.has('fast');
  const TEST = params.has('test');
  const TRIAL_OVERRIDE = parseInt(params.get('trials') || '', 10) || 0;
  const ms = (value) => (FAST ? Math.max(20, Math.round(value / 3)) : value);

  // Response windows shrink less than delays so scripted players have time to answer in fast mode
  const windowMs = (value) => (FAST ? Math.round(value / 1.5) : value);
  const sleep = (delay) => new Promise((resolve) => setTimeout(resolve, delay));
  const nextFrame = () => new Promise((resolve) => requestAnimationFrame(() => resolve()));

  function h(tag, attrs, ...children) {
    const el = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([key, value]) => {
      if (key === 'class') el.className = value;
      else if (key.startsWith('on')) el.addEventListener(key.slice(2), value);
      else el.setAttribute(key, value);
    });
    children.flat().forEach((child) => {
      if (child === null || child === undefined || child === false) return;
      el.append(child.nodeType ? child : document.createTextNode(String(child)));
    });
    return el;
  }

  const SVG_NS = 'http://www.w3.org/2000/svg';
  function svg(tag, attrs) {
    const el = document.createElementNS(SVG_NS, tag);
    Object.entries(attrs || {}).forEach(([key, value]) => el.setAttribute(key, value));
    return el;
  }

  // ---------- task runner ----------

  let run = null;

  function respondWith(value) {
    if (!run || !run.pending) return;
    const pending = run.pending;
    run.pending = null;
    clearTimeout(pending.timer);
    pending.resolve({ response: value, rt: Math.round((performance.now() - run.onset) * 10) / 10 });
  }

  function waitResponse(timeoutMs) {
    return new Promise((resolve) => {
      const pending = { resolve, timer: null };
      if (timeoutMs) {
        pending.timer = setTimeout(() => {
          run.pending = null;
          resolve({ response: null, rt: null });
        }, timeoutMs);
      }
      run.pending = pending;
    });
  }

  function abortRun() {
    if (!run) return;
    run.abort = true;
    if (run.pending) {
      clearTimeout(run.pending.timer);
      run.pending.resolve({ response: null, rt: null });
      run.pending = null;
    }
  }

  document.addEventListener('keydown', (event) => {
    if (!run) return;
    if (event.key === 'Escape') { abortRun(); return; }
    if (event.repeat) return;
    const response = run.keymap[event.key.toLowerCase()];
    if (response) {
      event.preventDefault();
      respondWith(response);
    }
  });

  function fixation() {
    return h('div', { class: 'fixation', 'aria-hidden': 'true' }, '+');
  }

  async function showStimulus(stage, nodes) {
    nodes.forEach((node) => node.setAttribute('data-trial', String(run.trialIndex)));
    stage.replaceChildren(...nodes);
    await nextFrame();
    run.onset = performance.now();
  }

  const DEFS = {
    stroop: {
      count: 48,
      keymap: { r: 'red', g: 'green', b: 'blue', y: 'yellow' },
      buttons: Tasks.COLOURS.map((c) => [c, c[0].toUpperCase() + c.slice(1) + ' (' + c[0].toUpperCase() + ')']),
      instructions: [
        'A colour word appears in coloured ink. Respond to the INK colour, not the word.',
        'Keys: R red, G green, B blue, Y yellow, or tap the buttons. Be fast and accurate.',
        'Four practice trials with feedback come first, then 48 scored trials.',
      ],
      build: (count, rng) => Tasks.stroopTrials(count, rng),
      practice: (rng) => Tasks.stroopTrials(4, rng),
      async trial(spec, stage, isPractice) {
        stage.replaceChildren(fixation());
        await sleep(ms(500));
        const word = h('div', { class: 'stroop-word', 'data-testid': 'stimulus', 'data-word': spec.word, 'data-ink': spec.ink }, spec.word.toUpperCase());
        word.style.color = 'var(--ink-' + spec.ink + ')';
        await showStimulus(stage, [word]);
        const result = await waitResponse(windowMs(3000));
        const correct = result.response !== null && result.response === spec.ink;
        if (isPractice && !run.abort) {
          stage.replaceChildren(h('div', { class: 'feedback' }, correct ? 'Correct' : result.response === null ? 'Too slow' : 'Wrong'));
          await sleep(ms(500));
        }
        return { condition: spec.condition, stimulus: spec.word + '/' + spec.ink, response: result.response, correct, rt: result.rt };
      },
    },
    nback: {
      count: 40,
      keymap: { ' ': 'press', m: 'press' },
      buttons: [['press', 'Match (space)']],
      instructions: [
        'Letters appear one at a time. Press when the current letter is the same as the one TWO letters earlier.',
        'Space bar, M, or the button. Do nothing when it does not match. About 3 in 10 letters are matches.',
        'You get 2 seconds per letter; the letter itself shows for half a second.',
      ],
      build: (count, rng) => Tasks.nbackSequence(count, 2, rng, 0.3),
      async trial(spec, stage) {
        const letter = h('div', { class: 'letter', 'data-testid': 'stimulus', 'data-letter': spec.letter }, spec.letter);
        if (TEST) letter.setAttribute('data-target', String(spec.isTarget));
        await showStimulus(stage, [letter]);
        const started = performance.now();
        if (!TEST) setTimeout(() => stage.replaceChildren(fixation()), ms(500));
        const result = await waitResponse(windowMs(2000));
        const remaining = windowMs(2000) - (performance.now() - started);
        if (remaining > 0 && !run.abort) await sleep(remaining);
        return {
          condition: spec.isTarget ? 'target' : 'nontarget', stimulus: spec.letter,
          response: result.response, correct: (result.response === 'press') === spec.isTarget, rt: result.rt,
        };
      },
    },
    gonogo: {
      count: 60,
      keymap: { ' ': 'press' },
      buttons: [['press', 'GO (space)']],
      instructions: [
        'Press as fast as you can when a GREEN CIRCLE appears.',
        'Do NOT press when a RED SQUARE appears. About 1 in 4 trials is a red square.',
        'Space bar or the button.',
      ],
      build: (count, rng) => Tasks.goNoGoTrials(count, rng, 0.25),
      async trial(spec, stage, isPractice, rng) {
        stage.replaceChildren(fixation());
        await sleep(ms(400 + Math.floor(rng() * 400)));
        const shape = h('div', {
          class: spec.kind === 'go' ? 'shape-go' : 'shape-nogo', 'data-testid': 'stimulus', 'data-kind': spec.kind,
          role: 'img', 'aria-label': spec.kind === 'go' ? 'Green circle' : 'Red square',
        });
        await showStimulus(stage, [shape]);
        const started = performance.now();
        if (!TEST) setTimeout(() => stage.replaceChildren(fixation()), ms(500));
        const result = await waitResponse(windowMs(1000));
        const remaining = windowMs(1000) - (performance.now() - started);
        if (remaining > 0 && !run.abort) await sleep(remaining);
        return {
          condition: spec.kind, stimulus: spec.kind === 'go' ? 'green_circle' : 'red_square',
          response: result.response, correct: (result.response === 'press') === (spec.kind === 'go'), rt: result.rt,
        };
      },
    },
    ultimatum: {
      count: 20,
      keymap: { a: 'accept', r: 'reject' },
      buttons: [['accept', 'Accept (A)'], ['reject', 'Reject (R)']],
      instructions: [
        'Another player has $10 and proposes how to split it. If you accept, you both get the split. If you reject, you both get nothing.',
        'Keys: A accept, R reject. There are no wrong answers. The proposer is simulated and every offer is random from $1 to $5.',
        'Nothing is paid out; this measures how you trade fairness against money.',
      ],
      build: (count, rng) => Tasks.ultimatumOffers(count, rng),
      async trial(spec, stage) {
        const offer = h('div', { class: 'split', 'data-testid': 'offer', 'data-offer': String(spec.offer) },
          h('span', {}, 'You get $' + spec.offer), h('span', { class: 'muted' }, 'They keep $' + (spec.pool - spec.offer)));
        await showStimulus(stage, [h('p', {}, 'Player 2 proposes:'), offer]);
        const result = await waitResponse(0);
        if (!run.abort) {
          stage.replaceChildren(h('div', { class: 'feedback' }, result.response === 'accept' ? 'Accepted' : 'Rejected'));
          await sleep(ms(500));
        }
        return { condition: 'offer_' + spec.offer, stimulus: String(spec.offer), response: result.response, correct: null, rt: result.rt };
      },
    },
  };

  const overlay = document.getElementById('overlay');
  const overlayBody = document.getElementById('overlay-body');

  function openOverlay(...nodes) {
    overlayBody.replaceChildren(...nodes);
    overlay.hidden = false;
  }

  function closeOverlay() {
    overlay.hidden = true;
    overlayBody.replaceChildren();
    renderAll();
  }

  function waitForClick(button) {
    return new Promise((resolve) => button.addEventListener('click', () => resolve(), { once: true }));
  }

  async function startTask(key) {
    const def = DEFS[key];
    const info = Tasks.TASK_INFO[key];
    const seed = Math.floor(Math.random() * 2147483647);
    const rng = Tasks.makeRng(seed);
    const specs = def.build(TRIAL_OVERRIDE || def.count, rng);
    const practiceSpecs = def.practice && !TRIAL_OVERRIDE ? def.practice(rng) : [];

    const startButton = h('button', { class: 'primary', 'data-testid': 'start-task' }, 'Start');
    const cancelButton = h('button', { class: 'secondary', 'data-testid': 'cancel-task' }, 'Back');
    openOverlay(h('h2', {}, info.title), h('p', { class: 'muted' }, info.construct),
      h('ul', {}, def.instructions.map((line) => h('li', {}, line))),
      h('div', { class: 'row' }, startButton, cancelButton));
    startButton.focus();
    const choice = await Promise.race([
      waitForClick(startButton).then(() => 'start'), waitForClick(cancelButton).then(() => 'cancel')]);
    if (choice === 'cancel') { closeOverlay(); return; }

    const progress = h('span', { class: 'muted', 'data-testid': 'trial-progress' }, '');
    const quit = h('button', { class: 'secondary', 'data-testid': 'quit-task' }, 'Quit (Esc)');
    const stage = h('div', { class: 'stage', 'data-testid': 'stage', 'aria-live': 'off' });
    const controls = h('div', { class: 'controls' }, def.buttons.map(([value, text]) => {
      const button = h('button', { 'data-resp': value, 'data-testid': 'resp-' + value }, text);
      button.addEventListener('pointerdown', (event) => { event.preventDefault(); respondWith(value); });
      return button;
    }));
    quit.addEventListener('click', abortRun);
    openOverlay(h('div', { class: 'play-head' }, h('strong', {}, info.title), progress, quit), stage, controls);

    run = { abort: false, pending: null, keymap: def.keymap, onset: 0, trialIndex: 'p' };
    stage.replaceChildren(h('div', { class: 'feedback' }, 'Get ready'));
    await sleep(ms(700));

    for (let i = 0; i < practiceSpecs.length && !run.abort; i++) {
      progress.textContent = 'Practice ' + (i + 1) + '/' + practiceSpecs.length;
      await def.trial(practiceSpecs[i], stage, true, rng);
    }
    const trials = [];
    for (let i = 0; i < specs.length && !run.abort; i++) {
      progress.textContent = 'Trial ' + (i + 1) + '/' + specs.length;
      run.trialIndex = i + 1;
      const record = await def.trial(specs[i], stage, false, rng);
      if (run.abort) break;
      trials.push(Object.assign({ n: i + 1 }, record));
    }
    const aborted = run.abort;
    run = null;
    if (aborted) { closeOverlay(); return; }

    const session = {
      id: key + '-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 6),
      task: key, ts: Date.now(), label: Store.getLabel(), seed, trials,
    };
    session.metrics = Tasks.score(key, trials);
    Store.add(session);
    showSummary(session);
  }

  function showSummary(session) {
    const info = Tasks.TASK_INFO[session.task];
    const again = h('button', { class: 'primary', 'data-testid': 'play-again' }, 'Play again');
    const done = h('button', { class: 'secondary', 'data-testid': 'close-summary' }, 'Close');
    again.addEventListener('click', () => { closeOverlay(); startTask(session.task); });
    done.addEventListener('click', closeOverlay);
    openOverlay(h('div', { 'data-testid': 'summary' }, h('h2', {}, info.title + ' complete'),
      metricsBlock(session), h('div', { class: 'row' }, again, done)));
  }

  // ---------- metric display ----------

  function formatMetric(def, value) {
    if (value === null || value === undefined) return 'n/a';
    const shown = def.scale ? Math.round(value * def.scale) : value;
    return shown + (def.unit ? (def.unit === '%' ? '%' : ' ' + def.unit) : '');
  }

  function referenceBar(def, value) {
    const lo = def.ref.mean - 3 * def.ref.sd;
    const hi = def.ref.mean + 3 * def.ref.sd;
    const x = (v) => 300 * Math.min(1, Math.max(0, (v - lo) / (hi - lo)));
    const chart = svg('svg', { viewBox: '0 0 300 40', role: 'img',
      'aria-label': def.label + ' compared with reference range' });
    chart.append(svg('rect', { class: 'band2', x: x(def.ref.mean - 2 * def.ref.sd), y: 12, width: x(def.ref.mean + 2 * def.ref.sd) - x(def.ref.mean - 2 * def.ref.sd), height: 16, rx: 4 }));
    chart.append(svg('rect', { class: 'band1', x: x(def.ref.mean - def.ref.sd), y: 12, width: x(def.ref.mean + def.ref.sd) - x(def.ref.mean - def.ref.sd), height: 16, rx: 4 }));
    chart.append(svg('line', { class: 'refmark', x1: x(def.ref.mean), x2: x(def.ref.mean), y1: 8, y2: 32 }));
    if (value !== null && value !== undefined) chart.append(svg('circle', { class: 'marker', cx: x(value), cy: 20, r: 7 }));
    return chart;
  }

  function metricBlock(def, value) {
    let verdict;
    if (value === null || value === undefined) verdict = 'Not enough valid trials to score this.';
    else if (def.higherBetter === null) {
      verdict = 'Reference sample rejects about ' + Math.round(def.ref.mean * 100) + '% of unfair offers. Neither answer is better; it shows how you weigh fairness against money.';
    } else {
      const below = Stats.percentile(value, def.ref.mean, def.ref.sd);
      const better = def.higherBetter ? below : 1 - below;
      verdict = 'Better than about ' + Math.round(better * 100) + '% of the reference sample.';
    }
    return h('div', { class: 'metric', 'data-testid': 'metric-' + def.key },
      h('div', { class: 'muted' }, def.label),
      h('div', { class: 'metric-value', 'data-testid': 'metric-value' }, formatMetric(def, value)),
      referenceBar(def, value), h('div', { class: 'muted' }, verdict));
  }

  function metricsBlock(session) {
    const info = Tasks.TASK_INFO[session.task];
    return h('div', {}, info.metrics.map((def) => metricBlock(def, session.metrics[def.key])),
      session.task === 'ultimatum' ? acceptBars(session.metrics.acceptByOffer) : null,
      h('p', { class: 'muted' }, 'Reference ranges are approximate teaching values, not clinical norms.'));
  }

  function acceptBars(acceptByOffer) {
    return h('div', { class: 'bars', 'data-testid': 'accept-bars' },
      h('div', { class: 'muted' }, 'Acceptance rate by offer'),
      acceptByOffer.map((row) => h('div', { class: 'bar-row' }, h('span', {}, '$' + row.offer),
        h('div', { class: 'bar-track' }, h('div', { class: 'bar-fill', style: 'width:' + Math.round(row.rate * 100) + '%' })),
        h('span', {}, Math.round(row.rate * 100) + '%'))));
  }

  function sparkline(values) {
    const chart = svg('svg', { viewBox: '0 0 300 40', role: 'img', 'aria-label': 'History of ' + values.length + ' sessions' });
    if (values.length < 2) return chart;
    const lo = Math.min(...values);
    const hi = Math.max(...values);
    const span = hi - lo || 1;
    const points = values.map((v, i) => (i * 296 / (values.length - 1) + 2) + ',' + (36 - ((v - lo) / span) * 32)).join(' ');
    chart.append(svg('polyline', { class: 'spark', points }));
    return chart;
  }

  // ---------- views ----------

  function renderPlay() {
    const view = document.getElementById('view-play');
    view.replaceChildren(h('p', { class: 'muted' }, 'Four classic paradigms from experimental psychology. Each takes 1 to 3 minutes.'),
      h('div', { class: 'grid' }, Object.keys(Tasks.TASK_INFO).map((key) => {
        const info = Tasks.TASK_INFO[key];
        const played = Store.load().filter((s) => s.task === key).length;
        const button = h('button', { class: 'primary', 'data-testid': 'play-' + key }, 'Play ' + info.title);
        button.addEventListener('click', () => startTask(key));
        return h('div', { class: 'card', 'data-testid': 'task-card-' + key },
          h('span', { class: 'tag' }, info.construct), h('h2', {}, info.title),
          h('p', { class: 'muted' }, info.blurb), h('p', { class: 'muted' }, played + ' session' + (played === 1 ? '' : 's') + ' saved'), button);
      })));
  }

  function renderResults() {
    const view = document.getElementById('view-results');
    const sessions = Store.load();
    view.replaceChildren(h('div', { class: 'grid' }, Object.keys(Tasks.TASK_INFO).map((key) => {
      const info = Tasks.TASK_INFO[key];
      const mine = sessions.filter((s) => s.task === key).sort((a, b) => a.ts - b.ts);
      const card = h('div', { class: 'card', 'data-testid': 'results-' + key }, h('h2', {}, info.title));
      if (!mine.length) {
        card.append(h('p', { class: 'muted' }, 'Not played yet.'));
        return card;
      }
      const latest = mine[mine.length - 1];
      const primary = info.metrics[0];
      card.append(h('p', { class: 'muted' }, mine.length + ' session' + (mine.length === 1 ? '' : 's') + '. Latest: ' + new Date(latest.ts).toLocaleString()),
        metricsBlock(latest));
      const series = mine.map((s) => s.metrics[primary.key]).filter((v) => v !== null && v !== undefined);
      if (series.length > 1) card.append(h('div', { class: 'muted' }, primary.label + ' over time'), sparkline(series));
      return card;
    })));
  }

  function classRows(sessions) {
    const labels = Array.from(new Set(sessions.map((s) => s.label))).sort();
    return labels.map((label) => {
      const cells = Object.keys(Tasks.TASK_INFO).map((key) => {
        const primary = Tasks.TASK_INFO[key].metrics[0];
        const mine = sessions.filter((s) => s.label === label && s.task === key);
        const values = mine.map((s) => s.metrics[primary.key]).filter((v) => v !== null && v !== undefined);
        const average = Stats.mean(values);
        return average === null ? '' : formatMetric(primary, average) + ' (' + mine.length + ')';
      });
      return { label, cells };
    });
  }

  function setStatus(text, kind) {
    const el = document.getElementById('data-status');
    if (el) { el.textContent = text; el.className = 'status ' + kind; }
  }

  function downloadCsv() {
    const blob = new Blob([Store.toCsv(Store.load())], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = h('a', { href: url, download: 'neuro-arcade-' + new Date().toISOString().slice(0, 10) + '.csv' });
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    setStatus('Exported ' + Store.load().length + ' sessions.', 'ok');
  }

  async function importCsv(file) {
    if (!file) return;
    try {
      const incoming = Store.fromCsv(await file.text());
      const result = Store.merge(Store.load(), incoming);
      Store.save(result.sessions);
      renderAll();
      setStatus('Imported ' + result.added + ' new sessions, skipped ' + result.skipped + ' already present.', 'ok');
    } catch (error) {
      setStatus('Import failed: ' + error.message, 'error');
    }
  }

  function renderData() {
    const view = document.getElementById('view-data');
    const sessions = Store.load();
    const label = h('input', { type: 'text', maxlength: '24', value: Store.getLabel(), 'data-testid': 'label-input', 'aria-label': 'Participant label' });
    label.addEventListener('input', () => Store.setLabel(label.value.trim() || 'me'));
    const fileInput = h('input', { type: 'file', accept: '.csv,text/csv', 'data-testid': 'import-csv', 'aria-label': 'Import CSV' });
    fileInput.addEventListener('change', () => importCsv(fileInput.files[0]));
    const exportButton = h('button', { class: 'primary', 'data-testid': 'export-csv' }, 'Export CSV');
    exportButton.addEventListener('click', downloadCsv);
    const clearButton = h('button', { class: 'danger', 'data-testid': 'clear-data' }, 'Delete all data');
    clearButton.addEventListener('click', () => {
      if (!window.confirm('Delete all saved sessions from this browser?')) return;
      Store.clear();
      renderAll();
      setStatus('All sessions deleted.', 'ok');
    });
    const rows = classRows(sessions);
    const table = h('table', { 'data-testid': 'class-table' },
      h('thead', {}, h('tr', {}, h('th', {}, 'Label'), Object.keys(Tasks.TASK_INFO).map((key) => h('th', {}, Tasks.TASK_INFO[key].title)))),
      h('tbody', {}, rows.map((row) => h('tr', {}, h('td', {}, row.label), row.cells.map((cell) => h('td', {}, cell))))));
    view.replaceChildren(
      h('div', { class: 'card' }, h('h2', {}, 'Participant label'),
        h('p', { class: 'muted' }, 'Stored with each session. Use a code or initials for classroom data, not full names.'), label),
      h('div', { class: 'card' }, h('h2', {}, 'Export and import'),
        h('p', { class: 'muted' }, sessions.length + ' sessions saved in this browser. The CSV has one row per trial; import merges files from other devices and skips duplicates.'),
        h('div', { class: 'row' }, exportButton, fileInput), h('div', { class: 'row' }, clearButton),
        h('div', { id: 'data-status', class: 'status', role: 'status', 'data-testid': 'data-status' })),
      h('div', { class: 'card' }, h('h2', {}, 'Class view'),
        h('p', { class: 'muted' }, 'Mean of each task’s main metric per label (session count in brackets): Stroop interference, 2-back d′, No-Go errors, unfair-offer rejection.'),
        h('div', { class: 'table-wrap' }, table)));
  }

  function renderAll() {
    const status = document.getElementById('data-status');
    const keep = status ? { text: status.textContent, cls: status.className } : null;
    renderPlay();
    renderResults();
    renderData();
    if (keep) setStatus(keep.text, keep.cls.replace('status', '').trim());
  }

  function selectTab(name) {
    document.querySelectorAll('.tabs button').forEach((button) => {
      button.setAttribute('aria-selected', String(button.dataset.tab === name));
    });
    ['play', 'results', 'data'].forEach((id) => { document.getElementById('view-' + id).hidden = id !== name; });
  }

  document.querySelectorAll('.tabs button').forEach((button) => {
    button.addEventListener('click', () => selectTab(button.dataset.tab));
  });

  renderAll();
})();
