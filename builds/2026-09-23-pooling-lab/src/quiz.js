/*
 * Pooling Lab — quiz question bank and scoring.
 *
 * Pure functions: buildQuestionBank(summary) returns an array of question
 * objects; checkAnswer(question, choiceIndex) returns a boolean. Five
 * questions are fixed conceptual checks; three are generated from whatever
 * simulation state is live right now, so the quiz always reflects the
 * chart currently on screen.
 */
(function (global) {
  'use strict';

  function fixedQuestions() {
    return [
      {
        id: 'tau-zero',
        text: 'If the between-group variance (tau²) is zero, what does the partial-pooling estimate collapse to?',
        choices: [
          'The complete-pooling estimate (the grand mean) for every group',
          'The no-pooling estimate (each group\'s own raw mean)',
          'Something exactly halfway between the two, always',
          'It becomes undefined / NaN',
        ],
        correctIndex: 0,
      },
      {
        id: 'sigma-zero',
        text: 'If the within-group (residual) variance is zero, what does the partial-pooling estimate collapse to?',
        choices: [
          'The complete-pooling estimate (the grand mean) for every group',
          'The no-pooling estimate (each group\'s own raw mean)',
          'Zero, regardless of the data',
          'It becomes undefined / NaN',
        ],
        correctIndex: 1,
      },
      {
        id: 'small-n-shrinks-more',
        text: 'Holding tau² and sigma² fixed, which group shrinks more toward the grand mean?',
        choices: [
          'A group with a small sample size',
          'A group with a large sample size',
          'Shrinkage does not depend on sample size',
          'Whichever group has the highest raw mean',
        ],
        correctIndex: 0,
      },
      {
        id: 'icc-meaning',
        text: 'An intraclass correlation (ICC) close to 1 mainly implies...',
        choices: [
          'Observations in the same group are nearly as different from each other as observations in different groups',
          'Almost all of the variance is between groups rather than within groups',
          'The sample size is too small to trust any of the numbers',
          'The groups have no real effect on the outcome at all',
        ],
        correctIndex: 1,
      },
      {
        id: 'random-intercepts-vs-fixed',
        text: 'A random-intercepts multilevel model differs from treating "group" as an ordinary fixed effect mainly because it...',
        choices: [
          'Estimates a completely unconstrained, independent mean for every group',
          'Assumes group means are themselves drawn from a shared distribution, so information is pooled across groups',
          'Ignores the grouping structure in the data entirely',
          'Requires every group to have exactly the same sample size',
        ],
        correctIndex: 1,
      },
    ];
  }

  /**
   * Build the three questions generated from the current simulation state.
   * @param {Object} summary - output of PoolingStats.computePoolingSummary
   */
  function dynamicQuestions(summary) {
    const groups = summary.perGroup;
    const groupLabel = (g) => 'Group ' + g.id + ' (n=' + g.n + ')';

    const smallest = groups.reduce((a, b) => (b.n < a.n ? b : a));
    const q1 = {
      id: 'dyn-smallest-n',
      text: 'Looking at the chart right now, which group has the smallest sample size?',
      choices: groups.map(groupLabel),
      correctIndex: groups.indexOf(smallest),
    };

    const highestWeight = groups.reduce((a, b) => (b.shrinkageWeight > a.shrinkageWeight ? b : a));
    const q2 = {
      id: 'dyn-least-shrinkage',
      text: 'Right now, which group\'s partial-pooling estimate sits closest to its own raw (no-pooling) mean — i.e. shrank the least?',
      choices: groups.map(groupLabel),
      correctIndex: groups.indexOf(highestWeight),
    };

    const tolerance = 1e-9;
    const diff = summary.empiricalICC === null ? 0 : summary.empiricalICC - summary.trueICC;
    let correctIndex3;
    if (summary.empiricalICC === null || Math.abs(diff) < tolerance) {
      correctIndex3 = 2;
    } else if (diff > 0) {
      correctIndex3 = 0;
    } else {
      correctIndex3 = 1;
    }
    const q3 = {
      id: 'dyn-icc-compare',
      text: 'Right now, is the empirical ICC (estimated from the sample) higher or lower than the true ICC used to generate the data?',
      choices: ['Higher than the true ICC', 'Lower than the true ICC', 'Equal (within rounding)'],
      correctIndex: correctIndex3,
    };

    return [q1, q2, q3];
  }

  function buildQuestionBank(summary) {
    return fixedQuestions().concat(dynamicQuestions(summary));
  }

  function checkAnswer(question, choiceIndex) {
    return choiceIndex === question.correctIndex;
  }

  global.PoolingQuiz = { buildQuestionBank, checkAnswer, fixedQuestions, dynamicQuestions };
})(typeof window !== 'undefined' ? window : globalThis);
