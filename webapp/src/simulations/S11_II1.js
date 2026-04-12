/**
 * S11 – Vermögensfluss  II.1  (§5.4)
 *
 * j_w = −D_w · ∇Φ_w + v_w · ρ_w
 *
 * Vermögenspotential (Def. 5.2):
 *   Φ_w = h(ρ_w) − β_w · V_w
 *   h(ρ) = α · ln(ρ/ρ₀)   (h' > 0, stabile Diffusion)
 *
 * Drei Flusskomponenten:
 *   1. −D_w·(α/ρ)·∇ρ      Diversifikation (nichtlineare Fick-Diffusion)
 *   2. +D_w·β_w·∇V_w       Standortattraktivität (hin zu guten Institutionen)
 *   3. +v_w·ρ_w             Konvektion (gerichtete Kapitalströme)
 *
 * Kopplung: ∂ρ_w/∂t = −∇·j_w + S_w  (Vermögenskontinuität)
 *
 * Lucas-Paradox (1990): V_w^{reich} ≫ V_w^{arm}
 *   → Kapital fließt von arm nach reich trotz Konzentrationsgefälle
 *
 * NOTE: Browser-MOL mit NX=51 Gitterpunkten (reduziert).
 * Neumann BC (j=0 an Rändern). Upwind-Schema für Konvektion.
 */

const NX = 51;
const L = 100;
const dx = L / (NX - 1);

// Gaußsches Anfangsprofil
function gaussianProfile(center, sigma, amplitude, baseline) {
  const rho = new Array(NX);
  for (let i = 0; i < NX; i++) {
    const xi = (i / (NX - 1)) * L;
    rho[i] = baseline + amplitude * Math.exp(-0.5 * ((xi - center) / sigma) ** 2);
  }
  return rho;
}

// Glatter räumlicher Sprung (Logistik)
function smoothStepProfile(x0, vLeft, vRight, width) {
  const prof = new Array(NX);
  for (let i = 0; i < NX; i++) {
    const xi = (i / (NX - 1)) * L;
    prof[i] = vRight + (vLeft - vRight) / (1 + Math.exp((xi - x0) / width));
  }
  return prof;
}

const S11_II1 = {
  id: 'S11',
  eqId: 'II.1',
  section: '§5.4',
  chapter: 5,
  chapterTitle: 'Kap. 5: Preise & Flüsse',
  title: 'Vermögensfluss',
  equationLatex: String.raw`\vec{j}_w = -D_w\,\nabla\Phi_w + \vec{v}_w\,\rho_w`,
  description:
    'Vermögen fließt entlang des negativen Gradienten des Vermögenspotentials Φ_w ' +
    'plus konvektivem Drift. Φ_w = h(ρ_w) − β_w·V_w: Konzentrationsterm h (Diversifikation) ' +
    'und Standortattraktivität V_w (Institutionenqualität). Drei Komponenten: ' +
    'Diversifikation, Standortanziehung, Konvektion. Erklärt das Lucas-Paradox (1990).',

  // ── State: spatial wealth density profile ρ_w(x) ──
  stateVars: [
    {
      name: 'rho_w',
      label: 'Vermögensdichte ρw(x)',
      unit: 'Wäh/km',
      initial: 10.0,
      min: 0.001,
      max: 200,
      floor: 1e-6,
      description: 'Räumliche Vermögensdichte (NX Gitterpunkte)',
      spatial: true,
      nx: NX,
      domainLength: L,
      initialProfile: gaussianProfile(50, 10, 50, 5),
    },
  ],

  // ── Exogenous: spatial profiles ──
  exogenous: [
    {
      name: 'V_w',
      label: 'Standortattraktivität Vw(x)',
      unit: 'dimensionslos',
      coupledTo: 'Institutionenqualität',
      defaultType: 'constant',
      defaultParams: { value: 5.0 },
      description: 'Räumliches Institutionenprofil; hoher Wert zieht Kapital an',
    },
    {
      name: 'v_w',
      label: 'Driftgeschwindigkeit vw(x)',
      unit: 'km/a',
      coupledTo: 'Investitionsprogramme',
      defaultType: 'constant',
      defaultParams: { value: 0 },
      description: 'Systematische Kapitaldrift (ZB-Intervention, Carry Trade)',
    },
    {
      name: 'S_w',
      label: 'Quellterm Sw(x)',
      unit: 'Wäh/(km·a)',
      coupledTo: 'Vermögensschöpfung',
      defaultType: 'constant',
      defaultParams: { value: 0 },
      description: 'Vermögensquellen/-senken; S>0 = Schöpfung, S<0 = Vernichtung',
    },
  ],

  // ── Parameters ──
  parameters: [
    { name: 'D_w', label: 'Diffusionskoeff. Dw', unit: 'km²/a', default: 10, min: 0.1, max: 100, step: 0.1, description: 'Kapitalmarktliberalisierung' },
    { name: 'alpha', label: 'Konz.-Sensitivität α', unit: 'dimlos', default: 5, min: 0.1, max: 20, step: 0.1, description: 'h(ρ) = α·ln(ρ/ρ₀), steuert Diversifikationsstärke' },
    { name: 'rho_0', label: 'Referenzdichte ρ₀', unit: 'Wäh/km', default: 10, min: 1, max: 100, step: 1, description: 'Neutrale Dichte (h=0 bei ρ=ρ₀)' },
    { name: 'beta_w', label: 'Standortsensitivität βw', unit: 'dimlos', default: 0, min: 0, max: 10, step: 0.1, description: 'Stärke der Standortanziehung in Φ_w' },
  ],

  // ── SDE mode ──
  sdeConfig: {
    label: 'Stochastische Fluktuationen',
    description: 'Additives Rauschen auf die Vermögensdichte: dρ = [MOL]dt + σ·dW',
    sigmaParams: [
      { name: 'sigma_rho', label: 'σρ (Dichterauschen)', default: 0.0, min: 0, max: 5, step: 0.1 },
    ],
  },

  // ── MOL RHS: ∂ρ_w/∂t = −∇·j_w + S_w ──
  rhs: (t, y, exog, params) => {
    const { D_w, alpha, rho_0, beta_w } = params;
    const drhodt = new Array(NX).fill(0);
    const FLOOR = 1e-6;

    // Compute Φ_w at each grid point
    const Phi = new Array(NX);
    for (let i = 0; i < NX; i++) {
      const xi = (i / (NX - 1)) * L;
      const ri = Math.max(y[i], FLOOR);
      const h = alpha * Math.log(ri / rho_0);
      const Vi = exog.V_w(xi);
      Phi[i] = h - beta_w * Vi;
    }

    // Diffusive flux on staggered grid: j_diff = -D_w * dΦ/dx
    // Convective flux (upwind): j_conv = v_w * ρ (upwind value)
    const j = new Array(NX - 1);
    for (let i = 0; i < NX - 1; i++) {
      const xi_mid = ((i + 0.5) / (NX - 1)) * L;
      const gradPhi = (Phi[i + 1] - Phi[i]) / dx;
      j[i] = -D_w * gradPhi;

      // Convection (upwind)
      const vi = exog.v_w(xi_mid);
      const rho_up = vi >= 0 ? y[i] : y[i + 1];
      j[i] += vi * Math.max(rho_up, FLOOR);
    }

    // Divergence → drho/dt (Neumann BC: j=0 at boundaries)
    drhodt[0] = -j[0] / dx + exog.S_w(0);
    for (let i = 1; i < NX - 1; i++) {
      const xi = (i / (NX - 1)) * L;
      drhodt[i] = -(j[i] - j[i - 1]) / dx + exog.S_w(xi);
    }
    drhodt[NX - 1] = j[NX - 2] / dx + exog.S_w(L);

    return drhodt;
  },

  // ── SDE diffusion ──
  diffusion: (t, y, _exog, _params, sigmaParams) => {
    return new Array(NX).fill(sigmaParams.sigma_rho || 0);
  },

  // ── Terms: flux components at domain midpoint ──
  terms: [
    {
      name: 'j_div',
      label: '−D·∇h (Diversifikation)',
      color: '#2563eb',
      compute: (t, y, exog, params) => {
        const mid = Math.floor(NX / 2);
        const r1 = Math.max(y[mid], 1e-6);
        const r2 = Math.max(y[mid + 1], 1e-6);
        const h1 = params.alpha * Math.log(r1 / params.rho_0);
        const h2 = params.alpha * Math.log(r2 / params.rho_0);
        return -params.D_w * (h2 - h1) / dx;
      },
    },
    {
      name: 'j_attr',
      label: '+Dβ∇Vw (Standort)',
      color: '#8b5cf6',
      compute: (t, y, exog, params) => {
        const mid = Math.floor(NX / 2);
        const x1 = (mid / (NX - 1)) * L;
        const x2 = ((mid + 1) / (NX - 1)) * L;
        return params.D_w * params.beta_w * (exog.V_w(x2) - exog.V_w(x1)) / dx;
      },
    },
    {
      name: 'j_conv',
      label: 'vw·ρw (Konvektion)',
      color: '#ef4444',
      compute: (t, y, exog, params) => {
        const mid = Math.floor(NX / 2);
        const xi = ((mid + 0.5) / (NX - 1)) * L;
        const vi = exog.v_w(xi);
        const rho_up = vi >= 0 ? y[mid] : y[mid + 1];
        return vi * Math.max(rho_up, 1e-6);
      },
    },
  ],

  // ── Derived outputs ──
  derivedOutputs: [
    {
      name: 'Phi_mid',
      label: 'Φw(x=L/2)',
      unit: 'dimlos',
      compute: (t, y, exog, params) => {
        const mid = Math.floor(NX / 2);
        const ri = Math.max(y[mid], 1e-6);
        const h = params.alpha * Math.log(ri / params.rho_0);
        const Vi = exog.V_w(L / 2);
        return h - params.beta_w * Vi;
      },
    },
    {
      name: 'x_cm',
      label: 'Schwerpunkt x̄',
      unit: 'km',
      compute: (t, y, exog, params) => {
        let sumXR = 0, sumR = 0;
        for (let i = 0; i < NX; i++) {
          const xi = (i / (NX - 1)) * L;
          sumXR += xi * Math.max(y[i], 0);
          sumR += Math.max(y[i], 0);
        }
        return sumR > 0 ? sumXR / sumR : L / 2;
      },
    },
    {
      name: 'mass',
      label: 'Masse ∫ρ dx',
      unit: 'Wäh',
      compute: (t, y, exog, params) => {
        let M = 0;
        for (let i = 0; i < NX; i++) M += Math.max(y[i], 0);
        return M * dx;
      },
    },
  ],

  // ── Presets ──
  presets: [
    {
      name: 'R1 Reine Diversifikation',
      description: 'β=0, v=0 → nichtlineare Fick-Diffusion j=−D(α/ρ)∇ρ, Gauß → Gleichvert.',
      stateOverrides: { rho_w: 10 },
      paramOverrides: { D_w: 30, alpha: 5, rho_0: 10, beta_w: 0 },
      exogOverrides: {
        V_w: { type: 'constant', params: { value: 5 } },
        v_w: { type: 'constant', params: { value: 0 } },
        S_w: { type: 'constant', params: { value: 0 } },
      },
    },
    {
      name: 'R2 Lucas-Paradox',
      description: 'V_w hoch links (reich), β_w=3 → Kapital bleibt trotz Konzentrationsgefälle links',
      stateOverrides: { rho_w: 10 },
      paramOverrides: { D_w: 10, alpha: 5, rho_0: 10, beta_w: 3 },
      exogOverrides: {
        V_w: { type: 'ramp', params: { valueStart: 8, valueEnd: 2, tStart: 0, tEnd: 1 } },
        v_w: { type: 'constant', params: { value: 0 } },
        S_w: { type: 'constant', params: { value: 0 } },
      },
    },
    {
      name: 'R3 Kapitalflucht',
      description: 'V_w kollabiert bei t=80 (Institutionenkrise) → Kapital flieht nach rechts',
      stateOverrides: { rho_w: 10 },
      paramOverrides: { D_w: 10, alpha: 5, rho_0: 10, beta_w: 2.5 },
      exogOverrides: {
        V_w: { type: 'step', params: { valueBefore: 8, valueAfter: 1, tSwitch: 80 } },
        v_w: { type: 'constant', params: { value: 0 } },
        S_w: { type: 'constant', params: { value: 0 } },
      },
    },
    {
      name: 'R4 Drift-Diffusion',
      description: 'v_w=0.5·sin(πx/L): konvektive Drift nach rechts, Diffusion wirkt dagegen',
      stateOverrides: { rho_w: 10 },
      paramOverrides: { D_w: 10, alpha: 4, rho_0: 10, beta_w: 0 },
      exogOverrides: {
        V_w: { type: 'constant', params: { value: 5 } },
        v_w: { type: 'sinusoidal', params: { offset: 0, amplitude: 0.5, frequency: 0.0314, phase: 0 } },
        S_w: { type: 'constant', params: { value: 0 } },
      },
    },
    {
      name: 'R5 Voll stochastisch',
      description: 'OU-moduliertes V_w, Poisson-Vermögensquellen, SDE-Dichte',
      stateOverrides: { rho_w: 10 },
      paramOverrides: { D_w: 8, alpha: 4, rho_0: 10, beta_w: 1 },
      sdeOverrides: { sigma_rho: 0.5 },
      exogOverrides: {
        V_w: { type: 'ornsteinUhlenbeck', params: { theta: 0.5, mu: 5, sigma: 1, x0: 5, seed: 55 } },
        v_w: { type: 'constant', params: { value: 0 } },
        S_w: { type: 'poissonJumps', params: { baseline: 0, lambda: 0.3, jumpMean: 1, jumpStd: 0.5, seed: 99 } },
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

export default S11_II1;
