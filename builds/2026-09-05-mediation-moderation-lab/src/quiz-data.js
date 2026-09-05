// Quiz: 8 fixed conceptual questions + 8 live questions whose scenario is
// freshly generated and whose correct answer is derived from the same
// mediation/moderation engine functions used in the two lab tabs — never a
// separately hardcoded fact. Classic script, depends on rng/stats/
// mediation-engine/moderation-engine already being loaded.

const FIXED_QUESTIONS = [
  {
    prompt: "In a mediation model X -> M -> Y, what does path 'a' represent?",
    choices: [
      "The relationship between X and M",
      "The relationship between M and Y, controlling for X",
      "The total effect of X on Y",
      "The direct effect of X on Y, controlling for M",
    ],
    correctIndex: 0,
    explanation: "Path a is the coefficient from regressing the mediator M on the predictor X.",
  },
  {
    prompt: "What does it mean if a bootstrap 95% confidence interval for an indirect effect (a x b) includes zero?",
    choices: [
      "The mediation effect is statistically significant",
      "The data cannot rule out a true indirect effect of zero — not statistically significant",
      "The direct effect must also be zero",
      "The sample size was too small to compute a p-value",
    ],
    correctIndex: 1,
    explanation: "A CI that includes zero means zero is a plausible value for the true indirect effect, so it isn't considered statistically significant at that confidence level.",
  },
  {
    prompt: "Why is bootstrapping generally preferred over the classic Sobel test for testing an indirect effect?",
    choices: [
      "Bootstrapping always gives a narrower confidence interval",
      "The Sobel test requires a larger sample size to run at all",
      "The sampling distribution of a product of two coefficients (a x b) is often skewed/non-normal, which the Sobel test's normal-theory approximation does not account for",
      "Bootstrapping does not require any assumptions about the regression model itself",
    ],
    correctIndex: 2,
    explanation: "a x b is a product of two estimates, and products of normally-distributed variables are generally not themselves normally distributed — bootstrapping doesn't assume normality of that product's sampling distribution the way the Sobel test does.",
  },
  {
    prompt: "In moderation analysis, why are the predictor X and moderator Z typically mean-centered before forming the interaction term X*Z?",
    choices: [
      "Centering is purely cosmetic and has no effect on the model",
      "It reduces structural multicollinearity between the interaction term and the main-effect terms, and makes the main-effect coefficients interpretable at the mean of the other variable",
      "It is required for the regression equations to be solvable at all",
      "It converts the moderation model into a mediation model",
    ],
    correctIndex: 1,
    explanation: "Without centering, X and X*Z (and Z and X*Z) tend to be highly correlated purely as an artifact of scale, and the main-effect coefficients would represent effects at X=0/Z=0 rather than at the variables' means.",
  },
  {
    prompt: "What is a 'simple slope' in the context of moderation analysis?",
    choices: [
      "The average slope across the entire sample, ignoring the moderator",
      "The slope of X predicting Y evaluated at one specific, fixed value of the moderator Z (e.g. -1 SD, mean, +1 SD)",
      "The correlation between X and Z",
      "The slope of the interaction term itself",
    ],
    correctIndex: 1,
    explanation: "A simple slope answers 'what is the effect of X on Y specifically when Z is high / average / low', which is what makes an interaction concrete and interpretable.",
  },
  {
    prompt: "What does the Johnson-Neyman technique identify?",
    choices: [
      "The single best-fit regression line",
      "The exact value(s) of the moderator at which the simple slope of X on Y transitions between statistically significant and non-significant",
      "The optimal sample size for detecting an interaction",
      "Whether X and M are correlated",
    ],
    correctIndex: 1,
    explanation: "Rather than picking arbitrary points (-1 SD/mean/+1 SD), the Johnson-Neyman technique solves directly for the moderator value(s) where the simple slope's significance boundary is crossed.",
  },
  {
    prompt: "In a mediation model, what is the relationship between the total effect (c), the direct effect (c'), and the indirect effect (a x b)?",
    choices: [
      "They are unrelated quantities",
      "c = c' + (a x b) — the total effect equals the direct effect plus the indirect effect",
      "c' is always larger than c",
      "a x b = c - 1",
    ],
    correctIndex: 1,
    explanation: "This is a defining algebraic identity of the single-mediator OLS model: the effect of X on Y with no mediator in the model (c) decomposes exactly into the effect that remains after adding M (c') plus the part that flows through M (a x b).",
  },
  {
    prompt: "True or False: a statistically significant interaction term (b3) guarantees that the simple slopes at both high and low levels of the moderator are individually significant.",
    choices: [
      "True",
      "False — a significant interaction only means the slope changes significantly across levels of the moderator; one simple slope can be significant while the other is not, or both could even be significant in opposite directions",
    ],
    correctIndex: 1,
    explanation: "A significant b3 tells you the slope itself changes with the moderator — it says nothing directly about whether any one simple slope crosses zero or reaches significance on its own.",
  },
];

function round(v, d) {
  const f = Math.pow(10, d);
  return Math.round(v * f) / f;
}

function liveMediationScenario(seedBase, offset) {
  const seed = hashSeed(seedBase + ':med:' + offset);
  const trueA = 0.8 + (offset % 3) * 0.4;
  const trueB = offset % 2 === 0 ? 1.2 : 0.15;
  const trueCPrime = 0.3;
  const sample = generateMediationSample({ trueA, trueB, trueCPrime, noiseSD: 1.5, n: 40, seed });
  const stats = analyzeMediation(sample, sample.rng, 1500);
  return stats;
}

function liveModerationScenario(seedBase, offset) {
  const seed = hashSeed(seedBase + ':mod:' + offset);
  const trueB1 = 1.0;
  const trueB2 = 0.5;
  const trueB3 = offset % 2 === 0 ? 0.6 : 0.02;
  const sample = generateModerationSample({ trueB1, trueB2, trueB3, noiseSD: 2.0, n: 40, seed });
  const stats = analyzeModeration(sample, 0.05);
  return stats;
}

function buildLiveQuestions(seedBase) {
  const q = [];

  // 1. Indirect effect significance (yes/no)
  {
    const s = liveMediationScenario(seedBase, 1);
    q.push({
      prompt: `A mediation sample was just generated (n=40). Its indirect effect (a x b) is ${round(s.indirect, 3)} with a bootstrap 95% CI of [${round(s.bootstrapCI[0], 3)}, ${round(s.bootstrapCI[1], 3)}]. Is this indirect effect statistically significant?`,
      choices: ['Yes, the CI excludes zero', 'No, the CI includes zero'],
      correctIndex: s.ciExcludesZero ? 0 : 1,
      explanation: `The bootstrap CI [${round(s.bootstrapCI[0], 3)}, ${round(s.bootstrapCI[1], 3)}] ${s.ciExcludesZero ? 'excludes' : 'includes'} zero, so the indirect effect is ${s.ciExcludesZero ? '' : 'not '}statistically significant at the 95% level.`,
    });
  }

  // 2. Estimated indirect effect value (multiple choice numeric)
  {
    const s = liveMediationScenario(seedBase, 2);
    const correct = round(s.indirect, 2);
    const options = [correct, round(correct + 0.6, 2), round(correct - 0.6, 2), round(correct + 1.3, 2)];
    q.push({
      prompt: `In another freshly generated mediation sample, path a = ${round(s.a, 3)} and path b = ${round(s.b, 3)}. Which of these is closest to the indirect effect (a x b)?`,
      choices: options.map(String),
      correctIndex: 0,
      explanation: `Indirect effect = a x b = ${round(s.a, 3)} x ${round(s.b, 3)} = ${correct}.`,
    });
  }

  // 3. Total vs direct effect magnitude
  {
    const s = liveMediationScenario(seedBase, 3);
    const totalBigger = Math.abs(s.c) > Math.abs(s.cPrime);
    q.push({
      prompt: `For this sample, the total effect c = ${round(s.c, 3)} and the direct effect c' = ${round(s.cPrime, 3)}. Which has the larger magnitude?`,
      choices: ['Total effect (c)', 'Direct effect (c\')', 'They are exactly equal'],
      correctIndex: totalBigger ? 0 : 1,
      explanation: `|c| = ${round(Math.abs(s.c), 3)} and |c'| = ${round(Math.abs(s.cPrime), 3)}, so the ${totalBigger ? 'total' : 'direct'} effect is larger in magnitude here.`,
    });
  }

  // 4. Partial mediation evidence
  {
    const s = liveMediationScenario(seedBase, 4);
    const partial = Math.abs(s.cPrime) < Math.abs(s.c);
    q.push({
      prompt: `Total effect c = ${round(s.c, 3)}, direct effect c' = ${round(s.cPrime, 3)}. Does this pattern show evidence consistent with at least partial mediation through M?`,
      choices: ['Yes, |c\'| < |c|', 'No, |c\'| is not smaller than |c|'],
      correctIndex: partial ? 0 : 1,
      explanation: `Partial mediation is suggested when the direct effect shrinks relative to the total effect once M is added — here |c'|=${round(Math.abs(s.cPrime), 3)} vs |c|=${round(Math.abs(s.c), 3)}.`,
    });
  }

  // 5. Interaction significance
  {
    const s = liveModerationScenario(seedBase, 1);
    q.push({
      prompt: `A moderation sample (n=40) produced an interaction coefficient b3 = ${round(s.beta[3], 3)}, p = ${round(s.interactionP, 4)}. Is the interaction statistically significant at alpha = .05?`,
      choices: ['Yes', 'No'],
      correctIndex: s.interactionSignificant ? 0 : 1,
      explanation: `p = ${round(s.interactionP, 4)} is ${s.interactionSignificant ? 'below' : 'above'} .05, so the interaction is ${s.interactionSignificant ? '' : 'not '}statistically significant.`,
    });
  }

  // 6. Simple slope at +1 SD significance
  {
    const s = liveModerationScenario(seedBase, 2);
    const hi = s.simpleSlopes[2];
    q.push({
      prompt: `At +1 SD of the moderator, the simple slope of X on Y is ${round(hi.slope, 3)} with p = ${round(hi.p, 4)}. Is this simple slope statistically significant?`,
      choices: ['Yes', 'No'],
      correctIndex: hi.significant ? 0 : 1,
      explanation: `p = ${round(hi.p, 4)} is ${hi.significant ? 'below' : 'above'} .05.`,
    });
  }

  // 7. Johnson-Neyman boundary existence
  {
    const s = liveModerationScenario(seedBase, 3);
    const hasBoundary = !!s.jnRoots;
    q.push({
      prompt: `For this sample, does a finite Johnson-Neyman region boundary exist (a moderator value where the simple slope's significance flips), or is the relationship uniformly significant/non-significant across the observed range?`,
      choices: ['A finite boundary exists', 'No finite boundary was found'],
      correctIndex: hasBoundary ? 0 : 1,
      explanation: hasBoundary
        ? `The solver found real root(s): ${s.jnRoots.map(r => round(r, 2)).join(', ')}.`
        : `The quadratic solve found no real roots, meaning the slope's significance does not change sign anywhere.`,
    });
  }

  // 8. Which simple slope is most significant
  {
    const s = liveModerationScenario(seedBase, 4);
    let minIdx = 0;
    for (let i = 1; i < s.simpleSlopes.length; i++) {
      if (s.simpleSlopes[i].p < s.simpleSlopes[minIdx].p) minIdx = i;
    }
    q.push({
      prompt: `Among the three simple slopes computed (-1 SD, Mean, +1 SD of the moderator), which has the smallest p-value (strongest evidence of a non-zero slope)?`,
      choices: s.simpleSlopes.map(ss => `${ss.label} (p = ${round(ss.p, 4)})`),
      correctIndex: minIdx,
      explanation: `${s.simpleSlopes[minIdx].label} has the smallest p-value (${round(s.simpleSlopes[minIdx].p, 4)}).`,
    });
  }

  return q;
}

function buildQuiz(seedBase) {
  seedBase = seedBase || String(Date.now());
  const fixed = FIXED_QUESTIONS.map(q => Object.assign({ type: 'fixed' }, q));
  const live = buildLiveQuestions(seedBase).map(q => Object.assign({ type: 'live' }, q));
  const all = fixed.concat(live);
  return all;
}
