/* CircuitLab quiz engine: pure, DOM-free question-building and scoring logic.
   Depends on REGIONS / REGION_ORDER / CIRCUITS / CIRCUIT_ORDER / VIGNETTES from data.js. */

function shuffleArray(arr, rng) {
  var random = rng || Math.random;
  var copy = arr.slice();
  for (var i = copy.length - 1; i > 0; i--) {
    var j = Math.floor(random() * (i + 1));
    var tmp = copy[i];
    copy[i] = copy[j];
    copy[j] = tmp;
  }
  return copy;
}

/** Build a shuffled multiple-choice list of region ids that always includes correctId. */
function buildRegionChoices(correctId, count, rng) {
  var pool = REGION_ORDER.filter(function (id) { return id !== correctId; });
  var distractors = shuffleArray(pool, rng).slice(0, Math.max(0, count - 1));
  return shuffleArray(distractors.concat([correctId]), rng);
}

function buildLabelQueue(rng) {
  var order = shuffleArray(REGION_ORDER, rng);
  return order.map(function (regionId) {
    return {
      type: 'label',
      regionId: regionId,
      view: REGIONS[regionId].view,
      choices: buildRegionChoices(regionId, 4, rng),
    };
  });
}

function buildFunctionQueue(rng) {
  var order = shuffleArray(REGION_ORDER, rng);
  return order.map(function (regionId) {
    return {
      type: 'function',
      regionId: regionId,
      view: REGIONS[regionId].view,
      prompt: REGIONS[regionId].fn,
    };
  });
}

function buildCircuitQueue(rng) {
  var order = shuffleArray(CIRCUIT_ORDER, rng);
  return order.map(function (circuitId) {
    return {
      type: 'circuit',
      circuitId: circuitId,
      sequence: CIRCUITS[circuitId].sequence,
    };
  });
}

function buildVignetteQueue(vignettes, rng) {
  var order = shuffleArray(vignettes, rng);
  return order.map(function (vignette) {
    return {
      type: 'vignette',
      vignette: vignette,
      choices: buildRegionChoices(vignette.targetRegion, 4, rng),
    };
  });
}

/**
 * Advance a circuit-trace attempt by one click.
 * progress: array of region ids clicked so far (in order).
 * sequence: the correct ordered sequence for the circuit.
 * clickedId: the region id just clicked.
 * Returns { status: 'correct-continue' | 'correct-complete' | 'incorrect', progress }.
 */
function checkCircuitClick(progress, sequence, clickedId) {
  var expectedIndex = progress.length;
  var expected = sequence[expectedIndex];
  if (clickedId !== expected) {
    return { status: 'incorrect', progress: progress };
  }
  var nextProgress = progress.concat([clickedId]);
  if (nextProgress.length === sequence.length) {
    return { status: 'correct-complete', progress: nextProgress };
  }
  return { status: 'correct-continue', progress: nextProgress };
}

function scoreSession(results) {
  var correct = 0;
  for (var i = 0; i < results.length; i++) {
    if (results[i].correct) {
      correct += 1;
    }
  }
  var total = results.length;
  var percent = total === 0 ? 0 : Math.round((correct / total) * 100);
  return { correct: correct, total: total, percent: percent };
}
