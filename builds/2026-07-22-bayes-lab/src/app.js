// Bayes Lab — state management, DOM wiring, and canvas rendering.
// Depends on window.BetaMath and window.AiNarrative (loaded before this script).
(function () {
  'use strict';

  const SCENARIOS = [
    {
      key: 'clinical',
      label: 'Clinical Response Rate',
      description: 'What proportion of participants show a clinically meaningful improvement after an intervention (e.g., a stress-reduction protocol)?',
      p0: 0.3,
      beliefRate: 30,
    },
    {
      key: 'screening',
      label: 'Screening Tool Positive Rate',
      description: 'What proportion of a target population screens positive on a risk/psychopathy screening instrument, relative to a known base rate?',
      p0: 0.15,
      beliefRate: 15,
    },
    {
      key: 'manipulation',
      label: 'Manipulation Check Pass Rate',
      description: 'What proportion of participants correctly report perceiving the experimental manipulation (an attention/manipulation check)?',
      p0: 0.8,
      beliefRate: 80,
    },
    {
      key: 'replication',
      label: 'Replication Success Rate',
      description: 'What proportion of pre-registered replication attempts reproduce the original effect direction?',
      p0: 0.5,
      beliefRate: 50,
    },
    {
      key: 'custom',
      label: 'Custom',
      description: '',
      p0: 0.5,
      beliefRate: 50,
    },
  ];

  const DEFAULT_BELIEF_WEIGHT = 2;

  const state = {
    scenario: SCENARIOS[0],
    priorMode: 'belief',
    beliefRate: SCENARIOS[0].beliefRate,
    beliefWeight: DEFAULT_BELIEF_WEIGHT,
    prior: { alpha: SCENARIOS[0].beliefRate / 100 * DEFAULT_BELIEF_WEIGHT, beta: (1 - SCENARIOS[0].beliefRate / 100) * DEFAULT_BELIEF_WEIGHT },
    trials: [], // { successes, failures }
  };

  function clampNumber(value, min, max, fallback) {
    const n = Number(value);
    if (!Number.isFinite(n)) return fallback;
    return Math.min(max, Math.max(min, n));
  }

  function priorFromBelief(ratePercent, weight) {
    const rate = clampNumber(ratePercent, 1, 99, 50) / 100;
    const w = clampNumber(weight, 2, 1000, DEFAULT_BELIEF_WEIGHT);
    return { alpha: rate * w, beta: (1 - rate) * w };
  }

  function cumulativeCounts(trials) {
    let successes = 0;
    let failures = 0;
    for (const t of trials) {
      successes += t.successes;
      failures += t.failures;
    }
    return { successes, failures };
  }

  function posteriorFor(prior, successes, failures) {
    return { alpha: prior.alpha + successes, beta: prior.beta + failures };
  }

  function $(id) {
    return document.getElementById(id);
  }

  function setText(id, text) {
    const el = $(id);
    el.textContent = text;
  }

  function fmtPct(x) {
    return (x * 100).toFixed(1) + '%';
  }

  function fmtNum(x) {
    return x.toFixed(3);
  }

  function populateScenarioSelect() {
    const select = $('scenario-select');
    select.textContent = '';
    for (const s of SCENARIOS) {
      const opt = document.createElement('option');
      opt.value = s.key;
      opt.textContent = s.label;
      select.appendChild(opt);
    }
  }

  function applyScenario(key) {
    const scenario = SCENARIOS.find((s) => s.key === key) || SCENARIOS[0];
    state.scenario = scenario;
    $('scenario-description').value = scenario.description;
    $('scenario-description').readOnly = scenario.key !== 'custom';
    $('p0-input').value = scenario.p0;
    state.beliefRate = scenario.beliefRate;
    state.beliefWeight = DEFAULT_BELIEF_WEIGHT;
    state.prior = priorFromBelief(state.beliefRate, state.beliefWeight);
    state.trials = [];
    syncBeliefControlsFromState();
    syncAdvancedControlsFromState();
    render();
  }

  function syncBeliefControlsFromState() {
    $('belief-rate').value = state.beliefRate;
    $('belief-rate-value').textContent = String(state.beliefRate);
    $('belief-weight').value = state.beliefWeight;
    $('belief-weight-value').textContent = String(state.beliefWeight);
  }

  function syncAdvancedControlsFromState() {
    $('prior-alpha').value = state.prior.alpha.toFixed(2);
    $('prior-beta').value = state.prior.beta.toFixed(2);
  }

  function setPriorMode(mode) {
    state.priorMode = mode;
    const belief = mode === 'belief';
    $('prior-mode-belief').classList.toggle('active', belief);
    $('prior-mode-advanced').classList.toggle('active', !belief);
    $('belief-mode-inputs').classList.toggle('hidden', !belief);
    $('advanced-mode-inputs').classList.toggle('hidden', belief);
    if (belief) {
      // Coming from Advanced: derive a belief rate/weight approximating the current prior.
      const total = state.prior.alpha + state.prior.beta;
      state.beliefWeight = clampNumber(total, 2, 1000, DEFAULT_BELIEF_WEIGHT);
      state.beliefRate = Math.round(clampNumber((state.prior.alpha / total) * 100, 1, 99, 50));
      syncBeliefControlsFromState();
    } else {
      syncAdvancedControlsFromState();
    }
  }

  function onBeliefInputsChanged() {
    state.beliefRate = clampNumber($('belief-rate').value, 1, 99, 50);
    state.beliefWeight = clampNumber($('belief-weight').value, 2, 1000, DEFAULT_BELIEF_WEIGHT);
    $('belief-rate-value').textContent = String(state.beliefRate);
    $('belief-weight-value').textContent = String(state.beliefWeight);
    state.prior = priorFromBelief(state.beliefRate, state.beliefWeight);
    render();
  }

  function onAdvancedInputsChanged() {
    const alpha = clampNumber($('prior-alpha').value, 0.01, 100000, state.prior.alpha);
    const beta = clampNumber($('prior-beta').value, 0.01, 100000, state.prior.beta);
    state.prior = { alpha, beta };
    render();
  }

  function addTrial(successes, failures) {
    if (successes < 0 || failures < 0 || !Number.isInteger(successes) || !Number.isInteger(failures)) {
      return; // reject invalid input rather than corrupting state
    }
    if (successes === 0 && failures === 0) return;
    state.trials.push({ successes, failures });
    render();
  }

  function undo() {
    state.trials.pop();
    render();
  }

  function resetTrials() {
    state.trials = [];
    render();
  }

  function drawChart(prior, posterior, p0) {
    const canvas = $('beta-chart');
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const marginLeft = 40;
    const marginBottom = 24;
    const plotW = w - marginLeft - 10;
    const plotH = h - marginBottom - 10;

    const steps = 400;
    const xs = [];
    const priorYs = [];
    const postYs = [];
    for (let i = 0; i <= steps; i++) {
      const x = 0.0025 + (i / steps) * 0.995;
      xs.push(x);
      priorYs.push(BetaMath.betaPdf(x, prior.alpha, prior.beta));
      postYs.push(BetaMath.betaPdf(x, posterior.alpha, posterior.beta));
    }
    const maxY = Math.max(1, ...priorYs, ...postYs) * 1.05;

    function toPx(x, y) {
      return [marginLeft + x * plotW, 10 + plotH - (y / maxY) * plotH];
    }

    // Axes
    ctx.strokeStyle = '#888';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(marginLeft, 10);
    ctx.lineTo(marginLeft, 10 + plotH);
    ctx.lineTo(marginLeft + plotW, 10 + plotH);
    ctx.stroke();

    ctx.fillStyle = '#aaa';
    ctx.font = '11px sans-serif';
    for (const tick of [0, 0.25, 0.5, 0.75, 1.0]) {
      const [px] = toPx(tick, 0);
      ctx.fillText(tick.toFixed(2), px - 10, h - 6);
    }

    // p0 threshold line
    const [p0x] = toPx(clampNumber(p0, 0, 1, 0.5), 0);
    ctx.strokeStyle = '#e0a030';
    ctx.setLineDash([4, 3]);
    ctx.beginPath();
    ctx.moveTo(p0x, 10);
    ctx.lineTo(p0x, 10 + plotH);
    ctx.stroke();
    ctx.setLineDash([]);

    function drawCurve(ys, color, alpha) {
      ctx.strokeStyle = color;
      ctx.globalAlpha = alpha;
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let i = 0; i < xs.length; i++) {
        const [px, py] = toPx(xs[i], ys[i]);
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.stroke();
      ctx.globalAlpha = 1;
    }

    drawCurve(priorYs, '#7fb3ff', 0.45);
    drawCurve(postYs, '#5ee6a8', 1);
  }

  function renderHistoryTable() {
    const body = $('history-body');
    body.textContent = '';
    let runningSuccesses = 0;
    let runningFailures = 0;
    state.trials.forEach((t, idx) => {
      runningSuccesses += t.successes;
      runningFailures += t.failures;
      const n = runningSuccesses + runningFailures;
      const post = posteriorFor(state.prior, runningSuccesses, runningFailures);
      const mean = BetaMath.betaMean(post.alpha, post.beta);
      const ci = BetaMath.credibleInterval(post.alpha, post.beta, 0.95);

      const row = document.createElement('tr');
      const cells = [
        String(idx + 1),
        String(n),
        fmtPct(mean),
        `[${fmtPct(ci.lower)}, ${fmtPct(ci.upper)}]`,
      ];
      for (const cellText of cells) {
        const td = document.createElement('td');
        td.textContent = cellText;
        row.appendChild(td);
      }
      body.appendChild(row);
    });
  }

  function currentComputedState() {
    const p0 = clampNumber($('p0-input').value, 0.01, 0.99, state.scenario.p0);
    const { successes, failures } = cumulativeCounts(state.trials);
    const n = successes + failures;
    const posterior = posteriorFor(state.prior, successes, failures);
    const mean = BetaMath.betaMean(posterior.alpha, posterior.beta);
    const mode = BetaMath.betaMode(posterior.alpha, posterior.beta);
    const variance = BetaMath.betaVariance(posterior.alpha, posterior.beta);
    const ci = BetaMath.credibleInterval(posterior.alpha, posterior.beta, 0.95);
    const probGreater = BetaMath.posteriorProbGreaterThan(posterior.alpha, posterior.beta, p0);
    const bf = BetaMath.savageDickeyBayesFactor(state.prior.alpha, state.prior.beta, posterior.alpha, posterior.beta, p0);
    const bfLabel = BetaMath.bayesFactorStrengthLabel(bf.bf10);
    const wilson = n > 0 ? BetaMath.wilsonScoreInterval(successes, n, 0.95) : { lower: 0, upper: 1 };
    const pValue = n > 0 ? BetaMath.exactBinomialTestPValue(successes, n, p0) : 1;
    const mle = n > 0 ? successes / n : null;

    return { p0, successes, failures, n, prior: state.prior, posterior, mean, mode, variance, ci, probGreater, bf, bfLabel, wilson, pValue, mle };
  }

  function render() {
    syncAdvancedControlsFromState();
    const c = currentComputedState();

    setText('prior-readout', `Prior: Beta(α=${c.prior.alpha.toFixed(2)}, β=${c.prior.beta.toFixed(2)})`);
    setText('trial-summary', `n = ${c.n} (${c.successes} successes, ${c.failures} failures)`);

    setText('posterior-mean', fmtPct(c.mean));
    setText('posterior-mode', c.mode === null ? 'undefined at this shape' : fmtPct(c.mode));
    setText('posterior-sd', fmtPct(Math.sqrt(c.variance)));
    setText('posterior-ci', `[${fmtPct(c.ci.lower)}, ${fmtPct(c.ci.upper)}]`);
    setText('posterior-prob-greater', fmtPct(c.probGreater));

    setText('bf10-value', c.bf.bf10.toFixed(2));
    setText('bf01-value', c.bf.bf01.toFixed(2));
    setText('bf-label', c.bfLabel);

    setText('freq-mle', c.mle === null ? '—' : fmtPct(c.mle));
    setText('freq-wilson-ci', `[${fmtPct(c.wilson.lower)}, ${fmtPct(c.wilson.upper)}]`);
    setText('freq-pvalue', c.n === 0 ? '—' : c.pValue.toFixed(4));

    drawChart(c.prior, c.posterior, c.p0);
    renderHistoryTable();
  }

  async function onGenerateNarrative() {
    const c = currentComputedState();
    const apiKey = $('api-key-input').value.trim();
    const narrativeState = {
      scenarioLabel: state.scenario.label,
      scenarioDescription: $('scenario-description').value,
      p0: c.p0,
      prior: c.prior,
      posterior: { alpha: c.posterior.alpha, beta: c.posterior.beta, mean: c.mean },
      n: c.n,
      successes: c.successes,
      ci: c.ci,
      probGreater: c.probGreater,
      bf: { bf10: c.bf.bf10, label: c.bfLabel },
      pValue: c.pValue,
      wilson: c.wilson,
    };
    $('btn-generate-narrative').disabled = true;
    setText('narrative-output', 'Generating…');
    try {
      const result = await AiNarrative.generateNarrative(narrativeState, apiKey || null);
      $('narrative-output').textContent = result.text;
    } finally {
      $('btn-generate-narrative').disabled = false;
    }
  }

  function wireEvents() {
    $('scenario-select').addEventListener('change', (e) => applyScenario(e.target.value));
    $('p0-input').addEventListener('input', render);
    $('scenario-description').addEventListener('input', render);

    $('prior-mode-belief').addEventListener('click', () => setPriorMode('belief'));
    $('prior-mode-advanced').addEventListener('click', () => setPriorMode('advanced'));
    $('belief-rate').addEventListener('input', onBeliefInputsChanged);
    $('belief-weight').addEventListener('input', onBeliefInputsChanged);
    $('prior-alpha').addEventListener('input', onAdvancedInputsChanged);
    $('prior-beta').addEventListener('input', onAdvancedInputsChanged);

    $('btn-add-success').addEventListener('click', () => addTrial(1, 0));
    $('btn-add-failure').addEventListener('click', () => addTrial(0, 1));
    $('btn-batch-add').addEventListener('click', () => {
      const s = parseInt($('batch-successes').value, 10);
      const f = parseInt($('batch-failures').value, 10);
      addTrial(Number.isNaN(s) ? -1 : s, Number.isNaN(f) ? -1 : f);
    });
    $('btn-undo').addEventListener('click', undo);
    $('btn-reset').addEventListener('click', resetTrials);
    $('btn-generate-narrative').addEventListener('click', onGenerateNarrative);
  }

  function init() {
    populateScenarioSelect();
    applyScenario(SCENARIOS[0].key);
    wireEvents();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Exposed for tests only.
  window.__bayesLabState = state;
})();
