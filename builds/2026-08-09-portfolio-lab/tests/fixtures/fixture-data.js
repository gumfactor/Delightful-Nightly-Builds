// TEST FIXTURE — synthetic 4-asset dataset for automated tests only.
// Not real market data. Injected via page.addInitScript() before
// navigation so data.js's `typeof window.PORTFOLIO_DATA === 'undefined'`
// guard leaves it untouched.
//
// Hand-constructed so cov_matrix[i][j] = corr[i][j] * vol[i] * vol[j]
// exactly, for volatility = [0.20, 0.10, 0.30, 0.05] and:
//   corr = [[ 1.0,  0.2,  0.6, -0.3],
//           [ 0.2,  1.0,  0.1, -0.5],
//           [ 0.6,  0.1,  1.0,  0.0],
//           [-0.3, -0.5,  0.0,  1.0]]
window.PORTFOLIO_DATA = {
  generated_at: '2026-08-09T00:00:00Z',
  years: 3,
  tickers: ['AAA', 'BBB', 'CCC', 'DDD'],
  meta: {
    AAA: { name: 'Fixture Asset AAA', sector: 'Test' },
    BBB: { name: 'Fixture Asset BBB', sector: 'Test' },
    CCC: { name: 'Fixture Asset CCC', sector: 'Test' },
    DDD: { name: 'Fixture Asset DDD', sector: 'Test' },
  },
  mean_return: { AAA: 0.10, BBB: 0.06, CCC: 0.14, DDD: 0.03 },
  volatility: { AAA: 0.20, BBB: 0.10, CCC: 0.30, DDD: 0.05 },
  cov_matrix: [
    [0.04, 0.004, 0.036, -0.003],
    [0.004, 0.01, 0.003, -0.0025],
    [0.036, 0.003, 0.09, 0.0],
    [-0.003, -0.0025, 0.0, 0.0025],
  ],
  corr_matrix: [
    [1.0, 0.2, 0.6, -0.3],
    [0.2, 1.0, 0.1, -0.5],
    [0.6, 0.1, 1.0, 0.0],
    [-0.3, -0.5, 0.0, 1.0],
  ],
};
