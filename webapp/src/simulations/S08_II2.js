/**
 * S08 – Fundamentale Preisdynamik  II.2  (§5.1)
 *
 * ṗ_k = (1/λ_k)(D_k − S_k) + η_k · p_k − φ_k / (I_k + ε)
 *
 * Declarative simulation config. The webapp reads this and builds
 * the UI (parameter sliders, function selectors, plots) automatically.
 */

const S08_II2 = {
  id: 'S08',
  eqId: 'II.2',
  section: '§5.1',
  chapter: 5,
  chapterTitle: 'Kap. 5: Preise & Flüsse',
  title: 'Fundamentale Preisdynamik',
  equationLatex: String.raw`\dot{p}_k = \frac{1}{\lambda_k}(D_k - S_k) \;+\; \eta_k\, p_k \;-\; \frac{\varphi_k}{\mathcal{I}_k + \varepsilon}`,
  description:
    'Preisänderung aus drei Mechanismen: Walrasianische Überschussnachfrage, ' +
    'endogene Inflationserwartung (selbstverstärkend), und Illiquiditätsprämie ' +
    '(Singularität bei I→0). Prop. 5.1 definiert 4 Regime (GG / Normal / Blase / Krise).',

  // ── State variables (endogenous) ──
  stateVars: [
    {
      name: 'p',
      label: 'Preis pₖ',
      unit: 'Währung/ME',
      initial: 10.0,
      min: 0.001,
      max: 1000,
      floor: 1e-6,
      description: 'Marktpreis des Gutes k',
    },
  ],

  // ── Exogenous variables (user defines function type) ──
  exogenous: [
    {
      name: 'D',
      label: 'Nachfrage Dₖ',
      unit: 'ME/a',
      coupledTo: 'V.1 (§6.1)',
      defaultType: 'sinusoidal',
      defaultParams: { offset: 100, amplitude: 15, frequency: 0.5, phase: 0 },
      description: 'Güternachfrage; in Vollmodell endogen via V.1',
    },
    {
      name: 'S',
      label: 'Angebot Sₖ',
      unit: 'ME/a',
      coupledTo: 'III.3 (§6.6)',
      defaultType: 'sinusoidal',
      defaultParams: { offset: 100, amplitude: 5, frequency: 0.5, phase: 0.3 },
      description: 'Güterangebot; in Vollmodell endogen via III.3',
    },
    {
      name: 'eta',
      label: 'Inflationserwartung ηₖ',
      unit: '1/a',
      coupledTo: 'III.4 (§6.7)',
      defaultType: 'constant',
      defaultParams: { value: 0.0 },
      description: 'Erwarteter Inflationstrend; in Vollmodell via III.4 endogen',
    },
    {
      name: 'I',
      label: 'Information Iₖ',
      unit: 'dimensionslos',
      coupledTo: 'II.3 (§5.6)',
      defaultType: 'constant',
      defaultParams: { value: 5.0 },
      description: 'Markt-Informationsniveau; in Vollmodell via II.3 endogen',
    },
  ],

  // ── Parameters (scalar, adjustable via sliders) ──
  parameters: [
    { name: 'lambda', label: 'Markttiefe λₖ', unit: 'ME·a/Wäh', default: 50, min: 1, max: 200, step: 1, description: 'Inversmaß der Preissensitivität' },
    { name: 'phi', label: 'Illiquidität φₖ', unit: 'Wäh/a', default: 0.02, min: 0, max: 10, step: 0.01, description: 'Stärke der Illiquiditätsprämie' },
    { name: 'eps', label: 'Regularisierung ε', unit: 'dimlos', default: 0.01, min: 0.001, max: 0.1, step: 0.001, description: 'Verhindert Division durch 0 bei I→0' },
  ],

  // ── SDE mode: volatility for each state variable ──
  sdeConfig: {
    label: 'Stochastische Erweiterung (VIII.1)',
    description: 'dp = [II.2 Drift]dt + σₚ·p·dW — geometrisch-Brownsche Preisvolatilität',
    sigmaParams: [
      { name: 'sigma_p', label: 'σₚ (Preisvolatilität)', default: 0.0, min: 0, max: 1, step: 0.01 },
    ],
  },

  // ── ODE right-hand side ──
  rhs: (t, y, exog, params) => {
    const p = Math.max(y[0], 1e-6);
    const D = exog.D(t);
    const S = exog.S(t);
    const eta = exog.eta(t);
    const I = exog.I(t);

    const walras = (D - S) / params.lambda;
    const inflation = eta * p;
    const illiquidity = -params.phi / (Math.max(I, 0) + params.eps);

    return [walras + inflation + illiquidity];
  },

  // ── SDE diffusion coefficient ──
  diffusion: (t, y, _exog, _params, sigmaParams) => {
    const p = Math.max(y[0], 1e-6);
    return [(sigmaParams.sigma_p || 0) * p];
  },

  // ── Named decomposition of the RHS into individual terms (for plotting) ──
  terms: [
    {
      name: 'walras',
      label: 'Walras (D−S)/λ',
      color: '#2563eb',
      compute: (t, y, exog, params) => (exog.D(t) - exog.S(t)) / params.lambda,
    },
    {
      name: 'inflation',
      label: 'Inflation η·p',
      color: '#f59e0b',
      compute: (t, y, exog, params) => exog.eta(t) * Math.max(y[0], 1e-6),
    },
    {
      name: 'illiquidity',
      label: '−φ/(I+ε)',
      color: '#ef4444',
      compute: (t, y, exog, params) => -params.phi / (Math.max(exog.I(t), 0) + params.eps),
    },
  ],

  // ── Presets (reproduce Python regimes) ──
  presets: [
    {
      name: 'R1 Normaler Handel',
      description: 'Walras dominiert, I hoch, η=0 — typischer effizienter Markt',
      stateOverrides: { p: 10 },
      paramOverrides: { lambda: 50, phi: 0.02, eps: 0.01 },
      exogOverrides: {
        D: { type: 'sinusoidal', params: { offset: 100, amplitude: 15, frequency: 0.5, phase: 0 } },
        S: { type: 'sinusoidal', params: { offset: 100, amplitude: 5, frequency: 0.5, phase: 0.3 } },
        eta: { type: 'constant', params: { value: 0 } },
        I: { type: 'constant', params: { value: 5 } },
      },
    },
    {
      name: 'R2 Blase',
      description: 'η=5%/a → exponentielles Wachstum, D>S (Krypto/Immobilien-Blase)',
      stateOverrides: { p: 10 },
      paramOverrides: { lambda: 30, phi: 0.1, eps: 0.01 },
      exogOverrides: {
        D: { type: 'sinusoidal', params: { offset: 120, amplitude: 10, frequency: 0.3, phase: 0 } },
        S: { type: 'sinusoidal', params: { offset: 100, amplitude: 5, frequency: 0.3, phase: 0 } },
        eta: { type: 'constant', params: { value: 0.05 } },
        I: { type: 'constant', params: { value: 2 } },
      },
    },
    {
      name: 'R3 Krise (Illiquidität)',
      description: 'I→0 ab t=25 — Lehman/Evergrande-Szenario, Preiskollaps',
      stateOverrides: { p: 10 },
      paramOverrides: { lambda: 50, phi: 1.5, eps: 0.005 },
      exogOverrides: {
        D: { type: 'sinusoidal', params: { offset: 100, amplitude: 5, frequency: 0.5, phase: 0 } },
        S: { type: 'sinusoidal', params: { offset: 100, amplitude: 5, frequency: 0.5, phase: 0 } },
        eta: { type: 'constant', params: { value: 0.01 } },
        I: { type: 'exponentialDecay', params: { initial: 5, rate: 0.2, tStart: 25 } },
      },
    },
    {
      name: 'R4 Stagflation',
      description: 'η>0 trotz D<S — Inflation bei Angebotsüberschuss (1970er-Ölschock)',
      stateOverrides: { p: 10 },
      paramOverrides: { lambda: 40, phi: 0.01, eps: 0.01 },
      exogOverrides: {
        D: { type: 'sinusoidal', params: { offset: 90, amplitude: 5, frequency: 0.4, phase: 0 } },
        S: { type: 'sinusoidal', params: { offset: 100, amplitude: 3, frequency: 0.4, phase: 0 } },
        eta: { type: 'constant', params: { value: 0.04 } },
        I: { type: 'constant', params: { value: 1 } },
      },
    },
    {
      name: 'R5 Gleichgewicht (π*=2%)',
      description: 'D≈S, η=π*=2%, I hoch — Fed-Inflationsziel',
      stateOverrides: { p: 10 },
      paramOverrides: { lambda: 80, phi: 0.05, eps: 0.01 },
      exogOverrides: {
        D: { type: 'sinusoidal', params: { offset: 100, amplitude: 2, frequency: 0.5, phase: 0 } },
        S: { type: 'sinusoidal', params: { offset: 100, amplitude: 2, frequency: 0.5, phase: 0 } },
        eta: { type: 'constant', params: { value: 0.02 } },
        I: { type: 'constant', params: { value: 10 } },
      },
    },
    {
      name: 'Stochastisch: OU-Nachfrage + GBM-Info',
      description: 'D als Ornstein–Uhlenbeck, I als geometrische Brownsche Bew.',
      stateOverrides: { p: 10 },
      paramOverrides: { lambda: 40, phi: 0.5, eps: 0.01 },
      sdeOverrides: { sigma_p: 0.05 },
      exogOverrides: {
        D: { type: 'ornsteinUhlenbeck', params: { theta: 0.3, mu: 100, sigma: 8, x0: 100, seed: 42 } },
        S: { type: 'constant', params: { value: 100 } },
        eta: { type: 'constant', params: { value: 0.01 } },
        I: { type: 'geometricBrownian', params: { mu: -0.01, sigma: 0.15, x0: 3, seed: 7 } },
      },
    },
  ],

  // ── Solver defaults ──
  solverDefaults: {
    tEnd: 60,
    rtol: 1e-8,
    atol: 1e-10,
    maxStep: 0.1,
    nPoints: 1000,
    sdeDt: 0.01,
    nPaths: 20,
  },
};

export default S08_II2;
