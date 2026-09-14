'use strict';

/* ERP epoch generation, averaging, SNR measurement, artifact rejection,
   and window-amplitude extraction for the CIT permutation test.
   Depends on mathlib.js (mean/standardDeviation/peakToPeak). Pure functions
   only — no DOM access — so Playwright can call these directly. */

const SAMPLE_RATE = 256; // Hz
const EPOCH_MS = 1000; // 1 second epochs
const N_SAMPLES = (SAMPLE_RATE * EPOCH_MS) / 1000; // 256 samples, power of 2 for FFT
const PRE_STIM_MS = 200;
const PRE_STIM_SAMPLES = Math.round((PRE_STIM_MS / 1000) * SAMPLE_RATE); // 51

function msToSampleIndex(ms) {
  return PRE_STIM_SAMPLES + Math.round((ms / 1000) * SAMPLE_RATE);
}

/* A Gaussian-shaped ERP component: amplitude at `latencyMs` post-stimulus,
   full-width-half-max of `widthMs`. Returns a Float64Array template with
   zero baseline before/after the bump — this is what makes the pre-stimulus
   window a clean noise-only reference for SNR/artifact measurement. */
function generateERPTemplate(latencyMs, amplitude, widthMs) {
  const template = new Float64Array(N_SAMPLES);
  const sigma = widthMs / 2.3548; // FWHM -> Gaussian sigma
  const msPerSample = 1000 / SAMPLE_RATE;
  for (let i = 0; i < N_SAMPLES; i++) {
    const tMs = (i - PRE_STIM_SAMPLES) * msPerSample;
    const z = (tMs - latencyMs) / sigma;
    template[i] = amplitude * Math.exp(-0.5 * z * z);
  }
  return template;
}

function generateEpoch(template, noiseSD, gaussianRng) {
  const epoch = new Float64Array(N_SAMPLES);
  for (let i = 0; i < N_SAMPLES; i++) {
    epoch[i] = template[i] + gaussianRng() * noiseSD;
  }
  return epoch;
}

/* A slow, whole-epoch deflection standing in for an eye-blink artifact. */
function addBlinkArtifact(epoch, blinkAmplitude) {
  const n = epoch.length;
  const out = Float64Array.from(epoch);
  for (let i = 0; i < n; i++) {
    out[i] += blinkAmplitude * Math.sin((Math.PI * i) / n);
  }
  return out;
}

function generateEpochSet(template, noiseSD, nTrials, gaussianRng, uniformRng, blinkRate, blinkAmplitude) {
  const epochs = [];
  const isArtifact = [];
  for (let t = 0; t < nTrials; t++) {
    let epoch = generateEpoch(template, noiseSD, gaussianRng);
    const contaminated = blinkRate > 0 && uniformRng() < blinkRate;
    if (contaminated) {
      epoch = addBlinkArtifact(epoch, blinkAmplitude);
    }
    epochs.push(epoch);
    isArtifact.push(contaminated);
  }
  return { epochs, isArtifact };
}

function averageEpochs(epochs) {
  const n = epochs[0].length;
  const avg = new Float64Array(n);
  for (let e = 0; e < epochs.length; e++) {
    const epoch = epochs[e];
    for (let i = 0; i < n; i++) avg[i] += epoch[i];
  }
  for (let i = 0; i < n; i++) avg[i] /= epochs.length;
  return avg;
}

/* Reject any epoch whose peak-to-peak amplitude exceeds `thresholdUV`. */
function rejectArtifacts(epochs, thresholdUV, peakToPeakFn) {
  const clean = [];
  let rejectedCount = 0;
  for (let i = 0; i < epochs.length; i++) {
    if (peakToPeakFn(epochs[i]) > thresholdUV) {
      rejectedCount++;
    } else {
      clean.push(epochs[i]);
    }
  }
  return { clean, rejectedCount };
}

/* Mean amplitude within a post-stimulus window, e.g. the classic 300-500ms
   P300 measurement window. Used as the single-trial summary statistic fed
   into the CIT permutation test. */
function windowMeanAmplitude(epoch, windowStartMs, windowEndMs) {
  const startIdx = msToSampleIndex(windowStartMs);
  const endIdx = Math.min(msToSampleIndex(windowEndMs), epoch.length - 1);
  let sum = 0;
  let count = 0;
  for (let i = startIdx; i <= endIdx; i++) {
    sum += epoch[i];
    count++;
  }
  return sum / count;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    SAMPLE_RATE,
    N_SAMPLES,
    PRE_STIM_SAMPLES,
    PRE_STIM_MS,
    msToSampleIndex,
    generateERPTemplate,
    generateEpoch,
    addBlinkArtifact,
    generateEpochSet,
    averageEpochs,
    rejectArtifacts,
    windowMeanAmplitude,
  };
}
