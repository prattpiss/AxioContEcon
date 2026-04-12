/**
 * S14 – Nutzenordnung  U.1  (§6.1, Kap. 6)
 *
 * u_i = u(c_i, l_i; γ_i, c_i*)
 *
 * Axiomatisch: u'>0 (Monotonie), u''<0 (Konkavität)
 *
 * Euler-Gleichung (V.1):
 *   ċ = c·(r−β)/γ    (Ramsey-Konsumdynamik)
 *
 * Habitformation (VI.4):
 *   ċ* = λ_c·(c−c*)   (Referenzpunkt-Drift)
 *
 * Kopplung:
 *   γ → Konsumwachstum: ċ/c = (r−β)/γ
 *   γ → Portfolio: w* = (μ−r)/(γ·σ²)  (Merton)
 *   I → eff. Preis: p_eff = p·(1+ψ/(I+ε))  (U.3)
 *
 * Zwei Spiralen:
 *   Stabilisierend: Verlust → γ↑ → weniger Risiko → Erholung
 *   Destabilisierend: Gewinn → γ↓ → mehr Risiko → Blase
 *
 * NOTE: ODE-System (2 Zustandsvariablen: c, c*).
 */

const S14_U1 = {
  id: 'S14',
  eqId: 'U.1',
  section: '§6.1',
  chapter: 6,
  chapterTitle: 'Kap. 6: Entscheidungen',
  title: 'Nutzenordnung',
  equationLatex: String.raw`\dot{c}_i = \frac{r - \beta_i}{\gamma_i}\,c_i \;,\qquad \dot{c}_i^* = \lambda_c(c_i - c_i^*)`,
  description:
    'Euler-Konsumgleichung aus Nutzenmaximierung (CRRA): Konsum wächst mit ' +
    '(r−β)/γ. Referenzpunkt c* verfolgt Konsum via Habitformation (VI.4). ' +
    'Surplus c−c* bestimmt Zufriedenheit. Kopplung: γ steuert auch Portfolioallokation ' +
    '(Merton w*), Information I steuert effektiven Preis (U.3).',

  // ── State: Konsum + Referenzpunkt ──
  stateVars: [
    {
      name: 'c',
      label: 'Konsum c',
      unit: 'Waehrung/a',
      initial: 1.0,
      min: 0.01,
      max: 50,
      floor: 1e-6,
      description: 'Realer Konsumfluss des Agenten',
    },
    {
      name: 'c_star',
      label: 'Referenzpunkt c*',
      unit: 'Waehrung/a',
      initial: 0.8,
      min: 0,
      max: 50,
      floor: 0,
      description: 'Habit/Aspirationsniveau (VI.4): dc*/dt = lambda_c·(c−c*)',
    },
  ],

  // ── Exogenous ──
  exogenous: [
    {
      name: 'r',
      label: 'Realzins r',
      unit: '1/a',
      coupledTo: 'VI.1 Taylor-Regel (§6.8)',
      defaultType: 'constant',
      defaultParams: { value: 0.04 },
      description: 'Realzins; in Vollmodell endogen via Taylor-Regel oder Marktgleichgewicht.',
    },
    {
      name: 'mu_stock',
      label: 'Aktienrendite mu',
      unit: '1/a',
      coupledTo: 'II.2 Preisdynamik',
      defaultType: 'constant',
      defaultParams: { value: 0.08 },
      description: 'Erwartete Aktienrendite (fuer Merton-Portfolioanteil).',
    },
    {
      name: 'I_info',
      label: 'Information I',
      unit: 'dimlos',
      coupledTo: 'II.3 (§5.6)',
      defaultType: 'constant',
      defaultParams: { value: 1.0 },
      description: 'Informationsniveau; bestimmt eff. Preis p_eff=p(1+psi/(I+eps)).',
    },
  ],

  // ── Parameters ──
  parameters: [
    { name: 'gamma', label: 'Risikoaversion gamma', unit: 'dimlos', default: 2.0, min: 0.1, max: 20, step: 0.1, description: 'CRRA-Parameter: hoehere gamma = risikoscheuer. Steuert sowohl Konsum als auch Portfolio.' },
    { name: 'beta_disc', label: 'Zeitpraeferenz beta', unit: '1/a', default: 0.03, min: 0.0, max: 0.2, step: 0.005, description: 'Diskontrate; r>beta -> Konsum steigt, r<beta -> Konsum faellt.' },
    { name: 'lambda_c', label: 'Habit-Geschw. lambda_c', unit: '1/a', default: 0.1, min: 0, max: 2, step: 0.01, description: 'Anpassungsgeschwindigkeit des Referenzpunkts. 0=kein Habit, gross=schnelle Anpassung (Hedonic Treadmill).' },
    { name: 'sigma_stock', label: 'Aktienvolatilitaet sigma', unit: 'dimlos', default: 0.20, min: 0.01, max: 1, step: 0.01, description: 'Volatilitaet der Aktienrendite (fuer Merton-Portfolioberechnung).' },
    { name: 'psi_illiq', label: 'Illiquiditaet psi', unit: 'dimlos', default: 0.1, min: 0, max: 2, step: 0.01, description: 'Illiquiditaetspraemie in U.3: p_eff = p*(1+psi/(I+eps)).' },
    { name: 'eps_reg', label: 'Regularisierung eps', unit: 'dimlos', default: 0.01, min: 0.001, max: 0.1, step: 0.001, description: 'Verhindert Division durch 0 bei I->0.' },
  ],

  // ── SDE mode ──
  sdeConfig: {
    label: 'Stochastische Einkommensschocks',
    description: 'dc = [Euler]dt + sigma_c·c·dW — multiplikative Konsumvolatilitaet',
    sigmaParams: [
      { name: 'sigma_c', label: 'sigma_c (Konsumvol.)', default: 0.0, min: 0, max: 0.3, step: 0.01 },
    ],
  },

  // ── ODE RHS: 2D system {c, c*} ──
  rhs: (t, y, exog, params) => {
    const c = Math.max(y[0], 1e-10);
    const c_star = y[1];
    const r_val = exog.r(t);
    const { gamma, beta_disc, lambda_c } = params;

    // Euler: dc/dt = c·(r-beta)/gamma
    const dcdt = c * (r_val - beta_disc) / gamma;

    // Habit: dc*/dt = lambda_c·(c-c*)
    const dc_star_dt = lambda_c * (c - c_star);

    return [dcdt, dc_star_dt];
  },

  // ── SDE diffusion ──
  diffusion: (t, y, _exog, _params, sigmaParams) => {
    const c = Math.max(y[0], 1e-10);
    return [
      (sigmaParams.sigma_c || 0) * c,
      0, // c* is deterministic
    ];
  },

  // ── Terms: decomposition ──
  terms: [
    {
      name: 'euler_growth',
      label: 'c·(r-beta)/gamma (Euler)',
      color: '#2196F3',
      compute: (t, y, exog, params) => {
        const c = Math.max(y[0], 1e-10);
        return c * (exog.r(t) - params.beta_disc) / params.gamma;
      },
    },
    {
      name: 'habit_drift',
      label: 'lambda_c·(c-c*) (Habit)',
      color: '#F44336',
      compute: (t, y, exog, params) => {
        return params.lambda_c * (Math.max(y[0], 1e-10) - y[1]);
      },
    },
  ],

  // ── Derived outputs ──
  derivedOutputs: [
    {
      name: 'surplus',
      label: 'Surplus c−c*',
      unit: 'Waehrung/a',
      compute: (t, y) => Math.max(y[0], 0) - y[1],
    },
    {
      name: 'growth_rate',
      label: 'cdot/c (%/a)',
      unit: '%/a',
      compute: (t, y, exog, params) => {
        return (exog.r(t) - params.beta_disc) / params.gamma * 100;
      },
    },
    {
      name: 'merton_share',
      label: 'Aktienanteil w* (%)',
      unit: '%',
      compute: (t, y, exog, params) => {
        const mu = exog.mu_stock(t);
        const r_val = exog.r(t);
        return (mu - r_val) / (params.gamma * params.sigma_stock ** 2) * 100;
      },
    },
    {
      name: 'p_eff_ratio',
      label: 'p_eff/p (U.3)',
      unit: 'dimlos',
      compute: (t, y, exog, params) => {
        const I = Math.max(exog.I_info(t), 0);
        return 1 + params.psi_illiq / (I + params.eps_reg);
      },
    },
    {
      name: 'u_crra',
      label: 'Nutzen u(c)',
      unit: 'dimlos',
      compute: (t, y, exog, params) => {
        const c = Math.max(y[0], 1e-10);
        const c_star = y[1];
        const x = Math.max(c - Math.max(c_star, 0), 1e-15);
        const g = params.gamma;
        if (Math.abs(g - 1) < 1e-10) return Math.log(x);
        return (Math.pow(x, 1 - g) - 1) / (1 - g);
      },
    },
  ],

  // ── Presets ──
  presets: [
    {
      name: 'R1 Standard-Euler (r>beta)',
      description: 'r=4%, beta=3%, gamma=2: Konsum waechst stetig mit 0.5%/a.',
      paramOverrides: { gamma: 2.0, beta_disc: 0.03, lambda_c: 0.0, sigma_stock: 0.20, psi_illiq: 0.1, eps_reg: 0.01 },
      stateOverrides: { c: 1.0, c_star: 0.8 },
      exogOverrides: {
        r: { type: 'constant', params: { value: 0.04 } },
        mu_stock: { type: 'constant', params: { value: 0.08 } },
        I_info: { type: 'constant', params: { value: 1.0 } },
      },
    },
    {
      name: 'R2 Ramsey Steady-State (r=beta)',
      description: 'r=beta=4%: Konsum bleibt konstant (V5-Validierung).',
      paramOverrides: { gamma: 2.0, beta_disc: 0.04, lambda_c: 0.0, sigma_stock: 0.20, psi_illiq: 0.1, eps_reg: 0.01 },
      stateOverrides: { c: 1.0, c_star: 0.8 },
      exogOverrides: {
        r: { type: 'constant', params: { value: 0.04 } },
        mu_stock: { type: 'constant', params: { value: 0.08 } },
        I_info: { type: 'constant', params: { value: 1.0 } },
      },
    },
    {
      name: 'R3 Hedonic Treadmill (Habit)',
      description: 'lambda_c=0.2: Referenzpunkt verfolgt Konsum. Surplus konvergiert.',
      paramOverrides: { gamma: 2.0, beta_disc: 0.03, lambda_c: 0.2, sigma_stock: 0.20, psi_illiq: 0.1, eps_reg: 0.01 },
      stateOverrides: { c: 1.0, c_star: 0.8 },
      exogOverrides: {
        r: { type: 'constant', params: { value: 0.05 } },
        mu_stock: { type: 'constant', params: { value: 0.08 } },
        I_info: { type: 'constant', params: { value: 1.0 } },
      },
    },
    {
      name: 'R4 Zinszyklus',
      description: 'Sinusfoermiger Realzins: zeigt Konsumoszillationen und Portfoliowechsel.',
      paramOverrides: { gamma: 2.0, beta_disc: 0.03, lambda_c: 0.1, sigma_stock: 0.20, psi_illiq: 0.1, eps_reg: 0.01 },
      stateOverrides: { c: 1.0, c_star: 0.8 },
      exogOverrides: {
        r: { type: 'sinusoidal', params: { offset: 0.04, amplitude: 0.02, frequency: 0.1, phase: 0 } },
        mu_stock: { type: 'constant', params: { value: 0.08 } },
        I_info: { type: 'constant', params: { value: 1.0 } },
      },
    },
    {
      name: 'R5 Illiquiditaetskrise (I sinkt)',
      description: 'Information faellt: eff. Preis steigt, Nutzen sinkt. Destabilisierungs-Spirale.',
      paramOverrides: { gamma: 2.0, beta_disc: 0.03, lambda_c: 0.1, sigma_stock: 0.20, psi_illiq: 0.5, eps_reg: 0.01 },
      stateOverrides: { c: 1.0, c_star: 0.8 },
      exogOverrides: {
        r: { type: 'constant', params: { value: 0.04 } },
        mu_stock: { type: 'constant', params: { value: 0.08 } },
        I_info: { type: 'ramp', params: { vStart: 2.0, vEnd: 0.05, tStart: 10, tEnd: 60 } },
      },
    },
  ],

  // ── Solver defaults ──
  solverDefaults: {
    tEnd: 100,
    rtol: 1e-8,
    atol: 1e-10,
    maxStep: 0.2,
    nPoints: 500,
    sdeDt: 0.05,
    nPaths: 5,
  },
};

export default S14_U1;
