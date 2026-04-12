/**
 * Dormand–Prince RK4(5) adaptive-step ODE solver.
 *
 * Solves dy/dt = f(t, y) on [t0, tEnd] with adaptive step control.
 * Returns { t: Float64Array, y: Float64Array[] } where y[i] is the i-th component.
 *
 * Butcher tableau: standard DP45 (same as SciPy / MATLAB ode45).
 */

// Dormand–Prince coefficients
const A = [0, 1/5, 3/10, 4/5, 8/9, 1, 1];
const B = [
  [],
  [1/5],
  [3/40, 9/40],
  [44/45, -56/15, 32/9],
  [19372/6561, -25360/2187, 64448/6561, -212/729],
  [9017/3168, -355/33, 46732/5247, 49/176, -5103/18656],
  [35/384, 0, 500/1113, 125/192, -2187/6784, 11/84],
];
// 5th-order weights (solution)
const C5 = [35/384, 0, 500/1113, 125/192, -2187/6784, 11/84, 0];
// 4th-order weights (error estimate)
const C4 = [5179/57600, 0, 7571/16695, 393/640, -92097/339200, 187/2100, 1/40];
// Error coefficients: E[i] = C5[i] - C4[i]
const E = C5.map((c, i) => c - C4[i]);

/**
 * @param {Function} f - RHS function (t, y) => dy[] (array of length n)
 * @param {[number, number]} tSpan - [t0, tEnd]
 * @param {number[]} y0 - initial conditions (array of length n)
 * @param {Object} opts - options
 * @param {number} [opts.rtol=1e-8] - relative tolerance
 * @param {number} [opts.atol=1e-10] - absolute tolerance
 * @param {number} [opts.maxStep=0.5] - maximum step size
 * @param {number} [opts.initialStep=0.01] - initial step size
 * @param {number} [opts.maxSteps=200000] - maximum number of steps
 * @param {number[]} [opts.tEval] - if provided, interpolate solution at these times
 * @returns {{ t: number[], y: number[][], success: boolean, message: string }}
 */
export function solveODE(f, tSpan, y0, opts = {}) {
  const rtol = opts.rtol ?? 1e-8;
  const atol = opts.atol ?? 1e-10;
  const maxStep = opts.maxStep ?? 0.5;
  const maxSteps = opts.maxSteps ?? 200000;
  const n = y0.length;

  let h = opts.initialStep ?? Math.min(0.01, (tSpan[1] - tSpan[0]) / 100);
  let t = tSpan[0];
  let y = [...y0];

  const ts = [t];
  const ys = [y.slice()];

  const k = Array.from({ length: 7 }, () => new Array(n));
  const yTmp = new Array(n);
  const y5 = new Array(n);

  let steps = 0;
  const safety = 0.9;
  const minFactor = 0.2;
  const maxFactor = 5.0;

  while (t < tSpan[1] - 1e-14) {
    if (steps++ > maxSteps) {
      return { t: ts, y: transposeY(ys, n), success: false, message: 'Max steps exceeded' };
    }

    h = Math.min(h, tSpan[1] - t, maxStep);
    if (h < 1e-15) break;

    // Stage 1
    const f0 = f(t, y);
    for (let j = 0; j < n; j++) k[0][j] = f0[j];

    // Stages 2-7
    for (let s = 1; s < 7; s++) {
      for (let j = 0; j < n; j++) {
        let sum = 0;
        for (let m = 0; m < s; m++) sum += B[s][m] * k[m][j];
        yTmp[j] = y[j] + h * sum;
      }
      const fi = f(t + A[s] * h, yTmp);
      for (let j = 0; j < n; j++) k[s][j] = fi[j];
    }

    // 5th-order solution
    for (let j = 0; j < n; j++) {
      let sum = 0;
      for (let s = 0; s < 7; s++) sum += C5[s] * k[s][j];
      y5[j] = y[j] + h * sum;
    }

    // Error estimate
    let errNorm = 0;
    for (let j = 0; j < n; j++) {
      let errJ = 0;
      for (let s = 0; s < 7; s++) errJ += E[s] * k[s][j];
      errJ *= h;
      const scale = atol + rtol * Math.max(Math.abs(y[j]), Math.abs(y5[j]));
      errNorm += (errJ / scale) ** 2;
    }
    errNorm = Math.sqrt(errNorm / n);

    if (errNorm <= 1.0) {
      // Accept step
      t += h;
      y = y5.slice();
      ts.push(t);
      ys.push(y.slice());

      // Increase step size
      const factor = errNorm > 0
        ? Math.min(maxFactor, safety * errNorm ** (-0.2))
        : maxFactor;
      h *= factor;
    } else {
      // Reject step, decrease h
      const factor = Math.max(minFactor, safety * errNorm ** (-0.25));
      h *= factor;
    }
  }

  const result = { t: ts, y: transposeY(ys, n), success: true, message: 'OK' };

  // Interpolate to tEval if requested
  if (opts.tEval && opts.tEval.length > 0) {
    result.y = interpolateResult(result.t, result.y, opts.tEval, n);
    result.t = [...opts.tEval];
  }

  return result;
}

/** Transpose from array-of-rows to array-of-components */
function transposeY(ys, n) {
  const out = Array.from({ length: n }, () => []);
  for (const row of ys) {
    for (let j = 0; j < n; j++) out[j].push(row[j]);
  }
  return out;
}

/** Linear interpolation to tEval grid */
function interpolateResult(tRaw, yRaw, tEval, n) {
  const out = Array.from({ length: n }, () => new Array(tEval.length));
  let idx = 0;
  for (let i = 0; i < tEval.length; i++) {
    while (idx < tRaw.length - 2 && tRaw[idx + 1] < tEval[i]) idx++;
    const t0 = tRaw[idx], t1 = tRaw[idx + 1] ?? tRaw[idx];
    const frac = t1 > t0 ? (tEval[i] - t0) / (t1 - t0) : 0;
    for (let j = 0; j < n; j++) {
      out[j][i] = yRaw[j][idx] + frac * ((yRaw[j][idx + 1] ?? yRaw[j][idx]) - yRaw[j][idx]);
    }
  }
  return out;
}

export default solveODE;
