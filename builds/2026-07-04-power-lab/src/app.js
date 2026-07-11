// Classic (non-module) script, loaded last after stats.js, quiz-data.js,
// charts.js, and quiz.js -- see the note at the top of charts.js for why,
// including the IIFE wrapper.
(function () {

const { computePower, computeRequiredN, powerLabel, effectSizeLabel, dToR, rToD, tToD } =
  window.PowerLabStats;
const { createDistributionChart, createPowerCurveChart } = window.PowerLabCharts;
const { initQuiz } = window.PowerLabQuiz;

const THEME_KEY = 'power-lab-theme';

// ---------- Theme ----------
function initTheme() {
  const root = document.documentElement;
  const toggle = document.getElementById('theme-toggle');
  const saved = localStorage.getItem(THEME_KEY) || 'dark';
  applyTheme(saved);

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    toggle.textContent = theme === 'dark' ? 'Light mode' : 'Dark mode';
  }

  toggle.addEventListener('click', () => {
    const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    localStorage.setItem(THEME_KEY, next);
  });
}

// ---------- Tabs ----------
function initTabs() {
  const tabButtons = document.querySelectorAll('[data-tab]');
  const panels = document.querySelectorAll('[data-tab-panel]');

  tabButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tab;
      tabButtons.forEach((b) => b.classList.toggle('active', b === btn));
      panels.forEach((p) => p.classList.toggle('active', p.dataset.tabPanel === target));
    });
  });
}

// ---------- Power Explorer ----------
function initExplorer() {
  const dRange = document.getElementById('d-range');
  const dNumber = document.getElementById('d-number');
  const nRange = document.getElementById('n-range');
  const nNumber = document.getElementById('n-number');
  const alphaSelect = document.getElementById('alpha-select');
  const testTypeSelect = document.getElementById('test-type-select');
  const tailsSelect = document.getElementById('tails-select');
  const dValueLabel = document.getElementById('d-value');
  const dLabel = document.getElementById('d-label');
  const nValueLabel = document.getElementById('n-value');
  const powerReadout = document.querySelector('[data-testid="power-readout"]');
  const powerLabelEl = document.getElementById('power-label');

  const distCanvas = document.getElementById('distribution-chart');
  const curveCanvas = document.getElementById('power-curve-chart');
  const distChart = createDistributionChart(distCanvas);
  const curveChart = createPowerCurveChart(curveCanvas);

  function readParams() {
    return {
      d: parseFloat(dNumber.value),
      n: parseInt(nNumber.value, 10),
      alpha: parseFloat(alphaSelect.value),
      testType: testTypeSelect.value,
      tails: tailsSelect.value,
    };
  }

  function syncPair(range, number, value) {
    range.value = value;
    number.value = value;
  }

  function render() {
    const params = readParams();
    const power = computePower(params);

    dValueLabel.textContent = params.d.toFixed(2);
    dLabel.textContent = effectSizeLabel(params.d);
    nValueLabel.textContent = params.n;
    powerReadout.textContent = `${(power * 100).toFixed(1)}%`;
    const label = powerLabel(power);
    powerLabelEl.textContent = label;
    powerLabelEl.className = `readout-label ${label.replace(/\s+/g, '-')}`;

    distChart.update(params);
    curveChart.update({ ...params, currentN: params.n, computePower });
  }

  dRange.addEventListener('input', () => { syncPair(dRange, dNumber, dRange.value); render(); });
  dNumber.addEventListener('input', () => {
    const v = Math.min(2, Math.max(0.05, parseFloat(dNumber.value) || 0.05));
    syncPair(dRange, dNumber, v);
    render();
  });
  nRange.addEventListener('input', () => { syncPair(nRange, nNumber, nRange.value); render(); });
  nNumber.addEventListener('input', () => {
    const v = Math.min(5000, Math.max(2, parseInt(nNumber.value, 10) || 2));
    nNumber.value = v;
    nRange.value = Math.min(500, v);
    render();
  });
  [alphaSelect, testTypeSelect, tailsSelect].forEach((el) =>
    el.addEventListener('change', render)
  );

  render();
}

// ---------- Sample Size Calculator ----------
function initSampleSize() {
  const powerInput = document.getElementById('ss-power');
  const dInput = document.getElementById('ss-d');
  const alphaSelect = document.getElementById('ss-alpha');
  const testTypeSelect = document.getElementById('ss-test-type');
  const tailsSelect = document.getElementById('ss-tails');
  const resultEl = document.querySelector('[data-testid="sample-size-result"]');
  const errorEl = document.querySelector('[data-testid="sample-size-error"]');
  const copyBtn = document.getElementById('copy-summary-btn');
  const copyStatus = document.querySelector('[data-testid="copy-status"]');

  let lastSummary = '';

  function render() {
    errorEl.textContent = '';
    resultEl.textContent = '';
    copyStatus.textContent = '';

    const power = parseFloat(powerInput.value);
    const d = parseFloat(dInput.value);
    const alpha = parseFloat(alphaSelect.value);
    const testType = testTypeSelect.value;
    const tails = tailsSelect.value;

    if (!(power > 0 && power < 1)) {
      errorEl.textContent = 'Target power must be strictly between 0 and 1 (e.g. 0.80).';
      return;
    }
    if (!(d > 0)) {
      errorEl.textContent = 'Effect size (d) must be a positive number.';
      return;
    }

    const n = computeRequiredN({ d, power, alpha, testType, tails });
    const designText = testType === 'two-sample' ? 'per group' : 'participants';
    lastSummary =
      `To detect an effect of d = ${d} with ${(power * 100).toFixed(0)}% power at ` +
      `alpha = ${alpha} (${tails}-tailed), you need N = ${n} ${designText} ` +
      `(${testType === 'two-sample' ? 'two independent groups' : 'one-sample / paired design'}).`;

    resultEl.innerHTML = `Required sample size: <strong>N = ${n}</strong> ${designText}<br />${lastSummary}`;
  }

  [powerInput, dInput].forEach((el) => el.addEventListener('input', render));
  [alphaSelect, testTypeSelect, tailsSelect].forEach((el) => el.addEventListener('change', render));

  copyBtn.addEventListener('click', async () => {
    if (!lastSummary) return;
    try {
      await navigator.clipboard.writeText(lastSummary);
      copyStatus.textContent = 'Copied to clipboard.';
    } catch {
      copyStatus.textContent = 'Copy unavailable in this browser context — select the text above manually.';
    }
  });

  render();
}

// ---------- Effect Size Converter ----------
function initEffectSizeConverter() {
  const directionSelect = document.getElementById('conversion-direction');
  const dRow = document.querySelector('[data-input-for="d-to-r,r-to-d"]');
  const dInput = document.getElementById('es-d-input');
  const dLabelEl = document.getElementById('es-d-label');
  const tRows = document.querySelectorAll('[data-input-for="t-to-d"]');
  const tInput = document.getElementById('es-t-input');
  const nInput = document.getElementById('es-n-input');
  const testTypeInput = document.getElementById('es-test-type-input');
  const resultEl = document.querySelector('[data-testid="effect-size-result"]');
  const errorEl = document.querySelector('[data-testid="effect-size-error"]');

  function updateVisibility() {
    const direction = directionSelect.value;
    const showD = direction === 'd-to-r' || direction === 'r-to-d';
    const showT = direction === 't-to-d';
    dRow.hidden = !showD;
    tRows.forEach((row) => { row.hidden = !showT; });
    dLabelEl.textContent = direction === 'r-to-d' ? "Pearson's r" : "Cohen's d";
  }

  function render() {
    errorEl.textContent = '';
    resultEl.textContent = '';
    const direction = directionSelect.value;

    try {
      if (direction === 'd-to-r') {
        const d = parseFloat(dInput.value);
        const r = dToR(d);
        resultEl.innerHTML = `d = ${d} → <strong>r = ${r.toFixed(3)}</strong>`;
      } else if (direction === 'r-to-d') {
        const r = parseFloat(dInput.value);
        if (Math.abs(r) >= 1) throw new RangeError('r must satisfy |r| < 1.');
        const d = rToD(r);
        resultEl.innerHTML = `r = ${r} → <strong>d = ${d.toFixed(3)}</strong> (${effectSizeLabel(d)})`;
      } else {
        const t = parseFloat(tInput.value);
        const n = parseInt(nInput.value, 10);
        const testType = testTypeInput.value;
        if (!(n > 0)) throw new RangeError('N must be positive.');
        const d = tToD({ t, n, testType });
        resultEl.innerHTML = `t = ${t}, N = ${n} → <strong>d = ${d.toFixed(3)}</strong> (${effectSizeLabel(d)})`;
      }
    } catch (err) {
      errorEl.textContent = err.message;
    }
  }

  directionSelect.addEventListener('change', () => { updateVisibility(); render(); });
  [dInput, tInput, nInput].forEach((el) => el.addEventListener('input', render));
  testTypeInput.addEventListener('change', render);

  updateVisibility();
  render();
}

// ---------- Init ----------
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initTabs();
  initExplorer();
  initSampleSize();
  initEffectSizeConverter();
  initQuiz(document.querySelector('[data-testid="panel-quiz"]'));
});

})();
