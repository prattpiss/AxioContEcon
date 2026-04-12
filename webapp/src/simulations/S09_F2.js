/**
 * S09 – Effektives Potential  F.2  (§5.2)
 *
 * μ_k^eff = p_k + α_H · p̄_k^H + ψ_k / (I_k + ε)
 *
 * Algebraische Gleichung, gekoppelt mit II.2 (p_k als ODE).
 * Drei Schichten: Objektiver Preis + Herding-Verzerrung + Illiquiditätszuschlag
 *
 * Prop 5.2: R1 = α_H|p̄_H|/p (Herding) , R2 = ψ/(p(I+ε)) (Illiquidität)
 * → 3 Regime: Effizient / Blase / Krise
 */

const S09_F2 = {
  id: 'S09',
  eqId: 'F.2',
  section: '§5.2',
  chapter: 5,
  chapterTitle: 'Kap. 5: Preise & Flüsse',
  title: 'Effektives Potential',
  equationLatex: String.raw`\mu_k^{\rm eff} = p_k + \alpha_H\,\bar{p}_k^{H} + \frac{\psi_k}{\mathcal{I}_k + \varepsilon}`,
  description:
    'Das effektive Potential μ_eff setzt sich aus dem Marktpreis p_k, einer Herding-Verzerrung ' +
    'α_H·p̄_H (Netzwerk-Peer-Signal) und einem Illiquiditätszuschlag ψ/(I+ε) zusammen. ' +
    'Prop 5.2: Drei Regime — Effizient (R1≪1,R2≪1), Blase (R1≫1), Krise (R2≫1). ' +
    'p_k wird intern über II.2 als ODE simuliert.',

  // ── State variables ──
  // We solve p_k via II.2 and compute μ_eff algebraically.
  // The webapp stores [p_k] and derives μ_eff as a computed output.
  stateVars: [
    {
      name: 'p',
      label: 'Preis pₖ',
      unit: 'Währung/ME',
      initial: 10.0,
      min: 0.001,
      max: 1000,
      floor: 1e-6,
      description: 'Marktpreis (via II.2 ODE)',
    },
  ],

  // ── Derived outputs (computed algebraically at each t) ──
  derivedOutputs: [
    {
      name: 'mu_eff',
      label: 'μ_eff (Eff. Potential)',
      unit: 'Währung/ME',
      color: '#8b5cf6',
      compute: (t, y, exog, params) => {
        const p = Math.max(y[0], 1e-6);
        const aH = exog.alpha_H(t);
        const pH = exog.p_bar_H(t);
        const I = exog.I(t);
        return p + aH * pH + params.psi / (Math.max(I, 0) + params.eps);
      },
    },
    {
      name: 'R1',
      label: 'R₁ (Herding-Ind.)',
      unit: 'dimlos',
      color: '#f59e0b',
      compute: (t, y, exog, params) => {
        const p = Math.max(y[0], 1e-6);
        return exog.alpha_H(t) * Math.abs(exog.p_bar_H(t)) / p;
      },
    },
    {
      name: 'R2',
      label: 'R₂ (Illiquid.-Ind.)',
      unit: 'dimlos',
      color: '#ef4444',
      compute: (t, y, exog, params) => {
        const p = Math.max(y[0], 1e-6);
        const I = exog.I(t);
        return params.psi / (p * (Math.max(I, 0) + params.eps));
      },
    },
  ],

  // ── Exogenous ──
  exogenous: [
    {
      name: 'D',
      label: 'Nachfrage Dₖ',
      unit: 'ME/a',
      coupledTo: 'V.1 (§6.1)',
      defaultType: 'ornsteinUhlenbeck',
      defaultParams: { theta: 0.3, mu: 100, sigma: 5, x0: 100, seed: 42 },
      description: 'Güternachfrage (OU-Prozess)',
    },
    {
      name: 'S',
      label: 'Angebot Sₖ',
      unit: 'ME/a',
      coupledTo: 'III.3 (§6.6)',
      defaultType: 'sinusoidal',
      defaultParams: { offset: 100, amplitude: 5, frequency: 0.5, phase: 0 },
      description: 'Güterangebot (Sinusförmig)',
    },
    {
      name: 'eta',
      label: 'Inflationserwartung ηₖ',
      unit: '1/a',
      coupledTo: 'III.4 (§6.7)',
      defaultType: 'constant',
      defaultParams: { value: 0.01 },
      description: 'Erwarteter Inflationstrend',
    },
    {
      name: 'I',
      label: 'Information Iₖ',
      unit: 'dimensionslos',
      coupledTo: 'II.3 (§5.6)',
      defaultType: 'constant',
      defaultParams: { value: 5.0 },
      description: 'Markt-Informationsniveau; ψ/(I+ε) → Illiquiditätszuschlag',
    },
    {
      name: 'alpha_H',
      label: 'Herding-Sensitivität αH',
      unit: 'dimensionslos',
      coupledTo: 'VI.1 (§6.9)',
      defaultType: 'constant',
      defaultParams: { value: 0.1 },
      description: 'Stärke der Herding-Verzerrung (0=Arrow-Debreu, ∞=Herdenlauf)',
    },
    {
      name: 'p_bar_H',
      label: 'Herding-Signal p̄H',
      unit: 'dimensionslos',
      coupledTo: 'V.7 Netzwerk',
      defaultType: 'ornsteinUhlenbeck',
      defaultParams: { theta: 1.0, mu: 0, sigma: 0.5, x0: 0, seed: 77 },
      description: 'Netzwerk-gewichtetes Peer-Preissignal Σ A_ij·θ_jk',
    },
  ],

  // ── Parameters ──
  parameters: [
    { name: 'lambda', label: 'Markttiefe λₖ', unit: 'ME·a/Wäh', default: 50, min: 1, max: 200, step: 1, description: 'Inversmaß der Preissensitivität (II.2)' },
    { name: 'phi', label: 'Illiquidität φₖ (II.2)', unit: 'Wäh/a', default: 0.02, min: 0, max: 10, step: 0.01, description: 'Stärke der II.2-Illiquiditätsprämie' },
    { name: 'psi', label: 'Illiquidität ψₖ (F.2)', unit: 'Wäh/ME', default: 0.1, min: 0, max: 10, step: 0.01, description: 'Stärke der F.2-Illiquiditätsprämie' },
    { name: 'eps', label: 'Regularisierung ε', unit: 'dimlos', default: 0.01, min: 0.001, max: 0.1, step: 0.001, description: 'Verhindert Division durch 0 bei I→0' },
  ],

  // ── SDE mode ──
  sdeConfig: {
    label: 'Stochastische Erweiterung (VIII.1)',
    description: 'dp = [II.2 Drift]dt + σₚ·p·dW — geometrisch-Brownsche Preisvolatilität',
    sigmaParams: [
      { name: 'sigma_p', label: 'σₚ (Preisvolatilität)', default: 0.0, min: 0, max: 1, step: 0.01 },
    ],
  },

  // ── ODE right-hand side (p_k via II.2) ──
  rhs: (t, y, exog, params) => {
    const p = Math.max(y[0], 1e-6);
    const D = exog.D(t);
    const S_val = exog.S(t);
    const eta = exog.eta(t);
    const I = exog.I(t);

    const walras = (D - S_val) / params.lambda;
    const inflation = eta * p;
    const illiquidity = -params.phi / (Math.max(I, 0) + params.eps);

    return [walras + inflation + illiquidity];
  },

  // ── SDE diffusion ──
  diffusion: (t, y, _exog, _params, sigmaParams) => {
    const p = Math.max(y[0], 1e-6);
    return [(sigmaParams.sigma_p || 0) * p];
  },

  // ── RHS term decomposition (for plot panel) ──
  terms: [
    {
      name: 'walras',
      label: '(D−S)/λ (Walras)',
      color: '#2563eb',
      compute: (t, y, exog, params) => (exog.D(t) - exog.S(t)) / params.lambda,
    },
    {
      name: 'inflation',
      label: 'η·p (Inflation)',
      color: '#f59e0b',
      compute: (t, y, exog, params) => exog.eta(t) * Math.max(y[0], 1e-6),
    },
    {
      name: 'illiquidity_II2',
      label: '−φ/(I+ε) (II.2)',
      color: '#ef4444',
      compute: (t, y, exog, params) => -params.phi / (Math.max(exog.I(t), 0) + params.eps),
    },
    {
      name: 'herding',
      label: 'αH·p̄H (Herding)',
      color: '#8b5cf6',
      compute: (t, y, exog, params) => exog.alpha_H(t) * exog.p_bar_H(t),
    },
    {
      name: 'illiquidity_F2',
      label: 'ψ/(I+ε) (F.2)',
      color: '#dc2626',
      compute: (t, y, exog, params) => params.psi / (Math.max(exog.I(t), 0) + params.eps),
    },
  ],

  // ── Presets ──
  presets: [
    {
      name: 'R1 Effizienter Markt',
      description: 'α_H≈0, I hoch → μ_eff ≈ p_k (neoklassischer Grenzfall)',
      stateOverrides: { p: 10 },
      paramOverrides: { lambda: 50, phi: 0.02, psi: 0.1, eps: 0.01 },
      exogOverrides: {
        D: { type: 'ornsteinUhlenbeck', params: { theta: 0.3, mu: 100, sigma: 5, x0: 100, seed: 42 } },
        S: { type: 'sinusoidal', params: { offset: 100, amplitude: 5, frequency: 0.5, phase: 0 } },
        eta: { type: 'constant', params: { value: 0.01 } },
        I: { type: 'constant', params: { value: 8 } },
        alpha_H: { type: 'constant', params: { value: 0.05 } },
        p_bar_H: { type: 'ornsteinUhlenbeck', params: { theta: 1.0, mu: 0, sigma: 0.5, x0: 0, seed: 77 } },
      },
    },
    {
      name: 'R2 Blase (Herding)',
      description: 'α_H steigt logistisch, p̄_H groß → μ_eff >> p_k',
      stateOverrides: { p: 10 },
      paramOverrides: { lambda: 30, phi: 0.1, psi: 0.3, eps: 0.01 },
      exogOverrides: {
        D: { type: 'ornsteinUhlenbeck', params: { theta: 0.2, mu: 115, sigma: 8, x0: 110, seed: 44 } },
        S: { type: 'sinusoidal', params: { offset: 100, amplitude: 3, frequency: 0.3, phase: 0 } },
        eta: { type: 'step', params: { before: 0.02, after: 0.06, tSwitch: 20 } },
        I: { type: 'constant', params: { value: 3 } },
        alpha_H: { type: 'logistic', params: { L: 0.8, k: 0.15, tMid: 30, baseline: 0.1 } },
        p_bar_H: { type: 'logistic', params: { L: 15, k: 0.1, tMid: 35, baseline: 2 } },
      },
    },
    {
      name: 'R3 Krise (Illiquidität)',
      description: 'I→0 (GBM), ψ/(I+ε)→∞ — Marktversagen',
      stateOverrides: { p: 10 },
      paramOverrides: { lambda: 50, phi: 0.5, psi: 3.0, eps: 0.005 },
      exogOverrides: {
        D: { type: 'ornsteinUhlenbeck', params: { theta: 0.5, mu: 100, sigma: 3, x0: 100, seed: 46 } },
        S: { type: 'sinusoidal', params: { offset: 100, amplitude: 3, frequency: 0.5, phase: 0 } },
        eta: { type: 'constant', params: { value: 0.005 } },
        I: { type: 'geometricBrownian', params: { mu: -0.03, sigma: 0.15, x0: 5, seed: 7 } },
        alpha_H: { type: 'logistic', params: { L: 1.5, k: 0.12, tMid: 40, baseline: 0.1 } },
        p_bar_H: { type: 'ornsteinUhlenbeck', params: { theta: 0.2, mu: -3, sigma: 2, x0: 2, seed: 55 } },
      },
    },
    {
      name: 'R4 Zyklus (Eff→Blase→Krise)',
      description: 'Vollständiger Krisenzyklus: effizient→Herding-Blase→Illiquiditätskrise',
      stateOverrides: { p: 10 },
      paramOverrides: { lambda: 40, phi: 0.3, psi: 2.0, eps: 0.005 },
      exogOverrides: {
        D: { type: 'ornsteinUhlenbeck', params: { theta: 0.2, mu: 105, sigma: 6, x0: 102, seed: 48 } },
        S: { type: 'constant', params: { value: 100 } },
        eta: { type: 'constant', params: { value: 0.02 } },
        I: { type: 'exponentialDecay', params: { initial: 5, rate: 0.06, tStart: 25 } },
        alpha_H: { type: 'logistic', params: { L: 0.7, k: 0.2, tMid: 30, baseline: 0.05 } },
        p_bar_H: { type: 'logistic', params: { L: 10, k: 0.15, tMid: 35, baseline: 0 } },
      },
    },
    {
      name: 'R5 Voll stochastisch',
      description: 'OU/GBM/Poisson für alle exogenen Variablen + SDE-Modus',
      stateOverrides: { p: 10 },
      paramOverrides: { lambda: 35, phi: 0.2, psi: 1.0, eps: 0.01 },
      sdeOverrides: { sigma_p: 0.05 },
      exogOverrides: {
        D: { type: 'ornsteinUhlenbeck', params: { theta: 0.5, mu: 100, sigma: 8, x0: 100, seed: 50 } },
        S: { type: 'ornsteinUhlenbeck', params: { theta: 0.3, mu: 95, sigma: 5, x0: 95, seed: 51 } },
        eta: { type: 'poissonJumps', params: { baseline: 0.02, lambda: 0.3, jumpMean: 0.01, jumpStd: 0.005, seed: 99 } },
        I: { type: 'geometricBrownian', params: { mu: -0.005, sigma: 0.1, x0: 3, seed: 52 } },
        alpha_H: { type: 'ornsteinUhlenbeck', params: { theta: 0.2, mu: 0.3, sigma: 0.15, x0: 0.3, seed: 53 } },
        p_bar_H: { type: 'ornsteinUhlenbeck', params: { theta: 0.5, mu: 0, sigma: 3, x0: 0, seed: 54 } },
      },
    },
    {
      name: 'Neoklassik (α_H=0, ψ=0)',
      description: 'Arrow-Debreu Grenzfall: keine Herding, keine Illiquidität → μ_eff ≡ p_k',
      stateOverrides: { p: 10 },
      paramOverrides: { lambda: 50, phi: 0.0, psi: 0.0, eps: 0.01 },
      exogOverrides: {
        D: { type: 'sinusoidal', params: { offset: 100, amplitude: 10, frequency: 0.5, phase: 0 } },
        S: { type: 'sinusoidal', params: { offset: 100, amplitude: 5, frequency: 0.5, phase: 0.3 } },
        eta: { type: 'constant', params: { value: 0 } },
        I: { type: 'constant', params: { value: 10 } },
        alpha_H: { type: 'constant', params: { value: 0 } },
        p_bar_H: { type: 'constant', params: { value: 0 } },
      },
    },
  ],

  // ── Solver defaults ──
  solverDefaults: {
    tEnd: 80,
    rtol: 1e-8,
    atol: 1e-10,
    maxStep: 0.1,
    nPoints: 1000,
    sdeDt: 0.01,
    nPaths: 20,
  },
};

export default S09_F2;
