// Hand-authored Signal Detection Theory scenarios grounded in forensic and
// affective-neuroscience research paradigms. Counts are illustrative, not real
// study data. d'/criterion for each are always computed live from sdt-math.js —
// nothing here is a precomputed "correct answer."

(function (global) {
  'use strict';

  const SCENARIOS = [
    {
      id: 'recognition-memory',
      title: 'Recognition Memory (Old/New Word Task)',
      domain: 'Psychopathy research',
      description:
        'Participants studied 60 words, then judged "old" or "new" among 120 test items ' +
        '(60 studied, 60 novel lures) in a forensic sample screened for psychopathic traits. ' +
        'This paradigm is commonly used to probe recollection versus familiarity-based memory ' +
        'in offender populations.',
      hits: 42, misses: 18, falseAlarms: 12, correctRejections: 48,
    },
    {
      id: 'threat-detection',
      title: 'Fearful Face Detection',
      domain: 'Affective neuroscience',
      description:
        'Participants viewed briefly presented faces (fearful or neutral, 60 of each) and pressed ' +
        'a button whenever they detected a fearful expression. Anxious individuals often show a ' +
        'liberal response bias toward reporting threat, at the cost of more false alarms on neutral faces.',
      hits: 54, misses: 6, falseAlarms: 30, correctRejections: 30,
    },
    {
      id: 'eyewitness-lineup',
      title: 'Eyewitness Lineup Identification',
      domain: 'Forensic neuroscience',
      description:
        'Fifty eyewitnesses viewed a six-person lineup containing the actual culprit (signal present); ' +
        'a matched group of fifty viewed a culprit-absent lineup with an innocent filler resembling the ' +
        'description (signal absent). Witnesses identified a lineup member or responded "not present."',
      hits: 33, misses: 17, falseAlarms: 12, correctRejections: 38,
    },
    {
      id: 'diagnostic-screening',
      title: 'Depression Screening Questionnaire',
      domain: 'Clinical screening',
      description:
        'A depression screening instrument was validated against clinical diagnosis in 200 patients ' +
        '(100 confirmed cases, 100 non-cases). High sensitivity and specificity are both required before ' +
        'a screening tool is considered fit for population use.',
      hits: 88, misses: 12, falseAlarms: 12, correctRejections: 88,
    },
    {
      id: 'deception-judgment',
      title: 'Deception Detection from Videotaped Statements',
      domain: 'Forensic neuroscience',
      description:
        'Trained judges watched fifty videotaped statements (25 truthful, 25 deceptive, matched for ' +
        'content) and judged truth versus lie for each. Human lie-detection accuracy from demeanor alone ' +
        'is famously close to chance in the research literature.',
      hits: 13, misses: 12, falseAlarms: 11, correctRejections: 14,
    },
    {
      id: 'radiology-detection',
      title: 'Radiological Tumor Detection',
      domain: 'Classic psychophysics reference case',
      description:
        'Radiologists reviewed 100 mammograms (50 containing a tumor, 50 without) under realistic time ' +
        'pressure. This is one of the original applied domains that motivated Signal Detection Theory ' +
        'as an analytic framework.',
      hits: 38, misses: 12, falseAlarms: 9, correctRejections: 41,
    },
  ];

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = SCENARIOS;
  } else {
    global.SDT_SCENARIOS = SCENARIOS;
  }
})(typeof window !== 'undefined' ? window : globalThis);
