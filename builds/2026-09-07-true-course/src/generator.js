/* True Course — puzzle generators.
 * Every generator builds parameters, calls into TC (engine.js) to compute
 * the correct answer, and rejects/redraws scenarios that fall too close to
 * a rule boundary to be unambiguous. No puzzle answer is ever hand-authored.
 */
(function (global) {
  'use strict';

  var TC = global.TC || {};

  // mulberry32 — small, fast, deterministic PRNG. Seeded identically it
  // always produces the same sequence, which is what makes the Daily
  // Challenge reproducible across players/devices on the same UTC date.
  function mulberry32(seed) {
    var a = seed >>> 0;
    return function () {
      a |= 0;
      a = (a + 0x6d2b79f5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function hashStringToSeed(str) {
    var h = 2166136261;
    for (var i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  }

  function randInt(rng, min, max) {
    return Math.floor(rng() * (max - min + 1)) + min;
  }

  function randFloat(rng, min, max) {
    return rng() * (max - min) + min;
  }

  function pick(rng, arr) {
    return arr[Math.floor(rng() * arr.length)];
  }

  function shuffle(rng, arr) {
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(rng() * (i + 1));
      var tmp = a[i];
      a[i] = a[j];
      a[j] = tmp;
    }
    return a;
  }

  function formatClock(hourFloat) {
    var h = Math.floor(hourFloat) % 24;
    if (h < 0) h += 24;
    var m = Math.round((hourFloat - Math.floor(hourFloat)) * 60);
    if (m === 60) {
      m = 0;
      h = (h + 1) % 24;
    }
    var hh = String(h).padStart(2, '0');
    var mm = String(m).padStart(2, '0');
    return hh + ':' + mm;
  }

  function generateSetDrift(rng) {
    for (var attempt = 0; attempt < 50; attempt++) {
      var trackDeg = randInt(rng, 0, 359);
      var distanceNm = randInt(rng, 6, 42);
      var boatSpeedKts = randInt(rng, 5, 14);
      var driftKts = Math.round(randFloat(rng, 0.5, boatSpeedKts * 0.55) * 10) / 10;
      var setDeg = randInt(rng, 0, 359);

      var result = TC.courseToSteer({
        trackDeg: trackDeg,
        distanceNm: distanceNm,
        boatSpeedKts: boatSpeedKts,
        setDeg: setDeg,
        driftKts: driftKts,
      });

      if (!result.solvable) continue;
      // Reject puzzles where the correction is too small to be a
      // meaningful test of the skill, or so large it rounds ambiguously.
      if (Math.abs(result.correctionDeg) < 3 || Math.abs(result.correctionDeg) > 45) continue;

      return {
        type: 'set-drift',
        params: {
          trackDeg: trackDeg,
          distanceNm: distanceNm,
          boatSpeedKts: boatSpeedKts,
          setDeg: setDeg,
          driftKts: driftKts,
        },
        correctAnswer: Math.round(result.headingDeg),
        sogKts: result.sogKts,
        etaHours: result.etaHours,
        tolerance: 2,
      };
    }
    // Extremely unlikely fallback: no current at all, always solvable.
    var fallbackTrack = randInt(rng, 0, 359);
    var fallbackResult = TC.courseToSteer({
      trackDeg: fallbackTrack,
      distanceNm: 10,
      boatSpeedKts: 8,
      setDeg: 0,
      driftKts: 0,
    });
    return {
      type: 'set-drift',
      params: {
        trackDeg: fallbackTrack,
        distanceNm: 10,
        boatSpeedKts: 8,
        setDeg: 0,
        driftKts: 0,
      },
      correctAnswer: Math.round(fallbackResult.headingDeg),
      sogKts: fallbackResult.sogKts,
      etaHours: fallbackResult.etaHours,
      tolerance: 2,
    };
  }

  function generateTideWindow(rng) {
    for (var attempt = 0; attempt < 50; attempt++) {
      var t0 = Math.round(randFloat(rng, 0, 11) * 2) / 2; // low tide clock hour
      var period = randFloat(rng, 5.8, 6.6); // hours from low to next high
      var t1 = t0 + period;
      var h0 = Math.round(randFloat(rng, 0.2, 1.0) * 10) / 10;
      var h1 = Math.round((h0 + randFloat(rng, 1.6, 3.4)) * 10) / 10;
      var chartedDepth = Math.round(randFloat(rng, 0.3, 2.2) * 10) / 10;
      var draft = Math.round(randFloat(rng, 0.8, 1.9) * 10) / 10;
      var margin = Math.round(randFloat(rng, 0.2, 0.5) * 10) / 10;
      var requiredHeight = Math.round((draft + margin - chartedDepth) * 10) / 10;

      // Keep well clear of h0/h1 boundaries so the window is a genuine
      // mid-leg puzzle, not a trivial "always"/"never" edge case.
      if (requiredHeight <= h0 + 0.15 || requiredHeight >= h1 - 0.15) continue;

      var result = TC.tideWindowStart({
        t0: t0,
        h0: h0,
        t1: t1,
        h1: h1,
        requiredHeight: requiredHeight,
      });
      if (result.status !== 'window') continue;

      var correctTime = result.startTime;
      var correctLabel = formatClock(correctTime);

      // Distractors: a real-but-wrong linear-interpolation estimate, an
      // off-by-one-hour slip, and the reciprocal-side error (as if the
      // solver had used cos instead of the correct branch).
      var linearFrac = (requiredHeight - h0) / (h1 - h0);
      var linearTime = t0 + linearFrac * (t1 - t0);
      var candidates = [
        correctTime,
        linearTime,
        correctTime + 1,
        t1 - (correctTime - t0),
      ];
      var labels = candidates.map(function (c) {
        return formatClock(c);
      });
      // Ensure all four displayed labels are textually distinct.
      var uniqueLabels = {};
      var ok = true;
      for (var i = 0; i < labels.length; i++) {
        if (uniqueLabels[labels[i]]) {
          ok = false;
          break;
        }
        uniqueLabels[labels[i]] = true;
      }
      if (!ok) continue;

      var choices = shuffle(rng, labels);

      return {
        type: 'tide-window',
        params: {
          t0: t0,
          h0: h0,
          t1: t1,
          h1: h1,
          chartedDepth: chartedDepth,
          draft: draft,
          margin: margin,
          requiredHeight: requiredHeight,
        },
        correctAnswer: correctLabel,
        choices: choices,
      };
    }
    throw new Error('generateTideWindow: exhausted attempts');
  }

  function generateRightOfWay(rng) {
    for (var attempt = 0; attempt < 80; attempt++) {
      var yourHeadingDeg = randInt(rng, 0, 359);
      var otherHeadingDeg = randInt(rng, 0, 359);
      var bearingToOtherDeg = randInt(rng, 0, 359);

      var margin = TC.encounterBoundaryMargin({
        yourHeadingDeg: yourHeadingDeg,
        otherHeadingDeg: otherHeadingDeg,
        bearingToOtherDeg: bearingToOtherDeg,
      });
      if (margin < 6) continue;

      var classification = TC.classifyEncounter({
        yourHeadingDeg: yourHeadingDeg,
        otherHeadingDeg: otherHeadingDeg,
        bearingToOtherDeg: bearingToOtherDeg,
      });

      return {
        type: 'right-of-way',
        params: {
          yourHeadingDeg: yourHeadingDeg,
          otherHeadingDeg: otherHeadingDeg,
          bearingToOtherDeg: bearingToOtherDeg,
        },
        correctAnswer: classification.giveWay, // 'you' | 'other' | 'both'
        encounterType: classification.type,
      };
    }
    throw new Error('generateRightOfWay: exhausted attempts');
  }

  function generateBuoyage(rng) {
    var variant = pick(rng, ['side', 'shape', 'parity']);
    var color = pick(rng, ['red', 'green']);
    var direction = pick(rng, ['inbound', 'outbound']);
    var number =
      color === 'red' ? randInt(rng, 1, 20) * 2 : randInt(rng, 1, 20) * 2 - 1;

    if (variant === 'side') {
      return {
        type: 'buoyage',
        variant: variant,
        params: { color: color, direction: direction, number: number },
        correctAnswer: TC.buoyage.sideForBuoy(color, direction),
        choices: shuffle(rng, ['port', 'starboard']),
      };
    }
    if (variant === 'shape') {
      return {
        type: 'buoyage',
        variant: variant,
        params: { color: color, direction: direction, number: number },
        correctAnswer: TC.buoyage.shapeForColor(color),
        choices: shuffle(rng, ['can', 'nun']),
      };
    }
    // parity variant: given only the number, ask which color it must be
    var parityNumber = randInt(rng, 1, 40);
    return {
      type: 'buoyage',
      variant: variant,
      params: { number: parityNumber },
      correctAnswer: TC.buoyage.colorForNumber(parityNumber),
      choices: shuffle(rng, ['red', 'green']),
    };
  }

  var GENERATORS = {
    'set-drift': generateSetDrift,
    'tide-window': generateTideWindow,
    'right-of-way': generateRightOfWay,
    buoyage: generateBuoyage,
  };

  function generatePuzzle(type, rng) {
    var fn = GENERATORS[type];
    if (!fn) throw new Error('unknown puzzle type: ' + type);
    return fn(rng);
  }

  var CHAPTER_ORDER = ['buoyage', 'right-of-way', 'tide-window', 'set-drift'];

  function dailySeed(dateStr) {
    return hashStringToSeed('true-course-daily-' + dateStr);
  }

  TC.mulberry32 = mulberry32;
  TC.hashStringToSeed = hashStringToSeed;
  TC.generatePuzzle = generatePuzzle;
  TC.CHAPTER_ORDER = CHAPTER_ORDER;
  TC.dailySeed = dailySeed;
  TC.formatClock = formatClock;

  global.TC = TC;
})(typeof window !== 'undefined' ? window : globalThis);
