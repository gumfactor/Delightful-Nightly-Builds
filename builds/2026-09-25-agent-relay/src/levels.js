// Agent Relay — hand-authored levels. Pure data, dual-exported like engine.js.

var TUTORIAL_LEVEL = {
  id: "tutorial",
  title: "Tutorial — First Relay",
  flavor: "Clone the repo, then split the next two tasks across your two lanes.",
  numLanes: 2,
  tasks: [
    { id: "A", name: "Clone Repository", duration: 3, deps: [] },
    { id: "B", name: "Install Dependencies", duration: 4, deps: ["A"] },
    { id: "C", name: "Read Existing Code", duration: 3, deps: ["A"] }
  ]
};

var CAMPAIGN_LEVELS = [
  {
    id: "L1",
    title: "Warm Start",
    flavor: "Small session, two lanes — get a feel for the ready queue.",
    numLanes: 2,
    tasks: [
      { id: "A", name: "Clone Repository", duration: 2, deps: [] },
      { id: "B", name: "Install Dependencies", duration: 3, deps: ["A"] },
      { id: "C", name: "Draft Implementation Plan", duration: 4, deps: ["A"] },
      { id: "D", name: "Write Unit Tests", duration: 3, deps: ["C"] }
    ]
  },
  {
    id: "L2",
    title: "Plan & Build",
    flavor: "Two lanes, one task that needs two other tasks finished first.",
    numLanes: 2,
    tasks: [
      { id: "A", name: "Clone Repository", duration: 2, deps: [] },
      { id: "B", name: "Install Dependencies", duration: 3, deps: ["A"] },
      { id: "C", name: "Draft Implementation Plan", duration: 4, deps: ["A"] },
      { id: "D", name: "Write Feature Code", duration: 6, deps: ["B", "C"] },
      { id: "E", name: "Write Unit Tests", duration: 5, deps: ["C"] }
    ]
  },
  {
    id: "L3",
    title: "Test & Fix",
    flavor: "A bug slipped through — chase it down while other work continues.",
    numLanes: 2,
    tasks: [
      { id: "A", name: "Write Feature Code", duration: 5, deps: [] },
      { id: "B", name: "Write Unit Tests", duration: 4, deps: ["A"] },
      { id: "C", name: "Run Test Suite", duration: 3, deps: ["B"] },
      { id: "D", name: "Fix Failing Tests", duration: 4, deps: ["C"] },
      { id: "E", name: "Fix Lint Errors", duration: 2, deps: ["A"] },
      { id: "F", name: "Verify Deployment", duration: 3, deps: ["D", "E"] }
    ]
  },
  {
    id: "L4",
    title: "Review Cycle",
    flavor: "Three lanes now — one pull request, four things gating it.",
    numLanes: 3,
    tasks: [
      { id: "A", name: "Draft Implementation Plan", duration: 3, deps: [] },
      { id: "B", name: "Write Feature Code", duration: 6, deps: ["A"] },
      { id: "C", name: "Write Unit Tests", duration: 4, deps: ["A"] },
      { id: "D", name: "Self Code Review", duration: 3, deps: ["B"] },
      { id: "E", name: "Security Review", duration: 4, deps: ["B"] },
      { id: "F", name: "Update Documentation", duration: 3, deps: ["A"] },
      { id: "G", name: "Open Pull Request", duration: 2, deps: ["D", "E", "C", "F"] }
    ]
  },
  {
    id: "L5",
    title: "Ship It",
    flavor: "Eight tasks, three lanes — the reviewer wants changes too.",
    numLanes: 3,
    tasks: [
      { id: "A", name: "Write Feature Code", duration: 5, deps: [] },
      { id: "B", name: "Write Unit Tests", duration: 4, deps: ["A"] },
      { id: "C", name: "Security Review", duration: 3, deps: ["A"] },
      { id: "D", name: "Update Documentation", duration: 2, deps: ["A"] },
      { id: "E", name: "Run Test Suite", duration: 3, deps: ["B"] },
      { id: "F", name: "Fix Failing Tests", duration: 3, deps: ["E"] },
      { id: "G", name: "Address Review Comments", duration: 4, deps: ["C"] },
      { id: "H", name: "Open Pull Request", duration: 2, deps: ["F", "G", "D"] }
    ]
  },
  {
    id: "L6",
    title: "Full Pipeline",
    flavor: "The whole session, start to finish. Nine tasks, three lanes.",
    numLanes: 3,
    tasks: [
      { id: "A", name: "Clone Repository", duration: 2, deps: [] },
      { id: "B", name: "Install Dependencies", duration: 3, deps: ["A"] },
      { id: "C", name: "Draft Implementation Plan", duration: 3, deps: ["A"] },
      { id: "D", name: "Write Feature Code", duration: 6, deps: ["B", "C"] },
      { id: "E", name: "Write Unit Tests", duration: 4, deps: ["C"] },
      { id: "F", name: "Run Test Suite", duration: 3, deps: ["D", "E"] },
      { id: "G", name: "Fix Failing Tests", duration: 3, deps: ["F"] },
      { id: "H", name: "Update Documentation", duration: 2, deps: ["D"] },
      { id: "I", name: "Open Pull Request", duration: 2, deps: ["G", "H"] }
    ]
  }
];

var Levels = {
  TUTORIAL_LEVEL: TUTORIAL_LEVEL,
  CAMPAIGN_LEVELS: CAMPAIGN_LEVELS
};

if (typeof module !== "undefined" && module.exports) {
  module.exports = Levels;
} else {
  window.Levels = Levels;
}
