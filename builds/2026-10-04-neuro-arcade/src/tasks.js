(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./stats.js'));
  else root.NATasks = factory(root.NAStats);
})(typeof self !== 'undefined' ? self : this, function (Stats) {
  const COLOURS = ['red', 'green', 'blue', 'yellow'];
  const NBACK_LETTERS = 'BCDFGHJK'.split('');
  const POOL = 10;

  // mulberry32: small seedable PRNG so a session can be reproduced from its seed
  function makeRng(seed) {
    let state = seed >>> 0;
    return function next() {
      state = (state + 0x6D2B79F5) >>> 0;
      let t = state;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function shuffle(items, rng) {
    const out = items.slice();
    for (let i = out.length - 1; i > 0; i--) {
      const j = Math.floor(rng() * (i + 1));
      [out[i], out[j]] = [out[j], out[i]];
    }
    return out;
  }

  function pick(items, rng) {
    return items[Math.floor(rng() * items.length)];
  }

  function stroopTrials(count, rng) {
    const congruentCount = Math.floor(count / 2);
    const conditions = shuffle(
      Array.from({ length: count }, (_, i) => (i < congruentCount ? 'congruent' : 'incongruent')), rng);
    return conditions.map((condition) => {
      const word = pick(COLOURS, rng);
      const ink = condition === 'congruent' ? word : pick(COLOURS.filter((c) => c !== word), rng);
      return { condition, word, ink };
    });
  }

  function nbackSequence(length, n, rng, targetRate) {
    const seq = [];
    for (let i = 0; i < length; i++) {
      const canTarget = i >= n;
      const isTarget = canTarget && rng() < targetRate;
      let letter;
      if (isTarget) letter = seq[i - n].letter;
      else if (canTarget) letter = pick(NBACK_LETTERS.filter((l) => l !== seq[i - n].letter), rng);
      else letter = pick(NBACK_LETTERS, rng);
      seq.push({ letter, isTarget });
    }
    return seq;
  }

  function goNoGoTrials(count, rng, nogoRate) {
    const nogoCount = Math.max(1, Math.round(count * nogoRate));
    const kinds = Array.from({ length: count }, (_, i) => (i < nogoCount ? 'nogo' : 'go'));
    return shuffle(kinds, rng).map((kind) => ({ kind }));
  }

  // Proposer offers the participant 1..5 of a $10 pool, each amount equally often
  function ultimatumOffers(count, rng) {
    const amounts = Array.from({ length: count }, (_, i) => (i % 5) + 1);
    return shuffle(amounts, rng).map((offer) => ({ offer, pool: POOL }));
  }

  function rtsWhere(trials, predicate) {
    return trials.filter((t) => t.rt !== null && t.rt !== undefined && predicate(t)).map((t) => t.rt);
  }

  function round(value, places) {
    if (value === null || value === undefined || Number.isNaN(value)) return null;
    const factor = 10 ** places;
    return Math.round(value * factor) / factor;
  }

  function scoreStroop(trials) {
    const answered = trials.filter((t) => t.response !== null);
    const correct = trials.filter((t) => t.correct === true);
    const congruentRt = Stats.mean(rtsWhere(correct, (t) => t.condition === 'congruent'));
    const incongruentRt = Stats.mean(rtsWhere(correct, (t) => t.condition === 'incongruent'));
    return {
      trials: trials.length,
      accuracy: trials.length ? round(correct.length / trials.length, 3) : null,
      timeouts: trials.length - answered.length,
      congruentRt: round(congruentRt, 1),
      incongruentRt: round(incongruentRt, 1),
      interference: congruentRt !== null && incongruentRt !== null ? round(incongruentRt - congruentRt, 1) : null,
    };
  }

  function signalDetection(trials, signalCondition) {
    const signal = trials.filter((t) => t.condition === signalCondition);
    const noise = trials.filter((t) => t.condition !== signalCondition);
    const hits = signal.filter((t) => t.response === 'press').length;
    const falseAlarms = noise.filter((t) => t.response === 'press').length;
    return {
      hits, signal: signal.length, falseAlarms, noise: noise.length,
      dPrime: round(Stats.dPrime(hits, signal.length, falseAlarms, noise.length), 2),
      hitRt: round(Stats.mean(rtsWhere(signal, (t) => t.response === 'press')), 1),
    };
  }

  function scoreNback(trials) {
    const sd = signalDetection(trials, 'target');
    return {
      trials: trials.length, hits: sd.hits, targets: sd.signal,
      falseAlarms: sd.falseAlarms, dPrime: sd.dPrime, hitRt: sd.hitRt,
    };
  }

  function scoreGoNoGo(trials) {
    const sd = signalDetection(trials, 'go');
    return {
      trials: trials.length, hits: sd.hits, goTrials: sd.signal,
      commissions: sd.falseAlarms, nogoTrials: sd.noise,
      commissionRate: sd.noise ? round(sd.falseAlarms / sd.noise, 3) : null,
      dPrime: sd.dPrime, goRt: sd.hitRt,
    };
  }

  function scoreUltimatum(trials) {
    const byOffer = {};
    trials.forEach((t) => {
      const offer = Number(t.stimulus);
      byOffer[offer] = byOffer[offer] || { offered: 0, accepted: 0 };
      byOffer[offer].offered += 1;
      if (t.response === 'accept') byOffer[offer].accepted += 1;
    });
    const offers = Object.keys(byOffer).map(Number).sort((a, b) => a - b);
    const unfair = trials.filter((t) => Number(t.stimulus) <= 2);
    const accepted = trials.filter((t) => t.response === 'accept');
    const lowestAccepted = accepted.length ? Math.min(...accepted.map((t) => Number(t.stimulus))) : null;
    return {
      trials: trials.length,
      earned: accepted.reduce((sum, t) => sum + Number(t.stimulus), 0),
      rejectUnfair: unfair.length ? round(unfair.filter((t) => t.response === 'reject').length / unfair.length, 3) : null,
      lowestAccepted,
      acceptByOffer: offers.map((offer) => ({
        offer, offered: byOffer[offer].offered,
        rate: round(byOffer[offer].accepted / byOffer[offer].offered, 3),
      })),
      decisionRt: round(Stats.mean(rtsWhere(trials, () => true)), 0),
    };
  }

  const SCORERS = { stroop: scoreStroop, nback: scoreNback, gonogo: scoreGoNoGo, ultimatum: scoreUltimatum };

  function score(task, trials) {
    if (!SCORERS[task]) throw new Error('Unknown task: ' + task);
    return SCORERS[task](trials);
  }

  // Approximate teaching reference values (healthy adult samples, typical keyboard versions).
  // Deliberately rounded; they are for classroom comparison, not norms for clinical use.
  const TASK_INFO = {
    stroop: {
      title: 'Stroop', blurb: 'Name the ink colour, ignore the word.', construct: 'Inhibitory control',
      metrics: [
        { key: 'interference', label: 'Interference effect', unit: 'ms', higherBetter: false, ref: { mean: 90, sd: 45 } },
        { key: 'accuracy', label: 'Accuracy', unit: '%', scale: 100, higherBetter: true, ref: { mean: 0.95, sd: 0.05 } },
      ],
    },
    nback: {
      title: '2-back', blurb: 'Press when the letter matches the one two back.', construct: 'Working memory',
      metrics: [
        { key: 'dPrime', label: 'Sensitivity (d′)', unit: '', higherBetter: true, ref: { mean: 2.2, sd: 0.9 } },
        { key: 'hitRt', label: 'Hit reaction time', unit: 'ms', higherBetter: false, ref: { mean: 650, sd: 120 } },
      ],
    },
    gonogo: {
      title: 'Go/No-Go', blurb: 'Tap for the green circle, hold back for the red square.', construct: 'Response inhibition',
      metrics: [
        { key: 'commissionRate', label: 'No-Go errors', unit: '%', scale: 100, higherBetter: false, ref: { mean: 0.25, sd: 0.12 } },
        { key: 'goRt', label: 'Go reaction time', unit: 'ms', higherBetter: false, ref: { mean: 380, sd: 60 } },
      ],
    },
    ultimatum: {
      title: 'Ultimatum Game', blurb: 'Accept or reject splits of $10 from another player.', construct: 'Social decision-making',
      metrics: [
        { key: 'rejectUnfair', label: 'Rejection of unfair offers ($1–$2)', unit: '%', scale: 100, higherBetter: null, ref: { mean: 0.6, sd: 0.3 } },
      ],
    },
  };

  return {
    COLOURS, NBACK_LETTERS, POOL, TASK_INFO,
    makeRng, shuffle, stroopTrials, nbackSequence, goNoGoTrials, ultimatumOffers,
    score, scoreStroop, scoreNback, scoreGoNoGo, scoreUltimatum,
  };
});
