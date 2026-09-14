'use strict';

/* Quiz question bank: 8 fixed conceptual questions + 8 questions
   regenerated on every load from the live math functions in mathlib.js
   and epochs.js. Depends on those two files being loaded first (classic
   <script> globals) in the browser, or required directly in Node tests. */

var FIXED_QUESTIONS = [
  {
    prompt: 'You average N single trials of EEG together to compute an ERP. What happens to the amplitude of random (trial-to-trial) noise in the average as N increases?',
    choices: [
      'It stays the same regardless of N',
      'It decreases proportionally to 1/N',
      'It decreases proportionally to 1/√N',
      'It increases proportionally to √N',
    ],
    correctIndex: 2,
    explanation:
      'Averaging N independent noisy trials reduces the noise standard deviation by a factor of √N, because the noise is uncorrelated across trials while the signal (which is time-locked to the stimulus) stays constant and adds up directly.',
  },
  {
    prompt: 'EEG recordings often show a sharp power-spectrum peak at 50 or 60 Hz. What causes it?',
    choices: [
      'A genuine brain oscillation at that frequency',
      'Electrical mains power-line interference',
      'The sampling rate of the amplifier',
      'The subject’s heartbeat',
    ],
    correctIndex: 1,
    explanation:
      'Mains electrical power (50 Hz in most of the world, 60 Hz in North America) is picked up by EEG electrodes and cabling as line noise, unrelated to brain activity.',
  },
  {
    prompt: 'In a permutation test comparing two conditions, what does the null distribution represent?',
    choices: [
      'The distribution of the raw data in each condition',
      'The distribution of the test statistic you would expect if condition labels carried no real information (built by reshuffling labels many times)',
      'The theoretical normal distribution of the test statistic',
      'The distribution of measurement noise only',
    ],
    correctIndex: 1,
    explanation:
      'A permutation test builds its null distribution empirically: it repeatedly shuffles which trials belong to which condition and recomputes the statistic each time, simulating what you’d see if the condition assignment were meaningless.',
  },
  {
    prompt: 'In the P300 Concealed Information Test (CIT), a significantly larger P300 to "probe" (crime-relevant) items than to "irrelevant" items is interpreted as evidence of what?',
    choices: [
      'The subject is lying about their name',
      'The subject recognizes the probe items as familiar/significant — i.e. concealed knowledge',
      'The subject has a neurological disorder',
      'The recording equipment is miscalibrated',
    ],
    correctIndex: 1,
    explanation:
      'The CIT (also called the Guilty Knowledge Test) infers concealed recognition, not deception directly — a larger P300 to probes reflects that the item is subjectively significant/familiar to the subject.',
  },
  {
    prompt: 'Why is the CIT not a perfect test — what statistical concept explains why a truly innocent subject (no real concealed knowledge) could still occasionally produce a "significant" probe-vs-irrelevant difference?',
    choices: [
      'Measurement error never occurs in EEG',
      'The false-positive rate (Type I error): even with no true effect, a p < 0.05 threshold flags roughly 5% of truly null cases as "significant" by chance',
      'Innocent subjects always have larger P300s',
      'The permutation test is deterministic and cannot be wrong',
    ],
    correctIndex: 1,
    explanation:
      'Any significance threshold has a nonzero false-positive rate by construction — at alpha = 0.05, about 1 in 20 truly innocent subjects will show a "significant" result purely from sampling noise, which is exactly what the Innocent Suspect toggle in the CIT Lab tab demonstrates.',
  },
  {
    prompt: 'Eye blinks contaminate EEG trials with large, slow voltage deflections. What is a basic, commonly used method to automatically flag and reject those trials?',
    choices: [
      'Delete every trial recorded in the second half of the session',
      'Threshold rejection on peak-to-peak amplitude — reject any trial whose max-minus-min voltage exceeds a chosen threshold',
      'Always keep every trial to preserve statistical power',
      'Manually re-record the entire session',
    ],
    correctIndex: 1,
    explanation:
      'Peak-to-peak amplitude thresholding is a simple, widely used artifact-rejection method: blink and other movement artifacts typically produce much larger voltage swings than genuine brain signal, so a threshold on max-minus-min voltage catches most of them.',
  },
  {
    prompt: 'What does a low-pass moving-average filter do to a signal?',
    choices: [
      'Amplifies high-frequency content and attenuates low-frequency content',
      'Attenuates high-frequency content while preserving low-frequency content',
      'Shifts every frequency component by a fixed amount',
      'Has no effect on the frequency spectrum',
    ],
    correctIndex: 1,
    explanation:
      'A moving average smooths a signal by locally averaging nearby samples, which suppresses fast (high-frequency) fluctuations while leaving slow (low-frequency) trends largely intact — a simple low-pass filter.',
  },
  {
    prompt: 'The classic radix-2 Cooley-Tukey FFT algorithm requires the input length to be a power of 2. Why?',
    choices: [
      'It is an arbitrary historical convention with no mathematical reason',
      'The algorithm recursively splits the sequence into halves at every stage, which only divides evenly all the way down to length 1 when the length is a power of 2',
      'Non-power-of-2 signals cannot contain any frequency information',
      'It is required by the sampling theorem',
    ],
    correctIndex: 1,
    explanation:
      'Radix-2 Cooley-Tukey works by recursively splitting the DFT of length N into two DFTs of length N/2 (even- and odd-indexed samples). That halving only terminates cleanly at length 1 when N is a power of 2.',
  },
];

function pick(uniformRng, arr) {
  return arr[Math.floor(uniformRng() * arr.length)];
}

function shuffleChoices(uniformRng, choices, correctIndex) {
  const indices = choices.map((_, i) => i);
  const mathlib = typeof module !== 'undefined' && module.exports ? require('./mathlib.js') : window;
  mathlib.fisherYatesShuffle(indices, uniformRng);
  const newChoices = indices.map((i) => choices[i]);
  const newCorrectIndex = indices.indexOf(correctIndex);
  return { choices: newChoices, correctIndex: newCorrectIndex };
}

/* Builds 8 fresh questions from the live math engine, seeded so a given
   run is reproducible for testing but different across page loads
   (callers pass Date.now() as the seed in the browser). */
function generateLiveQuestions(seed) {
  const mathlib = typeof module !== 'undefined' && module.exports ? require('./mathlib.js') : window;
  const epochs = typeof module !== 'undefined' && module.exports ? require('./epochs.js') : window;
  const rng = mathlib.mulberry32(seed);
  const questions = [];

  // Template A x2: SNR reduction
  [1, 2].forEach(() => {
    const nOptions = [4, 9, 16, 25, 36, 49, 64, 100];
    const N = pick(rng, nOptions);
    const noiseSD = pick(rng, [5, 8, 10, 12]);
    const correct = Math.round((noiseSD / Math.sqrt(N)) * 100) / 100;
    const distractors = [
      Math.round((noiseSD / N) * 100) / 100,
      Math.round(noiseSD * Math.sqrt(N) * 100) / 100,
      noiseSD,
    ];
    const rawChoices = [correct, ...distractors].map((v) => `${v} µV`);
    const { choices, correctIndex } = shuffleChoices(rng, rawChoices, 0);
    questions.push({
      prompt: `You average N = ${N} trials, each with single-trial noise SD = ${noiseSD} µV. What is the theoretical noise SD of the resulting average?`,
      choices,
      correctIndex,
      explanation: `Noise SD of the average = single-trial SD / √N = ${noiseSD} / √${N} = ${correct} µV.`,
    });
  });

  // Template B x2: FFT peak frequency
  [1, 2].forEach(() => {
    const freq = 5 + Math.floor(rng() * 36); // 5..40 Hz, integer -> exact bin
    const n = epochs.N_SAMPLES;
    const sr = epochs.SAMPLE_RATE;
    const sig = new Array(n);
    for (let i = 0; i < n; i++) sig[i] = Math.sin((2 * Math.PI * freq * i) / sr);
    const { re, im } = mathlib.fft(sig, new Array(n).fill(0));
    const { freqs, power } = mathlib.powerSpectrum(re, im, sr);
    let maxIdx = 0;
    for (let i = 1; i < power.length; i++) if (power[i] > power[maxIdx]) maxIdx = i;
    const detected = Math.round(freqs[maxIdx]);
    const distractors = [freq + 5, Math.max(1, freq - 5), Math.min(120, freq * 2)];
    const rawChoices = [`${detected} Hz`, ...distractors.map((f) => `${f} Hz`)];
    const { choices, correctIndex } = shuffleChoices(rng, rawChoices, 0);
    questions.push({
      prompt: `A pure ${freq} Hz sine wave is sampled at ${sr} Hz for ${n} samples and passed through the FFT. Which frequency bin shows the power-spectrum peak?`,
      choices,
      correctIndex,
      explanation: `The FFT correctly recovers the input frequency: the peak power bin lands at ${detected} Hz, matching the ${freq} Hz signal exactly (bin resolution here is ${(sr / n).toFixed(1)} Hz).`,
    });
  });

  // Template C x2: artifact rejection count (actually computed live)
  [1, 2].forEach(() => {
    const N = pick(rng, [60, 80, 100, 120]);
    const blinkRate = pick(rng, [0.15, 0.2, 0.25, 0.3]);
    const noiseSD = 3;
    const blinkAmp = 45;
    const threshold = 35;
    const template = epochs.generateERPTemplate(350, 5, 100);
    const trialRng = mathlib.mulberry32(Math.floor(rng() * 1e9));
    const g = mathlib.makeGaussianRng(trialRng);
    const { epochs: epochArr } = epochs.generateEpochSet(template, noiseSD, N, g, trialRng, blinkRate, blinkAmp);
    const { rejectedCount } = epochs.rejectArtifacts(epochArr, threshold, mathlib.peakToPeak);
    const distractors = [
      Math.max(0, rejectedCount - 8),
      rejectedCount + 8,
      Math.round(N * 0.5),
    ];
    const rawChoices = [`${rejectedCount} of ${N}`, ...distractors.map((d) => `${d} of ${N}`)];
    const { choices, correctIndex } = shuffleChoices(rng, rawChoices, 0);
    questions.push({
      prompt: `${N} trials are simulated with a ${Math.round(blinkRate * 100)}% blink-contamination rate and a ${threshold} µV peak-to-peak rejection threshold. Exactly how many trials get rejected in this run?`,
      choices,
      correctIndex,
      explanation: `Running the actual peak-to-peak rejection on this simulated trial set rejects ${rejectedCount} of ${N} trials — close to, but not exactly, ${Math.round(blinkRate * N)} (the contamination target), because a few contaminated trials can fall under threshold and vice versa.`,
    });
  });

  // Template D x2: CIT permutation test, innocent vs guilty comparison
  [1, 2].forEach(() => {
    const effect = pick(rng, [4, 5, 6, 7]);
    const template350 = epochs.generateERPTemplate(350, 3, 120);
    const noiseSD = 6;
    function windowAmps(amplitudeBoost, n) {
      const seed = Math.floor(rng() * 1e9);
      const trialRng = mathlib.mulberry32(seed);
      const g = mathlib.makeGaussianRng(trialRng);
      const boosted = Float64Array.from(template350, (v) => v + amplitudeBoost);
      const { epochs: arr } = epochs.generateEpochSet(boosted, noiseSD, n, g, trialRng, 0, 0);
      return arr.map((ep) => epochs.windowMeanAmplitude(ep, 300, 500));
    }
    const irrelevant = windowAmps(0, 60);
    const guiltyProbe = windowAmps(effect, 20);
    const innocentProbe = windowAmps(0, 20);
    const permRng = mathlib.mulberry32(Math.floor(rng() * 1e9));
    const guiltyResult = mathlib.permutationTest(guiltyProbe, irrelevant, 1000, permRng);
    const permRng2 = mathlib.mulberry32(Math.floor(rng() * 1e9));
    const innocentResult = mathlib.permutationTest(innocentProbe, irrelevant, 1000, permRng2);
    const guiltyLabel = 'Subject A';
    const innocentLabel = 'Subject B';
    const correctLabel = guiltyResult.pValue < innocentResult.pValue ? guiltyLabel : innocentLabel;
    const rawChoices = [guiltyLabel, innocentLabel];
    const { choices, correctIndex } = shuffleChoices(rng, rawChoices, correctLabel === guiltyLabel ? 0 : 1);
    questions.push({
      prompt: `${guiltyLabel} shows a probe-vs-irrelevant permutation-test p-value of ${guiltyResult.pValue.toFixed(3)}. ${innocentLabel} shows a p-value of ${innocentResult.pValue.toFixed(3)}. Based only on these p-values, which subject's data is more consistent with concealed recognition of the probe items?`,
      choices,
      correctIndex,
      explanation: `The smaller p-value indicates a probe-vs-irrelevant difference less consistent with chance. Here ${correctLabel} has the smaller p-value (${Math.min(guiltyResult.pValue, innocentResult.pValue).toFixed(3)}).`,
    });
  });

  return questions;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { FIXED_QUESTIONS, generateLiveQuestions };
}
