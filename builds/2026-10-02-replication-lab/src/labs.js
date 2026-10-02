/* Lab definitions: controls, prediction prompt, simulation and plain-language takeaway. */
(function (root) {
  'use strict';
  const S = root.Stats;
  const C = root.Charts;

  const pct = (value, digits) => (value * 100).toFixed(digits === undefined ? 1 : digits) + '%';
  const fixed = (value, digits) => value.toFixed(digits === undefined ? 2 : digits);

  const labs = [
    {
      id: 'power',
      tab: 'Power',
      title: 'Power: how often does a real effect show up?',
      intro: 'A real effect exists, but each study is a noisy sample. Power is the share of identical studies that reach significance. Low power means most real effects are missed, and the significant ones are less trustworthy than they look.',
      controls: [
        { id: 'd', label: 'True effect (Cohen\'s d)', min: 0.1, max: 1.2, step: 0.05, value: 0.4, fmt: (v) => fixed(v) },
        { id: 'n', label: 'Participants per group', min: 5, max: 300, step: 1, value: 25, fmt: (v) => String(v) },
        { id: 'alpha', label: 'Significance threshold (alpha)', min: 0.005, max: 0.1, step: 0.005, value: 0.05, fmt: (v) => fixed(v, 3) },
        { id: 'prior', label: 'Share of tested hypotheses that are true', min: 0.01, max: 0.9, step: 0.01, value: 0.1, fmt: (v) => pct(v, 0) },
      ],
      predict: { question: 'Out of 100 identical studies with these settings, how many will reach p < alpha?', min: 0, max: 100, value: 50, unit: 'of 100' },
      run(params, seed) {
        const sim = S.simulateStudies({ d: params.d, n: params.n, alpha: params.alpha, reps: 2000, seed });
        const analytic = S.analyticPower(params.d, params.n, params.alpha);
        const needed = S.requiredN(params.d, params.alpha, 0.8, 5000);
        const value = S.ppv(params.prior, sim.power, params.alpha);
        const hist = S.histogram(sim.pValues, 20, 0, 1);
        return {
          actual: sim.power * 100,
          stats: [
            { k: 'Simulated power', v: pct(sim.power), id: 'power' },
            { k: 'Analytic power (approx.)', v: pct(analytic) },
            { k: 'n per group for 80% power', v: needed === null ? '> 5000' : String(needed), id: 'needed' },
            { k: 'Chance a significant result is true', v: pct(value), id: 'ppv' },
          ],
          draw: (canvas) => C.drawHistogram(canvas, hist, {
            xLabel: 'p-value across 2,000 simulated studies',
            highlight: (x) => x < params.alpha,
            lines: [{ x: params.alpha, color: 'bad', label: 'alpha', dash: true }],
          }),
          takeaway: 'Red bars are the studies that "worked": ' + pct(sim.power, 0) + ' of them. ' +
            (sim.power < 0.5 ? 'Most real effects are missed at this sample size. ' : sim.power < 0.8 ? 'Better than a coin flip, still below the usual 80% target. ' : 'This design is adequately powered. ') +
            'If only ' + pct(params.prior, 0) + ' of tested ideas are true, a significant result has a ' + pct(value, 0) + ' chance of being real. You would need ' +
            (needed === null ? 'an impractical number of' : needed) + ' participants per group for 80% power.',
        };
      },
    },
    {
      id: 'peeking',
      tab: 'Peeking',
      title: 'Peeking: checking the data until it works',
      intro: 'There is no effect at all. A researcher tests after every batch of participants and stops as soon as p < alpha. Each look is another chance for noise to cross the line.',
      controls: [
        { id: 'nStart', label: 'Participants per group at the first look', min: 5, max: 50, step: 1, value: 10, fmt: (v) => String(v) },
        { id: 'step', label: 'New participants per group between looks', min: 1, max: 25, step: 1, value: 5, fmt: (v) => String(v) },
        { id: 'nMax', label: 'Maximum per group', min: 20, max: 300, step: 5, value: 100, fmt: (v) => String(v) },
        { id: 'alpha', label: 'Significance threshold (alpha)', min: 0.005, max: 0.1, step: 0.005, value: 0.05, fmt: (v) => fixed(v, 3) },
      ],
      predict: { question: 'With no real effect, what percent of studies will end up "significant" if the researcher peeks after every batch?', min: 0, max: 100, value: 10, unit: '%' },
      run(params, seed) {
        const nMax = Math.max(params.nMax, params.nStart);
        const result = S.simulatePeeking({ d: 0, nStart: params.nStart, step: params.step, nMax, alpha: params.alpha, reps: 1500, seed });
        const peak = Math.max(result.falsePositiveRate, params.alpha * 2);
        return {
          actual: result.falsePositiveRate * 100,
          stats: [
            { k: 'Looks at the data', v: String(result.looks.length) },
            { k: 'False positives, peeking', v: pct(result.falsePositiveRate), id: 'peek' },
            { k: 'False positives, one planned test', v: pct(result.fixedDesignRate), id: 'fixed' },
            { k: 'Inflation', v: fixed(result.falsePositiveRate / Math.max(result.fixedDesignRate, 1e-9), 1) + 'x' },
          ],
          draw: (canvas) => C.drawLines(canvas, {
            xLabel: 'participants per group at each look',
            yMax: Math.min(1, Math.ceil(peak * 10 + 1) / 10),
            series: [
              { label: 'cumulative false positives (peeking)', color: 'bad', points: result.looks.map((n, i) => [n, result.cumulativeRate[i]]) },
              { label: 'alpha', color: 'muted', dash: true, points: [[result.looks[0], params.alpha], [result.looks[result.looks.length - 1] + 0.001, params.alpha]] },
            ],
          }),
          takeaway: 'Nothing was real, yet ' + pct(result.falsePositiveRate, 0) + ' of studies reported an effect after ' + result.looks.length +
            ' looks, against ' + pct(result.fixedDesignRate, 0) + ' when the sample size was fixed in advance. Decide the stopping rule before collecting data, or use a method built for sequential designs.',
        };
      },
    },
    {
      id: 'forking',
      tab: 'Many outcomes',
      title: 'Many outcomes: report whichever one worked',
      intro: 'Still no real effect, but each participant is measured on several outcomes and the paper reports the study as a success if any outcome is significant. Correlated outcomes inflate less, because they are partly the same measurement.',
      controls: [
        { id: 'k', label: 'Number of outcomes measured', min: 1, max: 40, step: 1, value: 8, fmt: (v) => String(v) },
        { id: 'rho', label: 'Correlation between outcomes', min: 0, max: 0.9, step: 0.05, value: 0, fmt: (v) => fixed(v) },
        { id: 'n', label: 'Participants per group', min: 10, max: 200, step: 5, value: 30, fmt: (v) => String(v) },
        { id: 'alpha', label: 'Significance threshold (alpha)', min: 0.005, max: 0.1, step: 0.005, value: 0.05, fmt: (v) => fixed(v, 3) },
        { id: 'correction', label: 'Correction applied', type: 'select', value: 'none', options: [['none', 'None'], ['bonferroni', 'Bonferroni'], ['holm', 'Holm']] },
      ],
      predict: { question: 'What percent of no-effect studies will have at least one significant outcome?', min: 0, max: 100, value: 15, unit: '%' },
      run(params, seed) {
        const result = S.simulateForking({ k: params.k, rho: params.rho, n: params.n, alpha: params.alpha, reps: 1000, seed, correction: params.correction });
        return {
          actual: result.familywiseRate * 100,
          stats: [
            { k: 'Any outcome significant', v: pct(result.familywiseRate), id: 'family' },
            { k: 'First outcome alone', v: pct(result.singleOutcomeRate), id: 'single' },
            { k: 'Formula if independent', v: pct(result.independentExpectation) },
            { k: 'Average smallest p-value', v: fixed(result.meanSmallestP, 3) },
          ],
          draw: (canvas) => C.drawBars(canvas, [
            { label: 'one pre-chosen\noutcome', value: result.singleOutcomeRate, color: 'good' },
            { label: 'any outcome\n(as simulated)', value: result.familywiseRate, color: 'bad' },
            { label: 'independent\nformula', value: result.independentExpectation, color: 'muted' },
          ], Math.max(0.2, Math.ceil(Math.max(result.familywiseRate, result.independentExpectation) * 10) / 10)),
          takeaway: 'With ' + params.k + ' outcomes' + (params.correction === 'none' ? ' and no correction' : ' and ' + params.correction + ' correction') + ', ' +
            pct(result.familywiseRate, 0) + ' of studies found something, versus ' + pct(result.singleOutcomeRate, 0) + ' for a single pre-chosen outcome. Pre-register the primary outcome, or correct for the number of tests.',
        };
      },
    },
    {
      id: 'curse',
      tab: 'Winner\'s curse',
      title: 'Winner\'s curse: significant results exaggerate',
      intro: 'The effect is real but small. If only significant studies get written up, the published effect sizes are the lucky overestimates. Replications of those studies then "shrink".',
      controls: [
        { id: 'd', label: 'True effect (Cohen\'s d)', min: 0.1, max: 1.0, step: 0.05, value: 0.3, fmt: (v) => fixed(v) },
        { id: 'n', label: 'Participants per group', min: 10, max: 200, step: 5, value: 25, fmt: (v) => String(v) },
        { id: 'alpha', label: 'Significance threshold (alpha)', min: 0.005, max: 0.1, step: 0.005, value: 0.05, fmt: (v) => fixed(v, 3) },
      ],
      predict: { question: 'What will the average observed effect (d) be among the significant studies?', min: 0, max: 2, step: 0.05, value: 0.3, unit: 'd', digits: 2 },
      run(params, seed) {
        const sim = S.simulateStudies({ d: params.d, n: params.n, alpha: params.alpha, reps: 3000, seed });
        const published = sim.meanEffectSignificant;
        const hist = S.histogram(sim.effects, 30, -1, 2);
        const critical = S.tCritical(params.alpha, 2 * params.n - 2) * Math.sqrt(2 / params.n);
        const lines = [{ x: params.d, color: 'good', label: 'true d' }, { x: critical, color: 'bad', label: 'significance cutoff', dash: true }];
        if (published !== null) lines.push({ x: published, color: 'warn', label: 'published avg' });
        return {
          actual: published === null ? 0 : published,
          stats: [
            { k: 'True effect', v: fixed(params.d) },
            { k: 'Average of all studies', v: fixed(sim.meanEffectAll), id: 'all' },
            { k: 'Average of significant studies', v: published === null ? 'none' : fixed(published), id: 'published' },
            { k: 'Overestimate', v: published === null ? 'n/a' : fixed(published / params.d, 1) + 'x', id: 'inflation' },
          ],
          draw: (canvas) => C.drawHistogram(canvas, hist, {
            xLabel: 'observed effect size d in each study',
            xFormat: (v) => fixed(v, 1),
            highlight: (x) => x > critical,
            lines,
          }),
          takeaway: published === null ? 'No study reached significance at this size.' :
            'Averaged over every study the estimate is unbiased (' + fixed(sim.meanEffectAll) + '). Among the ' + pct(sim.power, 0) + ' that were significant it is ' + fixed(published) +
            ', ' + fixed(published / params.d, 1) + 'x the truth. Larger samples shrink this gap because small studies can only be significant when their estimate is large.',
        };
      },
    },
    {
      id: 'bayes',
      tab: 'Bayes',
      title: 'Bayesian updating: what the data do to your belief',
      intro: 'A coin-flip style experiment: some number of successes in n trials. The prior is what you believed before, the posterior is what you believe after. Strong priors move slowly; weak ones follow the data.',
      live: true,
      controls: [
        { id: 'n', label: 'Trials', min: 0, max: 200, step: 1, value: 20, fmt: (v) => String(v) },
        { id: 'k', label: 'Successes', min: 0, max: 200, step: 1, value: 14, fmt: (v) => String(v) },
        { id: 'prior', label: 'Prior belief', type: 'select', value: 'flat', options: [['flat', 'Flat: Beta(1, 1)'], ['skeptic', 'Skeptic around 50%: Beta(20, 20)'], ['optimist', 'Optimist around 80%: Beta(8, 2)']] },
        { id: 'ropeHalf', label: 'Practical equivalence zone around 50% (half-width)', min: 0.01, max: 0.2, step: 0.01, value: 0.05, fmt: (v) => fixed(v) },
      ],
      run(params) {
        const priors = { flat: [1, 1], skeptic: [20, 20], optimist: [8, 2] };
        const [priorA, priorB] = priors[params.prior];
        const successes = Math.min(params.k, params.n);
        const low = 0.5 - params.ropeHalf;
        const high = 0.5 + params.ropeHalf;
        const post = S.betaPosterior(priorA, priorB, successes, params.n, low, high);
        const bayesFactor = S.bayesFactor10(successes, params.n);
        const peak = Math.max(1, ...Array.from({ length: 99 }, (_, i) => S.betaPdf(post.a, post.b, (i + 1) / 100)));
        return {
          stats: [
            { k: 'Posterior mean', v: pct(post.mean), id: 'mean' },
            { k: '95% credible interval', v: pct(post.interval[0], 0) + ' to ' + pct(post.interval[1], 0), id: 'interval' },
            { k: 'Probability inside the zone', v: pct(post.pRope, 0), id: 'rope' },
            { k: 'Bayes factor vs 50% (flat alt.)', v: bayesFactor >= 1000 ? '> 1000' : bayesFactor < 0.001 ? '< 0.001' : fixed(bayesFactor, 2), id: 'bf' },
          ],
          draw: (canvas) => C.drawDensities(canvas, {
            yMax: Math.ceil((peak * 1.1) / 4) * 4,
            curves: [
              { label: 'prior', color: 'muted', dash: true, pdf: (x) => S.betaPdf(priorA, priorB, x) },
              { label: 'posterior', color: 'accent', pdf: (x) => S.betaPdf(post.a, post.b, x) },
            ],
            shade: [{ from: low, to: high, color: 'good' }],
          }),
          takeaway: 'After ' + successes + ' of ' + params.n + ' the best estimate is ' + pct(post.mean, 0) + ', and the data leave a 95% interval of ' + pct(post.interval[0], 0) + ' to ' + pct(post.interval[1], 0) +
            '. There is a ' + pct(post.pRope, 0) + ' chance the true rate is practically 50%. Change the prior and watch how much the same data are worth.',
        };
      },
    },
  ];

  root.Labs = labs;
})(window);
