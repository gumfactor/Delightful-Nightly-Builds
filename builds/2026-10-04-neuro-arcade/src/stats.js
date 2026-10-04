(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.NAStats = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  function mean(values) {
    return values.length ? values.reduce((sum, v) => sum + v, 0) / values.length : null;
  }

  function sd(values) {
    if (values.length < 2) return null;
    const mu = mean(values);
    return Math.sqrt(values.reduce((sum, v) => sum + (v - mu) ** 2, 0) / (values.length - 1));
  }

  // Inverse normal CDF (Acklam's rational approximation, |error| < 1.2e-9)
  function probit(p) {
    if (!(p > 0 && p < 1)) throw new RangeError('probit requires 0 < p < 1');
    const a = [-39.69683028665376, 220.9460984245205, -275.9285104469687, 138.357751867269, -30.66479806614716, 2.506628277459239];
    const b = [-54.47609879822406, 161.5858368580409, -155.6989798598866, 66.80131188771972, -13.28068155288572];
    const c = [-0.007784894002430293, -0.3223964580411365, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783];
    const d = [0.007784695709041462, 0.3224671290700398, 2.445134137142996, 3.754408661907416];
    const low = 0.02425;
    let q;
    if (p < low) {
      q = Math.sqrt(-2 * Math.log(p));
      return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
        ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
    }
    if (p <= 1 - low) {
      q = p - 0.5;
      const r = q * q;
      return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q /
        (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
    }
    q = Math.sqrt(-2 * Math.log(1 - p));
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
      ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
  }

  // Standard normal CDF via Abramowitz & Stegun 7.1.26 erf (|error| < 1.5e-7)
  function normalCdf(z) {
    const x = Math.abs(z) / Math.SQRT2;
    const t = 1 / (1 + 0.3275911 * x);
    const poly = ((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592;
    const erf = 1 - poly * t * Math.exp(-x * x);
    return z >= 0 ? 0.5 * (1 + erf) : 0.5 * (1 - erf);
  }

  // d' with log-linear correction so perfect or zero rates stay finite
  function dPrime(hits, signalTrials, falseAlarms, noiseTrials) {
    if (signalTrials <= 0 || noiseTrials <= 0) return null;
    const hitRate = (hits + 0.5) / (signalTrials + 1);
    const faRate = (falseAlarms + 0.5) / (noiseTrials + 1);
    return probit(hitRate) - probit(faRate);
  }

  // Fraction of a Normal(mean, sd) reference population scoring at or below value
  function percentile(value, refMean, refSd) {
    return normalCdf((value - refMean) / refSd);
  }

  return { mean, sd, probit, normalCdf, dPrime, percentile };
});
