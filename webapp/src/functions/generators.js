/**
 * Exogenous function generators.
 *
 * Each generator returns a function  t => value.
 * Stochastic generators pre-sample a path at fine resolution (dt=0.001),
 * then linearly interpolate during evaluation.
 *
 * USAGE:
 *   const fn = createFunction('sinusoidal', { offset: 100, amplitude: 15, frequency: 0.5 });
 *   fn(3.7); // => value at t=3.7
 */

import { createRNG } from '../solvers/eulerMaruyama.js';

// ─── Registry of all function types ───────────────────────────────
export const FUNCTION_TYPES = {
  constant: {
    label: 'Konstant',
    params: [
      { name: 'value', label: 'Wert', default: 1.0, min: -1e6, max: 1e6, step: 0.1 },
    ],
  },
  linear: {
    label: 'Linear',
    params: [
      { name: 'intercept', label: 'Startwert', default: 1.0, min: -1e6, max: 1e6, step: 0.1 },
      { name: 'slope', label: 'Steigung', default: 0.1, min: -100, max: 100, step: 0.01 },
    ],
  },
  sinusoidal: {
    label: 'Sinusförmig',
    params: [
      { name: 'offset', label: 'Offset', default: 100, min: -1e6, max: 1e6, step: 1 },
      { name: 'amplitude', label: 'Amplitude', default: 15, min: 0, max: 1e6, step: 0.5 },
      { name: 'frequency', label: 'Frequenz ω', default: 0.5, min: 0, max: 100, step: 0.1 },
      { name: 'phase', label: 'Phase φ', default: 0, min: -6.28, max: 6.28, step: 0.1 },
    ],
  },
  step: {
    label: 'Sprungfunktion',
    params: [
      { name: 'before', label: 'Vor Sprung', default: 1.0, min: -1e6, max: 1e6, step: 0.1 },
      { name: 'after', label: 'Nach Sprung', default: 2.0, min: -1e6, max: 1e6, step: 0.1 },
      { name: 'tSwitch', label: 't_Sprung', default: 20, min: 0, max: 1000, step: 1 },
    ],
  },
  ramp: {
    label: 'Rampe',
    params: [
      { name: 'vStart', label: 'Startwert', default: 1.0, min: -1e6, max: 1e6, step: 0.1 },
      { name: 'vEnd', label: 'Endwert', default: 5.0, min: -1e6, max: 1e6, step: 0.1 },
      { name: 'tStart', label: 't_Start', default: 10, min: 0, max: 1000, step: 1 },
      { name: 'tEnd', label: 't_Ende', default: 40, min: 0, max: 1000, step: 1 },
    ],
  },
  exponentialDecay: {
    label: 'Exponentieller Zerfall',
    params: [
      { name: 'initial', label: 'Anfangswert', default: 5.0, min: 0, max: 1e6, step: 0.1 },
      { name: 'rate', label: 'Zerfallsrate γ', default: 0.1, min: 0, max: 10, step: 0.01 },
      { name: 'tStart', label: 't_Start', default: 0, min: 0, max: 1000, step: 1 },
    ],
  },
  logistic: {
    label: 'Logistisch (S-Kurve)',
    params: [
      { name: 'L', label: 'Sättigungswert', default: 10, min: 0, max: 1e6, step: 0.5 },
      { name: 'k', label: 'Wachstumsrate', default: 0.3, min: 0.01, max: 10, step: 0.05 },
      { name: 'tMid', label: 'Wendepunkt t₀', default: 30, min: 0, max: 1000, step: 1 },
      { name: 'baseline', label: 'Baseline', default: 0, min: -1e6, max: 1e6, step: 0.1 },
    ],
  },
  brownianMotion: {
    label: 'Brownsche Bewegung',
    stochastic: true,
    params: [
      { name: 'mu', label: 'Drift μ', default: 0, min: -10, max: 10, step: 0.01 },
      { name: 'sigma', label: 'Volatilität σ', default: 1.0, min: 0, max: 50, step: 0.1 },
      { name: 'x0', label: 'Startwert', default: 5.0, min: -1e6, max: 1e6, step: 0.1 },
      { name: 'seed', label: 'Seed', default: 42, min: 1, max: 99999, step: 1 },
    ],
  },
  ornsteinUhlenbeck: {
    label: 'Ornstein–Uhlenbeck',
    stochastic: true,
    params: [
      { name: 'theta', label: 'Mean-Reversion θ', default: 0.5, min: 0, max: 10, step: 0.05 },
      { name: 'mu', label: 'Langzeit-Mittel μ', default: 5.0, min: -1e6, max: 1e6, step: 0.1 },
      { name: 'sigma', label: 'Volatilität σ', default: 0.5, min: 0, max: 50, step: 0.1 },
      { name: 'x0', label: 'Startwert', default: 5.0, min: -1e6, max: 1e6, step: 0.1 },
      { name: 'seed', label: 'Seed', default: 42, min: 1, max: 99999, step: 1 },
    ],
  },
  geometricBrownian: {
    label: 'Geometrische Brownsche Bew.',
    stochastic: true,
    params: [
      { name: 'mu', label: 'Drift μ', default: 0.02, min: -1, max: 1, step: 0.01 },
      { name: 'sigma', label: 'Volatilität σ', default: 0.1, min: 0, max: 5, step: 0.01 },
      { name: 'x0', label: 'Startwert', default: 100, min: 0.01, max: 1e6, step: 1 },
      { name: 'seed', label: 'Seed', default: 42, min: 1, max: 99999, step: 1 },
    ],
  },
  poissonJumps: {
    label: 'Poisson-Sprünge',
    stochastic: true,
    params: [
      { name: 'baseline', label: 'Baseline', default: 5.0, min: -1e6, max: 1e6, step: 0.1 },
      { name: 'lambda', label: 'Intensität λ', default: 0.5, min: 0, max: 100, step: 0.1 },
      { name: 'jumpMean', label: 'Sprunghöhe μ_J', default: -1.0, min: -100, max: 100, step: 0.1 },
      { name: 'jumpStd', label: 'Sprung-σ_J', default: 0.5, min: 0, max: 50, step: 0.1 },
      { name: 'seed', label: 'Seed', default: 42, min: 1, max: 99999, step: 1 },
    ],
  },
};

// ─── Factory ──────────────────────────────────────────────────────

/**
 * Create a function t => value from type name and parameters.
 * @param {string} type - key from FUNCTION_TYPES
 * @param {Object} params - parameter values
 * @param {number} tMax - maximum time (for stochastic pre-sampling)
 * @returns {Function} t => number
 */
export function createFunction(type, params, tMax = 100) {
  switch (type) {
    case 'constant':
      return () => params.value;

    case 'linear':
      return (t) => params.intercept + params.slope * t;

    case 'sinusoidal':
      return (t) => params.offset + params.amplitude * Math.sin(params.frequency * t + (params.phase || 0));

    case 'step':
      return (t) => t < params.tSwitch ? params.before : params.after;

    case 'ramp': {
      const { vStart, vEnd, tStart, tEnd } = params;
      return (t) => {
        if (t <= tStart) return vStart;
        if (t >= tEnd) return vEnd;
        return vStart + (vEnd - vStart) * (t - tStart) / (tEnd - tStart);
      };
    }

    case 'exponentialDecay':
      return (t) => params.initial * Math.exp(-params.rate * Math.max(t - (params.tStart || 0), 0));

    case 'logistic':
      return (t) => params.baseline + params.L / (1 + Math.exp(-params.k * (t - params.tMid)));

    case 'brownianMotion':
      return preSampleBrownian(params, tMax);

    case 'ornsteinUhlenbeck':
      return preSampleOU(params, tMax);

    case 'geometricBrownian':
      return preSampleGBM(params, tMax);

    case 'poissonJumps':
      return preSamplePoisson(params, tMax);

    default:
      return () => 0;
  }
}

// ─── Stochastic pre-samplers ─────────────────────────────────────

const STOCH_DT = 0.005; // fine resolution for pre-sampling

function preSampleBrownian(p, tMax) {
  const N = Math.ceil(tMax / STOCH_DT);
  const path = new Float64Array(N + 1);
  const rng = createRNG(p.seed || 42);
  path[0] = p.x0 ?? 0;
  const sqrtDt = Math.sqrt(STOCH_DT);
  for (let i = 1; i <= N; i++) {
    path[i] = path[i - 1] + (p.mu || 0) * STOCH_DT + (p.sigma || 1) * sqrtDt * rng.normal();
  }
  return makeLookup(path, STOCH_DT, N);
}

function preSampleOU(p, tMax) {
  const N = Math.ceil(tMax / STOCH_DT);
  const path = new Float64Array(N + 1);
  const rng = createRNG(p.seed || 42);
  path[0] = p.x0 ?? p.mu;
  const sqrtDt = Math.sqrt(STOCH_DT);
  for (let i = 1; i <= N; i++) {
    path[i] = path[i - 1]
      + p.theta * (p.mu - path[i - 1]) * STOCH_DT
      + p.sigma * sqrtDt * rng.normal();
  }
  return makeLookup(path, STOCH_DT, N);
}

function preSampleGBM(p, tMax) {
  const N = Math.ceil(tMax / STOCH_DT);
  const path = new Float64Array(N + 1);
  const rng = createRNG(p.seed || 42);
  path[0] = p.x0 ?? 1;
  const sqrtDt = Math.sqrt(STOCH_DT);
  for (let i = 1; i <= N; i++) {
    const dW = sqrtDt * rng.normal();
    // Exact: S_{i+1} = S_i * exp((mu - 0.5*sigma^2)*dt + sigma*dW)
    path[i] = path[i - 1] * Math.exp((p.mu - 0.5 * p.sigma ** 2) * STOCH_DT + p.sigma * dW);
  }
  return makeLookup(path, STOCH_DT, N);
}

function preSamplePoisson(p, tMax) {
  const N = Math.ceil(tMax / STOCH_DT);
  const path = new Float64Array(N + 1);
  const rng = createRNG(p.seed || 42);
  path[0] = p.baseline ?? 0;
  for (let i = 1; i <= N; i++) {
    let jump = 0;
    if (rng.uniform() < (p.lambda || 0.5) * STOCH_DT) {
      jump = (p.jumpMean || 0) + (p.jumpStd || 1) * rng.normal();
    }
    path[i] = path[i - 1] + jump;
  }
  return makeLookup(path, STOCH_DT, N);
}

/** Create a lookup function with linear interpolation from presampled path */
function makeLookup(path, dt, N) {
  return (t) => {
    const idx = t / dt;
    const i0 = Math.max(0, Math.min(Math.floor(idx), N - 1));
    const i1 = Math.min(i0 + 1, N);
    const frac = idx - i0;
    return path[i0] + frac * (path[i1] - path[i0]);
  };
}

export default createFunction;
