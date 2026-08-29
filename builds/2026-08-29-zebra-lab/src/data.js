// Zebra Lab — category and chapter taxonomy.
// Plain classic script (no ES modules) so this loads via <script> in a file:// page
// and also via a raw eval/vm load from Node in the pure-logic tests.

var ZL_CATEGORY_POPULATION_5 = {
  id: 'population',
  label: 'Population',
  values: [
    { id: 'undergrad', label: 'Undergraduate Sample' },
    { id: 'community', label: 'Community Sample' },
    { id: 'clinical', label: 'Clinical Sample' },
    { id: 'older_adult', label: 'Older Adult Sample' },
    { id: 'pediatric', label: 'Pediatric Sample' },
  ],
};

var ZL_CATEGORY_POPULATION_4 = {
  id: 'population',
  label: 'Population',
  values: [
    { id: 'undergrad', label: 'Undergraduate Sample' },
    { id: 'community', label: 'Community Sample' },
    { id: 'clinical', label: 'Clinical Sample' },
    { id: 'older_adult', label: 'Older Adult Sample' },
  ],
};

var ZL_CATEGORY_DESIGN_5 = {
  id: 'design',
  label: 'Study Design',
  values: [
    { id: 'randomized', label: 'Randomized Experiment' },
    { id: 'quasi', label: 'Quasi-Experiment' },
    { id: 'correlational', label: 'Correlational Study' },
    { id: 'case_study', label: 'Case Study' },
    { id: 'archival', label: 'Archival Study' },
  ],
};

var ZL_CATEGORY_DESIGN_4 = {
  id: 'design',
  label: 'Study Design',
  values: [
    { id: 'randomized', label: 'Randomized Experiment' },
    { id: 'quasi', label: 'Quasi-Experiment' },
    { id: 'correlational', label: 'Correlational Study' },
    { id: 'case_study', label: 'Case Study' },
  ],
};

var ZL_CATEGORY_CONFOUND_5 = {
  id: 'confound',
  label: 'Confound Control',
  values: [
    { id: 'random_assign', label: 'Random Assignment' },
    { id: 'matching', label: 'Matching' },
    { id: 'stat_control', label: 'Statistical Control (Covariates)' },
    { id: 'counterbalance', label: 'Counterbalancing' },
    { id: 'none_used', label: 'No Control Used' },
  ],
};

var ZL_CATEGORY_THREAT_5 = {
  id: 'threat',
  label: 'Threat to Validity',
  values: [
    { id: 'selection', label: 'Selection Bias' },
    { id: 'demand', label: 'Demand Characteristics' },
    { id: 'regression', label: 'Regression to the Mean' },
    { id: 'maturation', label: 'Maturation Effect' },
    { id: 'well_controlled', label: 'Well-Controlled (No Major Threat)' },
  ],
};

var ZL_CATEGORY_SAMPLE_SIZE_4 = {
  id: 'sample_size',
  label: 'Sample Size',
  values: [
    { id: 'small', label: 'Small (n < 30)' },
    { id: 'moderate', label: 'Moderate (n = 30-99)' },
    { id: 'large', label: 'Large (n = 100-299)' },
    { id: 'very_large', label: 'Very Large (n >= 300)' },
  ],
};

// The "position" category is implicit: its values are just the study numbers,
// and its assignment is always the identity (value index === position).
function zlMakePositionCategory(size) {
  var values = [];
  for (var i = 0; i < size; i++) {
    values.push({ id: 'study_' + (i + 1), label: 'Study #' + (i + 1) });
  }
  return { id: 'position', label: 'Study Number', values: values };
}

var ZL_CHAPTERS = [
  {
    id: 1,
    name: 'Intro',
    size: 4,
    clueTypes: ['eq', 'neq'],
    unlockRequirement: 0,
    categories: [ZL_CATEGORY_POPULATION_4, ZL_CATEGORY_DESIGN_4, ZL_CATEGORY_SAMPLE_SIZE_4],
  },
  {
    id: 2,
    name: 'Standard',
    size: 5,
    clueTypes: ['eq', 'neq', 'adjacent'],
    unlockRequirement: 3, // solves in chapter 1
    categories: [ZL_CATEGORY_POPULATION_5, ZL_CATEGORY_DESIGN_5, ZL_CATEGORY_CONFOUND_5, ZL_CATEGORY_THREAT_5],
  },
  {
    id: 3,
    name: 'Expert',
    size: 5,
    clueTypes: ['eq', 'neq', 'adjacent', 'less'],
    unlockRequirement: 3, // solves in chapter 2
    extraPruningPasses: 2,
    categories: [ZL_CATEGORY_POPULATION_5, ZL_CATEGORY_DESIGN_5, ZL_CATEGORY_CONFOUND_5, ZL_CATEGORY_THREAT_5],
  },
];

function zlGetChapter(chapterId) {
  for (var i = 0; i < ZL_CHAPTERS.length; i++) {
    if (ZL_CHAPTERS[i].id === chapterId) return ZL_CHAPTERS[i];
  }
  throw new Error('Unknown chapter id: ' + chapterId);
}

// Deterministic accurate snippets used to compose the AI-explainer's fallback text
// (and to ground the optional live Claude call) — no fabricated claims.
var ZL_METHOD_SNIPPETS = {
  random_assign: 'Random assignment equates groups on both known and unknown variables before the study begins, on average.',
  matching: 'Matching pairs participants on key variables before assigning them to conditions, reducing systematic group differences on those specific variables.',
  stat_control: 'Statistical control (covariates) adjusts for measured confounds after data collection, but only for variables the researcher thought to measure.',
  counterbalance: 'Counterbalancing varies the order in which conditions are presented, spreading out order effects across participants.',
  none_used: 'No confound-control method was used in this study.',
};

var ZL_THREAT_SNIPPETS = {
  selection: 'selection bias, where the groups being compared differ systematically before the study even starts',
  demand: 'demand characteristics, where participants pick up on cues about the hypothesis and change their behavior accordingly',
  regression: 'regression to the mean, where extreme scores drift toward average on retesting regardless of any intervention',
  maturation: 'maturation effects, where natural change over time is mistaken for an effect of the study',
  well_controlled: 'no major threat — this study was well-controlled',
};

// Which threats each method actually addresses (accurate, conservative mapping).
var ZL_METHOD_ADDRESSES = {
  random_assign: ['selection'],
  matching: ['selection'],
  stat_control: ['selection', 'maturation'],
  counterbalance: ['demand'],
  none_used: [],
};
