// Marginal Gains — optional AI Advisor.
// Every number sent to the model is already computed by engine.js; this file
// never invents data. With no API key supplied, buildFallbackNote() is used
// and zero network requests are made.

var AI_MODEL = "claude-haiku-4-5-20251001";

function largestGap(projects, allocation, optimalAllocation) {
  var worst = null;
  projects.forEach(function (p) {
    var playerHours = allocation[p.id] || 0;
    var optHours = optimalAllocation[p.id] || 0;
    var playerVal = Engine.projectValueAt(p, playerHours);
    var optVal = Engine.projectValueAt(p, optHours);
    var lost = optVal - playerVal;
    if (!worst || lost > worst.lost) {
      worst = { project: p, playerHours: playerHours, optHours: optHours, lost: lost };
    }
  });
  return worst;
}

function mostOverinvested(projects, allocation, optimalAllocation) {
  var worst = null;
  projects.forEach(function (p) {
    var playerHours = allocation[p.id] || 0;
    var optHours = optimalAllocation[p.id] || 0;
    var over = playerHours - optHours;
    if (!worst || over > worst.over) {
      worst = { project: p, over: over };
    }
  });
  return worst;
}

function buildFallbackNote(projects, allocation, scoreResult) {
  var gap = largestGap(projects, allocation, scoreResult.optimalAllocation);
  var over = mostOverinvested(projects, allocation, scoreResult.optimalAllocation);
  if (!gap || gap.lost <= 0) {
    return "This allocation was at or very near optimal — every hour was well spent.";
  }
  var msg =
    "You left " +
    gap.lost +
    " points on the table by putting " +
    gap.playerHours +
    "h into \"" +
    gap.project.name +
    "\" instead of the optimal " +
    gap.optHours +
    "h.";
  if (over && over.over > 0 && over.project.id !== gap.project.id) {
    msg +=
      ' Those extra hours would have gone further there than the ' +
      over.over +
      'h spent past-optimal on "' +
      over.project.name +
      '".';
  }
  return msg;
}

function buildPrompt(projects, allocation, scoreResult) {
  var lines = projects.map(function (p) {
    var playerHours = allocation[p.id] || 0;
    var optHours = scoreResult.optimalAllocation[p.id] || 0;
    return (
      p.name +
      " (" +
      p.category +
      "): you allocated " +
      playerHours +
      "h (value " +
      Engine.projectValueAt(p, playerHours) +
      "), optimal was " +
      optHours +
      "h (value " +
      Engine.projectValueAt(p, optHours) +
      ")"
    );
  });
  return (
    "A player just finished a resource-allocation puzzle. Budget: " +
    scoreResult.hoursUsed +
    " hours used of the total budget. Player scored " +
    scoreResult.percent +
    "% of the optimal total (grade " +
    scoreResult.grade +
    "). Per-project breakdown:\n" +
    lines.join("\n") +
    "\n\nIn 2-3 short sentences, give plain-English coaching on what they got right and what they'd allocate differently next time. Use only the numbers given above. Do not use markdown."
  );
}

// fetchImpl is injectable so tests can mock the network call.
function getAICoaching(apiKey, projects, allocation, scoreResult, fetchImpl) {
  var doFetch = fetchImpl || (typeof fetch !== "undefined" ? fetch : null);
  if (!apiKey || !doFetch) {
    return Promise.resolve(buildFallbackNote(projects, allocation, scoreResult));
  }
  var prompt = buildPrompt(projects, allocation, scoreResult);
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
      return buildFallbackNote(projects, allocation, scoreResult);
    });
}

var AIAdvisor = {
  buildFallbackNote: buildFallbackNote,
  buildPrompt: buildPrompt,
  getAICoaching: getAICoaching,
  largestGap: largestGap,
  mostOverinvested: mostOverinvested
};

if (typeof module !== "undefined" && module.exports) {
  module.exports = AIAdvisor;
} else {
  window.AIAdvisor = AIAdvisor;
}
