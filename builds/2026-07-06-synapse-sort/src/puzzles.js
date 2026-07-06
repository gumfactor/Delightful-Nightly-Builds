// Synapse Sort — curated puzzle bank.
// Classic script (no ES module export) so the game can be opened via file://.
// Each puzzle: 4 categories, each with exactly 4 unique items and a distinct
// difficulty tier (yellow = easiest, green, blue, purple = trickiest).

const PUZZLES = [
  {
    id: "p01",
    title: "Brain & Body",
    categories: [
      { name: "Brain Regions", difficulty: "yellow", items: ["AMYGDALA", "HIPPOCAMPUS", "CORTEX", "INSULA"] },
      { name: "Neurotransmitters & Hormones", difficulty: "green", items: ["DOPAMINE", "SEROTONIN", "CORTISOL", "OXYTOCIN"] },
      { name: "Ways Psychologists Talk About Stress", difficulty: "blue", items: ["AROUSAL", "HABITUATION", "RESILIENCE", "REAPPRAISAL"] },
      { name: "Research-Design Words", difficulty: "purple", items: ["CONFOUND", "BASELINE", "PLACEBO", "EXTINCTION"] }
    ]
  },
  {
    id: "p02",
    title: "Prompting the Machine",
    categories: [
      { name: "Parts of an LLM Request", difficulty: "yellow", items: ["PROMPT", "TOKEN", "CONTEXT WINDOW", "TEMPERATURE"] },
      { name: "Agent Building Blocks", difficulty: "green", items: ["SUBAGENT", "TOOLCALL", "ORCHESTRATION", "SANDBOX"] },
      { name: "Things That Go Wrong", difficulty: "blue", items: ["HALLUCINATION", "JAILBREAK", "LATENCY", "DRIFT"] },
      { name: "Claude Code Automation Types", difficulty: "purple", items: ["ROUTINE", "SKILL", "HOOK", "MCP"] }
    ]
  },
  {
    id: "p03",
    title: "Market Watch",
    categories: [
      { name: "Market Moods", difficulty: "yellow", items: ["BULL", "BEAR", "RALLY", "CORRECTION"] },
      { name: "Ways to Own a Slice", difficulty: "green", items: ["EQUITY", "BOND", "ETF", "OPTIONS"] },
      { name: "Portfolio Math", difficulty: "blue", items: ["YIELD", "LEVERAGE", "DILUTION", "COMPOUND"] },
      { name: "Trading Jargon", difficulty: "purple", items: ["SPREAD", "ARBITRAGE", "SHORT", "BUYBACK"] }
    ]
  },
  {
    id: "p04",
    title: "Great White North Brands",
    categories: [
      { name: "Coffee & Food Stops", difficulty: "yellow", items: ["TIM HORTONS", "MCCAIN", "LOBLAWS", "SOBEYS"] },
      { name: "Tech & Industry", difficulty: "green", items: ["SHOPIFY", "BOMBARDIER", "MAGNA", "BLACKBERRY"] },
      { name: "Banks & Finance", difficulty: "blue", items: ["RBC", "TD", "DESJARDINS", "MANULIFE"] },
      { name: "Wear It Home", difficulty: "purple", items: ["ROOTS", "LULULEMON", "CANADA GOOSE", "ARC'TERYX"] }
    ]
  },
  {
    id: "p05",
    title: "Finish Line to Fairway",
    categories: [
      { name: "Running Terms", difficulty: "yellow", items: ["TAPER", "CADENCE", "NEGATIVE SPLIT", "BONK"] },
      { name: "Golf Scoring", difficulty: "green", items: ["BIRDIE", "BOGEY", "EAGLE", "MULLIGAN"] },
      { name: "On the Water", difficulty: "blue", items: ["PORT", "STARBOARD", "KEEL", "BALLAST"] },
      { name: "Ways to Curve Off Course", difficulty: "purple", items: ["TACK", "HOOK", "SLICE", "DRAW"] }
    ]
  },
  {
    id: "p06",
    title: "Context Switching",
    categories: [
      { name: "Ways the Mind Files Things Away", difficulty: "yellow", items: ["SCHEMA", "PRIMING", "HEURISTIC", "BIAS"] },
      { name: "Parts of a Retrieval Pipeline", difficulty: "green", items: ["TOKEN", "EMBEDDING", "RETRIEVAL", "VECTOR"] },
      { name: "Signs the Market Turned", difficulty: "blue", items: ["RALLY", "CORRECTION", "RECESSION", "MOMENTUM"] },
      { name: "Big Five Banks", difficulty: "purple", items: ["RBC", "TD", "SCOTIABANK", "BMO"] }
    ]
  },
  {
    id: "p07",
    title: "Signal and Noise",
    categories: [
      { name: "Hormones Under Stress", difficulty: "yellow", items: ["CORTISOL", "ADRENALINE", "OXYTOCIN", "MELATONIN"] },
      { name: "When the Model Slips", difficulty: "green", items: ["HALLUCINATION", "DRIFT", "OVERFITTING", "TIMEOUT"] },
      { name: "Ways to Bet Against", difficulty: "blue", items: ["SHORT", "HEDGE", "MARGIN", "DERIVATIVE"] },
      { name: "Golf Score Words", difficulty: "purple", items: ["BIRDIE", "BOGEY", "EAGLE", "PAR"] }
    ]
  },
  {
    id: "p08",
    title: "Off the Grid",
    categories: [
      { name: "Brain Regions, Part Two", difficulty: "yellow", items: ["THALAMUS", "CEREBELLUM", "BRAINSTEM", "INSULA"] },
      { name: "Claude Code Automation", difficulty: "green", items: ["ROUTINE", "SKILL", "HOOK", "MCP"] },
      { name: "Outerwear Made in Canada", difficulty: "blue", items: ["ROOTS", "CANADA GOOSE", "ARC'TERYX", "MEC"] },
      { name: "Sailing Vocabulary", difficulty: "purple", items: ["PORT", "STARBOARD", "KEEL", "RUDDER"] }
    ]
  },
  {
    id: "p09",
    title: "Field Notes",
    categories: [
      { name: "Research-Design Words, Round Two", difficulty: "yellow", items: ["CONFOUND", "BASELINE", "PLACEBO", "BLINDING"] },
      { name: "Ways to Own a Slice of the Market", difficulty: "green", items: ["EQUITY", "BOND", "ETF", "OPTIONS"] },
      { name: "Grocery Aisle Canadiana", difficulty: "blue", items: ["LOBLAWS", "SOBEYS", "METRO", "MCCAIN"] },
      { name: "Running Workouts", difficulty: "purple", items: ["FARTLEK", "TEMPO RUN", "TAPER", "NEGATIVE SPLIT"] }
    ]
  },
  {
    id: "p10",
    title: "Full Stack",
    categories: [
      { name: "Building Blocks of an Agent", difficulty: "yellow", items: ["SUBAGENT", "TOOLCALL", "ORCHESTRATION", "SANDBOX"] },
      { name: "Portfolio Vocabulary", difficulty: "green", items: ["YIELD", "DIVIDEND", "PORTFOLIO", "TICKER"] },
      { name: "Planes, Trains, and Automobiles (Canadian)", difficulty: "blue", items: ["AIR CANADA", "WESTJET", "VIA RAIL", "PORTER"] },
      { name: "Golf Course Geography", difficulty: "purple", items: ["FAIRWAY", "DIVOT", "HANDICAP", "ROUGH"] }
    ]
  },
  {
    id: "p11",
    title: "Second Opinion",
    categories: [
      { name: "Ways Psychologists Describe a Reaction", difficulty: "yellow", items: ["VALENCE", "AROUSAL", "RUMINATION", "ALEXITHYMIA"] },
      { name: "Model Training Words", difficulty: "green", items: ["GRADIENT", "FINE-TUNE", "CHECKPOINT", "INFERENCE"] },
      { name: "Trading Jargon, Round Two", difficulty: "blue", items: ["ARBITRAGE", "SPREAD", "LIQUIDITY", "PREMIUM"] },
      { name: "Insurance & Finance Giants", difficulty: "purple", items: ["MANULIFE", "SUN LIFE", "DESJARDINS", "CIBC"] }
    ]
  },
  {
    id: "p12",
    title: "Under Pressure",
    categories: [
      { name: "Coping & Stress Terms", difficulty: "yellow", items: ["STRESSOR", "COPING", "RESILIENCE", "REAPPRAISAL"] },
      { name: "Things That Slow a Model Down", difficulty: "green", items: ["LATENCY", "BOTTLENECK", "TIMEOUT", "OVERFITTING"] },
      { name: "Market Weather", difficulty: "blue", items: ["BULL", "BEAR", "VOLATILITY", "INFLATION"] },
      { name: "Running Metrics", difficulty: "purple", items: ["CADENCE", "VO2 MAX", "SPLITS", "BONK"] }
    ]
  },
  {
    id: "p13",
    title: "Between the Lines",
    categories: [
      { name: "Brain Chemistry", difficulty: "yellow", items: ["DOPAMINE", "SEROTONIN", "GLUTAMATE", "GABA"] },
      { name: "Parts of the Transformer", difficulty: "green", items: ["ATTENTION", "ENCODER", "DECODER", "EMBEDDING"] },
      { name: "Bookstore & Retail Canadiana", difficulty: "blue", items: ["INDIGO", "HUDSON'S BAY", "CANADIAN TIRE", "RW&CO"] },
      { name: "Boat Parts", difficulty: "purple", items: ["BOW", "STERN", "HELM", "CLEAT"] }
    ]
  },
  {
    id: "p14",
    title: "Home Field Advantage",
    categories: [
      { name: "Ways We Judge Others (and Ourselves)", difficulty: "yellow", items: ["EMPATHY", "PSYCHOPATHY", "BIAS", "SCHEMA"] },
      { name: "Words on an Earnings Call", difficulty: "green", items: ["VALUATION", "MULTIPLE", "DISCOUNT", "CAPITAL GAIN"] },
      { name: "Industrial & Tech Canada", difficulty: "blue", items: ["BOMBARDIER", "MAGNA", "CGI", "OPEN TEXT"] },
      { name: "Ways to Curve Off Line", difficulty: "purple", items: ["HOOK", "SLICE", "DRAW", "TACK"] }
    ]
  },
  {
    id: "p15",
    title: "Ship It",
    categories: [
      { name: "Words in an Agent's System Prompt", difficulty: "yellow", items: ["GUARDRAIL", "SYSTEM PROMPT", "TOOLCALL", "SANDBOX"] },
      { name: "Index & Fund Words", difficulty: "green", items: ["INDEX", "ETF", "DERIVATIVE", "COMMODITY"] },
      { name: "Food & Beverage Giants", difficulty: "blue", items: ["SAPUTO", "COUCHE-TARD", "MCCAIN", "TIM HORTONS"] },
      { name: "Sailing Maneuvers", difficulty: "purple", items: ["TACK", "WAKE", "KNOT", "BUOY"] }
    ]
  },
  {
    id: "p16",
    title: "Mind Games",
    categories: [
      { name: "More Brain Regions", difficulty: "yellow", items: ["HIPPOCAMPUS", "AMYGDALA", "PREFRONTAL", "LIMBIC"] },
      { name: "Hormones & Neurotransmitters, Round Two", difficulty: "green", items: ["ADRENALINE", "MELATONIN", "GABA", "GLUTAMATE"] },
      { name: "Cognitive Shortcuts & Blind Spots", difficulty: "blue", items: ["HEURISTIC", "BIAS", "RUMINATION", "ALEXITHYMIA"] },
      { name: "Methods Words", difficulty: "purple", items: ["REPLICATION", "SAMPLE", "VARIANCE", "BLINDING"] }
    ]
  },
  {
    id: "p17",
    title: "Agent Ops",
    categories: [
      { name: "Ways an Agent Talks to Tools", difficulty: "yellow", items: ["TOOLCALL", "MCP", "SANDBOX", "GUARDRAIL"] },
      { name: "What You Tune", difficulty: "green", items: ["TEMPERATURE", "FINE-TUNE", "CHECKPOINT", "GRADIENT"] },
      { name: "When Things Break", difficulty: "blue", items: ["HALLUCINATION", "JAILBREAK", "DRIFT", "TIMEOUT"] },
      { name: "Pipeline Pieces", difficulty: "purple", items: ["RETRIEVAL", "VECTOR", "PIPELINE", "WORKFLOW"] }
    ]
  },
  {
    id: "p18",
    title: "Bull Market Bingo",
    categories: [
      { name: "Economic Weather", difficulty: "yellow", items: ["INFLATION", "RECESSION", "VOLATILITY", "CORRECTION"] },
      { name: "Ways to Structure a Position", difficulty: "green", items: ["OPTIONS", "FUTURES", "MARGIN", "LEVERAGE"] },
      { name: "Owner's Vocabulary", difficulty: "blue", items: ["EQUITY", "BOND", "PORTFOLIO", "TICKER"] },
      { name: "Reasons a Stock Moves", difficulty: "purple", items: ["DIVIDEND", "BUYBACK", "DILUTION", "CAPITAL GAIN"] }
    ]
  },
  {
    id: "p19",
    title: "Everyday Canadiana",
    categories: [
      { name: "Where You'd Grab a Coffee or Groceries", difficulty: "yellow", items: ["TIM HORTONS", "METRO", "CANADIAN TIRE", "INDIGO"] },
      { name: "Bank Cards in Your Wallet", difficulty: "green", items: ["SCOTIABANK", "BMO", "CIBC", "DESJARDINS"] },
      { name: "Grown in Canada, Worn Everywhere", difficulty: "blue", items: ["ROOTS", "MEC", "RW&CO", "HUDSON'S BAY"] },
      { name: "Industrial Giants", difficulty: "purple", items: ["BOMBARDIER", "MAGNA", "SAPUTO", "COUCHE-TARD"] }
    ]
  },
  {
    id: "p20",
    title: "Around the Buoy",
    categories: [
      { name: "Distance Running", difficulty: "yellow", items: ["FARTLEK", "TEMPO RUN", "VO2 MAX", "SPLITS"] },
      { name: "On the Green", difficulty: "green", items: ["FAIRWAY", "DIVOT", "HANDICAP", "PAR"] },
      { name: "Parts of a Sailboat", difficulty: "blue", items: ["BOW", "STERN", "KEEL", "RUDDER"] },
      { name: "Nautical Distance & Markers", difficulty: "purple", items: ["KNOT", "BUOY", "HELM", "WAKE"] }
    ]
  },
  {
    id: "p21",
    title: "Prior and Posterior",
    categories: [
      { name: "Words a Grant Reviewer Loves", difficulty: "yellow", items: ["REPLICATION", "SAMPLE", "VARIANCE", "RESILIENCE"] },
      { name: "Retrieval-Augmented Vocabulary", difficulty: "green", items: ["EMBEDDING", "VECTOR", "RETRIEVAL", "CONTEXT WINDOW"] },
      { name: "What Analysts Argue About", difficulty: "blue", items: ["VALUATION", "MULTIPLE", "YIELD", "PREMIUM"] },
      { name: "Grocery Aisle, One More Time", difficulty: "purple", items: ["LOBLAWS", "METRO", "SOBEYS", "TIM HORTONS"] }
    ]
  },
  {
    id: "p22",
    title: "Overclocked",
    categories: [
      { name: "Feelings, Named Precisely", difficulty: "yellow", items: ["VALENCE", "ALEXITHYMIA", "EMPATHY", "PSYCHOPATHY"] },
      { name: "Speed & Cost of Inference", difficulty: "green", items: ["LATENCY", "TOKEN", "TEMPERATURE", "INFERENCE"] },
      { name: "Words for Getting Paid", difficulty: "blue", items: ["DIVIDEND", "YIELD", "CAPITAL GAIN", "BUYBACK"] },
      { name: "Marathon-Adjacent Vocabulary", difficulty: "purple", items: ["TAPER", "BONK", "CADENCE", "NEGATIVE SPLIT"] }
    ]
  },
  {
    id: "p23",
    title: "Compile Time",
    categories: [
      { name: "Ways a Study Goes Wrong", difficulty: "yellow", items: ["CONFOUND", "REPLICATION", "BLINDING", "EXTINCTION"] },
      { name: "Words for How an Agent Is Wired", difficulty: "green", items: ["ORCHESTRATION", "WORKFLOW", "PIPELINE", "DECODER"] },
      { name: "Retail Wardrobe", difficulty: "blue", items: ["ROOTS", "LULULEMON", "RW&CO", "CANADIAN TIRE"] },
      { name: "Boat Handling", difficulty: "purple", items: ["HELM", "RUDDER", "CLEAT", "TACK"] }
    ]
  },
  {
    id: "p24",
    title: "Home Ice",
    categories: [
      { name: "Talking About the Nervous System", difficulty: "yellow", items: ["VAGUS", "LIMBIC", "MYELIN", "SYNAPSE"] },
      { name: "Words From a Term Sheet", difficulty: "green", items: ["LEVERAGE", "DILUTION", "MARGIN", "COMPOUND"] },
      { name: "Telecom & Tech Canada", difficulty: "blue", items: ["SHOPIFY", "BLACKBERRY", "OPEN TEXT", "CGI"] },
      { name: "Golf Shot Shapes & Slips", difficulty: "purple", items: ["HOOK", "SLICE", "MULLIGAN", "DIVOT"] }
    ]
  },
  {
    id: "p25",
    title: "No Assembly Required",
    categories: [
      { name: "Words for the Model Itself", difficulty: "yellow", items: ["TRANSFORMER", "ATTENTION", "GRADIENT", "DECODER"] },
      { name: "Fund & Contract Types", difficulty: "green", items: ["FUTURES", "COMMODITY", "CURRENCY", "DERIVATIVE"] },
      { name: "Money You'd Trust With Your Paycheque", difficulty: "blue", items: ["TD", "SUN LIFE", "BMO", "CIBC"] },
      { name: "Words for a Personal Best (or Worst)", difficulty: "purple", items: ["BONK", "PAR", "HANDICAP", "KNOT"] }
    ]
  },
  {
    id: "p26",
    title: "Signal Boost",
    categories: [
      { name: "Reading the Room (Emotionally)", difficulty: "yellow", items: ["REAPPRAISAL", "RUMINATION", "ATTACHMENT", "COPING"] },
      { name: "What Makes an Agent Reliable", difficulty: "green", items: ["GUARDRAIL", "CHECKPOINT", "SANDBOX", "INFERENCE"] },
      { name: "IPO Vocabulary", difficulty: "blue", items: ["EARNINGS", "GUIDANCE", "FLOAT", "LOCKUP"] },
      { name: "Home-Grown Grocery & Pharmacy", difficulty: "purple", items: ["LOBLAWS", "SHOPPERS DRUG MART", "CANADIAN TIRE", "INDIGO"] }
    ]
  },
  {
    id: "p27",
    title: "Tapering Off",
    categories: [
      { name: "The Body Under Load", difficulty: "yellow", items: ["STRESSOR", "AROUSAL", "HABITUATION", "COPING"] },
      { name: "Words on an Eval Dashboard", difficulty: "green", items: ["REGRESSION", "BOTTLENECK", "TIMEOUT", "JAILBREAK"] },
      { name: "Words From a Shareholder Letter", difficulty: "blue", items: ["COMPOUND", "LEVERAGE", "GUIDANCE", "EARNINGS"] },
      { name: "Words for the Long Haul", difficulty: "purple", items: ["TAPER", "BONK", "VO2 MAX", "TEMPO RUN"] }
    ]
  },
  {
    id: "p28",
    title: "System Reboot",
    categories: [
      { name: "Ways We Describe a Personality", difficulty: "yellow", items: ["PSYCHOPATHY", "EMPATHY", "ATTACHMENT", "ALEXITHYMIA"] },
      { name: "The Shape of a Model", difficulty: "green", items: ["TRANSFORMER", "EMBEDDING", "ENCODER", "ATTENTION"] },
      { name: "Wear, Drink, Drive Canadian", difficulty: "blue", items: ["LULULEMON", "TIM HORTONS", "CANADIAN TIRE", "ROOTS"] },
      { name: "Words for Wind and Water", difficulty: "purple", items: ["KEEL", "BALLAST", "WAKE", "BUOY"] }
    ]
  },
  {
    id: "p29",
    title: "Closing Bell",
    categories: [
      { name: "Names for a Feeling State", difficulty: "yellow", items: ["VALENCE", "AROUSAL", "RUMINATION", "COPING"] },
      { name: "End-of-Quarter Vocabulary", difficulty: "green", items: ["EARNINGS", "GUIDANCE", "BUYBACK", "DIVIDEND"] },
      { name: "Big Names, Big Aisles", difficulty: "blue", items: ["SOBEYS", "LOBLAWS", "METRO", "SHOPPERS DRUG MART"] },
      { name: "Score Talk", difficulty: "purple", items: ["BIRDIE", "EAGLE", "PAR", "HANDICAP"] }
    ]
  },
  {
    id: "p30",
    title: "Season Finale",
    categories: [
      { name: "What Ships in a Release Note", difficulty: "yellow", items: ["CHECKPOINT", "FINE-TUNE", "ARTIFACT", "ROUTINE"] },
      { name: "Words for Risk", difficulty: "green", items: ["HEDGE", "VOLATILITY", "MARGIN", "ARBITRAGE"] },
      { name: "From Coast to Coast (Airlines & Rail)", difficulty: "blue", items: ["AIR CANADA", "WESTJET", "VIA RAIL", "PORTER"] },
      { name: "Golf's Odd Vocabulary", difficulty: "purple", items: ["MULLIGAN", "BOGEY", "DIVOT", "HANDICAP"] }
    ]
  }
];

const DIFFICULTY_ORDER = ["yellow", "green", "blue", "purple"];
const DIFFICULTY_EMOJI = {
  yellow: "\u{1F7E8}",
  green: "\u{1F7E9}",
  blue: "\u{1F7E6}",
  purple: "\u{1F7EA}"
};
const DIFFICULTY_LABEL = {
  yellow: "Easy",
  green: "Medium",
  blue: "Hard",
  purple: "Tricky"
};

// Anchor date: the daily puzzle bank is aligned so 2026-07-06 (this build's
// date) maps to puzzle index 0, then increments by one UTC calendar day.
const ANCHOR_EPOCH_DAY = Math.floor(Date.UTC(2026, 6, 6) / 86400000);

function epochDayFromDateString(dateString) {
  const [year, month, day] = dateString.split("-").map(Number);
  return Math.floor(Date.UTC(year, month - 1, day) / 86400000);
}

function getPuzzleIndexForDate(dateString) {
  const dayOffset = epochDayFromDateString(dateString) - ANCHOR_EPOCH_DAY;
  const length = PUZZLES.length;
  return ((dayOffset % length) + length) % length;
}

function getPuzzleForDate(dateString) {
  return PUZZLES[getPuzzleIndexForDate(dateString)];
}
