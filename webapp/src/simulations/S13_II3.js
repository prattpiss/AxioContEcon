/**
 * S13 – Informationsfluss  II.3  (§5.6, Vorschau Kap. 7)
 *
 * İ_k = D_I·∇²I − ω·I + S_k − μ·I³ + β·|ṗ_k|
 *
 * Fünf Terme:
 *   1. D_I·∇²I                    Diffusion (Nachrichten breiten sich aus)
 *   2. −ω·I                       Zerfall (Vergessen)
 *   3. S_k = r_I·I·(1−I/I_max)    Word-of-Mouth (logistisch)
 *   4. −μ·I³                      Kubische Sättigung (Ginzburg-Landau)
 *   5. β·|ṗ|                      Preis-Feedback (Events create news)
 *
 * Kopplung:
 *   Preis → Info: β|ṗ| erzeugt I bei Preisbewegungen
 *   Info → Preis: ψ/(I+ε) Illiquiditätsprämie (via F.2, II.2)
 *
 * Analytik:
 *   Reichweite: ℓ = √(D_I/ω)
 *   Travelling Wave (Fisher-KPP): v = 2√(D_I·(r_I−ω)), existiert falls r_I > ω
 *
 * NOTE: Browser-MOL mit NX=51 Gitterpunkten (reduziert).
 * Neumann BC (dI/dx=0 an Rändern).
 */

const NX = 51;
const L = 100;
const dx = L / (NX - 1);

// Gaußsches Anfangsprofil
function gaussianProfile(center, sigma, amplitude, baseline) {
  const prof = new Array(NX);
  for (let i = 0; i < NX; i++) {
    const xi = (i / (NX - 1)) * L;
    prof[i] = baseline + amplitude * Math.exp(-0.5 * ((xi - center) / sigma) ** 2);
  }
  return prof;
}

// Sigmoid-Front (Info links vorhanden, rechts nicht)
function sigmoidFront(x0, width) {
  const prof = new Array(NX);
  for (let i = 0; i < NX; i++) {
    const xi = (i / (NX - 1)) * L;
    prof[i] = 1.0 / (1.0 + Math.exp((xi - x0) / width));
  }
  return prof;
}

const FLOOR = 1e-10;

const S13_II3 = {
  id: 'S13',
  eqId: 'II.3',
  section: '§5.6',
  chapter: 5,
  chapterTitle: 'Kap. 5: Preise & Flüsse',
  title: 'Informationsfluss',
  equationLatex: String.raw`\dot{\mathcal{I}}_k = D_{\mathcal{I}}\nabla^2\mathcal{I} - \omega\mathcal{I} + \mathcal{S}_k - \mu\mathcal{I}^3 + \beta|\dot{p}|`,
  description:
    'Information breitet sich räumlich aus (Diffusion), veraltet (Zerfall), wird durch ' +
    'Word-of-Mouth verstärkt, sättigt kubisch (Ginzburg-Landau) und koppelt an Preise ' +
    '(Events create news). Bidirektionale Kopplung: starke Preisbewegungen erzeugen Info, ' +
    'niedrige Info erhöht die Illiquiditätsprämie. Zwei Spiralen: stabilisierend (Crash → News → ' +
    'Erholung) vs. destabilisierend (Analystenflucht → I sinkt → Illiq-Spirale).',

  // ── State: spatial information density I(x) ──
  stateVars: [
    {
      name: 'I_info',
      label: 'Informationsfeld I(x)',
      unit: 'dimlos',
      initial: 0.2,
      min: 0,
      max: 2,
      floor: FLOOR,
      description: 'Räumliche Informationsdichte (NX Gitterpunkte)',
      spatial: true,
      nx: NX,
      domainLength: L,
      initialProfile: gaussianProfile(50, 8, 0.8, 0.01),
    },
  ],

  // ── Exogenous ──
  exogenous: [
    {
      name: 'dp_dt',
      label: 'Preisänderung |dp/dt|(x)',
      unit: 'Wäh/(ME·a)',
      coupledTo: 'Preisdynamik II.2',
      defaultType: 'constant',
      defaultParams: { value: 0 },
      description: 'Betrag der lokalen Preisänderung. β·|dp/dt| erzeugt Information.',
    },
    {
      name: 'S_ext',
      label: 'Externe Quellen S_ext(x)',
      unit: '1/a',
      coupledTo: 'Werbung, Medien, Patente',
      defaultType: 'constant',
      defaultParams: { value: 0 },
      description: 'Nicht-WoM Informationsquellen (Werbung, Medienberichte, Patentveröffentlichungen).',
    },
  ],

  // ── Parameters ──
  parameters: [
    { name: 'D_I', label: 'Info-Diffusion D_I', unit: 'km²/a', default: 2.0, min: 0.01, max: 20, step: 0.1, description: 'Kommunikationsinfrastruktur: Mundpropaganda (klein) → Internet (groß)' },
    { name: 'omega', label: 'Zerfallsrate ω', unit: '1/a', default: 0.05, min: 0.001, max: 1.0, step: 0.01, description: 'Vergessensrate: News (groß) → Grundwissen (klein)' },
    { name: 'r_I', label: 'WoM-Rate r_I', unit: '1/a', default: 0.0, min: 0, max: 1.0, step: 0.01, description: 'Word-of-Mouth Netto-Wachstumsrate. r_I > ω → Travelling Wave' },
    { name: 'I_max', label: 'Sättigung I_max', unit: 'dimlos', default: 1.0, min: 0.1, max: 5, step: 0.1, description: 'Maximale Informationsdichte (WoM-Decke)' },
    { name: 'mu_sat', label: 'Sättigung μ', unit: '1/a', default: 0.0, min: 0, max: 5, step: 0.1, description: 'Kubische Sättigung (Ginzburg-Landau); μ·I³ begrenzt Wachstum' },
    { name: 'beta', label: 'Preis-Kopplung β', unit: 'dimlos', default: 0.0, min: 0, max: 2, step: 0.01, description: 'Stärke des Events-create-news Mechanismus' },
    { name: 'sigma_adv', label: 'Werbeeffizienz σ_adv', unit: 'dimlos', default: 0.0, min: 0, max: 2, step: 0.01, description: 'Umwandlungseffizienz Werbeausgaben → Information' },
  ],

  // ── SDE mode ──
  sdeConfig: {
    label: 'Stochastische Fluktuationen',
    description: 'Additives Rauschen auf das Informationsfeld: dI = [RHS]dt + σ·dW',
    sigmaParams: [
      { name: 'sigma_I', label: 'σ_I (Info-Rauschen)', default: 0.0, min: 0, max: 0.5, step: 0.01 },
    ],
  },

  // ── MOL RHS: ∂I/∂t = D·∇²I − ω·I + r_I·I(1−I/Imax) + σ·E_adv + S_ext − μ·I³ + β·|dp| ──
  rhs: (t, y, exog, params) => {
    const { D_I, omega, r_I, I_max, mu_sat, beta, sigma_adv } = params;
    const dIdt = new Array(NX).fill(0);
    const dx2 = dx * dx;

    for (let i = 0; i < NX; i++) {
      const xi = (i / (NX - 1)) * L;
      const Ii = Math.max(y[i], FLOOR);

      // Term 1: Diffusion (Laplacian, Neumann BC)
      let lap;
      if (i === 0) {
        lap = (y[1] - Ii) / dx2;
      } else if (i === NX - 1) {
        lap = (y[NX - 2] - Ii) / dx2;
      } else {
        lap = (y[i - 1] - 2 * Ii + y[i + 1]) / dx2;
      }
      const diffusion = D_I * lap;

      // Term 2: Zerfall
      const decay = -omega * Ii;

      // Term 3: WoM (logistisch)
      const wom = r_I * Ii * (1.0 - Ii / I_max);

      // Term 4: Quellen (Werbung + externe Medien)
      const sources = (1.0 + sigma_adv) * exog.S_ext(xi);

      // Term 5: Sättigung
      const saturation = -mu_sat * Ii * Ii * Ii;

      // Term 6: Preis-Feedback
      const dp = exog.dp_dt(xi);
      const priceFb = beta * Math.abs(dp);

      dIdt[i] = diffusion + decay + wom + sources + saturation + priceFb;
    }

    return dIdt;
  },

  // ── SDE diffusion ──
  diffusion: (t, y, _exog, _params, sigmaParams) => {
    return new Array(NX).fill(sigmaParams.sigma_I || 0);
  },

  // ── Terms: flux components at domain midpoint ──
  terms: [
    {
      name: 'diffusion',
      label: 'D·∇²I (Diffusion)',
      color: '#2196F3',
      compute: (t, y, exog, params) => {
        const mid = Math.floor(NX / 2);
        const lap = (y[mid - 1] - 2 * y[mid] + y[mid + 1]) / (dx * dx);
        return params.D_I * lap;
      },
    },
    {
      name: 'decay',
      label: '−ω·I (Zerfall)',
      color: '#F44336',
      compute: (t, y, exog, params) => {
        const mid = Math.floor(NX / 2);
        return -params.omega * Math.max(y[mid], FLOOR);
      },
    },
    {
      name: 'wom',
      label: 'r_I·I·(1−I/I_max) (WoM)',
      color: '#4CAF50',
      compute: (t, y, exog, params) => {
        const mid = Math.floor(NX / 2);
        const Ii = Math.max(y[mid], FLOOR);
        return params.r_I * Ii * (1 - Ii / params.I_max);
      },
    },
    {
      name: 'saturation',
      label: '−μ·I³ (Sättigung)',
      color: '#9C27B0',
      compute: (t, y, exog, params) => {
        const mid = Math.floor(NX / 2);
        const Ii = Math.max(y[mid], FLOOR);
        return -params.mu_sat * Ii * Ii * Ii;
      },
    },
    {
      name: 'price_fb',
      label: 'β·|dp| (Preis-FB)',
      color: '#795548',
      compute: (t, y, exog, params) => {
        const xi = (Math.floor(NX / 2) / (NX - 1)) * L;
        return params.beta * Math.abs(exog.dp_dt(xi));
      },
    },
  ],

  // ── Derived outputs ──
  derivedOutputs: [
    {
      name: 'I_mid',
      label: 'I(x=L/2)',
      unit: 'dimlos',
      compute: (t, y) => {
        return Math.max(y[Math.floor(NX / 2)], 0);
      },
    },
    {
      name: 'illiq_premium',
      label: 'ψ/(I+ε) Illiquidität',
      unit: 'dimlos',
      compute: (t, y) => {
        const mid = Math.floor(NX / 2);
        const Ii = Math.max(y[mid], FLOOR);
        return 1.0 / (Ii + 0.01); // psi=1, eps=0.01
      },
    },
    {
      name: 'x_cm',
      label: 'Schwerpunkt x̄',
      unit: 'km',
      compute: (t, y) => {
        let sumXI = 0, sumI = 0;
        for (let i = 0; i < NX; i++) {
          const xi = (i / (NX - 1)) * L;
          sumXI += xi * Math.max(y[i], 0);
          sumI += Math.max(y[i], 0);
        }
        return sumI > 0 ? sumXI / sumI : L / 2;
      },
    },
    {
      name: 'mass',
      label: 'Info-Masse ∫I dx',
      unit: 'dimlos·km',
      compute: (t, y) => {
        let M = 0;
        for (let i = 0; i < NX; i++) M += Math.max(y[i], 0);
        return M * dx;
      },
    },
    {
      name: 'ell',
      label: 'Reichweite ℓ=√(D/ω)',
      unit: 'km',
      compute: (t, y, exog, params) => {
        return Math.sqrt(params.D_I / (params.omega + 1e-10));
      },
    },
  ],

  // ── Presets ──
  presets: [
    {
      name: 'R1 Reine Diffusion + Zerfall',
      description: 'S=0, μ=0, β=0: Gaußpeak diffundiert und zerfällt exponentiell.',
      stateOverrides: { I_info: 0.2 },
      paramOverrides: { D_I: 2.0, omega: 0.05, r_I: 0.0, I_max: 1.0, mu_sat: 0.0, beta: 0.0, sigma_adv: 0.0 },
      exogOverrides: {
        dp_dt: { type: 'constant', params: { value: 0 } },
        S_ext: { type: 'constant', params: { value: 0 } },
      },
    },
    {
      name: 'R2 Fisher-KPP Front',
      description: 'r_I=0.15 > ω=0.02 → Travelling Wave. Info-Front wandert nach rechts.',
      stateOverrides: { I_info: 0.2 },
      paramOverrides: { D_I: 1.0, omega: 0.02, r_I: 0.15, I_max: 1.0, mu_sat: 0.0, beta: 0.0, sigma_adv: 0.0 },
      initialProfileOverride: { I_info: sigmoidFront(15, 3) },
      exogOverrides: {
        dp_dt: { type: 'constant', params: { value: 0 } },
        S_ext: { type: 'constant', params: { value: 0 } },
      },
    },
    {
      name: 'R3 Preis-Crash → Info-Welle',
      description: 'β=0.3: Preiscrash erzeugt Informationswelle (stabilisierende Spirale).',
      stateOverrides: { I_info: 0.15 },
      paramOverrides: { D_I: 1.5, omega: 0.04, r_I: 0.0, I_max: 1.0, mu_sat: 0.5, beta: 0.3, sigma_adv: 0.0 },
      initialProfileOverride: { I_info: new Array(NX).fill(0.15) },
      exogOverrides: {
        dp_dt: { type: 'sinusoidal', params: { offset: 0, amplitude: 3.0, frequency: 0.12, phase: 0 } },
        S_ext: { type: 'constant', params: { value: 0 } },
      },
    },
    {
      name: 'R4 Illiquiditätsspirale',
      description: 'Hoher Zerfall (ω=0.12), schwaches β → I kollabiert → Illiq.prämie explodiert.',
      stateOverrides: { I_info: 0.5 },
      paramOverrides: { D_I: 0.5, omega: 0.12, r_I: 0.02, I_max: 1.0, mu_sat: 0.3, beta: 0.01, sigma_adv: 0.0 },
      initialProfileOverride: { I_info: gaussianProfile(50, 20, 0.3, 0.5) },
      exogOverrides: {
        dp_dt: { type: 'step', params: { before: 0, after: -0.5, tSwitch: 30 } },
        S_ext: { type: 'constant', params: { value: 0 } },
      },
    },
    {
      name: 'R5 Voll stochastisch',
      description: 'OU-Preisänderungen, Poisson-Medien-Events, SDE-Rauschen.',
      stateOverrides: { I_info: 0.2 },
      paramOverrides: { D_I: 1.5, omega: 0.06, r_I: 0.08, I_max: 1.0, mu_sat: 0.3, beta: 0.05, sigma_adv: 0.0 },
      sdeOverrides: { sigma_I: 0.02 },
      exogOverrides: {
        dp_dt: { type: 'ornsteinUhlenbeck', params: { theta: 0.5, mu: 0, sigma: 1.0, x0: 0, seed: 42 } },
        S_ext: { type: 'poissonJumps', params: { baseline: 0, lambda: 0.08, jumpMean: 0.5, jumpStd: 0.2, seed: 99 } },
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

export default S13_II3;
