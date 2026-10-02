/* UI wiring: tabs, controls, predict-then-run flow, calibration tracking. */
(function () {
  'use strict';
  const labs = window.Labs;
  const tabsEl = document.getElementById('tabs');
  const mainEl = document.getElementById('lab');
  const seedEl = document.getElementById('seed');
  const calibrationEl = document.getElementById('calibration');
  const history = [];

  function el(tag, attrs, children) {
    const node = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([key, value]) => {
      if (key === 'text') node.textContent = value;
      else node.setAttribute(key, value);
    });
    (children || []).forEach((child) => node.appendChild(child));
    return node;
  }

  function currentSeed() {
    const parsed = parseInt(seedEl.value, 10);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : 2026;
  }

  function renderCalibration() {
    if (history.length === 0) {
      calibrationEl.textContent = 'No predictions yet.';
      return;
    }
    const mean = history.reduce((sum, miss) => sum + miss, 0) / history.length;
    calibrationEl.textContent = 'Your predictions: ' + history.length + ', average miss ' + mean.toFixed(1) + ' points.';
  }

  function buildControl(spec, onChange) {
    const wrap = el('div', { class: 'control' });
    const outputId = 'out-' + spec.id;
    if (spec.type === 'select') {
      const select = el('select', { id: 'c-' + spec.id, 'data-testid': 'c-' + spec.id });
      spec.options.forEach(([value, label]) => {
        const option = el('option', { value, text: label });
        if (value === spec.value) option.selected = true;
        select.appendChild(option);
      });
      select.addEventListener('change', onChange);
      wrap.appendChild(el('label', { for: 'c-' + spec.id }, [el('span', { text: spec.label })]));
      wrap.appendChild(select);
      return { wrap, read: () => select.value };
    }
    const input = el('input', { type: 'range', id: 'c-' + spec.id, 'data-testid': 'c-' + spec.id, min: spec.min, max: spec.max, step: spec.step, value: spec.value });
    const output = el('output', { id: outputId, for: 'c-' + spec.id, text: spec.fmt(spec.value) });
    input.addEventListener('input', () => { output.textContent = spec.fmt(parseFloat(input.value)); onChange(); });
    wrap.appendChild(el('label', { for: 'c-' + spec.id }, [el('span', { text: spec.label }), output]));
    wrap.appendChild(input);
    return { wrap, read: () => parseFloat(input.value) };
  }

  function renderLab(lab) {
    mainEl.replaceChildren();
    const readers = {};
    const results = el('div', { 'data-testid': 'results' });
    const canvas = el('canvas', { 'data-testid': 'chart', role: 'img', 'aria-label': lab.title + ' chart' });
    let predictInput = null;
    let predictNote = null;
    let predictCard = null;

    const readParams = () => Object.fromEntries(Object.entries(readers).map(([id, read]) => [id, read()]));

    function show(result) {
      results.replaceChildren();
      const grid = el('div', { class: 'stats' });
      result.stats.forEach((stat) => {
        grid.appendChild(el('div', { class: 'stat' }, [
          el('div', { class: 'v', text: stat.v, 'data-testid': 'stat-' + (stat.id || stat.k) }),
          el('div', { class: 'k', text: stat.k }),
        ]));
      });
      results.appendChild(grid);
      results.appendChild(el('div', { class: 'card takeaway', 'data-testid': 'takeaway', style: 'margin-top:12px' }, [el('p', { text: result.takeaway })]));
      chartCard.hidden = false;
      result.draw(canvas);
    }

    function execute(seed, button) {
      const params = readParams();
      if (button) { button.disabled = true; button.textContent = 'Simulating...'; }
      setTimeout(() => {
        try {
          const result = lab.run(params, seed);
          show(result);
          if (predictInput && result.actual !== undefined) {
            const guess = parseFloat(predictInput.value);
            const miss = Math.abs(guess - result.actual) * (lab.predict.unit === 'd' ? 100 : 1);
            if (lab.predict.unit !== 'd') history.push(miss);
            const unit = lab.predict.unit === 'd' ? '' : ' points';
            const shownMiss = lab.predict.unit === 'd' ? (Math.abs(guess - result.actual)).toFixed(2) : miss.toFixed(1);
            predictNote.textContent = 'You said ' + guess + ', the simulation says ' + result.actual.toFixed(lab.predict.unit === 'd' ? 2 : 1) + '. Off by ' + shownMiss + unit + '.';
            predictCard.classList.add('done');
            renderCalibration();
          }
        } catch (error) {
          results.replaceChildren(el('p', { class: 'verdict bad', text: 'Could not run: ' + error.message }));
        } finally {
          if (button) { button.disabled = false; button.textContent = button.dataset.label; }
        }
      }, 20);
    }

    const controls = el('div', { class: 'controls' });
    const onChange = lab.live ? () => show(lab.run(readParams(), currentSeed())) : () => { if (predictCard) predictCard.classList.remove('done'); };
    lab.controls.forEach((spec) => {
      const built = buildControl(spec, onChange);
      readers[spec.id] = built.read;
      controls.appendChild(built.wrap);
    });

    const chartCard = el('div', { class: 'card' }, [canvas]);
    chartCard.hidden = true;

    mainEl.appendChild(el('div', { class: 'card' }, [el('h2', { text: lab.title }), el('p', { text: lab.intro, class: 'muted' }), controls]));

    if (lab.predict) {
      predictInput = el('input', { type: 'range', id: 'predict', 'data-testid': 'predict', min: lab.predict.min, max: lab.predict.max, step: lab.predict.step || 1, value: lab.predict.value });
      const predictOut = el('output', { for: 'predict', 'data-testid': 'predict-value', text: String(lab.predict.value) + ' ' + lab.predict.unit });
      predictInput.addEventListener('input', () => { predictOut.textContent = predictInput.value + ' ' + lab.predict.unit; });
      predictNote = el('p', { class: 'muted', 'data-testid': 'predict-note', text: 'Commit to a guess, then run the simulation.' });
      const run = el('button', { class: 'primary', 'data-testid': 'run', 'data-label': 'Lock in guess and run' , text: 'Lock in guess and run' });
      const reroll = el('button', { class: 'secondary', 'data-testid': 'reroll', 'data-label': 'New random sample', text: 'New random sample' });
      run.addEventListener('click', () => execute(currentSeed(), run));
      reroll.addEventListener('click', () => { seedEl.value = String(1 + Math.floor(Math.random() * 999999)); execute(currentSeed(), reroll); });
      predictCard = el('div', { class: 'card predict' }, [
        el('h2', { text: 'Predict first' }),
        el('label', { for: 'predict', text: lab.predict.question }),
        el('div', { class: 'row' }, [predictInput, predictOut]),
        el('div', { class: 'row' }, [run, reroll]),
        predictNote,
      ]);
      predictInput.style.flex = '1 1 200px';
      mainEl.appendChild(predictCard);
    }

    mainEl.appendChild(results);
    mainEl.appendChild(chartCard);
    if (lab.live) show(lab.run(readParams(), currentSeed()));
  }

  function select(index) {
    Array.from(tabsEl.children).forEach((button, i) => button.setAttribute('aria-selected', String(i === index)));
    renderLab(labs[index]);
  }

  labs.forEach((lab, index) => {
    const button = el('button', { role: 'tab', 'data-testid': 'tab-' + lab.id, text: lab.tab, 'aria-selected': 'false' });
    button.addEventListener('click', () => select(index));
    tabsEl.appendChild(button);
  });

  window.addEventListener('resize', () => {
    const active = Array.from(tabsEl.children).findIndex((button) => button.getAttribute('aria-selected') === 'true');
    if (active >= 0 && labs[active].live) select(active);
  });

  renderCalibration();
  select(0);
})();
