/* Voxel Lab — quiz bank. Conceptual questions are static; "computed"
 * questions generate their correct answer (and distractors) from the real
 * stats.js functions at build time, per question, so the check is always
 * against the live formula rather than a hardcoded fact. */

(function () {
  const CONCEPTUAL_QUESTIONS = [
    {
      id: 'c1',
      prompt: 'Which preprocessing step corrects for a subject moving their head during a scan?',
      choices: ['Motion Correction', 'Slice Timing Correction', 'Spatial Smoothing', 'Spatial Normalization'],
      correctIndex: 0,
    },
    {
      id: 'c2',
      prompt: 'Why is spatial smoothing typically applied before statistical analysis?',
      choices: [
        'To increase spatial resolution',
        'To improve signal-to-noise ratio and satisfy Gaussian random field assumptions used later',
        'To align anatomy across subjects',
        'To correct for scanner field drift over time',
      ],
      correctIndex: 1,
    },
    {
      id: 'c3',
      prompt: "What does spatial normalization accomplish?",
      choices: [
        'Removes thermal scanner noise',
        "Warps each subject's brain into a common template space for group comparison",
        'Corrects head motion between volumes',
        'Increases temporal resolution',
      ],
      correctIndex: 1,
    },
    {
      id: 'c4',
      prompt: 'In a canonical GLM analysis, what does convolving the task design (boxcar) with the HRF produce?',
      choices: [
        'The raw, unprocessed BOLD signal',
        'A predicted BOLD response shape to fit against the observed data',
        'The scanner noise floor',
        'A spatial smoothing kernel',
      ],
      correctIndex: 1,
    },
    {
      id: 'c5',
      prompt: "The famous 'dead salmon' fMRI study is used to illustrate:",
      choices: [
        'fMRI motion artifacts are always fatal to a study',
        'Testing thousands of voxels without correction can produce apparently active clusters even in a dead fish',
        'Slice timing correction is unnecessary at 3T',
        'Smoothing always improves statistical power',
      ],
      correctIndex: 1,
    },
    {
      id: 'c6',
      prompt: 'Which correction method controls the probability of making ANY false positive across all tests (family-wise error rate)?',
      choices: ['Bonferroni correction', 'No correction', 'Cluster-extent alone', 'Increasing sample size'],
      correctIndex: 0,
    },
    {
      id: 'c7',
      prompt: 'What does the Benjamini-Hochberg procedure control?',
      choices: [
        'The family-wise error rate exactly like Bonferroni',
        'The false discovery rate — the expected proportion of false positives among all results called significant',
        'The spatial smoothness of the data',
        'The signal-to-noise ratio of a single voxel',
      ],
      correctIndex: 1,
    },
    {
      id: 'c8',
      prompt: 'Why is Bonferroni correction often considered overly conservative for whole-brain fMRI data?',
      choices: [
        'It assumes all voxels are perfectly correlated with each other',
        'It treats tens of thousands of spatially correlated voxels as fully independent tests, deflating statistical power',
        'It only works when testing exactly 20 voxels',
        'It requires raw k-space data instead of statistical maps',
      ],
      correctIndex: 1,
    },
    {
      id: 'c9',
      prompt: 'What does cluster-extent thresholding require, beyond a per-voxel statistical threshold?',
      choices: [
        'A minimum number of spatially contiguous suprathreshold voxels',
        'A minimum amount of head motion',
        'A maximum smoothing kernel width',
        'A second, independent scanning session',
      ],
      correctIndex: 0,
    },
    {
      id: 'c10',
      prompt: 'Which of these is the typical order for early fMRI preprocessing steps?',
      choices: [
        'Smoothing → Motion Correction → Normalization',
        'Motion Correction → Slice Timing → Normalization → Smoothing',
        'Normalization → Motion Correction → Smoothing',
        'Statistical Thresholding → Motion Correction → Smoothing',
      ],
      correctIndex: 1,
    },
  ];

  function shuffleWithCorrect(labeledValues, correctLabel) {
    // labeledValues: array of {label, value}. Shuffle deterministically via
    // the supplied rng, then find the shuffled index whose label matches.
    return (rng) => {
      const arr = [...labeledValues];
      for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(rng() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
      }
      const correctIndex = arr.findIndex((item) => item.label === correctLabel);
      return { choices: arr.map((item) => item.value), correctIndex };
    };
  }

  function buildComputedQuestions(rng) {
    const stats = window.VoxelStats;
    const questions = [];

    // 1. Bonferroni threshold
    {
      const alphaOptions = [0.05, 0.01, 0.1];
      const nOptions = [1000, 5000, 8000, 10000, 20000];
      const alpha = alphaOptions[Math.floor(rng() * alphaOptions.length)];
      const n = nOptions[Math.floor(rng() * nOptions.length)];
      const correct = stats.bonferroniThreshold(alpha, n);
      const wrong1 = alpha * n;
      const wrong2 = alpha;
      const wrong3 = alpha / Math.sqrt(n);
      const fmt = (v) => v.toExponential(3);
      const build = shuffleWithCorrect(
        [
          { label: 'correct', value: fmt(correct) },
          { label: 'w1', value: fmt(wrong1) },
          { label: 'w2', value: fmt(wrong2) },
          { label: 'w3', value: fmt(wrong3) },
        ],
        'correct'
      );
      const { choices, correctIndex } = build(rng);
      questions.push({
        id: 'q-bonferroni',
        prompt: `With alpha = ${alpha} and ${n.toLocaleString()} independent voxels tested, what is the Bonferroni-corrected significance threshold?`,
        choices,
        correctIndex,
      });
    }

    // 2. Expected false positives, uncorrected
    {
      const alpha = 0.05;
      const n = [2000, 4000, 10000, 15000][Math.floor(rng() * 4)];
      const correct = Math.round(alpha * n);
      const build = shuffleWithCorrect(
        [
          { label: 'correct', value: `~${correct.toLocaleString()}` },
          { label: 'w1', value: `~${Math.round(correct / 2).toLocaleString()}` },
          { label: 'w2', value: `~${n.toLocaleString()} (all voxels)` },
          { label: 'w3', value: '0' },
        ],
        'correct'
      );
      const { choices, correctIndex } = build(rng);
      questions.push({
        id: 'q-expected-fp',
        prompt: `With ${n.toLocaleString()} independent voxels, no true signal anywhere, and an uncorrected threshold of p<0.05, about how many false positives should you expect on average?`,
        choices,
        correctIndex,
      });
    }

    // 3. HRF peak time, computed from the real HRF function
    {
      let peakTime = 0;
      let peakVal = -Infinity;
      for (let t = 0; t <= 20; t += 0.1) {
        const v = stats.doubleGammaHRF(t);
        if (v > peakVal) {
          peakVal = v;
          peakTime = t;
        }
      }
      const bucket = (t) => {
        if (t < 2) return '0-2 seconds';
        if (t < 4) return '2-4 seconds';
        if (t < 8) return '4-8 seconds';
        return '8+ seconds';
      };
      const correctBucket = bucket(peakTime);
      const allBuckets = ['0-2 seconds', '2-4 seconds', '4-8 seconds', '8+ seconds'];
      const build = shuffleWithCorrect(
        allBuckets.map((b) => ({ label: b === correctBucket ? 'correct' : b, value: b })),
        'correct'
      );
      const { choices, correctIndex } = build(rng);
      questions.push({
        id: 'q-hrf-peak',
        prompt: "Using this tool's canonical double-gamma HRF, how long after stimulus onset does the BOLD response peak?",
        choices,
        correctIndex,
      });
    }

    // 4. BH-FDR count on a small fixed p-value set
    {
      const pValues = [0.001, 0.008, 0.039, 0.041, 0.09];
      const alpha = 0.05;
      const significant = stats.benjaminiHochberg(pValues, alpha);
      const correctCount = significant.filter(Boolean).length;
      const build = shuffleWithCorrect(
        [
          { label: 'correct', value: `${correctCount} of ${pValues.length}` },
          { label: 'w1', value: `${Math.max(0, correctCount - 1)} of ${pValues.length}` },
          { label: 'w2', value: `${Math.min(pValues.length, correctCount + 1)} of ${pValues.length}` },
          { label: 'w3', value: `0 of ${pValues.length}` },
        ],
        'correct'
      );
      const { choices, correctIndex } = build(rng);
      questions.push({
        id: 'q-bh-count',
        prompt: `Given p-values [${pValues.join(', ')}] and alpha=${alpha}, how many are significant under the Benjamini-Hochberg procedure?`,
        choices,
        correctIndex,
      });
    }

    // 5. Cluster-extent correction of isolated single voxels
    {
      const width = 10;
      const height = 10;
      const mask = new Array(width * height).fill(false);
      // Scatter isolated single-voxel "activations" with no neighbors set.
      [12, 27, 45, 68, 81].forEach((i) => (mask[i] = true));
      const minSize = 2;
      const corrected = stats.clusterExtentThreshold(mask, width, height, minSize);
      const survivorCount = corrected.filter(Boolean).length;
      const build = shuffleWithCorrect(
        [
          { label: 'correct', value: `${survivorCount}` },
          { label: 'w1', value: '5' },
          { label: 'w2', value: '3' },
          { label: 'w3', value: '1' },
        ],
        'correct'
      );
      const { choices, correctIndex } = build(rng);
      questions.push({
        id: 'q-cluster-isolated',
        prompt: `5 isolated single voxels (no touching neighbors) pass an uncorrected threshold. With a minimum cluster size of ${minSize}, how many survive cluster-extent correction?`,
        choices,
        correctIndex,
      });
    }

    // 6. GLM beta recovery
    {
      const trueBeta = 2 + Math.floor(rng() * 3);
      const localRng = window.VoxelStats.mulberry32(Math.floor(rng() * 1e9));
      const n = 60;
      const predictor = Array.from({ length: n }, (_, i) => Math.sin((i / n) * Math.PI));
      const y = predictor.map((v) => trueBeta * v + stats.gaussianRandom(localRng) * 0.15);
      const design = predictor.map((v) => [1, v]);
      const beta = stats.leastSquaresBeta(design, y);
      const recovered = Math.round(beta[1]);
      const build = shuffleWithCorrect(
        [
          { label: 'correct', value: `${recovered}` },
          { label: 'w1', value: `${recovered + 1}` },
          { label: 'w2', value: `${Math.max(0, recovered - 1)}` },
          { label: 'w3', value: `${recovered + 2}` },
        ],
        'correct'
      );
      const { choices, correctIndex } = build(rng);
      questions.push({
        id: 'q-glm-beta',
        prompt: `A synthetic BOLD-like signal is generated in this tool with a true beta of ${trueBeta} plus noise, and a least-squares GLM fit is run on it. Rounded to the nearest whole number, what beta does the fit recover?`,
        choices,
        correctIndex,
      });
    }

    return questions;
  }

  /** Build the full 15-question quiz for this session: 9 conceptual + 6
   *  computed (computed questions/distractors are regenerated each build). */
  function buildQuiz(seed) {
    const rng = window.VoxelStats.mulberry32(seed);
    const conceptual = CONCEPTUAL_QUESTIONS.map((q) => ({ ...q, type: 'choice' }));
    const computed = buildComputedQuestions(rng).map((q) => ({ ...q, type: 'computed' }));
    return [...conceptual, ...computed];
  }

  window.VoxelQuiz = { buildQuiz, CONCEPTUAL_QUESTIONS, buildComputedQuestions };
})();
