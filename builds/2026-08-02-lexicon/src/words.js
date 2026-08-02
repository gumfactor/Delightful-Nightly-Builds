// Lexicon word bank — 48 curated terms across 4 domains, 12 each.
// Each clue is a general-knowledge, accurate one-sentence definition.
const WORD_BANK = [
  // --- Neuroscience / Psychology ---
  { word: "AMYGDALA", category: "neuro", clue: "Brain structure central to fear and threat detection." },
  { word: "CORTISOL", category: "neuro", clue: "Hormone released by the adrenal cortex during the stress response." },
  { word: "EMPATHY", category: "neuro", clue: "The capacity to share or understand another person's emotional state." },
  { word: "HEURISTIC", category: "neuro", clue: "A mental shortcut the brain uses to simplify a decision." },
  { word: "INSULA", category: "neuro", clue: "Brain region linked to interoception and disgust processing." },
  { word: "STRIATUM", category: "neuro", clue: "Subcortical region central to reward and motor processing." },
  { word: "COGNITION", category: "neuro", clue: "The mental processes involved in acquiring and using knowledge." },
  { word: "VALENCE", category: "neuro", clue: "The positive or negative quality of an emotional state." },
  { word: "AROUSAL", category: "neuro", clue: "The physiological activation level of the nervous system." },
  { word: "AGENCY", category: "neuro", clue: "The subjective sense of control over one's own actions." },
  { word: "SYNAPSE", category: "neuro", clue: "The junction where one neuron signals to another." },
  { word: "MEMORY", category: "neuro", clue: "The system for encoding, storing, and retrieving information." },

  // --- Statistics / Research Methods ---
  { word: "VARIANCE", category: "stats", clue: "The average squared deviation of values from their mean." },
  { word: "OUTLIER", category: "stats", clue: "A data point far removed from the rest of the observations." },
  { word: "SAMPLE", category: "stats", clue: "A subset of a population selected for study." },
  { word: "KURTOSIS", category: "stats", clue: "A measure of how heavy-tailed a distribution is." },
  { word: "POSTERIOR", category: "stats", clue: "In Bayesian terms, the updated belief after observing data." },
  { word: "CONFOUND", category: "stats", clue: "A variable that obscures a study's true causal relationship." },
  { word: "RESIDUAL", category: "stats", clue: "The difference between an observed value and a model's prediction." },
  { word: "ESTIMATE", category: "stats", clue: "An approximate value calculated from available data." },
  { word: "BASELINE", category: "stats", clue: "A reference measurement taken before an intervention." },
  { word: "CRITERION", category: "stats", clue: "A threshold used to decide between signal and noise." },
  { word: "ROBUST", category: "stats", clue: "Resistant to violations of a statistical method's assumptions." },
  { word: "SKEWNESS", category: "stats", clue: "A measure of the asymmetry of a probability distribution." },

  // --- AI / Machine Learning ---
  { word: "GRADIENT", category: "ai", clue: "The vector of partial derivatives used to update model weights." },
  { word: "EMBEDDING", category: "ai", clue: "A vector representation that captures an item's semantic meaning." },
  { word: "INFERENCE", category: "ai", clue: "The process of generating output from an already-trained model." },
  { word: "TOKEN", category: "ai", clue: "A chunk of text a language model processes as one unit." },
  { word: "LATENCY", category: "ai", clue: "The delay between a request and a system's response." },
  { word: "PIPELINE", category: "ai", clue: "A sequence of automated data-processing steps." },
  { word: "OVERFIT", category: "ai", clue: "When a model memorizes training data instead of generalizing." },
  { word: "ENDPOINT", category: "ai", clue: "A URL an API exposes to receive requests." },
  { word: "LATENT", category: "ai", clue: "A hidden variable that is not directly observed." },
  { word: "SANDBOX", category: "ai", clue: "An isolated environment for running untrusted code safely." },
  { word: "WEIGHTS", category: "ai", clue: "The learned parameters that scale a neural network's inputs." },
  { word: "CACHE", category: "ai", clue: "Temporary storage that speeds up repeated data access." },

  // --- Investing / Finance ---
  { word: "MARGIN", category: "finance", clue: "Borrowed money used to increase an investor's buying power." },
  { word: "DIVIDEND", category: "finance", clue: "A portion of a company's profit paid out to shareholders." },
  { word: "VOLATILE", category: "finance", clue: "Prone to large, rapid price swings." },
  { word: "LIQUIDITY", category: "finance", clue: "The ease of converting an asset to cash without moving its price." },
  { word: "HEDGE", category: "finance", clue: "A position taken to offset potential losses elsewhere." },
  { word: "PREMIUM", category: "finance", clue: "The price paid to buy an options contract." },
  { word: "ARBITRAGE", category: "finance", clue: "Profiting from a price difference for the same asset across markets." },
  { word: "CATALYST", category: "finance", clue: "An event expected to move an asset's price." },
  { word: "LEVERAGE", category: "finance", clue: "Using borrowed capital to amplify potential returns." },
  { word: "SPREAD", category: "finance", clue: "The gap between an asset's bid price and its ask price." },
  { word: "EQUITY", category: "finance", clue: "An ownership stake in a company." },
  { word: "YIELD", category: "finance", clue: "The income return on an investment, expressed as a percentage." },
];

const CATEGORY_LABELS = {
  neuro: "Neuroscience / Psychology",
  stats: "Statistics / Methods",
  ai: "AI / Machine Learning",
  finance: "Investing / Finance",
};

// Expose as CommonJS exports under Node (tests), and as globals in the browser
// (classic <script> tags share one top-level scope, so later scripts see these
// as plain identifiers without any window.* qualification needed).
if (typeof module !== "undefined" && module.exports) {
  module.exports = { WORD_BANK, CATEGORY_LABELS };
}
