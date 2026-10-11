/* Lesson definitions. Each lesson: { id, title, render(root) }. Templates are static; only numbers are interpolated. */
(function (root) {
  'use strict';

  const B = root.Bayes;
  const C = root.Charts;

  const pct = (v, digits = 1) => (Number.isFinite(v) ? `${(v * 100).toFixed(digits)}%` : '—');
  const num = (v, digits = 3) => (Number.isFinite(v) ? v.toFixed(digits) : '—');
  const sci = (v) => {
    if (!Number.isFinite(v)) return '—';
    if (v >= 1000 || (v < 0.001 && v > 0)) return v.toExponential(2);
    return v.toFixed(v >= 100 ? 0 : 2);
  };

  /** Read a numeric input, clamped to [min, max]; flags invalid text instead of throwing. */
  function readNum(input, min, max, fallback) {
    const raw = Number(input.value);
    const valid = input.value.trim() !== '' && Number.isFinite(raw);
    input.setAttribute('aria-invalid', String(!valid));
    if (!valid) return fallback;
    return Math.min(max, Math.max(min, raw));
  }

  const q = (scope, id) => scope.querySelector(`[data-testid="${id}"]`);

  function legend(items) {
    return `<ul class="legend">${items.map(([cls, text]) => `<li><span class="swatch ${cls}"></span>${text}</li>`).join('')}</ul>`;
  }

  // ---------------------------------------------------------------- Lesson 1
  const PRIORS = {
    flat: { a: 1, b: 1 },
    skeptic: { a: 10, b: 10 },
    optimist: { a: 8, b: 2 },
  };

  function renderBeta(host) {
    host.innerHTML = `
      <p class="lede">You have a probability θ you care about — say, the proportion of participants who respond to an intervention. A <strong>prior</strong> says what you believed before the data. The <strong>posterior</strong> is what you should believe after. Add data and watch the curve move.</p>
      <div class="panel grid2">
        <fieldset>
          <legend>1. Prior belief</legend>
          <label>Preset
            <select data-testid="prior-preset">
              <option value="flat">Flat — no idea (Beta 1,1)</option>
              <option value="skeptic">Skeptical — probably near 50% (Beta 10,10)</option>
              <option value="optimist">Optimistic — probably high (Beta 8,2)</option>
              <option value="custom">Custom</option>
            </select>
          </label>
          <div class="row">
            <label>α <input data-testid="prior-a" type="number" min="0.1" step="0.1" value="1"></label>
            <label>β <input data-testid="prior-b" type="number" min="0.1" step="0.1" value="1"></label>
          </div>
        </fieldset>
        <fieldset>
          <legend>2. Data (your own, or simulated)</legend>
          <div class="row">
            <label>Successes <input data-testid="data-k" type="number" min="0" step="1" value="0"></label>
            <label>Trials <input data-testid="data-n" type="number" min="0" step="1" value="0"></label>
          </div>
          <div class="row buttons">
            <button data-testid="add-success" type="button">+ success</button>
            <button data-testid="add-failure" type="button">+ failure</button>
            <button data-testid="reset-data" type="button" class="ghost">Reset</button>
          </div>
          <div class="row">
            <label>True θ for simulation <input data-testid="sim-theta" type="range" min="0" max="1" step="0.01" value="0.7"> <output data-testid="sim-theta-out">0.70</output></label>
            <button data-testid="simulate" type="button">Simulate 10 trials</button>
          </div>
        </fieldset>
      </div>
      <p class="msg" data-testid="beta-msg" role="status"></p>
      <div class="chartbox" data-testid="beta-chart"></div>
      ${legend([['s0', 'Prior'], ['s1', 'Likelihood (rescaled)'], ['s2', 'Posterior']])}
      <div class="panel">
        <div class="stats">
          <div><span>Posterior mean</span><strong data-testid="post-mean"></strong></div>
          <div><span>95% HDI</span><strong data-testid="post-hdi"></strong></div>
          <div><span>P(θ &gt; 0.5)</span><strong data-testid="post-gt-half"></strong></div>
          <div><span>Prior mean</span><strong data-testid="prior-mean"></strong></div>
          <div><span>Next 10 trials: expected successes</span><strong data-testid="pred-expected"></strong></div>
          <div><span>P(≥ 7 of next 10)</span><strong data-testid="pred-ge7"></strong></div>
        </div>
        <div class="row">
          <label>ROPE (practically equivalent to “no effect”) from <input data-testid="rope-lo" type="number" step="0.01" min="0" max="1" value="0.45"></label>
          <label>to <input data-testid="rope-hi" type="number" step="0.01" min="0" max="1" value="0.55"></label>
          <span>P(θ in ROPE) = <strong data-testid="rope-prob"></strong></span>
        </div>
      </div>
      <p class="note">Reading it: the posterior is the prior times the likelihood, renormalised. With a flat prior the posterior mean is (k+1)/(n+2) — after 3 of 3 successes it is 0.80, not 1.00, because 3 trials cannot rule out failures. The HDI is the narrowest interval holding 95% of the belief; unlike a confidence interval you may say “θ lies in here with 95% probability, given the model and prior”.</p>`;

    const el = {
      preset: q(host, 'prior-preset'), a: q(host, 'prior-a'), b: q(host, 'prior-b'),
      k: q(host, 'data-k'), n: q(host, 'data-n'), theta: q(host, 'sim-theta'),
      ropeLo: q(host, 'rope-lo'), ropeHi: q(host, 'rope-hi'),
    };

    function update() {
      const a = readNum(el.a, 0.1, 1000, 1);
      const b = readNum(el.b, 0.1, 1000, 1);
      const n = Math.round(readNum(el.n, 0, 100000, 0));
      let k = Math.round(readNum(el.k, 0, 100000, 0));
      let message = '';
      if (k > n) { k = n; el.k.value = String(n); message = 'Successes cannot exceed trials; set to the number of trials.'; }
      q(host, 'beta-msg').textContent = message;
      q(host, 'sim-theta-out').textContent = Number(el.theta.value).toFixed(2);

      const post = B.betaBinomialUpdate(a, b, k, n);
      const [lo, hi] = B.betaHDI(post.a, post.b, 0.95);
      const prior = C.sample((x) => B.betaPdf(x, a, b), 0.0005, 0.9995);
      const posterior = C.sample((x) => B.betaPdf(x, post.a, post.b), 0.0005, 0.9995);
      const posteriorPeak = Math.max(...posterior.filter(Number.isFinite));
      const like = C.scaleTo(C.sample((x) => Math.exp(k * Math.log(x) + (n - k) * Math.log(1 - x)), 0.0005, 0.9995), 0.9 * posteriorPeak);
      q(host, 'beta-chart').innerHTML = C.curveChart(
        [{ ys: prior, cls: 's0' }, { ys: n > 0 ? like : [], cls: 's1' }, { ys: posterior, cls: 's2', fill: true }].filter((s) => s.ys.length),
        { xmin: 0, xmax: 1, ticks: [0, 0.25, 0.5, 0.75, 1], label: 'Prior, likelihood and posterior for theta' },
      );
      q(host, 'post-mean').textContent = num(B.betaMean(post.a, post.b));
      q(host, 'post-hdi').textContent = `${num(lo)} – ${num(hi)}`;
      q(host, 'post-gt-half').textContent = pct(1 - B.betaCdf(0.5, post.a, post.b));
      q(host, 'prior-mean').textContent = num(B.betaMean(a, b));
      const predictive = B.predictivePmf(post.a, post.b, 10);
      q(host, 'pred-expected').textContent = (10 * B.betaMean(post.a, post.b)).toFixed(2);
      q(host, 'pred-ge7').textContent = pct(predictive.slice(7).reduce((s, v) => s + v, 0));
      const ropeLo = readNum(el.ropeLo, 0, 1, 0.45);
      const ropeHi = readNum(el.ropeHi, 0, 1, 0.55);
      q(host, 'rope-prob').textContent = pct(B.ropeProbability(post.a, post.b, ropeLo, ropeHi));
    }

    el.preset.addEventListener('change', () => {
      const preset = PRIORS[el.preset.value];
      if (preset) { el.a.value = String(preset.a); el.b.value = String(preset.b); }
      update();
    });
    [el.a, el.b].forEach((input) => input.addEventListener('input', () => { el.preset.value = 'custom'; update(); }));
    [el.k, el.n, el.theta, el.ropeLo, el.ropeHi].forEach((input) => input.addEventListener('input', update));
    const bump = (success) => {
      el.n.value = String(Math.round(Number(el.n.value) || 0) + 1);
      if (success) el.k.value = String(Math.round(Number(el.k.value) || 0) + 1);
      update();
    };
    q(host, 'add-success').addEventListener('click', () => bump(true));
    q(host, 'add-failure').addEventListener('click', () => bump(false));
    q(host, 'reset-data').addEventListener('click', () => { el.k.value = '0'; el.n.value = '0'; update(); });
    q(host, 'simulate').addEventListener('click', () => {
      const theta = Number(el.theta.value);
      let wins = 0;
      for (let i = 0; i < 10; i++) if (Math.random() < theta) wins++;
      el.n.value = String(Math.round(Number(el.n.value) || 0) + 10);
      el.k.value = String(Math.round(Number(el.k.value) || 0) + wins);
      update();
    });
    update();
  }

  // ---------------------------------------------------------------- Lesson 2
  const SCENARIOS = {
    screen: { prev: 1, sens: 90, spec: 90 },
    cheat: { prev: 5, sens: 95, spec: 95 },
    lie: { prev: 10, sens: 80, spec: 80 },
    balanced: { prev: 50, sens: 90, spec: 90 },
  };

  function renderBaseRate(host) {
    host.innerHTML = `
      <p class="lede">A test that is “90% accurate” can still be wrong most of the time when it flags something. The missing ingredient is the <strong>base rate</strong>. Here are 1,000 people; change the numbers and see who gets flagged.</p>
      <div class="panel">
        <label>Scenario (illustrative numbers)
          <select data-testid="scenario">
            <option value="screen">Screening test for a rare condition — 1% prevalence, 90/90</option>
            <option value="cheat">Plagiarism detector — 5% of essays copied, 95/95</option>
            <option value="lie">Brain-scan lie detector — 10% of witnesses lying, 80/80</option>
            <option value="balanced">Half of people have it — 50% prevalence, 90/90</option>
          </select>
        </label>
        <div class="sliders">
          <label>Prevalence <output data-testid="prev-out"></output><input data-testid="prev" type="range" min="0.1" max="60" step="0.1" value="1"></label>
          <label>Sensitivity (true positive rate) <output data-testid="sens-out"></output><input data-testid="sens" type="range" min="50" max="100" step="1" value="90"></label>
          <label>Specificity (true negative rate) <output data-testid="spec-out"></output><input data-testid="spec" type="range" min="50" max="100" step="1" value="90"></label>
        </div>
      </div>
      <div class="chartbox" data-testid="dots"></div>
      ${legend([['tp', 'Has it, flagged'], ['fp', 'Does not, flagged'], ['fn', 'Has it, missed'], ['tn', 'Does not, not flagged']])}
      <div class="panel">
        <p class="big" data-testid="freq-sentence"></p>
        <div class="stats">
          <div><span>P(condition | flagged)</span><strong data-testid="ppv"></strong></div>
          <div><span>P(no condition | not flagged)</span><strong data-testid="npv"></strong></div>
          <div><span>People flagged (of 1,000)</span><strong data-testid="flagged"></strong></div>
        </div>
      </div>
      <p class="note">Bayes’ rule in natural frequencies: P(condition | flagged) = true positives ÷ everyone flagged. Rare condition ⇒ the false positives from the huge healthy group swamp the few true positives. Try dropping prevalence to 0.1% or raising it to 50% and watch the green and red swap.</p>`;

    const prev = q(host, 'prev');
    const sens = q(host, 'sens');
    const spec = q(host, 'spec');

    function update() {
      const p = Number(prev.value) / 100;
      const se = Number(sens.value) / 100;
      const sp = Number(spec.value) / 100;
      q(host, 'prev-out').textContent = pct(p);
      q(host, 'sens-out').textContent = pct(se, 0);
      q(host, 'spec-out').textContent = pct(sp, 0);
      const counts = B.naturalFrequencies(p, se, sp, 1000);
      const flagged = counts.tp + counts.fp;
      q(host, 'dots').innerHTML = C.dotGrid(counts);
      const d = B.diagnostic(p, se, sp);
      q(host, 'ppv').textContent = pct(d.ppv);
      q(host, 'npv').textContent = pct(d.npv, 2);
      q(host, 'flagged').textContent = String(flagged);
      q(host, 'freq-sentence').textContent = flagged === 0
        ? 'Nobody is flagged at these settings.'
        : `Of ${flagged} people flagged, only ${counts.tp} actually have it (${pct(counts.tp / flagged, 0)}).`;
    }

    q(host, 'scenario').addEventListener('change', (event) => {
      const s = SCENARIOS[event.target.value];
      prev.value = String(s.prev); sens.value = String(s.sens); spec.value = String(s.spec);
      update();
    });
    [prev, sens, spec].forEach((input) => input.addEventListener('input', update));
    update();
  }

  // ---------------------------------------------------------------- Lesson 3
  const SKEPTIC = { a: 2, b: 8 };
  const ENTHUSIAST = { a: 8, b: 2 };

  /** Smallest n (<= limit) at which the two priors' posterior means differ by under `gap`. */
  function samplesToAgree(rate, gap = 0.05, limit = 5000) {
    for (let n = 0; n <= limit; n++) {
      const k = Math.round(n * rate);
      const a = B.betaMean(SKEPTIC.a + k, SKEPTIC.b + n - k);
      const b = B.betaMean(ENTHUSIAST.a + k, ENTHUSIAST.b + n - k);
      if (Math.abs(a - b) < gap) return n;
    }
    return null;
  }

  function renderTwo(host) {
    host.innerHTML = `
      <p class="lede">Two colleagues disagree about how often a treatment works: the <strong>skeptic</strong> starts at Beta(2, 8) (mean 20%), the <strong>enthusiast</strong> at Beta(8, 2) (mean 80%). Show them identical data. Does the argument end?</p>
      <div class="panel sliders">
        <label>Observed success rate <output data-testid="rate-out"></output><input data-testid="rate" type="range" min="0" max="1" step="0.01" value="0.6"></label>
        <label>Number of observations <output data-testid="count-out"></output><input data-testid="count" type="range" min="0" max="300" step="1" value="10"></label>
      </div>
      <div class="chartbox" data-testid="two-chart"></div>
      ${legend([['s0', 'Skeptic’s posterior'], ['s3', 'Enthusiast’s posterior']])}
      <div class="panel">
        <div class="stats">
          <div><span>Data</span><strong data-testid="two-data"></strong></div>
          <div><span>Skeptic’s mean</span><strong data-testid="mean-skeptic"></strong></div>
          <div><span>Enthusiast’s mean</span><strong data-testid="mean-enthusiast"></strong></div>
          <div><span>Disagreement</span><strong data-testid="mean-gap"></strong></div>
          <div><span>Observations until they agree within 5 points</span><strong data-testid="agree-n"></strong></div>
        </div>
      </div>
      <p class="note">With no data the two disagree by 60 points. The prior acts like ten extra imaginary observations, so its influence fades as real observations accumulate: this is why “priors are subjective” is a weaker objection than it sounds, and why a prior you can defend should be reported alongside the data.</p>`;

    const rate = q(host, 'rate');
    const count = q(host, 'count');

    function update() {
      const r = Number(rate.value);
      const n = Number(count.value);
      const k = Math.round(n * r);
      q(host, 'rate-out').textContent = pct(r, 0);
      q(host, 'count-out').textContent = String(n);
      const sk = B.betaBinomialUpdate(SKEPTIC.a, SKEPTIC.b, k, n);
      const en = B.betaBinomialUpdate(ENTHUSIAST.a, ENTHUSIAST.b, k, n);
      const f = (p) => (x) => B.betaPdf(x, p.a, p.b);
      q(host, 'two-chart').innerHTML = C.curveChart(
        [{ ys: C.sample(f(sk), 0.0005, 0.9995), cls: 's0', fill: true }, { ys: C.sample(f(en), 0.0005, 0.9995), cls: 's3', fill: true }],
        { xmin: 0, xmax: 1, ticks: [0, 0.25, 0.5, 0.75, 1], label: 'Skeptic and enthusiast posteriors' },
      );
      const ms = B.betaMean(sk.a, sk.b);
      const me = B.betaMean(en.a, en.b);
      q(host, 'two-data').textContent = `${k} of ${n}`;
      q(host, 'mean-skeptic').textContent = pct(ms);
      q(host, 'mean-enthusiast').textContent = pct(me);
      q(host, 'mean-gap').textContent = `${(Math.abs(me - ms) * 100).toFixed(1)} points`;
      const needed = samplesToAgree(Math.round(r * 100) / 100);
      q(host, 'agree-n').textContent = needed === null ? 'never (within 5,000)' : String(needed);
    }
    [rate, count].forEach((input) => input.addEventListener('input', update));
    update();
  }

  // ---------------------------------------------------------------- Lesson 4
  const BF_PRIORS = { uniform: { a: 1, b: 1 }, jeffreys: { a: 0.5, b: 0.5 }, tight: { a: 10, b: 10 } };

  function renderBF(host) {
    host.innerHTML = `
      <p class="lede">A p-value asks “how surprising is this data if the null is true?”. A <strong>Bayes factor</strong> asks “how much better does the null or the alternative predict this data?”. They can disagree — sometimes sharply. Test whether a coin (or a response rate) equals a null value θ₀.</p>
      <div class="panel">
        <div class="row buttons">
          <button type="button" data-testid="preset-lindley" data-k="5100" data-n="10000">Lindley: 5,100 / 10,000</button>
          <button type="button" data-testid="preset-clear" data-k="65" data-n="100">Clear effect: 65 / 100</button>
          <button type="button" data-testid="preset-ambiguous" data-k="7" data-n="10">Ambiguous: 7 / 10</button>
        </div>
        <div class="row">
          <label>Successes <input data-testid="bf-k" type="number" min="0" step="1" value="7"></label>
          <label>Trials <input data-testid="bf-n" type="number" min="1" step="1" value="10"></label>
          <label>Null value θ₀ <input data-testid="bf-null" type="number" min="0.01" max="0.99" step="0.01" value="0.5"></label>
          <label>Prior under H1
            <select data-testid="bf-prior">
              <option value="uniform">Uniform Beta(1,1)</option>
              <option value="jeffreys">Jeffreys Beta(½,½)</option>
              <option value="tight">Near the null Beta(10,10)</option>
            </select>
          </label>
        </div>
      </div>
      <p class="msg" data-testid="bf-msg" role="status"></p>
      <div class="chartbox" data-testid="bf-chart"></div>
      ${legend([['s0', 'Prior under H1'], ['s2', 'Posterior under H1'], ['vl', 'Null value θ₀']])}
      <div class="panel">
        <div class="stats">
          <div><span>Exact two-sided p-value</span><strong data-testid="bf-p"></strong></div>
          <div><span>BF₁₀ (alternative : null)</span><strong data-testid="bf10"></strong></div>
          <div><span>BF₀₁ (null : alternative)</span><strong data-testid="bf01"></strong></div>
          <div><span>Savage–Dickey check of BF₀₁</span><strong data-testid="bf-sd"></strong></div>
        </div>
        <p class="big" data-testid="bf-verdict"></p>
        <p data-testid="bf-contrast"></p>
      </div>
      <p class="note">Intuition: the alternative spreads its bets over every θ; the null bets everything on θ₀. If the data land near θ₀ and n is large, the null predicts them far better even when p &lt; .05 (Lindley’s paradox). Savage–Dickey: BF₀₁ equals posterior density at θ₀ divided by prior density at θ₀ — the plot shows those two heights.</p>`;

    const k = q(host, 'bf-k');
    const n = q(host, 'bf-n');
    const nul = q(host, 'bf-null');
    const priorSel = q(host, 'bf-prior');

    function update() {
      const trials = Math.round(readNum(n, 1, 200000, 10));
      let wins = Math.round(readNum(k, 0, 200000, 0));
      const theta0 = readNum(nul, 0.01, 0.99, 0.5);
      let message = '';
      if (wins > trials) { wins = trials; k.value = String(trials); message = 'Successes cannot exceed trials; set to the number of trials.'; }
      q(host, 'bf-msg').textContent = message;
      const prior = BF_PRIORS[priorSel.value];
      const post = B.betaBinomialUpdate(prior.a, prior.b, wins, trials);
      const p = B.binomialPValue(wins, trials, theta0);
      const bf10 = B.bayesFactor10(wins, trials, prior.a, prior.b, theta0);
      const bf01 = 1 / bf10;
      const sd = B.bayesFactor01SavageDickey(wins, trials, prior.a, prior.b, theta0);
      q(host, 'bf-chart').innerHTML = C.curveChart(
        [{ ys: C.sample((x) => B.betaPdf(x, prior.a, prior.b), 0.0005, 0.9995), cls: 's0' },
          { ys: C.sample((x) => B.betaPdf(x, post.a, post.b), 0.0005, 0.9995), cls: 's2', fill: true }],
        { xmin: 0, xmax: 1, ticks: [0, 0.25, 0.5, 0.75, 1], vlines: [{ x: theta0, cls: 'vl' }], label: 'Prior and posterior with null value marked' },
      );
      q(host, 'bf-p').textContent = p < 0.0001 ? '< 0.0001' : p.toFixed(4);
      q(host, 'bf10').textContent = sci(bf10);
      q(host, 'bf01').textContent = sci(bf01);
      q(host, 'bf-sd').textContent = sci(sd);
      q(host, 'bf-verdict').textContent = B.bayesFactorLabel(bf10);
      const significant = p < 0.05;
      const favoursNull = bf01 > 1;
      let contrast = 'p-value and Bayes factor point the same way here.';
      if (significant && favoursNull) contrast = 'Disagreement: p < .05 would reject the null, yet the data are more probable under the null than under this alternative.';
      else if (!significant && !favoursNull) contrast = 'Disagreement: p ≥ .05 is “not significant”, yet the Bayes factor favours the alternative. A non-significant p is not evidence of absence — or presence.';
      else if (!significant && favoursNull) contrast = 'Both agree there is no reliable evidence against the null; the Bayes factor additionally quantifies support for it.';
      q(host, 'bf-contrast').textContent = contrast;
    }

    host.querySelectorAll('button[data-k]').forEach((button) => {
      button.addEventListener('click', () => { k.value = button.dataset.k; n.value = button.dataset.n; nul.value = '0.5'; update(); });
    });
    [k, n, nul, priorSel].forEach((input) => input.addEventListener('input', update));
    update();
  }

  // ---------------------------------------------------------------- Lesson 5
  const SHRINK_PRESETS = {
    replication: { pm: 0, psd: 0.3, est: 0.8, se: 0.3 },
    precise: { pm: 0.4, psd: 0.15, est: 0.1, se: 0.04 },
    noisy: { pm: 0.4, psd: 0.15, est: 1.2, se: 0.6 },
  };

  function renderShrink(host) {
    host.innerHTML = `
      <p class="lede">Combining a prior estimate with a new one is a <strong>precision-weighted average</strong>: the more precise source gets more say. That is why a small, noisy study with a spectacular effect should be pulled toward what you already knew (<em>shrinkage</em>).</p>
      <div class="panel">
        <label>Preset
          <select data-testid="shrink-preset">
            <option value="replication">Flashy small study, skeptical prior (effect d)</option>
            <option value="precise">Large precise study contradicts the literature</option>
            <option value="noisy">Very noisy huge effect</option>
            <option value="custom">Custom</option>
          </select>
        </label>
        <div class="row">
          <label>Prior mean <input data-testid="sh-pm" type="number" step="0.05" value="0"></label>
          <label>Prior SD <input data-testid="sh-psd" type="number" step="0.05" min="0.001" value="0.3"></label>
          <label>New estimate <input data-testid="sh-est" type="number" step="0.05" value="0.8"></label>
          <label>Its standard error <input data-testid="sh-se" type="number" step="0.05" min="0.001" value="0.3"></label>
        </div>
      </div>
      <p class="msg" data-testid="sh-msg" role="status"></p>
      <div class="chartbox" data-testid="sh-chart"></div>
      ${legend([['s0', 'Prior'], ['s1', 'New estimate (likelihood)'], ['s2', 'Posterior']])}
      <div class="panel">
        <div class="stats">
          <div><span>Posterior mean</span><strong data-testid="sh-mean"></strong></div>
          <div><span>Posterior SD</span><strong data-testid="sh-sd"></strong></div>
          <div><span>95% interval</span><strong data-testid="sh-int"></strong></div>
          <div><span>Weight on new data</span><strong data-testid="sh-weight"></strong></div>
          <div><span>Shrunk away from the estimate by</span><strong data-testid="sh-shrunk"></strong></div>
        </div>
      </div>
      <p class="note">This is the Gaussian special case behind random-effects meta-analysis, empirical-Bayes shrinkage and regularised priors on effect sizes. It is the cheapest rigorous answer to “should I believe this exciting result?”.</p>`;

    const inputs = {
      pm: q(host, 'sh-pm'), psd: q(host, 'sh-psd'), est: q(host, 'sh-est'), se: q(host, 'sh-se'),
    };
    const preset = q(host, 'shrink-preset');

    function update() {
      const pm = readNum(inputs.pm, -100, 100, 0);
      const psd = readNum(inputs.psd, 0.001, 100, 0.3);
      const est = readNum(inputs.est, -100, 100, 0);
      const se = readNum(inputs.se, 0.001, 100, 0.3);
      const post = B.normalUpdate(pm, psd, est, se);
      const lo = Math.min(pm - 3.5 * psd, est - 3.5 * se, post.mean - 3.5 * post.sd);
      const hi = Math.max(pm + 3.5 * psd, est + 3.5 * se, post.mean + 3.5 * post.sd);
      const step = (hi - lo) / 4;
      const ticks = [0, 1, 2, 3, 4].map((i) => Number((lo + step * i).toFixed(2)));
      q(host, 'sh-chart').innerHTML = C.curveChart(
        [{ ys: C.sample((x) => B.normalPdf(x, pm, psd), lo, hi), cls: 's0' },
          { ys: C.sample((x) => B.normalPdf(x, est, se), lo, hi), cls: 's1' },
          { ys: C.sample((x) => B.normalPdf(x, post.mean, post.sd), lo, hi), cls: 's2', fill: true }],
        { xmin: lo, xmax: hi, ticks, label: 'Prior, new estimate and posterior' },
      );
      q(host, 'sh-mean').textContent = num(post.mean);
      q(host, 'sh-sd').textContent = num(post.sd);
      q(host, 'sh-int').textContent = `${num(post.mean - 1.96 * post.sd)} to ${num(post.mean + 1.96 * post.sd)}`;
      q(host, 'sh-weight').textContent = pct(post.dataWeight, 0);
      q(host, 'sh-shrunk').textContent = num(est - post.mean);
    }

    preset.addEventListener('change', () => {
      const p = SHRINK_PRESETS[preset.value];
      if (p) { inputs.pm.value = String(p.pm); inputs.psd.value = String(p.psd); inputs.est.value = String(p.est); inputs.se.value = String(p.se); }
      update();
    });
    Object.values(inputs).forEach((input) => input.addEventListener('input', () => { if (document.activeElement === input) preset.value = 'custom'; update(); }));
    update();
  }

  // ---------------------------------------------------------------- Lesson 6
  const QUIZ = [
    { text: 'A 95% credible interval means that, given the model, prior and data, there is a 95% probability the parameter lies inside it.', truth: true, why: 'This is exactly the Bayesian reading. A frequentist confidence interval does not license this sentence.' },
    { text: 'With a flat Beta(1,1) prior, after 3 successes in 3 trials the posterior mean for θ is 1.0.', truth: false, why: 'The posterior is Beta(4,1) with mean 4/5 = 0.80. Three trials cannot rule out failures.' },
    { text: 'A test with 90% sensitivity and 90% specificity, applied where prevalence is 1%, has a positive predictive value above 50%.', truth: false, why: 'PPV is about 8.3%: roughly 9 true positives against about 99 false positives per 1,000 people.' },
    { text: 'As the sample grows, a reasonable prior has less influence on the posterior.', truth: true, why: 'The likelihood’s weight grows with n while the prior stays fixed, so very different priors converge.' },
    { text: 'A p-value of .03 means there is a 3% probability that the null hypothesis is true.', truth: false, why: 'The p-value is P(data this extreme | null), not P(null | data). The latter needs a prior.' },
    { text: 'The posterior is proportional to the likelihood multiplied by the prior.', truth: true, why: 'Bayes’ rule up to a normalising constant — the whole engine in one line.' },
    { text: 'A Bayes factor BF₁₀ of 1 means the data do not favour either hypothesis.', truth: true, why: 'BF₁₀ = 1 means both hypotheses predicted the observed data equally well.' },
    { text: 'When combining a prior estimate with a new one, the less precise (larger SE) source gets more weight.', truth: false, why: 'Weights are proportional to precision (1/variance), so the more precise source dominates.' },
  ];
  const QUIZ_KEY = 'bayeslab.quiz';

  function loadHistory() {
    try {
      const parsed = JSON.parse(root.localStorage.getItem(QUIZ_KEY) || '[]');
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      return [];
    }
  }

  function saveHistory(entry) {
    const history = loadHistory().concat([entry]).slice(-20);
    try { root.localStorage.setItem(QUIZ_KEY, JSON.stringify(history)); } catch (error) { /* storage unavailable: history is optional */ }
    return history;
  }

  function renderQuiz(host) {
    const cards = QUIZ.map((item, i) => `
      <fieldset class="card" data-testid="quiz-q-${i}">
        <legend>Statement ${i + 1}</legend>
        <p>${item.text}</p>
        <div class="row">
          <label><input type="radio" name="quiz-${i}" value="true" data-testid="quiz-true-${i}"> True</label>
          <label><input type="radio" name="quiz-${i}" value="false" data-testid="quiz-false-${i}"> False</label>
        </div>
        <label>Confidence in your answer <output data-testid="quiz-conf-out-${i}">50%</output>
          <input type="range" min="50" max="100" step="5" value="50" data-testid="quiz-conf-${i}"></label>
        <p class="why" data-testid="quiz-why-${i}" hidden></p>
      </fieldset>`).join('');
    host.innerHTML = `
      <p class="lede">Knowing the answer is half of it; knowing <em>how sure you should be</em> is the other half. Answer each statement and state your confidence (50% = coin flip, 100% = certain). You are scored with the <strong>Brier score</strong>: 0 is perfect, 0.25 is what always saying “50%” earns, and confident wrong answers are punished hard.</p>
      ${cards}
      <div class="row buttons">
        <button type="button" data-testid="quiz-submit" disabled>Score my answers</button>
        <button type="button" data-testid="quiz-reset" class="ghost">Start over</button>
      </div>
      <div class="panel" data-testid="quiz-result" hidden>
        <div class="stats">
          <div><span>Correct</span><strong data-testid="quiz-correct"></strong></div>
          <div><span>Brier score</span><strong data-testid="quiz-brier"></strong></div>
          <div><span>Mean confidence</span><strong data-testid="quiz-meanconf"></strong></div>
        </div>
        <p data-testid="quiz-verdict"></p>
      </div>
      <div class="panel"><h3>Previous attempts</h3><ol data-testid="quiz-history"></ol></div>`;

    const submit = q(host, 'quiz-submit');
    const answered = () => QUIZ.every((_, i) => host.querySelector(`input[name="quiz-${i}"]:checked`));

    function renderHistory() {
      const history = loadHistory();
      q(host, 'quiz-history').innerHTML = history.length
        ? history.map((h) => `<li>${Number(h.brier).toFixed(3)} Brier, ${Number(h.correct)}/${QUIZ.length} correct</li>`).join('')
        : '<li class="muted">None yet.</li>';
    }

    QUIZ.forEach((_, i) => {
      const slider = q(host, `quiz-conf-${i}`);
      slider.addEventListener('input', () => { q(host, `quiz-conf-out-${i}`).textContent = `${slider.value}%`; });
      host.querySelectorAll(`input[name="quiz-${i}"]`).forEach((radio) => radio.addEventListener('change', () => { submit.disabled = !answered(); }));
    });

    submit.addEventListener('click', () => {
      if (!answered()) return;
      const items = [];
      let correct = 0;
      let confidenceSum = 0;
      QUIZ.forEach((item, i) => {
        const saysTrue = host.querySelector(`input[name="quiz-${i}"]:checked`).value === 'true';
        const confidence = Number(q(host, `quiz-conf-${i}`).value) / 100;
        items.push({ p: saysTrue ? confidence : 1 - confidence, outcome: item.truth });
        confidenceSum += confidence;
        const right = saysTrue === item.truth;
        if (right) correct++;
        const why = q(host, `quiz-why-${i}`);
        why.hidden = false;
        why.textContent = `${right ? 'Correct.' : 'Incorrect.'} The statement is ${item.truth ? 'true' : 'false'}. ${item.why}`;
        why.className = `why ${right ? 'right' : 'wrong'}`;
      });
      const brier = B.brierScore(items);
      const meanConfidence = confidenceSum / QUIZ.length;
      q(host, 'quiz-result').hidden = false;
      q(host, 'quiz-correct').textContent = `${correct} / ${QUIZ.length}`;
      q(host, 'quiz-brier').textContent = brier.toFixed(3);
      q(host, 'quiz-meanconf').textContent = pct(meanConfidence, 0);
      const accuracy = correct / QUIZ.length;
      let verdict = 'Well calibrated: confidence roughly matches accuracy.';
      if (meanConfidence - accuracy > 0.15) verdict = 'Overconfident: your stated confidence ran ahead of your accuracy.';
      else if (accuracy - meanConfidence > 0.15) verdict = 'Underconfident: you knew more than you gave yourself credit for.';
      q(host, 'quiz-verdict').textContent = verdict;
      saveHistory({ date: new Date().toISOString().slice(0, 10), brier, correct });
      renderHistory();
    });

    q(host, 'quiz-reset').addEventListener('click', () => renderQuiz(host));
    renderHistory();
  }

  root.Lessons = [
    { id: 'update', title: 'Update a belief', render: renderBeta },
    { id: 'base-rate', title: 'Base-rate trap', render: renderBaseRate },
    { id: 'two', title: 'Two researchers', render: renderTwo },
    { id: 'bayes-factor', title: 'Bayes factor vs p', render: renderBF },
    { id: 'shrinkage', title: 'Shrinkage', render: renderShrink },
    { id: 'quiz', title: 'Calibration quiz', render: renderQuiz },
  ];
  root.LessonInternals = { samplesToAgree, QUIZ };
})(window);
