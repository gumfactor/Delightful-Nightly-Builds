// Moderation model: Y = b0 + b1*Xc + b2*Zc + b3*(Xc*Zc), X and Z mean-centered
// before the interaction term is formed. Classic script, depends on rng.js
// and stats.js already being loaded.

function generateModerationSample(params) {
  const { trueB1, trueB2, trueB3, noiseSD, n, seed } = params;
  const rng = createRng(seed);
  const X = [], Z = [], Y = [];
  const rawX = [], rawZ = [];
  for (let i = 0; i < n; i++) {
    rawX.push(10 + 3 * nextGaussian(rng));
    rawZ.push(10 + 3 * nextGaussian(rng));
  }
  const xbar = mean(rawX), zbar = mean(rawZ);
  for (let i = 0; i < n; i++) {
    const xc = rawX[i] - xbar;
    const zc = rawZ[i] - zbar;
    const y = 20 + trueB1 * xc + trueB2 * zc + trueB3 * xc * zc + noiseSD * nextGaussian(rng);
    X.push(rawX[i]); Z.push(rawZ[i]); Y.push(y);
  }
  return { X, Z, Y, rng };
}

// Solves for the Johnson-Neyman region(s) of significance: the Z value(s)
// where the simple slope's t-statistic crosses +/- tCrit. This is the
// quadratic (b3^2 - tCrit^2*varB3)*z^2 + (2*b1*b3 - 2*tCrit^2*covB1B3)*z +
// (b1^2 - tCrit^2*varB1) = 0, derived by squaring both sides of
// |b1 + b3*z| = tCrit * sqrt(varB1 + z^2*varB3 + 2*z*covB1B3).
function solveJohnsonNeyman(b1, b3, varB1, varB3, covB1B3, tCrit) {
  const A = b3 * b3 - tCrit * tCrit * varB3;
  const B = 2 * b1 * b3 - 2 * tCrit * tCrit * covB1B3;
  const C = b1 * b1 - tCrit * tCrit * varB1;
  if (Math.abs(A) < 1e-12) {
    if (Math.abs(B) < 1e-12) return null;
    return [-C / B];
  }
  const disc = B * B - 4 * A * C;
  if (disc < 0) return null;
  const sq = Math.sqrt(disc);
  const z1 = (-B + sq) / (2 * A);
  const z2 = (-B - sq) / (2 * A);
  return [Math.min(z1, z2), Math.max(z1, z2)];
}

function analyzeModeration(sample, alpha) {
  alpha = alpha || 0.05;
  const { X, Z, Y } = sample;
  const n = X.length;
  const xbar = mean(X), zbar = mean(Z);
  const Xc = X.map(x => x - xbar), Zc = Z.map(z => z - zbar);
  const XZc = Xc.map((x, i) => x * Zc[i]);

  const r = ols(Xc.map((x, i) => [x, Zc[i], XZc[i]]), Y);
  const [b0, b1, b2, b3] = r.beta;
  const [se0, se1, se2, se3] = r.se;
  const dof = r.dof;
  const varB1 = r.cov[1][1], varB3 = r.cov[3][3], covB1B3 = r.cov[1][3];

  const sdZ = sampleSD(Z);
  const tCrit = studentTCritical(dof, alpha);

  const simpleSlopes = [-1, 0, 1].map(kSD => {
    const zVal = kSD * sdZ;
    const slope = b1 + b3 * zVal;
    const se = Math.sqrt(varB1 + zVal * zVal * varB3 + 2 * zVal * covB1B3);
    const t = slope / se;
    const p = studentTTwoTailedP(t, dof);
    return {
      label: kSD === 0 ? 'Mean' : (kSD < 0 ? '-1 SD' : '+1 SD'),
      zVal, slope, se, t, p, significant: p < alpha,
    };
  });

  const b3T = b3 / se3;
  const b3P = studentTTwoTailedP(b3T, dof);

  const jnRoots = solveJohnsonNeyman(b1, b3, varB1, varB3, covB1B3, tCrit);

  return {
    beta: [b0, b1, b2, b3], se: [se0, se1, se2, se3], cov: r.cov, dof,
    interactionT: b3T, interactionP: b3P, interactionSignificant: b3P < alpha,
    r2: r.r2, sdZ, tCrit, simpleSlopes, jnRoots, xbar, zbar,
  };
}
