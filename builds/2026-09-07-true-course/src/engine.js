/* True Course — navigation engine.
 * Pure functions only: no DOM access, no I/O. Every puzzle answer in the
 * game is computed by calling into this file, both when a puzzle is
 * generated and when the player's answer is checked, so there is never a
 * hand-authored answer key to drift out of sync with the math.
 */
(function (global) {
  'use strict';

  var TC = global.TC || {};

  function toRad(deg) {
    return (deg * Math.PI) / 180;
  }

  function toDeg(rad) {
    return (rad * 180) / Math.PI;
  }

  // Normalize to [0, 360)
  function normalizeDeg(deg) {
    var d = deg % 360;
    if (d < 0) d += 360;
    return d;
  }

  // Normalize to (-180, 180]
  function normalizeSigned(deg) {
    var d = normalizeDeg(deg + 180) - 180;
    if (d <= -180) d += 360;
    return d;
  }

  // Shortest angular distance between two bearings, always >= 0, in [0, 180].
  function angularDistance(a, b) {
    return Math.abs(normalizeSigned(a - b));
  }

  /**
   * Current-triangle course-to-steer.
   *
   * Given a desired ground track (trackDeg, true bearing) and distance, a
   * boat's speed through water, and a current's set (the true bearing the
   * current flows TOWARD) and drift (its speed), find the heading the boat
   * must steer so the current's cross-track push is exactly cancelled and
   * the resultant ground track matches trackDeg.
   *
   * Derivation: resolve both the boat's own velocity vector and the
   * current's velocity vector into components parallel and perpendicular
   * to the desired track. The perpendicular ("cross-track") components must
   * sum to zero for the resultant to lie exactly on the track:
   *
   *   boatSpeedKts * sin(headingDeg - trackDeg) + driftKts * sin(setDeg - trackDeg) = 0
   *
   * Solving for the correction angle (headingDeg - trackDeg) gives a closed
   * form. A solution only exists when the current's cross-track component
   * is within the boat's own speed (driftKts * |sin(beta)| <= boatSpeedKts);
   * otherwise the boat cannot hold the track at all against that current.
   */
  function courseToSteer(params) {
    var trackDeg = params.trackDeg;
    var distanceNm = params.distanceNm;
    var boatSpeedKts = params.boatSpeedKts;
    var setDeg = params.setDeg;
    var driftKts = params.driftKts;

    if (boatSpeedKts <= 0) {
      return { solvable: false, reason: 'boat speed must be positive' };
    }

    var betaRad = toRad(normalizeSigned(setDeg - trackDeg));
    var ratio = (driftKts / boatSpeedKts) * Math.sin(betaRad);

    if (Math.abs(ratio) > 1) {
      return { solvable: false, reason: 'current too strong to hold this track' };
    }

    var correctionRad = Math.asin(-ratio);
    var correctionDeg = toDeg(correctionRad);
    var headingDeg = normalizeDeg(trackDeg + correctionDeg);

    var sogKts =
      boatSpeedKts * Math.cos(correctionRad) + driftKts * Math.cos(betaRad);

    if (sogKts <= 0) {
      return { solvable: false, reason: 'resultant speed over ground is not positive' };
    }

    var etaHours = distanceNm / sogKts;

    return {
      solvable: true,
      headingDeg: headingDeg,
      correctionDeg: correctionDeg,
      sogKts: sogKts,
      etaHours: etaHours,
    };
  }

  /**
   * Cosine (harmonic) tide-height interpolation between a known low tide
   * (h0 at t0) and the following high tide (h1 at t1), h1 > h0 assumed.
   * This is the standard simplified sinusoidal approximation used for
   * estimating intermediate tide heights between two known extremes — it
   * is not tide-table-grade precision, and the game documents that.
   */
  function tideHeight(t, t0, h0, t1, h1) {
    if (t1 === t0) return h0;
    var frac = (t - t0) / (t1 - t0);
    return (h0 + h1) / 2 - ((h1 - h0) / 2) * Math.cos(Math.PI * frac);
  }

  /**
   * Find the first time within [t0, t1] (a rising low-to-high leg) at which
   * the tide reaches requiredHeight, given the tide is monotonically
   * increasing across that leg (h1 > h0).
   */
  function tideWindowStart(params) {
    var t0 = params.t0;
    var h0 = params.h0;
    var t1 = params.t1;
    var h1 = params.h1;
    var requiredHeight = params.requiredHeight;

    if (h1 <= h0) {
      return { status: 'invalid', reason: 'high tide height must exceed low tide height' };
    }
    if (requiredHeight <= h0) {
      return { status: 'always', startTime: t0 };
    }
    if (requiredHeight > h1) {
      return { status: 'never', startTime: null };
    }

    var cosVal = ((h0 + h1) / 2 - requiredHeight) / ((h1 - h0) / 2);
    if (cosVal > 1) cosVal = 1;
    if (cosVal < -1) cosVal = -1;

    var frac = Math.acos(cosVal) / Math.PI;
    var startTime = t0 + frac * (t1 - t0);

    return { status: 'window', startTime: startTime };
  }

  /**
   * COLREGS Rules 13/14/15 classifier for two power-driven vessels.
   *
   * yourHeadingDeg / otherHeadingDeg: true heading of each vessel.
   * bearingToOtherDeg: true bearing FROM your vessel TO the other vessel.
   *
   * Overtaking (Rule 13) uses the real regulatory threshold: a vessel
   * approaching from more than 22.5 degrees abaft another vessel's beam
   * (i.e. more than 112.5 degrees off that vessel's own bow) is overtaking
   * and must keep clear regardless of what a plain crossing rule would say.
   * Head-on (Rule 14) is reciprocal headings with each vessel seeing the
   * other nearly dead ahead. Otherwise it is a crossing situation (Rule 15):
   * whichever vessel has the other on her own starboard side must give way.
   */
  function classifyEncounter(params) {
    var yourHeadingDeg = normalizeDeg(params.yourHeadingDeg);
    var otherHeadingDeg = normalizeDeg(params.otherHeadingDeg);
    var bearingToOtherDeg = normalizeDeg(params.bearingToOtherDeg);
    var bearingToYouDeg = normalizeDeg(bearingToOtherDeg + 180);

    var relBearingFromYou = normalizeSigned(bearingToOtherDeg - yourHeadingDeg);
    var relBearingFromOther = normalizeSigned(bearingToYouDeg - otherHeadingDeg);
    var headingDiff = normalizeSigned(otherHeadingDeg - yourHeadingDeg);

    var isHeadOn =
      Math.abs(headingDiff) >= 174 &&
      Math.abs(relBearingFromYou) <= 6 &&
      Math.abs(relBearingFromOther) <= 6;

    if (isHeadOn) {
      return {
        type: 'head-on',
        giveWay: 'both',
        relBearingFromYou: relBearingFromYou,
        relBearingFromOther: relBearingFromOther,
      };
    }

    var otherIsOvertakingBoundary = Math.abs(relBearingFromOther) > 112.5;
    var youAreOvertakingBoundary = Math.abs(relBearingFromYou) > 112.5;

    if (otherIsOvertakingBoundary) {
      // The other vessel sees you abaft her beam: you are overtaking her.
      return {
        type: 'overtaking',
        giveWay: 'you',
        relBearingFromYou: relBearingFromYou,
        relBearingFromOther: relBearingFromOther,
      };
    }
    if (youAreOvertakingBoundary) {
      // You see the other vessel abaft your beam: she is overtaking you.
      return {
        type: 'overtaking',
        giveWay: 'other',
        relBearingFromYou: relBearingFromYou,
        relBearingFromOther: relBearingFromOther,
      };
    }

    return {
      type: 'crossing',
      giveWay: relBearingFromYou > 0 ? 'you' : 'other',
      relBearingFromYou: relBearingFromYou,
      relBearingFromOther: relBearingFromOther,
    };
  }

  /**
   * How far (in degrees) a given encounter is from the nearest
   * classification boundary — used by the puzzle generator to reject
   * scenarios that are too close to a rule threshold to be unambiguous.
   */
  function encounterBoundaryMargin(params) {
    var yourHeadingDeg = normalizeDeg(params.yourHeadingDeg);
    var otherHeadingDeg = normalizeDeg(params.otherHeadingDeg);
    var bearingToOtherDeg = normalizeDeg(params.bearingToOtherDeg);
    var bearingToYouDeg = normalizeDeg(bearingToOtherDeg + 180);

    var relBearingFromYou = normalizeSigned(bearingToOtherDeg - yourHeadingDeg);
    var relBearingFromOther = normalizeSigned(bearingToYouDeg - otherHeadingDeg);
    var headingDiff = normalizeSigned(otherHeadingDeg - yourHeadingDeg);

    var margins = [
      Math.abs(180 - Math.abs(headingDiff)), // distance from exact reciprocal
      Math.abs(Math.abs(relBearingFromYou) - 0), // distance from dead-ahead
      Math.abs(Math.abs(relBearingFromOther) - 0),
      Math.abs(Math.abs(relBearingFromYou) - 112.5), // distance from overtaking threshold
      Math.abs(Math.abs(relBearingFromOther) - 112.5),
      Math.abs(relBearingFromYou), // distance from port/starboard boundary (0)
      Math.abs(180 - Math.abs(relBearingFromYou)), // distance from dead-astern boundary
    ];

    return Math.min.apply(null, margins);
  }

  /**
   * IALA System B buoyage rules (used in Canada/US): "red right returning."
   */
  var buoyage = {
    sideForBuoy: function (color, direction) {
      if (direction === 'inbound') {
        return color === 'red' ? 'starboard' : 'port';
      }
      return color === 'red' ? 'port' : 'starboard';
    },
    shapeForColor: function (color) {
      return color === 'red' ? 'nun' : 'can';
    },
    colorForNumber: function (n) {
      return n % 2 === 0 ? 'red' : 'green';
    },
  };

  TC.toRad = toRad;
  TC.toDeg = toDeg;
  TC.normalizeDeg = normalizeDeg;
  TC.normalizeSigned = normalizeSigned;
  TC.angularDistance = angularDistance;
  TC.courseToSteer = courseToSteer;
  TC.tideHeight = tideHeight;
  TC.tideWindowStart = tideWindowStart;
  TC.classifyEncounter = classifyEncounter;
  TC.encounterBoundaryMargin = encounterBoundaryMargin;
  TC.buoyage = buoyage;

  global.TC = TC;
})(typeof window !== 'undefined' ? window : globalThis);
