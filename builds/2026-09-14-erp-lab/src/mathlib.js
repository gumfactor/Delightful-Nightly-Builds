'use strict';

/* Deterministic PRNG (mulberry32) + Box-Muller Gaussian transform.
   Everything in this file is pure functions over plain arrays/typed arrays —
   no DOM access — so it can be exercised directly from Playwright's
   page.evaluate() and cross-checked against hand-computed reference values. */

function mulberry32(seed) {
  let a = seed >>> 0;
  return function next() {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function makeGaussianRng(uniformRng) {
  let spare = null;
  return function nextGaussian() {
    if (spare !== null) {
      const v = spare;
      spare = null;
      return v;
    }
    let u1;
    do {
      u1 = uniformRng();
    } while (u1 <= Number.EPSILON);
    const u2 = uniformRng();
    const mag = Math.sqrt(-2.0 * Math.log(u1));
    const z0 = mag * Math.cos(2.0 * Math.PI * u2);
    const z1 = mag * Math.sin(2.0 * Math.PI * u2);
    spare = z1;
    return z0;
  };
}

function mean(arr) {
  let sum = 0;
  for (let i = 0; i < arr.length; i++) sum += arr[i];
  return sum / arr.length;
}

function standardDeviation(arr) {
  const m = mean(arr);
  let sumSq = 0;
  for (let i = 0; i < arr.length; i++) sumSq += (arr[i] - m) * (arr[i] - m);
  return Math.sqrt(sumSq / arr.length);
}

function peakToPeak(arr) {
  let min = Infinity;
  let max = -Infinity;
  for (let i = 0; i < arr.length; i++) {
    if (arr[i] < min) min = arr[i];
    if (arr[i] > max) max = arr[i];
  }
  return max - min;
}

/* Iterative radix-2 Cooley-Tukey FFT. `n` must be a power of 2.
   Returns { re, im } of the same length as the input. */
function fft(reInput, imInput) {
  const n = reInput.length;
  if (n === 0 || (n & (n - 1)) !== 0) {
    throw new Error('fft: length must be a power of 2');
  }
  const re = Float64Array.from(reInput);
  const im = imInput ? Float64Array.from(imInput) : new Float64Array(n);

  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1;
    for (; j & bit; bit >>= 1) {
      j ^= bit;
    }
    j ^= bit;
    if (i < j) {
      let tmp = re[i];
      re[i] = re[j];
      re[j] = tmp;
      tmp = im[i];
      im[i] = im[j];
      im[j] = tmp;
    }
  }

  for (let len = 2; len <= n; len <<= 1) {
    const ang = (-2 * Math.PI) / len;
    const wRe = Math.cos(ang);
    const wIm = Math.sin(ang);
    for (let i = 0; i < n; i += len) {
      let curRe = 1;
      let curIm = 0;
      const half = len / 2;
      for (let j = 0; j < half; j++) {
        const uRe = re[i + j];
        const uIm = im[i + j];
        const tRe = re[i + j + half] * curRe - im[i + j + half] * curIm;
        const tIm = re[i + j + half] * curIm + im[i + j + half] * curRe;
        re[i + j] = uRe + tRe;
        im[i + j] = uIm + tIm;
        re[i + j + half] = uRe - tRe;
        im[i + j + half] = uIm - tIm;
        const nextRe = curRe * wRe - curIm * wIm;
        const nextIm = curRe * wIm + curIm * wRe;
        curRe = nextRe;
        curIm = nextIm;
      }
    }
  }
  return { re, im };
}

/* One-sided power spectrum (DC .. Nyquist-1) from an FFT result. */
function powerSpectrum(re, im, sampleRate) {
  const n = re.length;
  const nBins = n / 2;
  const freqs = new Float64Array(nBins);
  const power = new Float64Array(nBins);
  for (let k = 0; k < nBins; k++) {
    freqs[k] = (k * sampleRate) / n;
    power[k] = (re[k] * re[k] + im[k] * im[k]) / (n * n);
  }
  return { freqs, power };
}

/* Centered moving-average low-pass filter. */
function movingAverageFilter(signal, windowSize) {
  const n = signal.length;
  const out = new Float64Array(n);
  const half = Math.floor(windowSize / 2);
  for (let i = 0; i < n; i++) {
    let sum = 0;
    let count = 0;
    for (let j = -half; j <= half; j++) {
      const idx = i + j;
      if (idx >= 0 && idx < n) {
        sum += signal[idx];
        count++;
      }
    }
    out[i] = sum / count;
  }
  return out;
}

function fisherYatesShuffle(arr, uniformRng) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(uniformRng() * (i + 1));
    const tmp = arr[i];
    arr[i] = arr[j];
    arr[j] = tmp;
  }
  return arr;
}

/* Two-sample permutation test on the difference of means, with
   add-one Laplace smoothing on the p-value (standard convention:
   the observed assignment itself always counts as one "permutation"
   at least as extreme as itself). */
function permutationTest(groupA, groupB, nPermutations, uniformRng) {
  const observedDiff = mean(groupA) - mean(groupB);
  const nA = groupA.length;
  const combined = groupA.concat(groupB);
  const nullDistribution = new Array(nPermutations);
  let countExtreme = 0;
  for (let p = 0; p < nPermutations; p++) {
    const shuffled = fisherYatesShuffle(combined.slice(), uniformRng);
    const permA = shuffled.slice(0, nA);
    const permB = shuffled.slice(nA);
    const d = Math.abs(mean(permA) - mean(permB));
    nullDistribution[p] = d;
    if (d >= Math.abs(observedDiff)) countExtreme++;
  }
  const pValue = (countExtreme + 1) / (nPermutations + 1);
  return { observedDiff, nullDistribution, pValue, nPermutations };
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    mulberry32,
    makeGaussianRng,
    mean,
    standardDeviation,
    peakToPeak,
    fft,
    powerSpectrum,
    movingAverageFilter,
    fisherYatesShuffle,
    permutationTest,
  };
}
