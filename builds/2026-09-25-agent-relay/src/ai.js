// Agent Relay — optional "Mission Debrief" AI panel.
// Every number sent to the model is already computed by engine.js; this file
// never invents data and never sends personal data. With no API key supplied,
// buildFallbackNote() is used and zero network requests are made.

var AI_MODEL = "claude-haiku-4-5-20251001";

// Find the task whose finish time equals the player's makespan — the task
// that actually determined how long the run took.
function findBottleneckTask(level, placed, makespan) {
  var found = null;
  level.tasks.forEach(function (t) {
    var p = placed[t.id];
    if (p && p.finish === makespan) found = t;
  });
  return found;
}

function buildFallbackNote(level, playerResult, solverResult) {
  var gap = playerResult.makespan - solverResult.optimal;
  if (gap <= 0) {
    return "This schedule matched the true optimal makespan of " + solverResult.optimal + " minutes — every lane finished with no avoidable idle time.";
  }
  var bottleneck = findBottleneckTask(level, playerResult.placed, playerResult.makespan);
  var msg =
    "You finished in " +
    playerResult.makespan +
    " minutes, " +
    gap +
    " minute" +
    (gap === 1 ? "" : "s") +
    " past the true optimal of " +
    solverResult.optimal +
    ".";
  if (bottleneck) {
    msg += ' The last task to finish was "' + bottleneck.name + '" — look at whether an earlier lane choice for it, or for what it was waiting on, could have started it sooner.';
  }
  return msg;
}

function buildPrompt(level, playerResult, solverResult) {
  var lines = level.tasks.map(function (t) {
    var p = playerResult.placed[t.id];
    return t.name + " (duration " + t.duration + "m): finished at " + p.finish + "m on lane " + (p.lane + 1);
  });
  return (
    'A player just finished the scheduling puzzle "' +
    level.title +
    '" with ' +
    level.numLanes +
    " parallel lanes. Player's total makespan: " +
    playerResult.makespan +
    " minutes. True optimal makespan: " +
    solverResult.optimal +
    " minutes. Grade: " +
    playerResult.grade +
    ". Per-task result:\n" +
    lines.join("\n") +
    "\n\nIn 2-3 short sentences, give plain-English coaching on what the player's lane/order choices got right and what they'd change next time. Use only the numbers given above. Do not use markdown."
  );
}

// fetchImpl is injectable so tests can mock the network call.
function getAICoaching(apiKey, level, playerResult, solverResult, fetchImpl) {
  var doFetch = fetchImpl || (typeof fetch !== "undefined" ? fetch : null);
  if (!apiKey || !doFetch) {
    return Promise.resolve(buildFallbackNote(level, playerResult, solverResult));
  }
  var prompt = buildPrompt(level, playerResult, solverResult);
  return doFetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
      "anthropic-dangerous-direct-browser-access": "true"
    },
    body: JSON.stringify({
      model: AI_MODEL,
      max_tokens: 200,
      messages: [{ role: "user", content: prompt }]
    })
  })
    .then(function (res) {
      if (!res.ok) throw new Error("AI request failed");
      return res.json();
    })
    .then(function (data) {
      var text = data && data.content && data.content[0] && data.content[0].text;
      if (!text) throw new Error("No AI text in response");
      return String(text);
    })
    .catch(function () {
      return buildFallbackNote(level, playerResult, solverResult);
    });
}

var AIDebrief = {
  buildFallbackNote: buildFallbackNote,
  buildPrompt: buildPrompt,
  getAICoaching: getAICoaching,
  findBottleneckTask: findBottleneckTask
};

if (typeof module !== "undefined" && module.exports) {
  module.exports = AIDebrief;
} else {
  window.AIDebrief = AIDebrief;
}
