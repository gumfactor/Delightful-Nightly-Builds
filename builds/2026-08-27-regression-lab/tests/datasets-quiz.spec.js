const { test, expect } = require('@playwright/test');
const D = require('../src/datasets.js');
const Q = require('../src/quiz.js');

test.describe('preset datasets — each triggers its intended diagnostic', () => {
  test('well-behaved preset is not flagged for heteroscedasticity or non-linearity', () => {
    const diag = Q.diagnoseDataset(D.PRESETS['well-behaved'].points);
    expect(diag.verdict).toBe('well-behaved');
  });

  test('heteroscedastic preset is diagnosed as heteroscedastic', () => {
    const diag = Q.diagnoseDataset(D.PRESETS.heteroscedastic.points);
    expect(diag.verdict).toBe('heteroscedastic');
  });

  test('non-linear preset is diagnosed as non-linear', () => {
    const diag = Q.diagnoseDataset(D.PRESETS['non-linear'].points);
    expect(diag.verdict).toBe('non-linear');
  });

  test('outlier preset is diagnosed as an outlier, dominating Cook\'s Distance', () => {
    const diag = Q.diagnoseDataset(D.PRESETS.outlier.points);
    expect(diag.verdict).toBe('outlier');
    expect(diag.dominance).toBeGreaterThan(5);
  });

  test('every preset except custom has at least 4 points (enough for full diagnostics)', () => {
    D.PRESET_ORDER.filter((k) => k !== 'custom').forEach((key) => {
      expect(D.PRESETS[key].points.length).toBeGreaterThanOrEqual(4);
    });
  });
});

test.describe('multicollinearity data generator', () => {
  test('actual correlation tracks the requested target correlation', () => {
    const low = D.buildMulticollinearData(0.0, 20);
    const high = D.buildMulticollinearData(0.95, 20);
    const M = require('../src/math.js');
    const rLow = Math.abs(M.correlation(low.x1, low.x2));
    const rHigh = Math.abs(M.correlation(high.x1, high.x2));
    expect(rHigh).toBeGreaterThan(rLow);
    expect(rHigh).toBeGreaterThan(0.85);
  });

  test('VIF grows sharply as requested correlation approaches 1', () => {
    const M = require('../src/math.js');
    const mid = D.buildMulticollinearData(0.5, 20);
    const high = D.buildMulticollinearData(0.98, 20);
    const vifMid = M.vifPair(mid.x1, mid.x2).vif;
    const vifHigh = M.vifPair(high.x1, high.x2).vif;
    expect(vifHigh).toBeGreaterThan(vifMid * 3);
  });
});

test.describe('quiz session generation', () => {
  test('a quiz session has exactly 4 diagnose questions and 8 concept questions', () => {
    const session = Q.buildQuizSession(1);
    expect(session.filter((q) => q.type === 'diagnose').length).toBe(4);
    expect(session.filter((q) => q.type === 'concept').length).toBe(8);
    expect(session.length).toBe(12);
  });

  test('the same seed always reproduces the same question order', () => {
    const a = Q.buildQuizSession(7).map((q) => q.id);
    const b = Q.buildQuizSession(7).map((q) => q.id);
    expect(a).toEqual(b);
  });

  test('different seeds produce different question orderings', () => {
    const a = Q.buildQuizSession(7).map((q) => q.id);
    const b = Q.buildQuizSession(8).map((q) => q.id);
    expect(a).not.toEqual(b);
  });

  test('every diagnose question\'s correctIndex points at the option matching its live-computed verdict', () => {
    const session = Q.buildQuizSession(3);
    session.filter((q) => q.type === 'diagnose').forEach((q) => {
      expect(q.options[q.correctIndex]).toBe(Q.DIAGNOSIS_LABELS[q.verdict]);
    });
  });

  test('every concept question has exactly one correct option within range', () => {
    Q.CONCEPT_QUESTIONS.forEach((q) => {
      expect(q.correct).toBeGreaterThanOrEqual(0);
      expect(q.correct).toBeLessThan(q.options.length);
    });
  });
});
