/**
 * S10 – Allgemeiner Güterfluss  F.1  (§5.3)
 *
 * j⃗_{n_k} = −D_k · ∇μ_k^eff
 *
 * Expandiert (F.2 eingesetzt):
 * j = −D_k[∇p_k + α_H·∇p̄_H + ∇(ψ/(I+ε))]
 *
 * Räumliche 1D-Simulation: Güterdichte n_k(x,t) auf [0,L].
 * p_k = p0·(n/n0)^γ (Standortdruck, ∂p/∂n > 0 → stabile Diffusion).
 * Kopplung: P.3 ∂n/∂t = −∇·j + q   (Kontinuität)
 *           F.2 μ_eff = p + α_H·p̄_H + ψ/(I+ε)
 *
 * Drei Flusskomponenten:
 *   1. −D·∇p          Preisarbitrage
 *   2. −D·α_H·∇p̄_H    Herding-Fluss
 *   3. −D·∇(ψ/(I+ε))  Informationssog (Güter → hohem I)
 *
 * Prop 5.3: Skalentrennung D_phys << D_info (10 Größenordnungen)
 *
 * NOTE: Das Webapp-Modell simuliert die räumliche Dynamik als
 * 1D Method-of-Lines PDE direkt im Browser. Da die MOL-Simulation
 * rechenintensiv ist, wird hier eine vereinfachte Version mit
 * weniger Gitterpunkten verwendet.
 */

const NX = 51; // Gitterpunkte (reduziert für Browser-Performance)
const L = 100;
const dx = L / (NX - 1);

// Gaußsches Anfangsprofil
function gaussianProfile(center, sigma, amplitude, baseline) {
  const n = new Array(NX);
  for (let i = 0; i < NX; i++) {
    const xi = (i / (NX - 1)) * L;
    n[i] = baseline + amplitude * Math.exp(-0.5 * ((xi - center) / sigma) ** 2);
  }
  return n;
}

const S10_F1 = {
  id: 'S10',
  eqId: 'F.1',
  section: '§5.3',
  chapter: 5,
  chapterTitle: 'Kap. 5: Preise & Flüsse',
  title: 'Allgemeiner Güterfluss',
  equationLatex: String.raw`\vec{j}_{n_k} = -D_k\,\nabla\mu_k^{\rm eff}`,
  description:
    'Güter fließen entlang des negativen Gradienten des effektiven Potentials μ_eff. ' +
    'Expandiert: j = −D_k[∇p + α_H∇p̄_H + ∇(ψ/(I+ε))]. Drei Komponenten: ' +
    'Preisarbitrage, Herding-Fluss, Informationssog. Kopplung mit P.3 (Kontinuität) ' +
    'und F.2 (eff. Potential). Prop 5.3: D-Skalentrennung (10 Größenordnungen).',

  // ── State: spatial density profile n_k(x) ──
  // We use NX state variables representing n_k at each grid point.
  // The webapp solver treats this as an ODE system (Method of Lines).
  stateVars: [
    {
      name: 'n',
      label: 'Güterdichte nₖ(x)',
      unit: 'ME/km',
      initial: 10.0,
      min: 0.001,
      max: 200,
      floor: 1e-6,
      description: 'Räumliche Güterdichte (NX Gitterpunkte)',
      spatial: true,
      nx: NX,
      domainLength: L,
      initialProfile: gaussianProfile(50, 10, 50, 10),
    },
  ],

  // ── Exogenous: spatial profiles ──
  exogenous: [
    {
      name: 'I',
      label: 'Information Iₖ(x)',
      unit: 'dimensionslos',
      coupledTo: 'II.3 (§5.6)',
      defaultType: 'constant',
      defaultParams: { value: 5.0 },
      description: 'Räumliches Informationsprofil; bestimmt Illiquiditätssog',
    },
    {
      name: 'p_bar_H',
      label: 'Herding-Signal p̄H(x)',
      unit: 'dimensionslos',
      coupledTo: 'V.7 Netzwerk',
      defaultType: 'constant',
      defaultParams: { value: 0 },
      description: 'Räumliches Herding-Signal; Gradient treibt Herding-Fluss',
    },
    {
      name: 'q',
      label: 'Quellterm qₖ(x)',
      unit: 'ME/(km·a)',
      coupledTo: 'III.3 (§6.5)',
      defaultType: 'constant',
      defaultParams: { value: 0 },
      description: 'Produktions-/Konsum-Quellen; q>0 = Produktion, q<0 = Konsum',
    },
  ],

  // ── Parameters ──
  parameters: [
    { name: 'D_k', label: 'Diffusionskonst. Dₖ', unit: 'km²/a', default: 10, min: 0.1, max: 100, step: 0.1, description: 'Transportinfrastruktur-Geschwindigkeit' },
    { name: 'alpha_H', label: 'Herding αH', unit: 'dimlos', default: 0, min: 0, max: 2, step: 0.01, description: 'Herding-Sensitivität (F.2)' },
    { name: 'psi', label: 'Illiquidität ψₖ', unit: 'Wäh/ME', default: 0, min: 0, max: 10, step: 0.1, description: 'Informationskosten-Zuschlag (F.2)' },
    { name: 'eps', label: 'Regularisierung ε', unit: 'dimlos', default: 0.01, min: 0.001, max: 0.1, step: 0.001, description: 'Verhindert Division durch 0' },
    { name: 'p0', label: 'Referenzpreis p₀', unit: 'Wäh/ME', default: 10, min: 1, max: 100, step: 1, description: 'Preis bei n=n₀' },
    { name: 'n0', label: 'Referenzdichte n₀', unit: 'ME/km', default: 20, min: 1, max: 100, step: 1, description: 'Dichte bei p=p₀' },
    { name: 'gamma', label: 'Preiselastizität γ', unit: 'dimlos', default: 0.5, min: 0.1, max: 2, step: 0.05, description: 'Exponent der Preis-Dichte-Beziehung' },
  ],

  // ── SDE mode ──
  sdeConfig: {
    label: 'Stochastische Fluktuationen',
    description: 'Additive Rausch auf die Dichte: dn = [MOL]dt + σ·dW',
    sigmaParams: [
      { name: 'sigma_n', label: 'σₙ (Dichterauschen)', default: 0.0, min: 0, max: 5, step: 0.1 },
    ],
  },

  // ── MOL RHS: ∂n/∂t = −∇·j + q ──
  // The state y is a flat array of NX density values.
  rhs: (t, y, exog, params) => {
    const { D_k, alpha_H, psi, eps, p0, n0, gamma } = params;
    const dndt = new Array(NX).fill(0);

    // Compute μ_eff at each grid point
    const mu = new Array(NX);
    for (let i = 0; i < NX; i++) {
      const ni = Math.max(y[i], 1e-6);
      const xi = (i / (NX - 1)) * L;
      const pi = p0 * Math.pow(ni / n0, gamma);
      const Ii = exog.I(xi);
      const pHi = exog.p_bar_H(xi);
      mu[i] = pi + alpha_H * pHi + psi / (Math.max(Ii, 0) + eps);
    }

    // Flux on staggered grid (NX-1 interfaces)
    const j = new Array(NX - 1);
    for (let i = 0; i < NX - 1; i++) {
      j[i] = -D_k * (mu[i + 1] - mu[i]) / dx;
    }

    // Divergence → dndt (Neumann BC: j=0 at boundaries)
    dndt[0] = -j[0] / dx + exog.q(0);
    for (let i = 1; i < NX - 1; i++) {
      const xi = (i / (NX - 1)) * L;
      dndt[i] = -(j[i] - j[i - 1]) / dx + exog.q(xi);
    }
    dndt[NX - 1] = j[NX - 2] / dx + exog.q(L);

    return dndt;
  },

  // ── SDE diffusion ──
  diffusion: (t, y, _exog, _params, sigmaParams) => {
    return new Array(NX).fill(sigmaParams.sigma_n || 0);
  },

  // ── Terms: flux components (evaluated at domain midpoint for display) ──
  terms: [
    {
      name: 'j_price',
      label: '−D∇p (Arbitrage)',
      color: '#2563eb',
      compute: (t, y, exog, params) => {
        const mid = Math.floor(NX / 2);
        const n1 = Math.max(y[mid], 1e-6);
        const n2 = Math.max(y[mid + 1], 1e-6);
        const p1 = params.p0 * Math.pow(n1 / params.n0, params.gamma);
        const p2 = params.p0 * Math.pow(n2 / params.n0, params.gamma);
        return -params.D_k * (p2 - p1) / dx;
      },
    },
    {
      name: 'j_herding',
      label: '−Dα_H∇p̄H (Herding)',
      color: '#8b5cf6',
      compute: (t, y, exog, params) => {
        const mid = Math.floor(NX / 2);
        const x1 = (mid / (NX - 1)) * L;
        const x2 = ((mid + 1) / (NX - 1)) * L;
        return -params.D_k * params.alpha_H * (exog.p_bar_H(x2) - exog.p_bar_H(x1)) / dx;
      },
    },
    {
      name: 'j_info',
      label: '−D∇(ψ/(I+ε)) (Infosog)',
      color: '#ef4444',
      compute: (t, y, exog, params) => {
        const mid = Math.floor(NX / 2);
        const x1 = (mid / (NX - 1)) * L;
        const x2 = ((mid + 1) / (NX - 1)) * L;
        const ill1 = params.psi / (Math.max(exog.I(x1), 0) + params.eps);
        const ill2 = params.psi / (Math.max(exog.I(x2), 0) + params.eps);
        return -params.D_k * (ill2 - ill1) / dx;
      },
    },
  ],

  // ── Presets ──
  presets: [
    {
      name: 'R1 Reine Diffusion',
      description: 'α_H=0, ψ=0 → Fick\'sche Diffusion j=−D∇p, Gaußprofil → Gleichverteilung',
      stateOverrides: { n: 10 },
      paramOverrides: { D_k: 50, alpha_H: 0, psi: 0, eps: 0.01, p0: 10, n0: 20, gamma: 0.5 },
      exogOverrides: {
        I: { type: 'constant', params: { value: 10 } },
        p_bar_H: { type: 'constant', params: { value: 0 } },
        q: { type: 'constant', params: { value: 0 } },
      },
    },
    {
      name: 'R2 Herding-Fluss',
      description: 'α_H=0.8, p̄_H fällt räumlich → Herding-Drift treibt Güter',
      stateOverrides: { n: 10 },
      paramOverrides: { D_k: 3, alpha_H: 0.8, psi: 0.1, eps: 0.01, p0: 10, n0: 20, gamma: 0.3 },
      exogOverrides: {
        I: { type: 'constant', params: { value: 5 } },
        p_bar_H: { type: 'ramp', params: { valueStart: 10, valueEnd: 0, tStart: 0, tEnd: 100 } },
        q: { type: 'constant', params: { value: 0 } },
      },
    },
    {
      name: 'R3 Informationssog',
      description: 'ψ=3, I(x) fällt → ψ/(I+ε) steigt → Güter fließen zum hohen I',
      stateOverrides: { n: 10 },
      paramOverrides: { D_k: 4, alpha_H: 0, psi: 3, eps: 0.01, p0: 10, n0: 20, gamma: 0.3 },
      exogOverrides: {
        I: { type: 'ramp', params: { valueStart: 10, valueEnd: 0.5, tStart: 0, tEnd: 100 } },
        p_bar_H: { type: 'constant', params: { value: 0 } },
        q: { type: 'constant', params: { value: 0 } },
      },
    },
    {
      name: 'R4 Skalentrennung',
      description: 'D_phys=2 vs D_info=50 — Entkopplung Real- vs Finanzökonomie',
      stateOverrides: { n: 10 },
      paramOverrides: { D_k: 2, alpha_H: 0.2, psi: 0.5, eps: 0.01, p0: 10, n0: 15, gamma: 0.4 },
      exogOverrides: {
        I: { type: 'constant', params: { value: 5 } },
        p_bar_H: { type: 'sinusoidal', params: { offset: 0, amplitude: 2, frequency: 0.063, phase: 0 } },
        q: { type: 'constant', params: { value: 0 } },
      },
    },
    {
      name: 'R5 Voll stochastisch',
      description: 'OU-modulierte Information, Poisson-Quellen, SDE-Dichte',
      stateOverrides: { n: 10 },
      paramOverrides: { D_k: 4, alpha_H: 0.5, psi: 1.5, eps: 0.01, p0: 10, n0: 20, gamma: 0.4 },
      sdeOverrides: { sigma_n: 0.5 },
      exogOverrides: {
        I: { type: 'ornsteinUhlenbeck', params: { theta: 0.3, mu: 4, sigma: 1, x0: 4, seed: 42 } },
        p_bar_H: { type: 'ornsteinUhlenbeck', params: { theta: 0.5, mu: 0, sigma: 2, x0: 0, seed: 55 } },
        q: { type: 'poissonJumps', params: { baseline: 0, lambda: 0.3, jumpMean: 1, jumpStd: 0.5, seed: 99 } },
      },
    },
  ],

  // ── Solver defaults ──
  solverDefaults: {
    tEnd: 200,
    rtol: 1e-6,
    atol: 1e-8,
    maxStep: 0.5,
    nPoints: 500,
    sdeDt: 0.05,
    nPaths: 5,
  },
};

export default S10_F1;
