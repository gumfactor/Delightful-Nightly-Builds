// Fixed bank of 18 realistic study-design scenarios for the Power Intuition
// Quiz. The "correct" power is never hardcoded here -- it's computed at
// runtime from computePower() in quiz.js so the quiz can never drift out of
// sync with the Power Explorer's math.
//
// alpha and tails default to the most common case (.05, two-tailed) unless
// the scenario specifically illustrates the effect of changing them.
//
// Classic (non-module) script wrapped in an IIFE -- see stats.js for why.
(function () {

const QUIZ_BANK = [
  {
    id: 1,
    description:
      'A pilot comparing two therapy conditions on a self-report anxiety measure. Small effect (d = 0.2), n = 20 per group.',
    d: 0.2, n: 20, alpha: 0.05, testType: 'two-sample', tails: 'two',
    insight: 'Small effects need much larger samples than most pilot studies collect.',
  },
  {
    id: 2,
    description:
      'Two independent groups, a medium effect size (d = 0.5), n = 20 per group -- a common "convenience sample" size.',
    d: 0.5, n: 20, alpha: 0.05, testType: 'two-sample', tails: 'two',
    insight: 'Even a textbook "medium" effect is badly underpowered at n = 20 per group.',
  },
  {
    id: 3,
    description:
      'The classic rule-of-thumb scenario: medium effect (d = 0.5), n = 64 per group -- the textbook sample size for 80% power.',
    d: 0.5, n: 64, alpha: 0.05, testType: 'two-sample', tails: 'two',
    insight: 'This is the number many methods courses teach by heart -- and it only just clears 80%.',
  },
  {
    id: 4,
    description:
      'A large effect size (d = 0.8) but a small pilot sample, n = 15 per group.',
    d: 0.8, n: 15, alpha: 0.05, testType: 'two-sample', tails: 'two',
    insight: 'A large true effect helps, but it does not make a tiny sample safe.',
  },
  {
    id: 5,
    description:
      'A strong manipulation check (d = 1.2), n = 20 per group.',
    d: 1.2, n: 20, alpha: 0.05, testType: 'two-sample', tails: 'two',
    insight: 'Manipulation checks with very large effects can be adequately powered even with small n.',
  },
  {
    id: 6,
    description:
      'A small-to-medium effect (d = 0.3), n = 50 per group -- a typical online-panel study.',
    d: 0.3, n: 50, alpha: 0.05, testType: 'two-sample', tails: 'two',
    insight: 'Small-to-medium effects are the most common in psychology, and the most chronically underpowered.',
  },
  {
    id: 7,
    description:
      'The same small-to-medium effect (d = 0.3), but n = 100 per group.',
    d: 0.3, n: 100, alpha: 0.05, testType: 'two-sample', tails: 'two',
    insight: 'Doubling n from the previous scenario helps, but still falls short of 80% power.',
  },
  {
    id: 8,
    description:
      'The same small-to-medium effect (d = 0.3), n = 175 per group -- the sample actually required for 80% power here.',
    d: 0.3, n: 175, alpha: 0.05, testType: 'two-sample', tails: 'two',
    insight: 'This is what "well-powered" actually costs for a small-to-medium effect -- far more than most budgets assume.',
  },
  {
    id: 9,
    description:
      'A paired pre/post design, d = 0.4, n = 30 participants.',
    d: 0.4, n: 30, alpha: 0.05, testType: 'one-sample', tails: 'two',
    insight: 'Paired designs are more efficient than between-subjects designs of the same nominal n.',
  },
  {
    id: 10,
    description:
      'A paired design, medium effect (d = 0.5), n = 34 -- near the textbook n for 80% power in a paired t-test.',
    d: 0.5, n: 34, alpha: 0.05, testType: 'one-sample', tails: 'two',
    insight: 'Paired designs need roughly half the participants of a between-subjects design for the same power.',
  },
  {
    id: 11,
    description:
      'A directional (one-tailed) hypothesis, medium effect, n = 50 per group.',
    d: 0.5, n: 50, alpha: 0.05, testType: 'two-sample', tails: 'one',
    insight: 'One-tailed tests reach a given power with less N -- but only justify one-tailed testing when the direction was truly predicted in advance.',
  },
  {
    id: 12,
    description:
      'A small effect (d = 0.2), but a large online panel, n = 800 per group.',
    d: 0.2, n: 800, alpha: 0.05, testType: 'two-sample', tails: 'two',
    insight: 'Big-data panels can detect small effects reliably -- the tradeoff is cost and recruitment time, not statistics.',
  },
  {
    id: 13,
    description:
      'A tiny effect (d = 0.1), n = 50 per group -- many real individual-difference effects are this small.',
    d: 0.1, n: 50, alpha: 0.05, testType: 'two-sample', tails: 'two',
    insight: 'Most individual-difference correlations in psychology are small, and typical sample sizes cannot reliably detect them.',
  },
  {
    id: 14,
    description:
      'The classic scenario (d = 0.5, n = 64 per group), but with a Bonferroni-corrected alpha = .01 for multiple comparisons.',
    d: 0.5, n: 64, alpha: 0.01, testType: 'two-sample', tails: 'two',
    insight: 'Multiple-comparison corrections protect against false positives, but they quietly cost you power.',
  },
  {
    id: 15,
    description:
      'The classic scenario (d = 0.5, n = 64 per group), but with a more liberal alpha = .10.',
    d: 0.5, n: 64, alpha: 0.10, testType: 'two-sample', tails: 'two',
    insight: 'A more liberal alpha buys power, at the cost of more false positives across your research program.',
  },
  {
    id: 16,
    description:
      'A moderately strong social-psychology manipulation effect (d = 0.65), n = 40 per group.',
    d: 0.65, n: 40, alpha: 0.05, testType: 'two-sample', tails: 'two',
    insight: 'Well-designed manipulations with reliable effects can be adequately powered at modest sample sizes.',
  },
  {
    id: 17,
    description:
      'A typical small in-lab study: medium-small effect (d = 0.4), n = 25 per group -- close to the median reported in many psychology subfields.',
    d: 0.4, n: 25, alpha: 0.05, testType: 'two-sample', tails: 'two',
    insight: 'This scenario resembles the median psychology study -- and the median psychology study is underpowered.',
  },
  {
    id: 18,
    description:
      'A very large effect (d = 1.0), but a tiny pilot sample, n = 10 per group.',
    d: 1.0, n: 10, alpha: 0.05, testType: 'two-sample', tails: 'two',
    insight: 'Pilot studies are for feasibility, not for confirming effects -- even huge true effects are a coin flip at n = 10.',
  },
];

window.PowerLabQuizData = { QUIZ_BANK };

})();
