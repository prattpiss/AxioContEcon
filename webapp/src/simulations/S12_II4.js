/**
 * S12 – Geldfluss  II.4  (§5.5)
 *
 * j_m = −D_m · ∇r + σ_m · E_Kredit
 *
 * Kreditfeld (Analogie zum E-Feld):
 *   E_Kredit = −∇Φ_Kredit
 *
 * Expandiert:
 *   j_m = −D_m · ∇r − σ_m · ∇Φ_Kredit
 *
 * Zwei Flusskomponenten:
 *   1. −D_m · ∇r                  Carry Trade (Geld → hoher Zins)
 *   2. −σ_m · ∇Φ_Kredit           Kreditkanal (Bankkreditanreiz)
 *
 * Lokaler Zinssatz:
 *   r(x,t) = r_base + κ · ln(ρ_m/ρ₀)
 *
 * Zwei Regime:
 *   ZINSGETRIEBEN: −D_m·∇r dominiert (normale Geldpolitik)
 *   KREDITGETRIEBEN: σ_m·E_Kredit dominiert (QE, Credit Crunch)
 *
 * Nullzinsgrenze: r → 0 ⇒ ∇r ≈ 0 ⇒ nur Kreditkanal wirkt
 *   → erklärt warum QE trotz Nullzins expansiv ist
 *
 * NOTE: Browser-MOL mit NX=51 Gitterpunkten (reduziert).
 * Neumann BC (j=0 an Rändern). Radau-ähnliche Stabilität via kleinen max_step.
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

// Rampe
function rampProfile(vLeft, vRight) {
  const prof = new Array(NX);
  for (let i = 0; i < NX; i++) {
    prof[i] = vLeft + (vRight - vLeft) * (i / (NX - 1));
  }
  return prof;
}

const FLOOR = 1e-6;

const S12_II4 = {
  id: 'S12',
  eqId: 'II.4',
  section: '§5.5',
  chapter: 5,
  chapterTitle: 'Kap. 5: Preise & Flüsse',
  title: 'Geldfluss',
  equationLatex: String.raw`\vec{j}_m = -D_m\,\nabla r + \sigma_m\,\vec{E}_{\mathrm{Kredit}}`,
  description:
    'Geld fließt entlang des Zinsgefälles (Carry Trade) und entlang des Kreditfeldes ' +
    '(Bankenkreditvergabe). Zwei Regime: Zinsgetrieben (normale Geldpolitik) vs. ' +
    'Kreditgetrieben (QE, Credit Crunch). An der Nullzinsgrenze (r→0) dominiert ' +
    'der Kreditkanal — erklärt warum QE nach 2008 trotz Nullzins expansiv wirkte.',

  // ── State: spatial money density profile ρ_m(x) ──
  stateVars: [
    {
      name: 'rho_m',
      label: 'Gelddichte ρm(x)',
      unit: 'Wäh/km',
      initial: 10.0,
      min: 0.001,
      max: 200,
      floor: FLOOR,
      description: 'Räumliche Gelddichte (NX Gitterpunkte)',
      spatial: true,
      nx: NX,
      domainLength: L,
      initialProfile: gaussianProfile(35, 12, 60, 5),
    },
  ],

  // ── Exogenous: spatial profiles ──
  exogenous: [
    {
      name: 'Phi_Kredit',
      label: 'Kreditpotential Φ_Kredit(x)',
      unit: 'dimensionslos',
      coupledTo: 'Bankenkreditvergabe',
      defaultType: 'constant',
      defaultParams: { value: 0 },
      description: 'Kreditfeld der Banken; E_Kredit = −∇Φ. Hohes Φ = starker Kreditanreiz.',
    },
    {
      name: 'r_base_exog',
      label: 'Leitzins r_base(t)',
      unit: '1/a',
      coupledTo: 'Zentralbank',
      defaultType: 'constant',
      defaultParams: { value: 0.03 },
      description: 'Leitzins der Zentralbank; r(x) = r_base + κ·ln(ρ/ρ₀).',
    },
    {
      name: 'Q_m',
      label: 'Geldquellen Qm(x)',
      unit: 'Wäh/(km·a)',
      coupledTo: 'Geldschöpfung (M.1)',
      defaultType: 'constant',
      defaultParams: { value: 0 },
      description: 'Geldquellen/-senken; Q>0 = Geldschöpfung, Q<0 = Vernichtung.',
    },
  ],

  // ── Parameters ──
  parameters: [
    { name: 'D_m', label: 'Zinsdiffusion Dm', unit: 'km²·a', default: 50, min: 0.1, max: 200, step: 0.1, description: 'Geschwindigkeit des Zinsarbitrage-Flusses' },
    { name: 'sigma_m', label: 'Kreditkopplung σm', unit: 'km²/a', default: 0, min: 0, max: 50, step: 0.1, description: 'Stärke des Kreditkanal-Einflusses' },
    { name: 'kappa', label: 'Zins-Dichte-Sens. κ', unit: 'dimlos', default: 1.0, min: 0.1, max: 5, step: 0.1, description: 'r = r_base + κ·ln(ρ/ρ₀); lokale Zinsreaktion auf Gelddichte' },
    { name: 'rho_0', label: 'Referenzdichte ρ₀', unit: 'Wäh/km', default: 10, min: 1, max: 100, step: 1, description: 'Neutrale Dichte (r = r_base bei ρ = ρ₀)' },
  ],

  // ── SDE mode ──
  sdeConfig: {
    label: 'Stochastische Fluktuationen',
    description: 'Additives Rauschen auf die Gelddichte: dρ = [MOL]dt + σ·dW',
    sigmaParams: [
      { name: 'sigma_rho', label: 'σρ (Dichterauschen)', default: 0.0, min: 0, max: 5, step: 0.1 },
    ],
  },

  // ── MOL RHS: ∂ρ_m/∂t = −∇·j_m + Q_m ──
  rhs: (t, y, exog, params) => {
    const { D_m, sigma_m, kappa, rho_0 } = params;
    const drhodt = new Array(NX).fill(0);

    // Compute local interest rate r(x) and Phi_Kredit(x)
    const r = new Array(NX);
    const PhiK = new Array(NX);
    for (let i = 0; i < NX; i++) {
      const xi = (i / (NX - 1)) * L;
      const ri = Math.max(y[i], FLOOR);
      const rBase = exog.r_base_exog(t);
      r[i] = rBase + kappa * Math.log(ri / rho_0);
      PhiK[i] = exog.Phi_Kredit(xi);
    }

    // Flux on staggered grid: j = -D_m * dr/dx - sigma_m * dPhi/dx
    const j = new Array(NX - 1);
    for (let i = 0; i < NX - 1; i++) {
      const gradR = (r[i + 1] - r[i]) / dx;
      const gradPhi = (PhiK[i + 1] - PhiK[i]) / dx;
      j[i] = -D_m * gradR - sigma_m * gradPhi;
    }

    // Divergence → drho/dt (Neumann BC: j=0 at boundaries)
    drhodt[0] = -j[0] / dx + exog.Q_m(0);
    for (let i = 1; i < NX - 1; i++) {
      const xi = (i / (NX - 1)) * L;
      drhodt[i] = -(j[i] - j[i - 1]) / dx + exog.Q_m(xi);
    }
    drhodt[NX - 1] = j[NX - 2] / dx + exog.Q_m(L);

    return drhodt;
  },

  // ── SDE diffusion ──
  diffusion: (t, y, _exog, _params, sigmaParams) => {
    return new Array(NX).fill(sigmaParams.sigma_rho || 0);
  },

  // ── Terms: flux components at domain midpoint ──
  terms: [
    {
      name: 'j_zins',
      label: '−Dm·∇r (Zinsgradient)',
      color: '#2563eb',
      compute: (t, y, exog, params) => {
        const mid = Math.floor(NX / 2);
        const r1 = params.kappa * Math.log(Math.max(y[mid], FLOOR) / params.rho_0);
        const r2 = params.kappa * Math.log(Math.max(y[mid + 1], FLOOR) / params.rho_0);
        // r_base cancels in gradient
        return -params.D_m * (r2 - r1) / dx;
      },
    },
    {
      name: 'j_kredit',
      label: '−σm·∇Φ (Kreditkanal)',
      color: '#8b5cf6',
      compute: (t, y, exog, params) => {
        const mid = Math.floor(NX / 2);
        const x1 = (mid / (NX - 1)) * L;
        const x2 = ((mid + 1) / (NX - 1)) * L;
        return -params.sigma_m * (exog.Phi_Kredit(x2) - exog.Phi_Kredit(x1)) / dx;
      },
    },
  ],

  // ── Derived outputs ──
  derivedOutputs: [
    {
      name: 'r_mid',
      label: 'r(x=L/2)',
      unit: '1/a',
      compute: (t, y, exog, params) => {
        const mid = Math.floor(NX / 2);
        const ri = Math.max(y[mid], FLOOR);
        const rBase = exog.r_base_exog(t);
        return rBase + params.kappa * Math.log(ri / params.rho_0);
      },
    },
    {
      name: 'x_cm',
      label: 'Schwerpunkt x̄',
      unit: 'km',
      compute: (t, y) => {
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
      label: 'Geldmenge ∫ρm dx',
      unit: 'Wäh',
      compute: (t, y) => {
        let M = 0;
        for (let i = 0; i < NX; i++) M += Math.max(y[i], 0);
        return M * dx;
      },
    },
  ],

  // ── Presets ──
  presets: [
    {
      name: 'R1 Reiner Zinsgradient',
      description: 'σ_m=0 → j = −D·∇r: reiner Carry Trade. Geld fließt von niedrig-r nach hoch-r.',
      stateOverrides: { rho_m: 10 },
      paramOverrides: { D_m: 50, sigma_m: 0, kappa: 1.0, rho_0: 10 },
      exogOverrides: {
        Phi_Kredit: { type: 'constant', params: { value: 0 } },
        r_base_exog: { type: 'constant', params: { value: 0.03 } },
        Q_m: { type: 'constant', params: { value: 0 } },
      },
    },
    {
      name: 'R2 Kreditgetrieben',
      description: 'D_m klein, σ_m groß → Kreditkanal dominiert. Geld folgt Bankenanreizen.',
      stateOverrides: { rho_m: 10 },
      paramOverrides: { D_m: 1.5, sigma_m: 20, kappa: 0.8, rho_0: 10 },
      exogOverrides: {
        Phi_Kredit: { type: 'ramp', params: { vStart: 8, vEnd: 1, tStart: 0, tEnd: 100 } },
        r_base_exog: { type: 'constant', params: { value: 0.02 } },
        Q_m: { type: 'constant', params: { value: 0 } },
      },
    },
    {
      name: 'R3 Nullzinsgrenze + QE',
      description: 'r_base sinkt auf 0 bei t=60, QE (Φ_Kredit + Q_m) ab t=80.',
      stateOverrides: { rho_m: 10 },
      paramOverrides: { D_m: 15, sigma_m: 8, kappa: 2.5, rho_0: 15 },
      exogOverrides: {
        Phi_Kredit: { type: 'logistic', params: { L: 3, k: 0.2, tMid: 80, baseline: 0 } },
        r_base_exog: { type: 'logistic', params: { L: 0.049, k: -0.3, tMid: 60, baseline: 0.001 } },
        Q_m: { type: 'logistic', params: { L: 0.5, k: 0.2, tMid: 80, baseline: 0 } },
      },
    },
    {
      name: 'R4 Credit Crunch',
      description: 'Φ_Kredit kollabiert bei t=80 → Kreditkanal versagt. Geld zieht sich ins Zentrum zurück.',
      stateOverrides: { rho_m: 10 },
      paramOverrides: { D_m: 10, sigma_m: 10, kappa: 2.0, rho_0: 12 },
      exogOverrides: {
        Phi_Kredit: { type: 'logistic', params: { L: 4.5, k: -0.3, tMid: 80, baseline: 0.5 } },
        r_base_exog: { type: 'constant', params: { value: 0.03 } },
        Q_m: { type: 'constant', params: { value: 0 } },
      },
    },
    {
      name: 'R5 Voll stochastisch',
      description: 'OU-Leitzins, Poisson-QE-Injektionen, SDE-Dichterauschen.',
      stateOverrides: { rho_m: 10 },
      paramOverrides: { D_m: 10, sigma_m: 5, kappa: 2.0, rho_0: 10 },
      sdeOverrides: { sigma_rho: 0.5 },
      exogOverrides: {
        Phi_Kredit: { type: 'ornsteinUhlenbeck', params: { theta: 0.4, mu: 3, sigma: 0.5, x0: 3, seed: 55 } },
        r_base_exog: { type: 'ornsteinUhlenbeck', params: { theta: 0.5, mu: 0.03, sigma: 0.005, x0: 0.03, seed: 77 } },
        Q_m: { type: 'poissonJumps', params: { baseline: 0, lambda: 0.25, jumpMean: 0.5, jumpStd: 0.2, seed: 99 } },
      },
    },
  ],

  // ── Solver defaults ──
  solverDefaults: {
    tEnd: 200,
    rtol: 1e-6,
    atol: 1e-8,
    maxStep: 0.3,
    nPoints: 500,
    sdeDt: 0.05,
    nPaths: 5,
  },
};

export default S12_II4;
