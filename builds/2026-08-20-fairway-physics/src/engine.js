/* Fairway Physics — pure physics/scoring engine. No DOM access, no globals
   beyond `window.FairwayEngine`, so this file is directly testable via
   Playwright's page.evaluate() and reusable unmodified by app.js. */
(function (global) {
  'use strict';

  var CLUBS = {
    driver: { label: 'Driver', baseCarry: 230, rollFactor: 0.15, windSensitivity: 1.0 },
    threewood: { label: '3-Wood', baseCarry: 210, rollFactor: 0.12, windSensitivity: 0.9 },
    fiveiron: { label: '5-Iron', baseCarry: 175, rollFactor: 0.06, windSensitivity: 0.7 },
    eightiron: { label: '8-Iron', baseCarry: 145, rollFactor: 0.03, windSensitivity: 0.55 },
    pw: { label: 'Pitching Wedge', baseCarry: 110, rollFactor: 0.01, windSensitivity: 0.4 },
    putter: { label: 'Putter', baseCarry: 0, rollFactor: 0, windSensitivity: 0 }
  };

  var WIND_DISTANCE_YD_PER_MPH = 1.5;
  var WIND_LATERAL_YD_PER_MPH = 0.8;
  var ELEVATION_YD_PER_FT = 0.33;
  var DRAW_FADE_MAGNITUDE_YD = 18;
  var ROUGH_ROLL_MULTIPLIER = 0.4;
  var PUTT_CAPTURE_RADIUS_YD = 0.5;
  var MAX_PUTT_DISTANCE_YD = 15;

  function toRadians(deg) {
    return (deg * Math.PI) / 180;
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function getClub(clubId) {
    var club = CLUBS[clubId];
    if (!club) {
      throw new Error('Unknown club: ' + clubId);
    }
    return club;
  }

  function computeCarryDistance(clubId, powerPct) {
    var club = getClub(clubId);
    var pct = clamp(powerPct, 0, 100) / 100;
    return club.baseCarry * pct;
  }

  // windDirectionDeg: 0 = pure tailwind (helping), 180 = pure headwind,
  // 90 = crosswind left-to-right, 270 = crosswind right-to-left.
  function computeWindEffect(carryYards, windSpeedMph, windDirectionDeg, clubId) {
    var club = getClub(clubId);
    var rad = toRadians(windDirectionDeg);
    var tailwindComponent = windSpeedMph * Math.cos(rad);
    var crosswindComponent = windSpeedMph * Math.sin(rad);
    var distanceDelta = tailwindComponent * WIND_DISTANCE_YD_PER_MPH * club.windSensitivity;
    var hangTimeFraction = clamp(carryYards / 230, 0, 1.3);
    var lateralDrift =
      crosswindComponent * WIND_LATERAL_YD_PER_MPH * club.windSensitivity * hangTimeFraction;
    return { distanceDelta: distanceDelta, lateralDrift: lateralDrift };
  }

  function computeElevationEffect(elevationChangeFt) {
    return -elevationChangeFt * ELEVATION_YD_PER_FT;
  }

  function computeShotShapeCurve(shape, carryYards, clubId) {
    var club = getClub(clubId);
    var scale = carryYards / club.baseCarry || 0;
    if (shape === 'draw') {
      return -DRAW_FADE_MAGNITUDE_YD * scale;
    }
    if (shape === 'fade') {
      return DRAW_FADE_MAGNITUDE_YD * scale;
    }
    return 0;
  }

  function rollMultiplierForLie(lieType) {
    if (lieType === 'bunker' || lieType === 'water' || lieType === 'ob') {
      return 0;
    }
    if (lieType === 'rough') {
      return ROUGH_ROLL_MULTIPLIER;
    }
    return 1;
  }

  function computeRoll(carryYards, clubId, landingLieType) {
    var club = getClub(clubId);
    return carryYards * club.rollFactor * rollMultiplierForLie(landingLieType);
  }

  var HAZARD_TYPES = { bunker: true, water: true, ob: true };

  function findZoneMatch(point, zones, typeFilter) {
    for (var i = 0; i < zones.length; i++) {
      var zone = zones[i];
      if (typeFilter && !typeFilter[zone.type]) continue;
      if (
        point.x >= zone.xMin &&
        point.x <= zone.xMax &&
        point.y >= zone.yMin &&
        point.y <= zone.yMax
      ) {
        return zone.type;
      }
    }
    return null;
  }

  // Priority order: hazards (bunker/water/ob) always win, even if they sit
  // inside the green's capture circle (a real greenside bunker does not
  // stop being a bunker) — then the green circle, then the broader
  // fairway/rough corridor rectangles, then an off-corridor OB/rough
  // default. This lets a fairway rectangle's yMax reach all the way to the
  // pin without ever masking the green circle underneath it.
  function classifyLie(point, hole) {
    var hazardMatch = findZoneMatch(point, hole.zones, HAZARD_TYPES);
    if (hazardMatch) return hazardMatch;

    var dxToPin = point.x - hole.pin.x;
    var dyToPin = point.y - hole.pin.y;
    if (Math.sqrt(dxToPin * dxToPin + dyToPin * dyToPin) <= hole.greenRadius) {
      return 'green';
    }

    var corridorMatch = findZoneMatch(point, hole.zones, { fairway: true, rough: true });
    if (corridorMatch) return corridorMatch;

    if (point.y < -20 || point.y > hole.yardage + 20 || Math.abs(point.x) > 60) {
      return 'ob';
    }
    return 'rough';
  }

  // state: { position: {x,y} }. shotInput: { club, powerPct, aimDeg, shape,
  // windSpeedMph, windDirectionDeg }. Returns the shot's resolution without
  // mutating state.
  function resolveShot(state, shotInput, hole) {
    var club = getClub(shotInput.club);
    var baseCarry = computeCarryDistance(shotInput.club, shotInput.powerPct);
    var wind = computeWindEffect(
      baseCarry,
      shotInput.windSpeedMph || 0,
      shotInput.windDirectionDeg || 0,
      shotInput.club
    );
    var elevationDelta = computeElevationEffect(hole.elevationChangeFt || 0);
    var effectiveCarry = Math.max(0, baseCarry + wind.distanceDelta + elevationDelta);
    var curve = computeShotShapeCurve(shotInput.shape || 'straight', effectiveCarry, shotInput.club);
    var aimLateral = effectiveCarry * Math.tan(toRadians(shotInput.aimDeg || 0));
    var lateralOffset = aimLateral + curve + wind.lateralDrift;

    var landingPoint = {
      x: state.position.x + lateralOffset,
      y: state.position.y + effectiveCarry
    };
    var landingLie = classifyLie(landingPoint, hole);
    var roll = computeRoll(effectiveCarry, shotInput.club, landingLie);
    var finalPoint = { x: landingPoint.x, y: landingPoint.y + roll };
    var finalLie = classifyLie(finalPoint, hole);

    var penalty = finalLie === 'water' || finalLie === 'ob';
    var resultPosition = penalty ? state.position : finalPoint;

    return {
      club: shotInput.club,
      clubLabel: club.label,
      landingPoint: landingPoint,
      landingLie: landingLie,
      rollYards: roll,
      finalPoint: finalPoint,
      finalLie: finalLie,
      penalty: penalty,
      resultPosition: resultPosition,
      carryYards: effectiveCarry
    };
  }

  // puttInput: { powerPct, aimDeg }. Uses the hole's fixed greenBreakYd
  // (lateral pull over the full green, like a constant crosswind) the same
  // way resolveShot folds in wind drift, so putting reuses one mental model.
  function resolvePutt(position, hole, puttInput) {
    var distance = MAX_PUTT_DISTANCE_YD * (clamp(puttInput.powerPct, 0, 100) / 100);
    var dxToPin = hole.pin.x - position.x;
    var dyToPin = hole.pin.y - position.y;
    var distanceToPin = Math.sqrt(dxToPin * dxToPin + dyToPin * dyToPin);
    var directionX = distanceToPin === 0 ? 0 : dxToPin / distanceToPin;
    var directionY = distanceToPin === 0 ? 1 : dyToPin / distanceToPin;
    var aimRad = toRadians(puttInput.aimDeg || 0);
    var aimedDirX = directionX * Math.cos(aimRad) - directionY * Math.sin(aimRad);
    var aimedDirY = directionX * Math.sin(aimRad) + directionY * Math.cos(aimRad);
    var breakYd = (hole.greenBreakYd || 0) * (distance / MAX_PUTT_DISTANCE_YD);

    var newPoint = {
      x: position.x + aimedDirX * distance + breakYd,
      y: position.y + aimedDirY * distance
    };
    var dxFinal = newPoint.x - hole.pin.x;
    var dyFinal = newPoint.y - hole.pin.y;
    var finalDistanceToPin = Math.sqrt(dxFinal * dxFinal + dyFinal * dyFinal);
    var holed = finalDistanceToPin <= PUTT_CAPTURE_RADIUS_YD;

    return {
      newPoint: holed ? hole.pin : newPoint,
      distanceToPin: finalDistanceToPin,
      holed: holed
    };
  }

  function scoreHole(strokes, par) {
    var delta = strokes - par;
    if (delta <= -2) return { label: 'Eagle', delta: delta };
    if (delta === -1) return { label: 'Birdie', delta: delta };
    if (delta === 0) return { label: 'Par', delta: delta };
    if (delta === 1) return { label: 'Bogey', delta: delta };
    if (delta === 2) return { label: 'Double Bogey', delta: delta };
    return { label: delta > 0 ? 'Triple Bogey+' : 'Condor+', delta: delta };
  }

  // Deterministic string hash (djb2) so the same (dateStr, holeIndex) pair
  // always produces the same wind — no Date.now()/Math.random() involved.
  function hashString(str) {
    var hash = 5381;
    for (var i = 0; i < str.length; i++) {
      hash = (hash * 33) ^ str.charCodeAt(i);
    }
    return hash >>> 0;
  }

  function dailySeed(dateStr, holeIndex) {
    var hash = hashString(dateStr + '#' + holeIndex);
    var windSpeedMph = hash % 21; // 0-20 mph
    var windDirectionDeg = Math.floor(hash / 21) % 360;
    return { windSpeedMph: windSpeedMph, windDirectionDeg: windDirectionDeg };
  }

  function formatScoreLabel(delta) {
    if (delta === 0) return 'E';
    return delta > 0 ? '+' + delta : String(delta);
  }

  global.FairwayEngine = {
    CLUBS: CLUBS,
    HOLE_CAPTURE_RADIUS_YD: PUTT_CAPTURE_RADIUS_YD,
    MAX_PUTT_DISTANCE_YD: MAX_PUTT_DISTANCE_YD,
    computeCarryDistance: computeCarryDistance,
    computeWindEffect: computeWindEffect,
    computeElevationEffect: computeElevationEffect,
    computeShotShapeCurve: computeShotShapeCurve,
    computeRoll: computeRoll,
    classifyLie: classifyLie,
    resolveShot: resolveShot,
    resolvePutt: resolvePutt,
    scoreHole: scoreHole,
    dailySeed: dailySeed,
    formatScoreLabel: formatScoreLabel
  };
})(typeof window !== 'undefined' ? window : globalThis);
