/**
 * Euler–Maruyama SDE solver for Itô SDEs:
 *
 *   dY = drift(t, Y) dt + diffusion(t, Y) dW
 *
 * Supports multiple Monte Carlo paths with seeded PRNG.
 *
 * @param {Function} drift     - (t, y) => dy[]  (deterministic part)
 * @param {Function} diffusion - (t, y) => sigma[] (noise coefficient per component)
 * @param {[number, number]} tSpan - [t0, tEnd]
 * @param {number[]} y0 - initial conditions
 * @param {Object}   opts
 * @param {number}   [opts.dt=0.01]     - fixed step size
 * @param {number}   [opts.nPaths=10]   - number of Monte Carlo paths
 * @param {number}   [opts.seed=42]     - PRNG seed
 * @returns {{ t: number[], paths: number[][][], mean: number[][], std: number[][] }}
 *   paths[pathIdx][component][timeIdx]
 *   mean[component][timeIdx], std[component][timeIdx]
 */
export function solveEulerMaruyama(drift, diffusion, tSpan, y0, opts = {}) {
  const dt = opts.dt ?? 0.01;
  const nPaths = opts.nPaths ?? 10;
  const seed = opts.seed ?? 42;
  const n = y0.length;

  const nSteps = Math.ceil((tSpan[1] - tSpan[0]) / dt);
  const sqrtDt = Math.sqrt(dt);

  // Time grid
  const t = new Array(nSteps + 1);
  for (let i = 0; i <= nSteps; i++) {
    t[i] = tSpan[0] + i * dt;
  }
  t[nSteps] = tSpan[1]; // exact end

  // Seeded PRNG (xoshiro128**)
  const rng = createRNG(seed);

  // All paths
  const paths = [];

  for (let p = 0; p < nPaths; p++) {
    const path = Array.from({ length: n }, () => new Float64Array(nSteps + 1));
    for (let j = 0; j < n; j++) path[j][0] = y0[j];

    for (let i = 0; i < nSteps; i++) {
      const ti = t[i];
      const yi = new Array(n);
      for (let j = 0; j < n; j++) yi[j] = path[j][i];

      const f = drift(ti, yi);
      const g = diffusion(ti, yi);

      for (let j = 0; j < n; j++) {
        const dW = sqrtDt * rng.normal();
        path[j][i + 1] = yi[j] + f[j] * dt + g[j] * dW;
      }
    }
    paths.push(path);
  }

  // Compute mean and std across paths
  const mean = Array.from({ length: n }, () => new Float64Array(nSteps + 1));
  const std = Array.from({ length: n }, () => new Float64Array(nSteps + 1));

  for (let i = 0; i <= nSteps; i++) {
    for (let j = 0; j < n; j++) {
      let sum = 0, sum2 = 0;
      for (let p = 0; p < nPaths; p++) {
        const v = paths[p][j][i];
        sum += v;
        sum2 += v * v;
      }
      mean[j][i] = sum / nPaths;
      std[j][i] = Math.sqrt(Math.max(0, sum2 / nPaths - (sum / nPaths) ** 2));
    }
  }

  return {
    t: Array.from(t),
    paths: paths.map(p => p.map(c => Array.from(c))),
    mean: mean.map(c => Array.from(c)),
    std: std.map(c => Array.from(c)),
  };
}

/**
 * Seeded xoshiro128** PRNG with Box–Muller normal generation.
 */
function createRNG(seed) {
  // Initialize state from seed using splitmix32
  let s = seed | 0;
  function splitmix32() {
    s = (s + 0x9e3779b9) | 0;
    let z = s;
    z = Math.imul(z ^ (z >>> 16), 0x85ebca6b);
    z = Math.imul(z ^ (z >>> 13), 0xc2b2ae35);
    return (z ^ (z >>> 16)) >>> 0;
  }

  let state = new Uint32Array(4);
  for (let i = 0; i < 4; i++) state[i] = splitmix32();

  function xoshiro128ss() {
    const r = Math.imul(rotl(Math.imul(state[1], 5), 7), 9);
    const t = state[1] << 9;
    state[2] ^= state[0];
    state[3] ^= state[1];
    state[1] ^= state[2];
    state[0] ^= state[3];
    state[2] ^= t;
    state[3] = rotl(state[3], 11);
    return (r >>> 0) / 4294967296;
  }

  function rotl(x, k) {
    return ((x << k) | (x >>> (32 - k))) >>> 0;
  }

  // Box–Muller for standard normal
  let hasSpare = false;
  let spare = 0;

  function normal() {
    if (hasSpare) {
      hasSpare = false;
      return spare;
    }
    let u, v, s;
    do {
      u = 2 * xoshiro128ss() - 1;
      v = 2 * xoshiro128ss() - 1;
      s = u * u + v * v;
    } while (s >= 1 || s === 0);
    const mul = Math.sqrt(-2 * Math.log(s) / s);
    spare = v * mul;
    hasSpare = true;
    return u * mul;
  }

  return {
    uniform: xoshiro128ss,
    normal,
  };
}

export { createRNG };
export default solveEulerMaruyama;
