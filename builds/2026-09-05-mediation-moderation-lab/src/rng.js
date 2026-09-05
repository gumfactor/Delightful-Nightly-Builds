// Seeded pseudo-random number generation. Classic script — attaches to window.
// mulberry32: small, fast, well-distributed PRNG seeded by a 32-bit integer.
// Using a seeded PRNG (rather than Math.random()) makes every "random" sample
// and every bootstrap resample exactly reproducible given the same seed.

function createRng(seed) {
  let state = seed >>> 0;
  return function next() {
    state |= 0;
    state = (state + 0x6D2B79F5) | 0;
    let t = Math.imul(state ^ (state >>> 15), 1 | state);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Box-Muller transform: converts two uniform(0,1) draws into one standard-normal draw.
function nextGaussian(rng) {
  let u = 0, v = 0;
  while (u === 0) u = rng();
  while (v === 0) v = rng();
  return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
}

// Deterministic string -> 32-bit integer hash, used to turn a user-typed seed
// (e.g. "lecture-3") into a numeric seed for createRng.
function hashSeed(str) {
  str = String(str);
  let h = 2166136261 >>> 0;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}
