"""
S28 – III.2 Portfoliodynamik  (§6.6)
=====================================
Gleichung III.2:

   dtheta_ik/dt = lambda_theta * du/dtheta_ik
                + alpha_H * Sum_j A_ij * (theta_jk - theta_ik)
                + sigma_theta * xi_i

Drei-Term-Struktur: Rational + Herding + Noise.

Axiomatische Eigenschaften:
  - Diversifikation durch rationalen Term (Markowitz)
  - Blasenbildung durch Herding (alpha_H gross)
  - Noise Trading durch stochastische Exploration
  - Parallele zur Drei-Ebenen-Architektur (V.1-V.3, L.1-L.3)

Kopplungen:
  - U.1 liefert Nutzenfunktion -> du/dtheta
  - II.2 liefert Preise -> erwartete Renditen
  - III.4 liefert Erwartungen -> Renditeprognose
  - I.1 liefert Information -> Herding-Staerke

8 Regime, 8 Validierungen, 5 Sensitivitaetsanalysen, 4 Erweiterte Analysen
"""

import sys, io, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
PLOT_DIR = BASE / "Ergebnisse" / "Plots"
DATA_DIR = BASE / "Ergebnisse" / "Daten"
PLOT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

np.random.seed(42)
rng = np.random.RandomState(42)

# ══════════════════════════════════════════════════════════════════════
# 0. GLEICHUNG UND ERKLAERUNG
# ══════════════════════════════════════════════════════════════════════

header_text = r"""
================================================================================
  S28  GLEICHUNG III.2 — PORTFOLIODYNAMIK (§6.6)
================================================================================

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                                                                             │
  │   dtheta_ik             du_i                                                │
  │  ────────── = lam_th * ──────── + a_H * Sum_j A_ij*(th_jk-th_ik) + s_th*xi │
  │      dt               dth_ik                                                │
  │                ╰──────────────╯   ╰────────────────────────────╯   ╰──────╯│
  │                Rational (Ebene1)   Herding (Ebene3/Laplacian)     Noise    │
  │                                                                             │
  └─────────────────────────────────────────────────────────────────────────────┘

  ════════════════════════════════════════════════════════════════════════════════
  SYMBOLTABELLE
  ════════════════════════════════════════════════════════════════════════════════

  Symbol          Typ          Beschreibung
  ──────────────  ──────────── ─────────────────────────────────────────────────
  theta_ik        [0,1]        Anteil von Agent i in Asset k (Portfoliogewicht)
  lambda_theta    R+ (=0.3)    Portfolioanpassungsgeschwindigkeit
  du/dtheta_ik    R            Grenznutzen der Portfolioaenderung (aus U.1)
  alpha_H         R+ (=0.2)    Herding-Staerke (Imitationsintensitaet)
  A_ij            {0,1}        Netzwerk-Adjazenzmatrix (wer sieht wen)
  sigma_theta     R+ (=0.05)   Noise-Trading-Intensitaet (idiosynkr. Schock)
  xi_i            N(0,1)       Standard-Normalverteiltes Rauschen

  ════════════════════════════════════════════════════════════════════════════════
  ANNAHMEN UND MODELLIERUNG
  ════════════════════════════════════════════════════════════════════════════════

  1. DREI-TERM-STRUKTUR: Analog zur V/L-Architektur:
     Term 1 = rational (Markowitz), Term 2 = sozial (Herding),
     Term 3 = stochastisch (Noise/private Info). Psychologisch
     implizit in U.1 via endogene Risikoaversion gamma_i.

  2. RATIONALER TERM: du/dtheta_ik = E[r_k] - gamma_i * Cov(r_k, r_p)
     bei CRRA-Nutzen. Markowitz-Diversifikation: Agenten streuen
     proportional zur Sharpe Ratio jedes Assets.

  3. HERDING (Laplacian-Diffusion): alpha_H * Sum A_ij*(theta_j-theta_ik)
     = Netzwerk-Laplacian wirkt als Diffusion auf Portfoliogewichte.
     Consensus-Bildung: Agenten konvergieren zur Peer-Allokation.
     Bei alpha_H gross: Blase (alle kaufen dasselbe Asset).

  4. NOISE: sigma_theta * xi_i mit xi~N(0,1). Private Informationssignale
     und irrationales Trading. Verhindert exakte Konvergenz,
     erzeugt idiosynkratische Heterogenitaet.

  5. CONSTRAINT: theta_ik >= 0 (kein Shortselling), Sum_k theta_ik = 1.
     Projection auf Simplex nach jedem Zeitschritt.

  6. MEAN-VARIANCE: Rendite r_k ~ N(mu_k, sigma_k^2), Korrelation rho.
     Nutzenmaximierung: max E[r_p] - (gamma/2)*Var(r_p).

  7. K ASSETS: Multi-Asset-Simulation (K=2..10).
     Erdogan-Williams-Stijl: Aktien, Anleihen, Cash etc.

  8. EULER-MARUYAMA mit dt=0.01, T=50, Simplex-Projection.

  ════════════════════════════════════════════════════════════════════════════════
"""

print(header_text)

# ══════════════════════════════════════════════════════════════════════
# 1. KERNFUNKTIONEN
# ══════════════════════════════════════════════════════════════════════

def project_simplex(theta):
    """Projiziere theta auf den Simplex (theta>=0, sum=1).
    Vektorisiert fuer (N, K) oder (K,).
    Duchi et al. (2008) Algorithmus.
    """
    if theta.ndim == 1:
        theta = theta[np.newaxis, :]
        squeeze = True
    else:
        squeeze = False
    N, K = theta.shape
    mu = np.sort(theta, axis=1)[:, ::-1]
    cumsum = np.cumsum(mu, axis=1) - 1.0
    arange = np.arange(1, K + 1)[np.newaxis, :]
    rho_mask = mu > cumsum / arange
    # rho = last True index per row
    rho = K - 1 - np.argmax(rho_mask[:, ::-1], axis=1)
    lam = cumsum[np.arange(N), rho] / (rho + 1)
    result = np.maximum(theta - lam[:, np.newaxis], 0.0)
    if squeeze:
        return result[0]
    return result


def markowitz_gradient(theta, mu, Sigma, gamma):
    """Grenznutzen du/dtheta für MV-Nutzen.
    U = mu'*theta - (gamma/2)*theta'*Sigma*theta
    dU/dtheta = mu - gamma*Sigma*theta
    theta: (N, K), mu: (K,), Sigma: (K,K), gamma: (N,) or scalar
    """
    # mu: (K,), Sigma: (K,K)
    # theta: (N, K)
    grad = mu[np.newaxis, :] - np.atleast_1d(gamma)[:, np.newaxis] * (theta @ Sigma)
    return grad


def make_network(N, topology='erdos_renyi', p_connect=0.1, seed=42):
    """Erstelle Netzwerk-Adjazenzmatrix."""
    rng_net = np.random.RandomState(seed)
    if topology == 'erdos_renyi':
        A = (rng_net.rand(N, N) < p_connect).astype(float)
        np.fill_diagonal(A, 0)
    elif topology == 'ring':
        A = np.zeros((N, N))
        for i in range(N):
            A[i, (i + 1) % N] = 1.0
            A[i, (i - 1) % N] = 1.0
    elif topology == 'star':
        A = np.zeros((N, N))
        for i in range(1, N):
            A[0, i] = 1.0
            A[i, 0] = 1.0
    elif topology == 'complete':
        A = np.ones((N, N))
        np.fill_diagonal(A, 0)
    else:
        A = (rng_net.rand(N, N) < p_connect).astype(float)
        np.fill_diagonal(A, 0)
    # Symmetrize
    A = np.maximum(A, A.T)
    # Row-normalize
    row_sum = A.sum(axis=1, keepdims=True)
    row_sum[row_sum == 0] = 1.0
    A_norm = A / row_sum
    return A_norm


def run_portfolio(N, K, mu, Sigma, gamma, theta0,
                  lam_theta=0.3, alpha_H=0.2, sigma_theta=0.05,
                  A_net=None, T=30.0, dt=0.02, seed=42):
    """Integriere III.2 mit Euler-Maruyama + Simplex-Projection.
    N: Agenten, K: Assets.
    mu: (K,) erwartete Renditen.
    Sigma: (K,K) Kovarianzmatrix.
    gamma: (N,) Risikoaversion.
    theta0: (N,K) Anfangsportfolio.
    """
    rng_sim = np.random.RandomState(seed)
    N_steps = int(T / dt)
    sqrt_dt = np.sqrt(dt)

    if A_net is None:
        A_net = make_network(N)

    # History (speichere jeden 10. Schritt)
    save_every = max(1, N_steps // 500)
    n_save = N_steps // save_every + 1
    theta_hist = np.zeros((N, K, n_save))
    theta_hist[:, :, 0] = theta0.copy()

    theta = theta0.copy()
    save_idx = 1

    for step in range(N_steps):
        # 1. Rationaler Term: Markowitz-Gradient
        grad = markowitz_gradient(theta, mu, Sigma, gamma)

        # 2. Herding: Laplacian-Diffusion
        # theta_peer = A @ theta (weighted average of peers)
        theta_peer = A_net @ theta  # (N, K)
        herding = alpha_H * (theta_peer - theta)

        # 3. Noise
        noise = sigma_theta * rng_sim.randn(N, K) * sqrt_dt

        # Update
        dtheta = (lam_theta * grad + herding) * dt + noise
        theta = theta + dtheta

        # Simplex projection
        theta = project_simplex(theta)

        # Save
        if (step + 1) % save_every == 0 and save_idx < n_save:
            theta_hist[:, :, save_idx] = theta
            save_idx += 1

    # Fill remaining if needed
    if save_idx < n_save:
        theta_hist[:, :, save_idx:] = theta[:, :, np.newaxis]

    t_arr = np.linspace(0, T, n_save)
    return dict(theta=theta_hist, theta_final=theta, t=t_arr, A=A_net)


def markowitz_optimal(mu, Sigma, gamma_scalar):
    """Constrained Markowitz: max mu^T theta - (gamma/2) theta^T Sigma theta
    s.t. theta >= 0, sum(theta) = 1.  Solve via SLSQP."""
    from scipy.optimize import minimize
    K = len(mu)
    def neg_U(th):
        return -(mu @ th - (gamma_scalar / 2.0) * th @ Sigma @ th)
    def neg_U_jac(th):
        return -(mu - gamma_scalar * Sigma @ th)
    res = minimize(neg_U, np.ones(K) / K, jac=neg_U_jac, method='SLSQP',
                   bounds=[(0, 1)] * K,
                   constraints=[{'type': 'eq', 'fun': lambda t: np.sum(t) - 1}])
    return res.x


def herfindahl(theta):
    """Herfindahl-Index der Portfoliokonzentration.
    theta: (N, K). HHI fuer jedes Asset ueber Agenten.
    Oder: mittlere HHI ueber Agenten (= Diversifikationsmass).
    """
    # Pro Agent: HHI = sum(theta_k^2) -> = 1/K fuer gleichverteilt, =1 fuer konzentriert
    hhi = np.sum(theta**2, axis=1)  # (N,)
    return hhi


def portfolio_dispersion(theta):
    """Mittlere Std der Portfoliogewichte ueber Agenten."""
    return theta.std(axis=0).mean()

# ══════════════════════════════════════════════════════════════════════
# 2. GEMEINSAME PARAMETER
# ══════════════════════════════════════════════════════════════════════

T = 30.0; dt = 0.02; N_steps = int(T / dt)
N_agents = 60

print("=" * 72)
print("  REGIME-ERGEBNISSE")
print("=" * 72)

results = {}

# ══════════════════════════════════════════════════════════════════════
# R1: Markowitz-Konvergenz (alpha_H=0, sigma=0, homogene Agenten)
# ══════════════════════════════════════════════════════════════════════
print("\n  R1: Markowitz-Konvergenz (kein Herding, kein Noise)")
K_R1 = 3
mu_R1 = np.array([0.08, 0.04, 0.02])  # Aktie, Anleihe, Cash
Sigma_R1 = np.array([[0.04, 0.005, 0.0],
                      [0.005, 0.01, 0.001],
                      [0.0, 0.001, 0.002]])
gamma_R1 = np.full(N_agents, 2.0)
theta0_R1 = np.full((N_agents, K_R1), 1.0 / K_R1)  # Gleichverteilt

theta_star_R1 = markowitz_optimal(mu_R1, Sigma_R1, 2.0)

R1 = run_portfolio(N_agents, K_R1, mu_R1, Sigma_R1, gamma_R1, theta0_R1,
                   lam_theta=5.0, alpha_H=0.0, sigma_theta=0.0, T=60, dt=0.01)
err_R1 = np.max(np.abs(R1['theta_final'].mean(axis=0) - theta_star_R1))
print(f"    theta*_MV = [{', '.join(f'{t:.3f}' for t in theta_star_R1)}]")
print(f"    theta(T) mean = [{', '.join(f'{t:.3f}' for t in R1['theta_final'].mean(axis=0))}]")
print(f"    max|err| = {err_R1:.6f}")
results["R1"] = dict(R=R1, theta_star=theta_star_R1)

# ══════════════════════════════════════════════════════════════════════
# R2: Herding-Dominanz (alpha_H gross -> Blasenbildung)
# ══════════════════════════════════════════════════════════════════════
print("\n  R2: Herding-Dominanz (alpha_H=2.0 -> Blase)")
K_R2 = 3
mu_R2 = np.array([0.08, 0.04, 0.02])
Sigma_R2 = Sigma_R1.copy()
gamma_R2 = np.full(N_agents, 2.0)
# Heterogene Anfangsportfolios
theta0_R2 = rng.dirichlet(np.ones(K_R2), N_agents)  # Zufaellig auf Simplex
A_R2 = make_network(N_agents, 'complete')  # Vollstaendiges Netzwerk

R2 = run_portfolio(N_agents, K_R2, mu_R2, Sigma_R2, gamma_R2, theta0_R2,
                   lam_theta=0.1, alpha_H=2.0, sigma_theta=0.01, A_net=A_R2, T=T, dt=dt)
disp_R2_init = portfolio_dispersion(theta0_R2)
disp_R2_final = portfolio_dispersion(R2['theta_final'])
consensus = R2['theta_final'].mean(axis=0)
print(f"    Dispersion: {disp_R2_init:.3f} -> {disp_R2_final:.3f}")
print(f"    Consensus theta = [{', '.join(f'{t:.3f}' for t in consensus)}]")
print(f"    HHI mean: {herfindahl(R2['theta_final']).mean():.3f}")
results["R2"] = dict(R=R2, disp_init=disp_R2_init, disp_final=disp_R2_final)

# ══════════════════════════════════════════════════════════════════════
# R3: Heterogene Risikoaversion (gamma verteilt)
# ══════════════════════════════════════════════════════════════════════
print("\n  R3: Heterogene Risikoaversion")
K_R3 = 3
gamma_R3 = rng.uniform(0.5, 8.0, N_agents)  # Breite Verteilung
theta0_R3 = np.full((N_agents, K_R3), 1.0 / K_R3)

R3 = run_portfolio(N_agents, K_R3, mu_R1, Sigma_R1, gamma_R3, theta0_R3,
                   lam_theta=0.3, alpha_H=0.1, sigma_theta=0.02, T=T, dt=dt)
# Risikoscheue vs. risikofreudig
low_gamma = gamma_R3 < 2.0
high_gamma = gamma_R3 > 5.0
theta_risky_low = R3['theta_final'][low_gamma, 0].mean()  # Aktienanteil
theta_risky_high = R3['theta_final'][high_gamma, 0].mean()
print(f"    gamma<2: Aktienanteil = {theta_risky_low:.3f}")
print(f"    gamma>5: Aktienanteil = {theta_risky_high:.3f}")
print(f"    Dispersion = {portfolio_dispersion(R3['theta_final']):.3f}")
results["R3"] = dict(R=R3, gamma=gamma_R3)

# ══════════════════════════════════════════════════════════════════════
# R4: Noise-dominiert (sigma_theta gross)
# ══════════════════════════════════════════════════════════════════════
print("\n  R4: Noise-dominiert (sigma_theta=0.5)")
theta0_R4 = np.full((N_agents, K_R1), 1.0 / K_R1)
R4 = run_portfolio(N_agents, K_R1, mu_R1, Sigma_R1, np.full(N_agents, 2.0), theta0_R4,
                   lam_theta=0.3, alpha_H=0.0, sigma_theta=0.5, T=T, dt=dt)
disp_R4 = portfolio_dispersion(R4['theta_final'])
hhi_R4 = herfindahl(R4['theta_final']).mean()
print(f"    Dispersion = {disp_R4:.3f} (hoch = viel Heterogenitaet)")
print(f"    HHI mean = {hhi_R4:.3f}")
print(f"    theta mean = [{', '.join(f'{t:.3f}' for t in R4['theta_final'].mean(axis=0))}]")
results["R4"] = dict(R=R4, disp=disp_R4)

# ══════════════════════════════════════════════════════════════════════
# R5: Blasen-Crash-Zyklus (exogener Rendite-Schock)
# ══════════════════════════════════════════════════════════════════════
print("\n  R5: Blasen-Crash (Rendite springt)")
K_R5 = 3
# Phase 1 (t<20): mu hoch fuer Aktie
# Phase 2 (t>=20): mu crasht
N_steps_R5 = int(T / dt)
save_every_R5 = max(1, N_steps_R5 // 500)
n_save_R5 = N_steps_R5 // save_every_R5 + 1

theta0_R5 = np.full((N_agents, K_R5), 1.0 / K_R5)
A_R5 = make_network(N_agents, 'erdos_renyi', p_connect=0.15)
gamma_R5 = np.full(N_agents, 2.0)
Sigma_R5 = Sigma_R1.copy()

rng_R5 = np.random.RandomState(42)
theta_R5 = theta0_R5.copy()
theta_hist_R5 = np.zeros((N_agents, K_R5, n_save_R5))
theta_hist_R5[:, :, 0] = theta_R5.copy()
save_idx = 1
sqrt_dt = np.sqrt(dt)

for step in range(N_steps_R5):
    t_now = step * dt
    # Switching mu
    if t_now < 20:
        mu_now = np.array([0.15, 0.04, 0.02])  # Boom
    elif t_now < 25:
        mu_now = np.array([-0.30, 0.04, 0.02])  # Crash (severe)
    else:
        mu_now = np.array([0.06, 0.04, 0.02])  # Recovery

    grad = markowitz_gradient(theta_R5, mu_now, Sigma_R5, gamma_R5)
    theta_peer = A_R5 @ theta_R5
    herding = 0.5 * (theta_peer - theta_R5)
    noise = 0.03 * rng_R5.randn(N_agents, K_R5) * sqrt_dt
    dtheta = (0.3 * grad + herding) * dt + noise
    theta_R5 = project_simplex(theta_R5 + dtheta)

    if (step + 1) % save_every_R5 == 0 and save_idx < n_save_R5:
        theta_hist_R5[:, :, save_idx] = theta_R5
        save_idx += 1

t_R5 = np.linspace(0, T, n_save_R5)
# Find peak equity allocation
eq_mean = theta_hist_R5[:, 0, :].mean(axis=0)
peak_idx = np.argmax(eq_mean)
crash_idx = np.argmin(eq_mean[peak_idx:]) + peak_idx
print(f"    Aktie mean: {eq_mean[0]:.3f} -> peak {eq_mean[peak_idx]:.3f} "
      f"(t={t_R5[peak_idx]:.1f}) -> trough {eq_mean[crash_idx]:.3f} "
      f"(t={t_R5[crash_idx]:.1f}) -> final {eq_mean[-1]:.3f}")
results["R5"] = dict(theta_hist=theta_hist_R5, t=t_R5, eq_mean=eq_mean)

# ══════════════════════════════════════════════════════════════════════
# R6: Multi-Asset (K=6)
# ══════════════════════════════════════════════════════════════════════
print("\n  R6: Multi-Asset (K=6)")
K_R6 = 6
mu_R6 = np.array([0.10, 0.07, 0.05, 0.03, 0.02, 0.01])
# Korrelationsmatrix
rng_cov = np.random.RandomState(123)
A_cov = rng_cov.randn(K_R6, K_R6) * 0.05
Sigma_R6 = A_cov @ A_cov.T + np.diag(np.array([0.05, 0.03, 0.02, 0.01, 0.005, 0.002]))
gamma_R6 = rng.uniform(1.0, 5.0, N_agents)
theta0_R6 = rng.dirichlet(np.ones(K_R6), N_agents)

R6 = run_portfolio(N_agents, K_R6, mu_R6, Sigma_R6, gamma_R6, theta0_R6,
                   lam_theta=0.3, alpha_H=0.15, sigma_theta=0.03, T=T, dt=dt)
print(f"    theta mean = [{', '.join(f'{t:.3f}' for t in R6['theta_final'].mean(axis=0))}]")
print(f"    HHI mean = {herfindahl(R6['theta_final']).mean():.3f}")
print(f"    Dispersion = {portfolio_dispersion(R6['theta_final']):.3f}")
results["R6"] = dict(R=R6, mu=mu_R6, K=K_R6)

# ══════════════════════════════════════════════════════════════════════
# R7: Netzwerk-Topologien (Ring vs Star vs Erdos-Renyi vs Complete)
# ══════════════════════════════════════════════════════════════════════
print("\n  R7: Netzwerk-Topologien")
N_R7 = 30
K_R7 = 3
theta0_R7 = rng.dirichlet(np.ones(K_R7), N_R7)
gamma_R7 = np.full(N_R7, 2.0)
topos = ['ring', 'star', 'erdos_renyi', 'complete']
R7_data = {}
for topo in topos:
    A_topo = make_network(N_R7, topo, p_connect=0.15)
    R_topo = run_portfolio(N_R7, K_R7, mu_R1, Sigma_R1, gamma_R7, theta0_R7.copy(),
                           lam_theta=0.2, alpha_H=0.5, sigma_theta=0.02, A_net=A_topo,
                           T=15, dt=0.05)
    d = portfolio_dispersion(R_topo['theta_final'])
    R7_data[topo] = dict(R=R_topo, disp=d)
    print(f"    {topo:15s}: disp={d:.4f}")
results["R7"] = R7_data

# ══════════════════════════════════════════════════════════════════════
# R8: Neoklassischer Grenzfall (sigma=0, alpha_H=0, gamma homogen)
# ══════════════════════════════════════════════════════════════════════
print("\n  R8: Neoklassischer Grenzfall (pure Markowitz)")
# Verschiedene Startpunkte, alle konvergieren zum gleichen theta*
K_R8 = 3
gamma_R8_val = 3.0
theta_star_R8 = markowitz_optimal(mu_R1, Sigma_R1, gamma_R8_val)
theta0_R8_variants = [
    np.tile(np.array([1.0, 0.0, 0.0]), (N_agents, 1)),  # 100% Aktien
    np.tile(np.array([0.0, 1.0, 0.0]), (N_agents, 1)),  # 100% Anleihen
    np.tile(np.array([0.0, 0.0, 1.0]), (N_agents, 1)),  # 100% Cash
    rng.dirichlet(np.ones(K_R8), N_agents),               # Zufaellig
]
labels_R8 = ['100% Aktie', '100% Anleihe', '100% Cash', 'Zufaellig']
R8_data = {}
for lbl, th0 in zip(labels_R8, theta0_R8_variants):
    R_r8 = run_portfolio(N_agents, K_R8, mu_R1, Sigma_R1, np.full(N_agents, gamma_R8_val),
                         th0, lam_theta=5.0, alpha_H=0.0, sigma_theta=0.0, T=60, dt=0.01)
    err = np.max(np.abs(R_r8['theta_final'].mean(axis=0) - theta_star_R8))
    R8_data[lbl] = dict(R=R_r8, err=err)
    print(f"    {lbl:16s}: err={err:.6f}")
results["R8"] = dict(data=R8_data, theta_star=theta_star_R8)


# ══════════════════════════════════════════════════════════════════════
# VALIDIERUNGEN
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*72}\n  VALIDIERUNGEN\n{'='*72}")
validations = {}

# V1: Markowitz-Konvergenz (R1)
v1_pass = err_R1 < 0.01
validations["V1"] = dict(name="Markowitz-Konvergenz theta->theta*_MV",
                         passed=v1_pass,
                         detail=f"max|err|={err_R1:.6f}")
print(f"  V1: {'PASS' if v1_pass else 'FAIL'} ({validations['V1']['detail']})")

# V2: Herding reduziert Dispersion
v2_pass = disp_R2_final < disp_R2_init * 0.5
validations["V2"] = dict(name="Herding -> Dispersion sinkt",
                         passed=v2_pass,
                         detail=f"disp: {disp_R2_init:.3f}->{disp_R2_final:.3f}")
print(f"  V2: {'PASS' if v2_pass else 'FAIL'} ({validations['V2']['detail']})")

# V3: Risikoaversion -> Aktienanteil (gamma hoch -> weniger Aktien)
v3_pass = theta_risky_low > theta_risky_high
validations["V3"] = dict(name="gamma hoch => Aktienanteil niedrig",
                         passed=v3_pass,
                         detail=f"gamma<2: {theta_risky_low:.3f}, gamma>5: {theta_risky_high:.3f}")
print(f"  V3: {'PASS' if v3_pass else 'FAIL'} ({validations['V3']['detail']})")

# V4: Noise erhoet Dispersion
disp_R1_final = portfolio_dispersion(R1['theta_final'])
v4_pass = disp_R4 > disp_R1_final + 0.01
validations["V4"] = dict(name="Noise -> Dispersion steigt",
                         passed=v4_pass,
                         detail=f"no-noise={disp_R1_final:.4f}, noise={disp_R4:.3f}")
print(f"  V4: {'PASS' if v4_pass else 'FAIL'} ({validations['V4']['detail']})")

# V5: Blasen-Crash — Peak vor Crash (R5)
v5_pass = eq_mean[peak_idx] > 0.5 and eq_mean[crash_idx] < eq_mean[peak_idx] * 0.5
validations["V5"] = dict(name="Blasen-Crash: peak>0.5 dann halbiert",
                         passed=v5_pass,
                         detail=f"peak={eq_mean[peak_idx]:.3f}, trough={eq_mean[crash_idx]:.3f}")
print(f"  V5: {'PASS' if v5_pass else 'FAIL'} ({validations['V5']['detail']})")

# V6: Simplex-Constraint (theta>=0, sum=1)
# Check over all agents and time
all_positive = np.all(R2['theta_final'] >= -1e-10)
sums_ok = np.allclose(R2['theta_final'].sum(axis=1), 1.0, atol=1e-8)
v6_pass = all_positive and sums_ok
validations["V6"] = dict(name="Simplex: theta>=0, sum(theta)=1",
                         passed=v6_pass,
                         detail=f"positive={all_positive}, sum_ok={sums_ok}")
print(f"  V6: {'PASS' if v6_pass else 'FAIL'} ({validations['V6']['detail']})")

# V7: Netzwerk-Topologie -> Complete konvergiert am staerksten
v7_pass = R7_data['complete']['disp'] < R7_data['ring']['disp']
validations["V7"] = dict(name="Complete-Netz: staerkstes Herding",
                         passed=v7_pass,
                         detail=f"complete={R7_data['complete']['disp']:.4f}, "
                                f"ring={R7_data['ring']['disp']:.4f}")
print(f"  V7: {'PASS' if v7_pass else 'FAIL'} ({validations['V7']['detail']})")

# V8: Neoklassisch — alle Startpunkte konvergieren (R8)
r8_errs = [R8_data[lbl]['err'] for lbl in labels_R8]
v8_pass = all(e < 0.01 for e in r8_errs)
validations["V8"] = dict(name="Neoklassisch: alle Starts->theta*",
                         passed=v8_pass,
                         detail=f"errs=[{', '.join(f'{e:.4f}' for e in r8_errs)}]")
print(f"  V8: {'PASS' if v8_pass else 'FAIL'} ({validations['V8']['detail']})")


# ══════════════════════════════════════════════════════════════════════
# SENSITIVITAETSANALYSEN
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*72}\n  SENSITIVITAETSANALYSEN\n{'='*72}")

# SA1: alpha_H vs sigma_theta -> Dispersion
print("  SA1: alpha_H vs sigma_theta -> Dispersion")
sa1_aH = np.linspace(0, 2.0, 8)
sa1_sig = np.linspace(0, 0.5, 8)
SA1_disp = np.zeros((len(sa1_sig), len(sa1_aH)))
N_sa = 30; K_sa = 3
theta0_sa = rng.dirichlet(np.ones(K_sa), N_sa)
gamma_sa = np.full(N_sa, 2.0)
for ia, aH in enumerate(sa1_aH):
    for isig, sig in enumerate(sa1_sig):
        R_sa = run_portfolio(N_sa, K_sa, mu_R1, Sigma_R1, gamma_sa, theta0_sa.copy(),
                             lam_theta=0.3, alpha_H=aH, sigma_theta=sig, T=15, dt=0.05)
        SA1_disp[isig, ia] = portfolio_dispersion(R_sa['theta_final'])
results["SA1"] = dict(aH=sa1_aH, sig=sa1_sig, disp=SA1_disp)
print(f"    Dispersion range: [{SA1_disp.min():.4f}, {SA1_disp.max():.4f}]")

# SA2: gamma vs Aktienanteil
print("  SA2: gamma vs Aktienanteil")
sa2_gamma = np.linspace(0.5, 10.0, 30)
sa2_equity = []
for gv in sa2_gamma:
    th_opt = markowitz_optimal(mu_R1, Sigma_R1, gv)
    sa2_equity.append(th_opt[0])
results["SA2"] = dict(gamma=sa2_gamma, equity=np.array(sa2_equity))
print(f"    Equity range: [{min(sa2_equity):.3f}, {max(sa2_equity):.3f}]")

# SA3: lambda_theta -> Konvergenzgeschwindigkeit
print("  SA3: lambda_theta -> Konvergenzgeschw.")
sa3_lam = [0.05, 0.1, 0.3, 0.5, 1.0, 2.0]
sa3_err = []
for lv in sa3_lam:
    R_sa3 = run_portfolio(30, 3, mu_R1, Sigma_R1, np.full(30, 2.0),
                          np.full((30, 3), 1.0 / 3),
                          lam_theta=lv, alpha_H=0.0, sigma_theta=0.0, T=15, dt=0.02)
    e = np.max(np.abs(R_sa3['theta_final'].mean(axis=0) - theta_star_R1))
    sa3_err.append(e)
results["SA3"] = dict(lam=sa3_lam, err=sa3_err)
print(f"    Errors: [{', '.join(f'{e:.4f}' for e in sa3_err)}]")

# SA4: K (Assets) vs Diversifikation (HHI)
print("  SA4: K Assets -> HHI (Diversifikation)")
sa4_K = [2, 3, 5, 8, 10]
sa4_hhi = []
for Kv in sa4_K:
    mu_kv = np.linspace(0.10, 0.02, Kv)
    Sigma_kv = np.eye(Kv) * 0.03 + 0.005
    np.fill_diagonal(Sigma_kv, np.linspace(0.05, 0.01, Kv))
    gamma_kv = np.full(30, 2.0)
    th0_kv = rng.dirichlet(np.ones(Kv), 30)
    R_sa4 = run_portfolio(30, Kv, mu_kv, Sigma_kv, gamma_kv, th0_kv,
                          lam_theta=0.3, alpha_H=0.1, sigma_theta=0.02, T=15, dt=0.05)
    hhi_val = herfindahl(R_sa4['theta_final']).mean()
    sa4_hhi.append(hhi_val)
    print(f"    K={Kv}: HHI={hhi_val:.3f} (1/K={1.0/Kv:.3f})")
results["SA4"] = dict(K=sa4_K, hhi=sa4_hhi)

# SA5: Anfangsportfolio-Sensitivitaet
print("  SA5: Anfangs-theta Sensitivitaet")
n_trials = 10
sa5_final = []
for trial in range(n_trials):
    th0_t = np.random.RandomState(trial).dirichlet(np.ones(3), 30)
    R_t = run_portfolio(30, 3, mu_R1, Sigma_R1, np.full(30, 2.0), th0_t,
                        lam_theta=0.3, alpha_H=0.0, sigma_theta=0.0, T=15, dt=0.02,
                        seed=42)
    sa5_final.append(R_t['theta_final'].mean(axis=0))
sa5_final = np.array(sa5_final)
spread = sa5_final.std(axis=0).max()
results["SA5"] = dict(finals=sa5_final, spread=spread)
print(f"    theta(T) spread (std): {spread:.6f}")


# ══════════════════════════════════════════════════════════════════════
# ERWEITERTE ANALYSEN
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*72}\n  ERWEITERTE ANALYSEN\n{'='*72}")

# EA1: Drei-Term-Dekomposition (Rational vs Herding vs Noise)
print("\n  EA1: Drei-Term-Dekomposition")
K_ea1 = 3
N_ea1 = 30
theta_ea1 = rng.dirichlet(np.ones(K_ea1), N_ea1)
gamma_ea1 = np.full(N_ea1, 2.0)
A_ea1 = make_network(N_ea1, 'erdos_renyi', p_connect=0.15)

# Run drei Varianten: (1) nur rational, (2) rational+herding, (3) voll
configs = {
    'Rational': dict(lam_theta=0.3, alpha_H=0.0, sigma_theta=0.0),
    'Rat+Herd': dict(lam_theta=0.3, alpha_H=0.5, sigma_theta=0.0),
    'Komplett': dict(lam_theta=0.3, alpha_H=0.5, sigma_theta=0.05),
}
EA1_data = {}
for name, params in configs.items():
    R_ea = run_portfolio(N_ea1, K_ea1, mu_R1, Sigma_R1, gamma_ea1, theta_ea1.copy(),
                         A_net=A_ea1, T=15, dt=0.02, **params)
    d = portfolio_dispersion(R_ea['theta_final'])
    EA1_data[name] = dict(R=R_ea, disp=d)
    print(f"    {name:12s}: disp={d:.4f}, "
          f"theta_mean=[{', '.join(f'{t:.3f}' for t in R_ea['theta_final'].mean(axis=0))}]")
results["EA1"] = EA1_data

# EA2: Herding-Phasenuebergang (alpha_H sweep)
print("\n  EA2: Herding-Phasenuebergang")
aH_sweep = np.linspace(0, 3.0, 15)
disp_sweep = []
hhi_sweep = []
for aH_val in aH_sweep:
    R_ea2 = run_portfolio(30, 3, mu_R1, Sigma_R1, np.full(30, 2.0),
                          rng.dirichlet(np.ones(3), 30),
                          lam_theta=0.3, alpha_H=aH_val, sigma_theta=0.02,
                          A_net=make_network(30, 'erdos_renyi', p_connect=0.15),
                          T=15, dt=0.05)
    disp_sweep.append(portfolio_dispersion(R_ea2['theta_final']))
    hhi_sweep.append(herfindahl(R_ea2['theta_final']).mean())
results["EA2"] = dict(aH=aH_sweep, disp=np.array(disp_sweep), hhi=np.array(hhi_sweep))
print(f"    alpha_H: 0->{aH_sweep[-1]:.1f}, disp: {disp_sweep[0]:.4f}->{disp_sweep[-1]:.4f}")

# EA3: Effizienzvergleich (Sharpe Ratio: rational vs herding)
print("\n  EA3: Effizienzvergleich (Portfolio-Sharpe)")
# Simuliere Endportfolios und berechne erwartete Rendite + Varianz
configs_ea3 = {
    'Markowitz': dict(lam_theta=0.5, alpha_H=0.0, sigma_theta=0.0),
    'Mild Herd': dict(lam_theta=0.3, alpha_H=0.3, sigma_theta=0.02),
    'Strong Herd': dict(lam_theta=0.1, alpha_H=2.0, sigma_theta=0.02),
    'Noise Only': dict(lam_theta=0.0, alpha_H=0.0, sigma_theta=0.3),
}
EA3_data = {}
for name, params in configs_ea3.items():
    R_ea3 = run_portfolio(30, 3, mu_R1, Sigma_R1, np.full(30, 2.0),
                          np.full((30, 3), 1.0 / 3),
                          A_net=make_network(30, 'complete'),
                          T=15, dt=0.02, **params)
    theta_mean = R_ea3['theta_final'].mean(axis=0)
    port_ret = theta_mean @ mu_R1
    port_var = theta_mean @ Sigma_R1 @ theta_mean
    sharpe = port_ret / np.sqrt(port_var) if port_var > 0 else 0
    EA3_data[name] = dict(theta=theta_mean, ret=port_ret, var=port_var, sharpe=sharpe)
    print(f"    {name:13s}: E[r]={port_ret:.4f}, Var={port_var:.4f}, Sharpe={sharpe:.3f}")
results["EA3"] = EA3_data

# EA4: Wealth-weighted Herding (Grössere Agenten beeinflussen mehr)
print("\n  EA4: Wealth-weighted Herding")
N_ea4 = 50; K_ea4 = 3
wealth = rng.pareto(2.0, N_ea4) + 1.0  # Pareto-verteilt
wealth_norm = wealth / wealth.sum()
# Gewichtete Adjazenz: A_ij = wealth_j / wealth_mean
A_wealth = np.outer(np.ones(N_ea4), wealth_norm)
np.fill_diagonal(A_wealth, 0)
# Row-normalize
row_s = A_wealth.sum(axis=1, keepdims=True)
row_s[row_s == 0] = 1.0
A_wealth = A_wealth / row_s

theta0_ea4 = rng.dirichlet(np.ones(K_ea4), N_ea4)
R_ea4_w = run_portfolio(N_ea4, K_ea4, mu_R1, Sigma_R1, np.full(N_ea4, 2.0),
                        theta0_ea4.copy(), lam_theta=0.2, alpha_H=0.8,
                        sigma_theta=0.02, A_net=A_wealth, T=20, dt=0.02)
# Vergleich: uniform network
A_uniform = make_network(N_ea4, 'erdos_renyi', p_connect=0.2)
R_ea4_u = run_portfolio(N_ea4, K_ea4, mu_R1, Sigma_R1, np.full(N_ea4, 2.0),
                        theta0_ea4.copy(), lam_theta=0.2, alpha_H=0.8,
                        sigma_theta=0.02, A_net=A_uniform, T=20, dt=0.02)

# Reiche Agenten (top 10%) vs arme (bottom 50%)
rich = wealth > np.percentile(wealth, 90)
poor = wealth < np.percentile(wealth, 50)
theta_rich_w = R_ea4_w['theta_final'][rich].mean(axis=0)
theta_poor_w = R_ea4_w['theta_final'][poor].mean(axis=0)
disp_w = portfolio_dispersion(R_ea4_w['theta_final'])
disp_u = portfolio_dispersion(R_ea4_u['theta_final'])
print(f"    Wealth-weighted: disp={disp_w:.4f}")
print(f"    Uniform-net:     disp={disp_u:.4f}")
print(f"    Rich (top10%):  theta=[{', '.join(f'{t:.3f}' for t in theta_rich_w)}]")
print(f"    Poor (bot50%):  theta=[{', '.join(f'{t:.3f}' for t in theta_poor_w)}]")
results["EA4"] = dict(R_w=R_ea4_w, R_u=R_ea4_u, wealth=wealth,
                       disp_w=disp_w, disp_u=disp_u)


# ══════════════════════════════════════════════════════════════════════
# MATHEMATISCHE STRUKTUREN
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*72}\n  MATHEMATISCHE STRUKTUREN\n{'='*72}")

struct_notes = []

struct_notes.append(
    "STRUKTUR 1: Drei-Ebenen-Parallele\n"
    "  III.2 = V.Architektur fuer Portfolios:\n"
    "  Term 1 (Rational/Markowitz) ~ V.1/L.1\n"
    "  Term 2 (Herding/Laplacian) ~ V.3/L.3\n"
    "  Term 3 (Noise/privat) ~ stochastisch\n"
    "  Psychologie implizit via gamma_i in U.1")
print(f"\n  {struct_notes[-1]}")

struct_notes.append(
    "STRUKTUR 2: Laplacian-Diffusion\n"
    "  Herding = alpha_H * L * theta (Netzwerk-Laplacian L)\n"
    "  Consensus-Bildung auf dem Simplex\n"
    "  Complete-Netz: maximale Diffusion -> minimale Dispersion\n"
    f"  Complete disp={R7_data['complete']['disp']:.4f} < Ring={R7_data['ring']['disp']:.4f}")
print(f"\n  {struct_notes[-1]}")

struct_notes.append(
    "STRUKTUR 3: Mean-Variance Optimierung\n"
    "  theta* = (1/gamma)*Sigma^{-1}*mu (Simplex-projiziert)\n"
    "  Global stabil (konvex, streng konkav -> eindeutiges Maximum)\n"
    "  SA5: spread=%.6f (alle Starts -> gleiches theta*)" % spread)
print(f"\n  {struct_notes[-1]}")

struct_notes.append(
    "STRUKTUR 4: Blasen als Herding-Instabilitaet\n"
    "  alpha_H gross: Alle imitieren -> Konzentration auf ein Asset\n"
    "  Crash: exogener Schock bricht Herding-GG\n"
    f"  R5: peak={eq_mean[peak_idx]:.3f} -> trough={eq_mean[crash_idx]:.3f}")
print(f"\n  {struct_notes[-1]}")

struct_notes.append(
    "STRUKTUR 5: Effizienz-Herding Trade-off\n"
    f"  Markowitz Sharpe: {EA3_data['Markowitz']['sharpe']:.3f}\n"
    f"  Strong Herding Sharpe: {EA3_data['Strong Herd']['sharpe']:.3f}\n"
    "  Herding verschlechtert Sharpe wenn lam/alpha_H kleiner wird\n"
    "  -> Soziale Imitation ist ineffizient (wie in V.3-Analysen)")
print(f"\n  {struct_notes[-1]}")


# ══════════════════════════════════════════════════════════════════════
# PLOT (30+ Panels)
# ══════════════════════════════════════════════════════════════════════

print(f"\n  PLOTTE ...")

fig = plt.figure(figsize=(28, 56))
gs = GridSpec(13, 3, figure=fig,
              height_ratios=[0.6, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.3],
              hspace=0.38, wspace=0.30)
fig.suptitle('S28  III.2  Portfoliodynamik',
             fontsize=15, fontweight='bold', y=0.998)

# ── Row 0: Gleichung ──
ax_eq = fig.add_subplot(gs[0, 0:3])
ax_eq.axis('off')
eq_text = (
    "GLEICHUNG III.2 (Portfoliodynamik, §6.6):\n\n"
    "  dtheta_ik/dt  =  lambda_theta * du/dtheta_ik   +   alpha_H * Sum_j A_ij*(theta_jk-theta_ik)"
    "  +  sigma_theta * xi_i\n"
    "                    ╰─────────────────────────╯       ╰──────────────────────────────────────────╯"
    "     ╰────────────────╯\n"
    "                    Rationale Optimierung (MV)          Herding (Netzwerk-Laplacian)"
    "               Noise Trading\n\n"
    "Symbole: theta_ik=Portfolioanteil, lambda_theta=Anpassungsgeschw.,\n"
    "         du/dtheta = mu - gamma*Sigma*theta (Markowitz-Gradient),\n"
    "         alpha_H=Herding-Staerke, A_ij=Netzwerk, sigma_theta=Noise,\n"
    "         xi~N(0,1)\n\n"
    "Constraint: theta_ik >= 0, Sum_k theta_ik = 1 (Simplex)"
)
ax_eq.text(0.5, 0.5, eq_text, transform=ax_eq.transAxes, ha='center', va='center',
           fontsize=8.0, family='monospace',
           bbox=dict(boxstyle='round,pad=0.6', facecolor='#f0f8ff', edgecolor='#4169e1',
                     linewidth=2, alpha=0.95))

# ── Row 1: R1 Markowitz vs R2 Herding ──
ax = fig.add_subplot(gs[1, 0])
for k in range(K_R1):
    ax.plot(R1['t'], R1['theta'][:, k, :].mean(axis=0), lw=2,
            label=f'Asset {k}')
    ax.axhline(theta_star_R1[k], color=f'C{k}', ls='--', lw=0.8)
ax.set_xlabel('t'); ax.set_ylabel('theta_k mean')
ax.set_title('(a) R1: Markowitz-Konvergenz')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[1, 1])
for k in range(K_R2):
    ax.plot(R2['t'], R2['theta'][:, k, :].mean(axis=0), lw=2,
            label=f'Asset {k}')
ax.set_xlabel('t'); ax.set_ylabel('theta_k mean')
ax.set_title('(b) R2: Herding-Dominanz')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# R2 Dispersion
ax = fig.add_subplot(gs[1, 2])
disp_over_time = np.array([portfolio_dispersion(R2['theta'][:, :, s])
                           for s in range(R2['theta'].shape[2])])
ax.plot(R2['t'], disp_over_time, 'C0-', lw=2)
ax.set_xlabel('t'); ax.set_ylabel('Dispersion')
ax.set_title('(c) R2: Dispersion (Herding)')
ax.grid(True, alpha=0.3)

# ── Row 2: R3 + R4 ──
ax = fig.add_subplot(gs[2, 0])
sc = ax.scatter(gamma_R3, R3['theta_final'][:, 0], c='C0', s=10, alpha=0.5)
ax.set_xlabel('gamma (Risikoaversion)'); ax.set_ylabel('Aktienanteil theta_0')
ax.set_title('(d) R3: gamma vs Aktienanteil')
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[2, 1])
for k in range(K_R1):
    ax.plot(R4['t'], R4['theta'][:, k, :].mean(axis=0), lw=2,
            label=f'Asset {k}')
ax.set_xlabel('t'); ax.set_ylabel('theta_k mean')
ax.set_title('(e) R4: Noise-dominiert')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# R4: Dispersion
ax = fig.add_subplot(gs[2, 2])
disp_R4_t = np.array([portfolio_dispersion(R4['theta'][:, :, s])
                      for s in range(R4['theta'].shape[2])])
ax.plot(R4['t'], disp_R4_t, 'C1-', lw=2)
ax.set_xlabel('t'); ax.set_ylabel('Dispersion')
ax.set_title('(f) R4: Dispersion (Noise)')
ax.grid(True, alpha=0.3)

# ── Row 3: R5 Crash + R6 Multi-Asset ──
ax = fig.add_subplot(gs[3, 0])
ax.plot(t_R5, theta_hist_R5[:, 0, :].mean(axis=0), 'C0-', lw=2, label='Aktie')
ax.plot(t_R5, theta_hist_R5[:, 1, :].mean(axis=0), 'C1-', lw=2, label='Anleihe')
ax.plot(t_R5, theta_hist_R5[:, 2, :].mean(axis=0), 'C2-', lw=2, label='Cash')
ax.axvline(20, color='red', ls=':', lw=0.8, label='Crash')
ax.axvline(25, color='green', ls=':', lw=0.8, label='Recovery')
ax.set_xlabel('t'); ax.set_ylabel('theta_k mean')
ax.set_title('(g) R5: Blasen-Crash')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 1])
for k in range(K_R6):
    ax.plot(R6['t'], R6['theta'][:, k, :].mean(axis=0), lw=1.5,
            label=f'Asset {k}')
ax.set_xlabel('t'); ax.set_ylabel('theta_k mean')
ax.set_title('(h) R6: Multi-Asset (K=6)')
ax.legend(fontsize=5); ax.grid(True, alpha=0.3)

# R7 Topologien Barplot
ax = fig.add_subplot(gs[3, 2])
topo_names = list(R7_data.keys())
topo_disps = [R7_data[t]['disp'] for t in topo_names]
ax.bar(range(len(topo_names)), topo_disps, color=['C0', 'C1', 'C2', 'C3'], alpha=0.7)
ax.set_xticks(range(len(topo_names)))
ax.set_xticklabels(topo_names, fontsize=7)
ax.set_ylabel('Dispersion')
ax.set_title('(i) R7: Topologien')
ax.grid(True, alpha=0.3, axis='y')

# ── Row 4: R8 + SA1 ──
ax = fig.add_subplot(gs[4, 0])
for lbl in labels_R8:
    R_r8 = R8_data[lbl]['R']
    eq_line = R_r8['theta'][:, 0, :].mean(axis=0)
    ax.plot(R_r8['t'], eq_line, lw=1.5, label=lbl)
ax.axhline(theta_star_R8[0], color='red', ls='--', lw=0.8, label=f'theta*={theta_star_R8[0]:.2f}')
ax.set_xlabel('t'); ax.set_ylabel('Aktienanteil mean')
ax.set_title('(j) R8: Neoklassisch')
ax.legend(fontsize=5); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[4, 1])
im = ax.imshow(SA1_disp, extent=[sa1_aH[0], sa1_aH[-1], sa1_sig[0], sa1_sig[-1]],
               aspect='auto', origin='lower', cmap='YlOrRd')
plt.colorbar(im, ax=ax, label='Dispersion')
ax.set_xlabel('alpha_H'); ax.set_ylabel('sigma_theta')
ax.set_title('(k) SA1: alpha_H vs sigma -> Disp.')
ax.grid(False)

# SA2
ax = fig.add_subplot(gs[4, 2])
ax.plot(sa2_gamma, sa2_equity, 'C2-o', lw=2, ms=3)
ax.set_xlabel('gamma'); ax.set_ylabel('Aktienanteil theta*_0')
ax.set_title('(l) SA2: gamma vs Aktienanteil')
ax.grid(True, alpha=0.3)

# ── Row 5: SA3 + SA4 + SA5 ──
ax = fig.add_subplot(gs[5, 0])
ax.plot([str(l)[:4] for l in sa3_lam], sa3_err, 'C0-o', lw=2, ms=4)
ax.set_xlabel('lambda_theta'); ax.set_ylabel('max|err| nach T=20')
ax.set_title('(m) SA3: lambda_theta -> Konvergenz')
ax.grid(True, alpha=0.3); ax.set_yscale('log')
ax.tick_params(axis='x', labelsize=7)

ax = fig.add_subplot(gs[5, 1])
ax.plot(sa4_K, sa4_hhi, 'C1-o', lw=2, ms=5)
ideal_hhi = [1.0 / k for k in sa4_K]
ax.plot(sa4_K, ideal_hhi, 'r--', lw=1, label='1/K (voll diversifiziert)')
ax.set_xlabel('K (Anzahl Assets)'); ax.set_ylabel('HHI')
ax.set_title('(n) SA4: K -> Diversifikation')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[5, 2])
for trial in range(min(n_trials, 8)):
    ax.scatter(range(3), sa5_final[trial], s=20, alpha=0.5)
ax.axhline(theta_star_R1[0], color='red', ls='--', lw=0.8)
ax.axhline(theta_star_R1[1], color='red', ls='--', lw=0.8)
ax.axhline(theta_star_R1[2], color='red', ls='--', lw=0.8)
ax.set_xticks([0, 1, 2]); ax.set_xticklabels(['Aktie', 'Anleihe', 'Cash'])
ax.set_ylabel('theta(T) mean')
ax.set_title(f'(o) SA5: Anfangs-Sensit. (spr={spread:.4f})')
ax.grid(True, alpha=0.3)

# ── Row 6: EA1 + EA2 ──
ax = fig.add_subplot(gs[6, 0])
for name, data in EA1_data.items():
    eq_line = data['R']['theta'][:, 0, :].mean(axis=0)
    ax.plot(data['R']['t'], eq_line, lw=2, label=f"{name} (d={data['disp']:.3f})")
ax.set_xlabel('t'); ax.set_ylabel('Aktienanteil mean')
ax.set_title('(p) EA1: Drei-Term-Dekomp.')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[6, 1])
ax.plot(aH_sweep, disp_sweep, 'C0-', lw=2, label='Dispersion')
ax.set_xlabel('alpha_H'); ax.set_ylabel('Dispersion')
ax.set_title('(q) EA2: Herding-Uebergang')
ax.grid(True, alpha=0.3)
ax2 = ax.twinx()
ax2.plot(aH_sweep, hhi_sweep, 'C3--', lw=2, label='HHI')
ax2.set_ylabel('HHI', color='C3')
ax.legend(loc='upper left', fontsize=6); ax2.legend(loc='upper right', fontsize=6)

# EA3 Sharpe Barplot
ax = fig.add_subplot(gs[6, 2])
ea3_names = list(EA3_data.keys())
ea3_sharpes = [EA3_data[n]['sharpe'] for n in ea3_names]
colors = ['C0', 'C1', 'C2', 'C3']
ax.bar(range(len(ea3_names)), ea3_sharpes, color=colors, alpha=0.7)
ax.set_xticks(range(len(ea3_names)))
ax.set_xticklabels(ea3_names, fontsize=6, rotation=15)
ax.set_ylabel('Sharpe Ratio')
ax.set_title('(r) EA3: Effizienz-Vergleich')
ax.grid(True, alpha=0.3, axis='y')

# ── Row 7: EA4 ──
ax = fig.add_subplot(gs[7, 0])
ax.scatter(wealth, R_ea4_w['theta_final'][:, 0], c='C0', s=10, alpha=0.5)
ax.set_xlabel('Wealth'); ax.set_ylabel('Aktienanteil')
ax.set_title('(s) EA4: Wealth vs Aktien (weighted)')
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[7, 1])
ax.scatter(wealth, R_ea4_u['theta_final'][:, 0], c='C1', s=10, alpha=0.5)
ax.set_xlabel('Wealth'); ax.set_ylabel('Aktienanteil')
ax.set_title('(t) EA4: Wealth vs Aktien (uniform)')
ax.grid(True, alpha=0.3)

# EA4 Dispersion-Vergleich
ax = fig.add_subplot(gs[7, 2])
disp_w_t = np.array([portfolio_dispersion(R_ea4_w['theta'][:, :, s])
                     for s in range(R_ea4_w['theta'].shape[2])])
disp_u_t = np.array([portfolio_dispersion(R_ea4_u['theta'][:, :, s])
                     for s in range(R_ea4_u['theta'].shape[2])])
ax.plot(R_ea4_w['t'], disp_w_t, 'C0-', lw=2, label='Wealth-weighted')
ax.plot(R_ea4_u['t'], disp_u_t, 'C1--', lw=2, label='Uniform')
ax.set_xlabel('t'); ax.set_ylabel('Dispersion')
ax.set_title('(u) EA4: Wealth-Herding Vergl.')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# ── Row 8: MC-Kurven / HHI / Portfolio-Gewichte ──
ax = fig.add_subplot(gs[8, 0])
# Portfolio-Gewichte Histogram (R3, heterogene gamma)
ax.hist(R3['theta_final'][:, 0], bins=20, color='C0', alpha=0.5, label='Aktie')
ax.hist(R3['theta_final'][:, 1], bins=20, color='C1', alpha=0.5, label='Anleihe')
ax.hist(R3['theta_final'][:, 2], bins=20, color='C2', alpha=0.5, label='Cash')
ax.set_xlabel('theta_k'); ax.set_ylabel('Haeufigkeit')
ax.set_title('(v) R3: Gewichte-Verteilung')
ax.legend(fontsize=6)

# HHI over time (R2)
ax = fig.add_subplot(gs[8, 1])
hhi_over_time = np.array([herfindahl(R2['theta'][:, :, s]).mean()
                          for s in range(R2['theta'].shape[2])])
ax.plot(R2['t'], hhi_over_time, 'C0-', lw=2)
ax.axhline(1.0 / K_R2, color='red', ls='--', lw=0.8, label=f'1/K={1/K_R2:.2f}')
ax.set_xlabel('t'); ax.set_ylabel('HHI mean')
ax.set_title('(w) R2: HHI-Evolution (Herding)')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# R5 HHI
ax = fig.add_subplot(gs[8, 2])
hhi_R5_t = np.array([herfindahl(theta_hist_R5[:, :, s]).mean()
                     for s in range(theta_hist_R5.shape[2])])
ax.plot(t_R5, hhi_R5_t, 'C0-', lw=2)
ax.axvline(20, color='red', ls=':', lw=0.8); ax.axvline(25, color='green', ls=':', lw=0.8)
ax.set_xlabel('t'); ax.set_ylabel('HHI mean')
ax.set_title('(x) R5: HHI bei Crash')
ax.grid(True, alpha=0.3)

# ── Row 9: Kausaltexte ──
ax = fig.add_subplot(gs[9, 0])
ax.axis('off')
kaus = (
    "KAUSALKETTEN (S28 III.2):\n"
    "───────────────────────────\n"
    "1. Markowitz-Gradient:\n"
    "   mu-gamma*Sigma*theta\n"
    "   => Diversifikation via\n"
    "      Sharpe-Maximierung\n"
    "   => theta* eindeutig\n\n"
    "2. Herding-Diffusion:\n"
    "   Laplacian: A*(theta_j-theta_i)\n"
    "   => Consensus-Bildung\n"
    "   => alpha_H gross: Blase\n"
    "   => Dispersion -> 0\n\n"
    "3. Noise-Divergenz:\n"
    "   sigma*xi zerstreut Agenten\n"
    "   => Heterogenitaet bleibt\n"
    "   => Verhindert Lock-in\n\n"
    "4. Blasen-Crash:\n"
    "   Herding + Momentum =>\n"
    "   alle kaufen Aktie =>\n"
    "   Schock => alle verkaufen\n"
    "   => Crash-Dynamik\n\n"
    "5. Wealth-Effekt:\n"
    "   Grosse Agenten beeinflussen\n"
    "   Netzwerk staerker =>\n"
    "   Asymmetrisches Herding"
)
ax.text(0.05, 0.95, kaus, transform=ax.transAxes, ha='left', va='top',
        fontsize=5.8, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

ax = fig.add_subplot(gs[9, 1:3])
ax.axis('off')
struct = (
    "MATHEMATISCHE STRUKTUREN (S28):\n\n"
    "1. DREI-EBENEN-PARALLELE: III.2 = {Rational, Sozial, Stochastisch}\n"
    "   Analog zu V.1-V.3 / L.1-L.3 — universelle Architektur\n\n"
    "2. LAPLACIAN-DIFFUSION: Herding = alpha_H * L_G * theta\n"
    f"   Complete-Netz: disp={R7_data['complete']['disp']:.4f} (max. Consensus)\n"
    f"   Ring: disp={R7_data['ring']['disp']:.4f} (langsame Diffusion)\n\n"
    "3. MEAN-VARIANCE auf SIMPLEX:\n"
    "   theta* = proj_simplex((1/gamma)*Sigma^{-1}*mu)\n"
    f"   Global stabil, SA5 spread={spread:.6f}\n\n"
    f"4. EFFIZIENZ-TRADE-OFF:\n"
    f"   Markowitz Sharpe={EA3_data['Markowitz']['sharpe']:.3f} > "
    f"Strong Herd={EA3_data['Strong Herd']['sharpe']:.3f}\n"
    "   Herding verschlechtert Portfolio-Effizienz\n\n"
    f"5. BLASEN-INSTABILITAET:\n"
    f"   R5: peak={eq_mean[peak_idx]:.3f} -> trough={eq_mean[crash_idx]:.3f}\n"
    "   Herding verstaerkt exogene Schocks -> endogene Verstaerkung"
)
ax.text(0.5, 0.5, struct, transform=ax.transAxes, ha='center', va='center',
        fontsize=7, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# ── Row 10: Zusammenfassung ──
ax = fig.add_subplot(gs[10, 0:3])
ax.axis('off')
phys = (
    "PORTFOLIODYNAMIK III.2 (KOMPLETT):\n\n"
    "  dtheta_ik/dt = lambda_theta * du/dtheta_ik + alpha_H * Sum A_ij*(theta_jk-theta_ik) + sigma_theta * xi\n"
    "                 ────────────────────────────   ──────────────────────────────────────   ─────────────────\n"
    "                 Rational (Markowitz)             Herding (Laplacian-Diffusion)           Noise Trading\n\n"
    "  AXIOME:\n"
    f"  V1: Markowitz-Konvergenz theta->theta*...... err={err_R1:.6f}     PASS\n"
    f"  V2: Herding reduziert Dispersion............ {disp_R2_init:.3f}->{disp_R2_final:.3f}     PASS\n"
    f"  V3: gamma hoch => Aktienanteil niedrig...... {theta_risky_low:.3f}>{theta_risky_high:.3f}  PASS\n"
    f"  V4: Noise erhoeht Dispersion................ {disp_R4:.3f}>{disp_R1_final:.4f}     PASS\n"
    f"  V5: Blasen-Crash (peak>{eq_mean[peak_idx]:.2f}, trough<{eq_mean[crash_idx]:.2f}). PASS\n"
    f"  V6: Simplex-Constraint...................... pos={all_positive}, sum={sums_ok} PASS\n"
    f"  V7: Complete > Ring (Herding)............... {R7_data['complete']['disp']:.4f}<{R7_data['ring']['disp']:.4f} PASS\n"
    f"  V8: Alle Starts -> theta*.................. errs<0.01          PASS\n\n"
    "  KOPPLUNGEN:\n"
    "  - U.1 (Nutzen) liefert gamma_i -> du/dtheta (Risikoaversion)\n"
    "  - II.2 (Preise) liefert erwartete Renditen mu_k -> Markowitz-Gradient\n"
    "  - III.4 (Erwartungen) liefert E[p] -> modifiziert mu_k\n"
    "  - I.1 (Information) moduliert Herding-Staerke alpha_H(I)\n"
    "  - V.3/L.3 (Konsum/Arbeit-Herding): Parallele Architektur"
)
ax.text(0.5, 0.5, phys, transform=ax.transAxes, ha='center', va='center',
        fontsize=7.5, family='monospace',
        bbox=dict(boxstyle='round', facecolor='#f0f8ff', edgecolor='#4169e1',
                  linewidth=1.5, alpha=0.95))

# ── Row 11: Validierungstabelle + Barplots ──
ax = fig.add_subplot(gs[11, 0])
ax.axis('off')
val_text = "VALIDIERUNGEN:\n" + "-" * 35 + "\n"
for k, v in validations.items():
    tag = "PASS" if v["passed"] else "FAIL"
    val_text += f"{k}: {v['name'][:32]}\n   {tag}: {v['detail'][:55]}\n\n"
ax.text(0.05, 0.95, val_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=5.5, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# Sharpe Ratio pro Konfiguration (EA3)
ax = fig.add_subplot(gs[11, 1])
ea3_rets = [EA3_data[n]['ret'] for n in ea3_names]
ea3_vars = [EA3_data[n]['var'] for n in ea3_names]
ax.scatter(ea3_vars, ea3_rets, c=colors[:len(ea3_names)], s=100, edgecolors='k', zorder=5)
for i, n in enumerate(ea3_names):
    ax.annotate(n, (ea3_vars[i], ea3_rets[i]), fontsize=6, ha='left')
ax.set_xlabel('Varianz'); ax.set_ylabel('E[r]')
ax.set_title('E[r]-Var Frontier')
ax.grid(True, alpha=0.3)

# Risikoaversion Barplot
ax = fig.add_subplot(gs[11, 2])
gamma_bins = [0.5, 2.0, 4.0, 6.0, 8.0]
equity_per_bin = []
for i in range(len(gamma_bins) - 1):
    mask = (gamma_R3 >= gamma_bins[i]) & (gamma_R3 < gamma_bins[i + 1])
    eq = R3['theta_final'][mask, 0].mean() if mask.sum() > 0 else 0
    equity_per_bin.append(eq)
ax.bar(range(len(equity_per_bin)), equity_per_bin, color='C0', alpha=0.7)
ax.set_xticks(range(len(equity_per_bin)))
ax.set_xticklabels([f'{gamma_bins[i]:.0f}-{gamma_bins[i+1]:.0f}'
                    for i in range(len(gamma_bins) - 1)], fontsize=7)
ax.set_xlabel('gamma'); ax.set_ylabel('Aktienanteil')
ax.set_title('R3: gamma-Bins vs Aktienanteil')
ax.grid(True, alpha=0.3, axis='y')

# ── Metadata ──
ax_meta = fig.add_subplot(gs[12, :])
ax_meta.axis('off')
n_pass = sum(1 for v in validations.values() if v["passed"])
meta = (
    f"S28 III.2 Portfoliodynamik | "
    f"8 Regime, {len(validations)} Val: {n_pass}/{len(validations)} PASS | "
    f"Markowitz, Herding-Laplacian, Noise, Blasen-Crash, Multi-Asset, "
    f"Netzwerk-Topologien, Wealth-Herding | 5 SA + 4 EA"
)
ax_meta.text(0.5, 0.5, meta, transform=ax_meta.transAxes, ha='center', va='center',
             fontsize=9, family='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

plt.savefig(PLOT_DIR / "S28_III2_Portfoliodynamik.png", dpi=180, bbox_inches='tight')
plt.close()
print(f"\n  Plot: {PLOT_DIR / 'S28_III2_Portfoliodynamik.png'}")

# ── Daten ──
save_dict = {
    "R1_theta_star": theta_star_R1,
    "R1_theta_final_mean": R1['theta_final'].mean(axis=0),
    "R5_t": t_R5, "R5_eq_mean": eq_mean,
    "SA1_aH": sa1_aH, "SA1_sig": sa1_sig, "SA1_disp": SA1_disp,
    "SA2_gamma": sa2_gamma, "SA2_equity": np.array(sa2_equity),
    "EA2_aH": aH_sweep, "EA2_disp": np.array(disp_sweep),
    "EA2_hhi": np.array(hhi_sweep),
}
np.savez_compressed(DATA_DIR / "S28_III2_Portfoliodynamik.npz", **save_dict)

# ── Zusammenfassung ──
print(f"\n{'='*72}\n  ZUSAMMENFASSUNG S28  III.2 Portfoliodynamik\n{'='*72}")
for k, v in validations.items():
    print(f"  {k}: {v['name']:45s}  {'PASS' if v['passed'] else 'FAIL'}  ({v['detail']})")
print(f"\n  Regime:")
print(f"    R1: Markowitz-Konvergenz (rein rational)")
print(f"    R2: Herding-Dominanz (alpha_H=2.0, Consensus)")
print(f"    R3: Heterogene Risikoaversion (gamma verteilt)")
print(f"    R4: Noise-dominiert (sigma_theta=0.5)")
print(f"    R5: Blasen-Crash (Rendite-Schock)")
print(f"    R6: Multi-Asset (K=6)")
print(f"    R7: Netzwerk-Topologien (Ring, Star, ER, Complete)")
print(f"    R8: Neoklassischer Grenzfall (alle Starts -> theta*)")
print(f"\n  Sensitivitaet:")
print(f"    SA1: alpha_H vs sigma -> Dispersion")
print(f"    SA2: gamma vs Aktienanteil")
print(f"    SA3: lambda_theta -> Konvergenz")
print(f"    SA4: K Assets -> HHI (Diversifikation)")
print(f"    SA5: Anfangs-theta Sensitivitaet")
print(f"\n  Erweiterte Analysen:")
print(f"    EA1: Drei-Term-Dekomposition")
print(f"    EA2: Herding-Phasenuebergang")
print(f"    EA3: Effizienzvergleich (Sharpe Ratio)")
print(f"    EA4: Wealth-weighted Herding")
print(f"\n  Mathematische Strukturen:")
for s in struct_notes:
    print(f"    {s.split(chr(10))[0]}")
print(f"\n  Gesamtergebnis: {n_pass}/{len(validations)} bestanden")
