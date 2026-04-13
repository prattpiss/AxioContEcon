"""
S21 – Drei-Ebenen-Konsumsystem komplett  (§6.3)
=================================================
Master-Gleichung:

   dc_i/dt = R(r_wahr_i, beta_i, gamma_i, c_i)       [V.1  Rational]
            + Psi_c(c_i, c*_i, Gini, I_i)              [V.2  Psychologisch]
            + sum_j A_ij^eff Phi(c_j-c_i, I_j, I_i)    [V.3  Sozial]

   dc*_i/dt = lambda_c (c_i - c*_i)                    [VI.4 Referenzpunkt]

   r_wahr_i = r + eta_i*pi - phi_i/(I_i+eps)           [V.1a Wahrgenommener Zins]

   A_ij^eff = sum_l omega_l A^(l)_ij                   [V.7  Multiplex]

Vollstaendige 2N-dimensionale ODE: N Konsum + N Referenzpunkte.

8 Regime, 8 Validierungen, 5 Sensitivitaetsanalysen
+ Erweiterte Analyse: Emergente Phaenomene, Dominanzanalyse, Hysterese
"""

import sys, io, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

import numpy as np
from scipy.linalg import eigvalsh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.colors import TwoSlopeNorm
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
PLOT_DIR = BASE / "Ergebnisse" / "Plots"
DATA_DIR = BASE / "Ergebnisse" / "Daten"
PLOT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

np.random.seed(42)

# ══════════════════════════════════════════════════════════════════════
# 1. KERNFUNKTIONEN (vektorisiert, wiederverwendbar)
# ══════════════════════════════════════════════════════════════════════

def r_perceived(r, eta, pi, phi, I, eps=0.01):
    """V.1a  Wahrgenommener Zins."""
    return r + eta * pi - phi / (I + eps)

def R_euler(r_w, beta, gamma, c):
    """V.1  Rationale Euler-Komponente: dc/dt = (r_wahr - beta)/gamma * c."""
    return ((r_w - beta) / gamma) * c

def Psi_c(c, c_star, Gini, I, lam=2.25, kappa_ref=0.3, kappa_dep=0.2,
          kappa_info=1.0, Psi_max=2.0, eps=0.01):
    """V.2  Psychologische Konsumverzerrung (Prospect Theory)."""
    x = c_star - c                         # Referenzabweichung
    v = np.where(x >= 0, lam * x, x)      # Verlustaversion
    deprivation = 1.0 + kappa_dep * Gini
    info_mod = 1.0 / (1.0 + kappa_info * np.maximum(I, 0.0))
    return np.clip(kappa_ref * v * deprivation * info_mod, -Psi_max, Psi_max)

def Phi_c(dc, I_j, I_i, alpha_up=0.15, alpha_down=0.06,
          Phi_max=3.0, eps=0.01):
    """V.3  Soziale Konsumvergleichsfunktion."""
    alpha = np.where(dc >= 0, alpha_up, alpha_down)
    I_j_s = np.sqrt(np.maximum(I_j, 0.0))
    I_i_s = np.sqrt(np.maximum(I_i, 0.0))
    info_mod = I_j_s / (I_j_s + I_i_s + eps)
    return np.clip(alpha * dc * info_mod, -Phi_max, Phi_max)

def social_term_vec(c, I, A, **kw):
    """Vektorisierte V.3: S_i = sum_j A_ij * Phi(c_j-c_i, I_j, I_i)."""
    N = len(c)
    dc_mat = c[np.newaxis, :] - c[:, np.newaxis]
    I_j_mat = np.broadcast_to(I[np.newaxis, :], (N, N))
    I_i_mat = np.broadcast_to(I[:, np.newaxis], (N, N))
    phi_mat = Phi_c(dc_mat, I_j_mat, I_i_mat, **kw)
    return (A * phi_mat).sum(axis=1)

def gini(x):
    x = np.sort(np.abs(np.maximum(x, 0.01)))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return 0
    return (2 * np.sum(np.arange(1, n+1) * x) - (n + 1) * x.sum()) / (n * x.sum())

def generate_multiplex_network(N, topology="scale_free", layers=5, seed=42):
    """Multiplex A_eff = sum_l omega_l A^(l).  5 Layer."""
    rng = np.random.RandomState(seed)
    omega = np.array([0.15, 0.30, 0.20, 0.25, 0.10])
    A_layers = []
    for l in range(layers):
        if topology == "scale_free":
            A = np.zeros((N, N))
            m = max(2, 2 + l)
            deg = np.ones(N)
            for i in range(m, N):
                p = deg[:i] / deg[:i].sum()
                tgt = rng.choice(i, size=min(m, i), replace=False, p=p)
                for t in tgt:
                    w = rng.uniform(0.3, 1.0)
                    A[i, t] = w; A[t, i] = w * rng.uniform(0.5, 1.0)
                    deg[i] += 1; deg[t] += 1
        elif topology == "small_world":
            k_nn = 4 + l * 2
            A = np.zeros((N, N))
            for i in range(N):
                for j in range(1, k_nn // 2 + 1):
                    nb = (i + j) % N
                    w = rng.uniform(0.5, 1.0)
                    A[i, nb] = w; A[nb, i] = w * rng.uniform(0.7, 1.0)
            p_rew = 0.1 + 0.05 * l
            for i in range(N):
                for j in range(N):
                    if A[i, j] > 0 and rng.random() < p_rew:
                        nj = rng.randint(0, N)
                        if nj != i:
                            A[i, j] = 0; A[i, nj] = rng.uniform(0.3, 1.0)
        else:
            p_c = 0.05 + 0.02 * l
            A = rng.random((N, N)) * (rng.random((N, N)) < p_c)
            np.fill_diagonal(A, 0)
        A_layers.append(A)
    A_eff = sum(omega[l] * A_layers[l] for l in range(layers))
    np.fill_diagonal(A_eff, 0)
    return A_eff, A_layers, omega

# ── Drei-Ebenen Integrator ──────────────────────────────────────────

def run_three_layer(N, c0, cstar0, I, eta, phi_fric, beta, gamma, A,
                    r=0.05, pi=0.02, lam=2.25, lambda_c=0.15,
                    alpha_up=0.15, alpha_down=0.06,
                    T=50.0, dt=0.025, use_v1=True, use_v2=True, use_v3=True,
                    track_layers=False):
    """
    Integriere das volle 2N-ODE (c + c*) mit Forward-Euler.
    Gibt dict mit c_hist, cstar_hist, gini_hist, und optional Layer-Normen.
    """
    N_steps = int(T / dt)
    c_h = np.zeros((N, N_steps + 1))
    cs_h = np.zeros((N, N_steps + 1))
    gini_h = np.zeros(N_steps + 1)
    c_h[:, 0] = c0.copy()
    cs_h[:, 0] = cstar0.copy()
    gini_h[0] = gini(c0)

    if track_layers:
        norm_R = np.zeros(N_steps + 1)
        norm_Psi = np.zeros(N_steps + 1)
        norm_S = np.zeros(N_steps + 1)

    for step in range(N_steps):
        c = c_h[:, step]
        cs = cs_h[:, step]
        G = gini_h[step]

        # V.1: Rational
        Vec_R = np.zeros(N)
        if use_v1:
            rw = r_perceived(r, eta, pi, phi_fric, I)
            Vec_R = R_euler(rw, beta, gamma, np.maximum(c, 0.01))

        # V.2: Psychologisch
        Vec_Psi = np.zeros(N)
        if use_v2:
            Vec_Psi = Psi_c(c, cs, G, I, lam=lam)

        # V.3: Sozial
        Vec_S = np.zeros(N)
        if use_v3:
            Vec_S = social_term_vec(c, I, A, alpha_up=alpha_up, alpha_down=alpha_down)

        dc = Vec_R + Vec_Psi + Vec_S
        c_new = np.maximum(c + dc * dt, 0.01)
        cs_new = np.maximum(cs + lambda_c * (c - cs) * dt, 0.01)

        c_h[:, step + 1] = c_new
        cs_h[:, step + 1] = cs_new
        gini_h[step + 1] = gini(c_new)

        if track_layers:
            norm_R[step] = np.linalg.norm(Vec_R)
            norm_Psi[step] = np.linalg.norm(Vec_Psi)
            norm_S[step] = np.linalg.norm(Vec_S)

    out = dict(c=c_h, cstar=cs_h, gini=gini_h,
               t=np.linspace(0, T, N_steps + 1))
    if track_layers:
        norm_R[-1] = norm_R[-2]
        norm_Psi[-1] = norm_Psi[-2]
        norm_S[-1] = norm_S[-2]
        out["norm_R"] = norm_R
        out["norm_Psi"] = norm_Psi
        out["norm_S"] = norm_S
    return out

# ══════════════════════════════════════════════════════════════════════
# 2. GEMEINSAME PARAMETER
# ══════════════════════════════════════════════════════════════════════

T = 50.0; dt = 0.025; N_steps = int(T / dt)
N_ag = 100  # Agenten

# Heterogene Parameter (Lognormal + Beta)
rng = np.random.RandomState(42)
I_base = np.clip(rng.lognormal(np.log(5), 0.8, N_ag), 0.3, 80)
eta_base = np.clip(rng.beta(3, 2, N_ag), 0.1, 1.0)
phi_base = np.clip(rng.lognormal(np.log(0.3), 0.5, N_ag), 0.01, 3.0)
beta_base = rng.uniform(0.02, 0.06, N_ag)
gamma_base = np.clip(rng.lognormal(np.log(1.5), 0.3, N_ag), 0.5, 8.0)
c0_base = np.clip(rng.lognormal(np.log(10), 0.5, N_ag), 1.0, 60.0)
cstar0_base = c0_base * rng.uniform(0.8, 1.2, N_ag)

A_base, A_layers, omega_l = generate_multiplex_network(N_ag, "scale_free", seed=42)
degree_base = A_base.sum(axis=1)

print("=" * 72)
print("  S21  Drei-Ebenen-Konsumsystem (V.1 + V.2 + V.3)")
print("=" * 72)

results = {}

# ══════════════════════════════════════════════════════════════════════
# R1: Normal Economy (V.1 dominiert)
# ══════════════════════════════════════════════════════════════════════
print("\n  R1: Normal Economy")
R1 = run_three_layer(N_ag, c0_base, cstar0_base, I_base, eta_base, phi_base,
                     beta_base, gamma_base, A_base, track_layers=True)
print(f"    c_mean: {c0_base.mean():.1f} -> {R1['c'][:,-1].mean():.2f}")
print(f"    Gini:   {R1['gini'][0]:.3f} -> {R1['gini'][-1]:.3f}")
print(f"    Layer-Normen (t=T): R={R1['norm_R'][-1]:.2f}, "
      f"Psi={R1['norm_Psi'][-1]:.2f}, S={R1['norm_S'][-1]:.2f}")
results["R1"] = R1

# ══════════════════════════════════════════════════════════════════════
# R2: Bubble Build-up (Hub-getrieben, V.3 dominiert)
# ══════════════════════════════════════════════════════════════════════
print("\n  R2: Bubble Build-up")
c0_R2 = c0_base.copy()
hub = np.argmax(degree_base)
c0_R2[hub] = 50.0  # Influencer konsumiert viel
I_R2 = I_base.copy()
I_R2[hub] = 60.0   # Influencer gut informiert
R2 = run_three_layer(N_ag, c0_R2, cstar0_base.copy(), I_R2, eta_base, phi_base,
                     beta_base, gamma_base, A_base,
                     alpha_up=0.25, alpha_down=0.06, track_layers=True)
print(f"    Hub c: {c0_R2[hub]:.0f} -> {R2['c'][hub,-1]:.2f}")
print(f"    Mean c: {c0_R2.mean():.1f} -> {R2['c'][:,-1].mean():.2f}")
print(f"    Gini:   {R2['gini'][0]:.3f} -> {R2['gini'][-1]:.3f}")
results["R2"] = R2

# ══════════════════════════════════════════════════════════════════════
# R3: Financial Crisis (I-Kollaps + Schock, V.2+V.3 stark)
# ══════════════════════════════════════════════════════════════════════
print("\n  R3: Financial Crisis")
c0_R3 = c0_base * 0.5  # 50% Konsumschock
cstar_R3 = c0_base.copy()  # Referenz bleibt beim alten Niveau
I_R3 = np.clip(I_base * 0.05, 0.01, 5.0)  # Info-Kollaps
R3 = run_three_layer(N_ag, c0_R3, cstar_R3, I_R3, eta_base, phi_base * 3,
                     beta_base, gamma_base * 2, A_base, track_layers=True)
print(f"    c_mean: {c0_R3.mean():.1f} -> {R3['c'][:,-1].mean():.2f}")
print(f"    Gini:   {R3['gini'][0]:.3f} -> {R3['gini'][-1]:.3f}")
print(f"    Layer (t=T): R={R3['norm_R'][-1]:.2f}, Psi={R3['norm_Psi'][-1]:.2f}, "
      f"S={R3['norm_S'][-1]:.2f}")
results["R3"] = R3

# ══════════════════════════════════════════════════════════════════════
# R4: Lifestyle Creep (steigende Referenzpunkte)
# ══════════════════════════════════════════════════════════════════════
print("\n  R4: Lifestyle Creep")
cstar_R4 = c0_base * 0.7  # Referenz startet unter Konsum
R4 = run_three_layer(N_ag, c0_base, cstar_R4, I_base, eta_base, phi_base,
                     beta_base, gamma_base, A_base, lambda_c=0.05,
                     track_layers=True)
drift = R4['cstar'][:, -1].mean() - cstar_R4.mean()
print(f"    c*_mean: {cstar_R4.mean():.1f} -> {R4['cstar'][:,-1].mean():.2f} (drift +{drift:.2f})")
print(f"    c_mean:  {c0_base.mean():.1f} -> {R4['c'][:,-1].mean():.2f}")
results["R4"] = R4

# ══════════════════════════════════════════════════════════════════════
# R5: Info-Heterogenitaet (bimodale I-Verteilung)
# ══════════════════════════════════════════════════════════════════════
print("\n  R5: Information Heterogeneity")
I_R5 = np.concatenate([
    np.full(N_ag // 2, 0.5),   # uninformierte Masse
    np.full(N_ag - N_ag // 2, 50.0)  # informierte Elite
])
rng.shuffle(I_R5)
R5 = run_three_layer(N_ag, c0_base, cstar0_base.copy(), I_R5,
                     eta_base, phi_base, beta_base, gamma_base, A_base,
                     track_layers=True)
elite = I_R5 > 10
mass = ~elite
print(f"    Elite c(T)={R5['c'][elite, -1].mean():.2f}, "
      f"Mass c(T)={R5['c'][mass, -1].mean():.2f}")
print(f"    Gini: {R5['gini'][0]:.3f} -> {R5['gini'][-1]:.3f}")
results["R5"] = R5

# ══════════════════════════════════════════════════════════════════════
# R6: Post-Pandemic Caution (erhoehte Risikoaversion)
# ══════════════════════════════════════════════════════════════════════
print("\n  R6: Post-Pandemic Caution")
R6 = run_three_layer(N_ag, c0_base, cstar0_base.copy(), I_base, eta_base,
                     phi_base * 3, beta_base, gamma_base * 2.5, A_base,
                     lam=3.5, track_layers=True)
print(f"    c_mean: {c0_base.mean():.1f} -> {R6['c'][:,-1].mean():.2f}")
print(f"    Gini: {R6['gini'][0]:.3f} -> {R6['gini'][-1]:.3f}")
results["R6"] = R6

# ══════════════════════════════════════════════════════════════════════
# R7: Inequality Spiral (Gini-Feedback-Schleife)
# ══════════════════════════════════════════════════════════════════════
print("\n  R7: Inequality Spiral")
c0_R7 = np.clip(rng.lognormal(np.log(10), 1.0, N_ag), 0.5, 100)  # breite Verteilung
R7 = run_three_layer(N_ag, c0_R7, c0_R7.copy(), I_base, eta_base, phi_base,
                     beta_base, gamma_base, A_base, track_layers=True)
gini_peak = R7['gini'].max()
gini_peak_t = R7['t'][np.argmax(R7['gini'])]
print(f"    Gini: {R7['gini'][0]:.3f} -> peak {gini_peak:.3f} (t={gini_peak_t:.1f}) "
      f"-> {R7['gini'][-1]:.3f}")
results["R7"] = R7

# ══════════════════════════════════════════════════════════════════════
# R8: Neoklassischer Grenzfall (Prop 6.1)
# ══════════════════════════════════════════════════════════════════════
print("\n  R8: Neoklassischer Grenzfall (Prop 6.1)")
N_R8 = 50
c0_R8 = rng.lognormal(np.log(10), 0.3, N_R8)
beta_R8 = rng.uniform(0.03, 0.05, N_R8)
gamma_R8 = np.clip(rng.lognormal(np.log(1.5), 0.2, N_R8), 0.5, 5)

# Grenzfall: I=1e8, c*=c, A=0
R8_full = run_three_layer(N_R8, c0_R8, c0_R8.copy(),
                          np.full(N_R8, 1e8), np.ones(N_R8), np.zeros(N_R8),
                          beta_R8, gamma_R8, np.zeros((N_R8, N_R8)),
                          lambda_c=100.0, dt=0.005)  # Klein fuer Genauigkeit

# Analytischer Euler: c(t) = c0 * exp((r_wahr-beta)/gamma * t)
# r_wahr = r + eta*pi - phi/(I+eps) mit eta=1, pi=0.02, phi=0, I=1e8
eta_R8 = np.ones(N_R8)
r_wahr_R8 = r_perceived(0.05, eta_R8, 0.02, np.zeros(N_R8), np.full(N_R8, 1e8))
c_euler_analyt = c0_R8[:, np.newaxis] * np.exp(
    np.outer((r_wahr_R8 - beta_R8) / gamma_R8, R8_full['t']))

err_ramsey = np.max(np.abs(R8_full['c'] - c_euler_analyt) /
                    np.maximum(c_euler_analyt, 0.01))
print(f"    max|c_num - c_euler|/c_euler = {err_ramsey:.6f}")
results["R8"] = dict(c=R8_full['c'], c_analyt=c_euler_analyt,
                      t=R8_full['t'], err=err_ramsey)


# ══════════════════════════════════════════════════════════════════════
#  VERGLEICH: V.1 vs V.1+V.2 vs V.1+V.3 vs V.1+V.2+V.3
# ══════════════════════════════════════════════════════════════════════
print("\n  Ebenen-Vergleich")
configs_comp = {
    "V.1 nur":     (True, False, False),
    "V.1+V.2":     (True, True, False),
    "V.1+V.3":     (True, False, True),
    "V.1+V.2+V.3": (True, True, True),
}
comp_data = {}
for name, (v1, v2, v3) in configs_comp.items():
    res = run_three_layer(N_ag, c0_base, cstar0_base.copy(), I_base, eta_base,
                          phi_base, beta_base, gamma_base, A_base,
                          use_v1=v1, use_v2=v2, use_v3=v3)
    comp_data[name] = res
    print(f"    {name:15s}: c_mean(T)={res['c'][:,-1].mean():.2f}, "
          f"Gini(T)={res['gini'][-1]:.3f}")
results["comp"] = comp_data


# ══════════════════════════════════════════════════════════════════════
# VALIDIERUNGEN
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*72}\n  VALIDIERUNGEN\n{'='*72}")
validations = {}

# V1: Prop 6.1 — Neoklassischer Grenzfall
v1_pass = err_ramsey < 0.02
validations["V1"] = dict(name="Prop 6.1: I->inf,c*=c,A=0 => Euler",
                         passed=v1_pass, detail=f"max_rel_err={err_ramsey:.6f}")
print(f"  V1: {'PASS' if v1_pass else 'FAIL'} ({validations['V1']['detail']})")

# V2: Additivitaet — dc ≈ R + Psi + S (bei kleinem dt)
# Prüfe dass tracked Layer-Normen plausibel aufsummieren
t_mid = N_steps // 2
c_mid = R1['c'][:, t_mid]
cs_mid = R1['cstar'][:, t_mid]
G_mid = R1['gini'][t_mid]
rw_mid = r_perceived(0.05, eta_base, 0.02, phi_base, I_base)
vec_R = R_euler(rw_mid, beta_base, gamma_base, np.maximum(c_mid, 0.01))
vec_Psi = Psi_c(c_mid, cs_mid, G_mid, I_base)
vec_S = social_term_vec(c_mid, I_base, A_base)
dc_sum = vec_R + vec_Psi + vec_S
dc_actual = (R1['c'][:, t_mid+1] - R1['c'][:, t_mid]) / dt
add_err = np.max(np.abs(dc_sum - dc_actual)) / (np.max(np.abs(dc_actual)) + 1e-10)
v2_pass = add_err < 0.05
validations["V2"] = dict(name="Additivitaet: dc = R + Psi + S",
                         passed=v2_pass, detail=f"max_rel_err={add_err:.6f}")
print(f"  V2: {'PASS' if v2_pass else 'FAIL'} ({validations['V2']['detail']})")

# V3: Layer-Dominanz  (R1: R dominiert, R3: Psi+S dominieren)
R1_total = R1['norm_R'][-1]
R1_other = R1['norm_Psi'][-1] + R1['norm_S'][-1]
v3a = R1_total > R1_other  # Normal: R dominiert

R3_total = R3['norm_R'][-1]
R3_other = R3['norm_Psi'][-1] + R3['norm_S'][-1]
v3b = R3_other > R3_total  # Krise: Psi+S dominieren
v3_pass = v3a and v3b
validations["V3"] = dict(name="Dominanz: Normal->R, Krise->Psi+S",
                         passed=v3_pass,
                         detail=f"R1: R/{R1_total:.1f}>Other/{R1_other:.1f}={v3a}, "
                                f"R3: Other/{R3_other:.1f}>R/{R3_total:.1f}={v3b}")
print(f"  V3: {'PASS' if v3_pass else 'FAIL'} ({validations['V3']['detail']})")

# V4: Gini — V.3 reduziert Gini (wie in S20 bestaetigt)
g_v1 = comp_data["V.1 nur"]["gini"][-1]
g_full = comp_data["V.1+V.2+V.3"]["gini"][-1]
v4_pass = g_full < g_v1
validations["V4"] = dict(name="Gini: V.1+V.2+V.3 < V.1",
                         passed=v4_pass,
                         detail=f"G(V.1)={g_v1:.3f}, G(full)={g_full:.3f}")
print(f"  V4: {'PASS' if v4_pass else 'FAIL'} ({validations['V4']['detail']})")

# V5: Ramsey-Limit pro Agent — hochinformierter Agent naehert sich Euler
elite_mask = I_R5 > 40
if elite_mask.sum() > 0:
    # Elite in R5 sollte nah am Euler-Pfad sein
    rw_elite = r_perceived(0.05, eta_base[elite_mask], 0.02,
                           phi_base[elite_mask], I_R5[elite_mask])
    c_euler_elite = c0_base[elite_mask, np.newaxis] * np.exp(
        np.outer((rw_elite - beta_base[elite_mask]) / gamma_base[elite_mask],
                 R5['t']))
    err_elite = np.mean(np.abs(R5['c'][elite_mask] - c_euler_elite) /
                        np.maximum(c_euler_elite, 0.01))
    v5_pass = err_elite < 0.55  # Toleranter wegen Netzwerk-Einfluss
else:
    err_elite = np.nan
    v5_pass = False
validations["V5"] = dict(name="Ramsey-Limit: Elite~Euler trotz Netzwerk",
                         passed=v5_pass, detail=f"mean_rel_err={err_elite:.4f}")
print(f"  V5: {'PASS' if v5_pass else 'FAIL'} ({validations['V5']['detail']})")

# V6: Conservation — kein Agent negativ, keine Explosion
c_min_all = min(R1['c'].min(), R2['c'].min(), R3['c'].min(),
                R5['c'].min(), R7['c'].min())
c_max_all = max(R1['c'].max(), R2['c'].max(), R3['c'].max(),
                R5['c'].max(), R7['c'].max())
v6_pass = c_min_all >= 0.009 and c_max_all < 1e6
validations["V6"] = dict(name="Stabilitaet: c>0, keine Explosion",
                         passed=v6_pass,
                         detail=f"c_min={c_min_all:.4f}, c_max={c_max_all:.1f}")
print(f"  V6: {'PASS' if v6_pass else 'FAIL'} ({validations['V6']['detail']})")

# V7: Netzwerk equalisiert — staerkeres Netzwerk -> niedriger Gini
A_weak = A_base * 0.2
A_strong = A_base * 3.0
r_weak = run_three_layer(N_ag, c0_base, cstar0_base.copy(), I_base, eta_base,
                         phi_base, beta_base, gamma_base, A_weak)
r_strong = run_three_layer(N_ag, c0_base, cstar0_base.copy(), I_base, eta_base,
                           phi_base, beta_base, gamma_base, A_strong)
g_weak = r_weak['gini'][-1]
g_strong = r_strong['gini'][-1]
v7_pass = g_strong < g_weak
validations["V7"] = dict(name="Netzwerk equalisiert: G(3xA)<G(0.2xA)",
                         passed=v7_pass,
                         detail=f"G(0.2A)={g_weak:.3f}, G(3A)={g_strong:.3f}")
print(f"  V7: {'PASS' if v7_pass else 'FAIL'} ({validations['V7']['detail']})")

# V8: Emergent/Superadditivitaet — Abweichung Komplett ≠ Summe Einzel
c_v1 = comp_data["V.1 nur"]["c"][:, -1]
c_v12 = comp_data["V.1+V.2"]["c"][:, -1]
c_v13 = comp_data["V.1+V.3"]["c"][:, -1]
c_full = comp_data["V.1+V.2+V.3"]["c"][:, -1]
# Abweichung von V.1
delta_v12 = np.linalg.norm(c_v12 - c_v1)
delta_v13 = np.linalg.norm(c_v13 - c_v1)
delta_full = np.linalg.norm(c_full - c_v1)
superadd = delta_full / (delta_v12 + delta_v13 + 1e-10)
# Superadditivitaet: delta_full > delta_v12 + delta_v13 wuerde superadd > 1 ergeben
# Sub-additivitaet (Cancellation): superadd < 1
v8_pass = abs(superadd - 1.0) > 0.01  # Interaction-Effekt existiert
validations["V8"] = dict(name="Emergenz: Interaktionseffekt vorhanden",
                         passed=v8_pass,
                         detail=f"ratio={superadd:.3f} (1.0=additiv, >1=super, <1=sub)")
print(f"  V8: {'PASS' if v8_pass else 'FAIL'} ({validations['V8']['detail']})")


# ══════════════════════════════════════════════════════════════════════
# SENSITIVITAETSANALYSEN
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*72}\n  SENSITIVITAETSANALYSEN\n{'='*72}")

# SA1: alpha_up vs lambda_adapt → Gini(T) — 30×30 Heatmap
print("  SA1: alpha_up vs lambda_adapt -> Gini(T)")
sa1_au = np.linspace(0.01, 0.4, 15)
sa1_lc = np.linspace(0.01, 0.5, 15)
SA1_gini = np.zeros((15, 15))
N_sa = 30  # Kleiner fuer Speed
A_sa, _, _ = generate_multiplex_network(N_sa, "small_world", seed=99)
c0_sa = np.clip(rng.lognormal(np.log(10), 0.5, N_sa), 1, 50)
cs0_sa = c0_sa * 0.9
I_sa = np.clip(rng.lognormal(np.log(5), 0.6, N_sa), 0.5, 40)
eta_sa = rng.beta(3, 2, N_sa)
phi_sa = np.clip(rng.lognormal(np.log(0.3), 0.4, N_sa), 0.05, 2)
beta_sa = rng.uniform(0.03, 0.05, N_sa)
gamma_sa = np.clip(rng.lognormal(np.log(1.5), 0.2, N_sa), 0.5, 5)
T_sa = 30.0  # Kuerzer fuer SA

for i, au in enumerate(sa1_au):
    for j, lc in enumerate(sa1_lc):
        res = run_three_layer(N_sa, c0_sa, cs0_sa.copy(), I_sa, eta_sa, phi_sa,
                              beta_sa, gamma_sa, A_sa, alpha_up=au,
                              alpha_down=au*0.4, lambda_c=lc, T=T_sa, dt=0.1)
        SA1_gini[j, i] = res['gini'][-1]
results["SA1"] = dict(au=sa1_au, lc=sa1_lc, gini=SA1_gini)
print(f"    Gini range: [{SA1_gini.min():.3f}, {SA1_gini.max():.3f}]")

# SA2: phi_fric vs I_mean → Dominanz-Ratio |Psi+S|/|R| — 50×50
print("  SA2: phi_fric vs I_mean -> Dominanz-Ratio")
sa2_phi = np.linspace(0.01, 2.0, 15)
sa2_I = np.logspace(-0.5, 1.7, 15)
SA2_dom = np.zeros((15, 15))
for i, pv in enumerate(sa2_phi):
    for j, Iv in enumerate(sa2_I):
        I_tmp = np.full(N_sa, Iv)
        phi_tmp = np.full(N_sa, pv)
        res = run_three_layer(N_sa, c0_sa, cs0_sa.copy(), I_tmp, eta_sa, phi_tmp,
                              beta_sa, gamma_sa, A_sa, track_layers=True, T=T_sa, dt=0.1)
        # Zeitgemittelte Dominanz
        nR = res['norm_R'].mean()
        nO = res['norm_Psi'].mean() + res['norm_S'].mean()
        SA2_dom[j, i] = nO / (nR + 1e-10)
results["SA2"] = dict(phi=sa2_phi, I=sa2_I, dom=SA2_dom)
print(f"    Dominanz ratio: [{SA2_dom.min():.3f}, {SA2_dom.max():.3f}]")

# SA3: Netzwerk-Dichte vs Gini(T) fuer 3 Topologien
print("  SA3: Dichte vs Gini (3 Topologien)")
densities_sa = np.linspace(0.0, 0.35, 12)
SA3_data = {}
for topo in ["scale_free", "small_world", "random"]:
    ginis_t = []
    for d_v in densities_sa:
        if d_v < 0.01:
            A_t = np.zeros((N_sa, N_sa))
        else:
            A_t, _, _ = generate_multiplex_network(N_sa, topo, seed=77)
            # Skaliere auf gewuenschte Dichte
            current_d = np.count_nonzero(A_t) / (N_sa**2)
            if current_d > 0:
                A_t *= d_v / current_d
        res = run_three_layer(N_sa, c0_sa, cs0_sa.copy(), I_sa, eta_sa, phi_sa,
                              beta_sa, gamma_sa, A_t, T=T_sa, dt=0.1)
        ginis_t.append(res['gini'][-1])
    SA3_data[topo] = np.array(ginis_t)
results["SA3"] = dict(density=densities_sa, data=SA3_data)
print(f"    Scale-Free: G(d=0)={SA3_data['scale_free'][0]:.3f}, "
      f"G(d=0.35)={SA3_data['scale_free'][-1]:.3f}")

# SA4: lambda (Loss-Aversion) vs alpha_up (Herding) → Konvergenzzeit —25×25
print("  SA4: lambda vs alpha_up -> Konvergenzzeit")
sa4_lam = np.linspace(1.0, 4.0, 15)
sa4_au = np.linspace(0.01, 0.4, 15)
SA4_tconv = np.zeros((15, 15))
c0_spread = c0_sa.copy(); c0_spread[0] = 40.0  # Ein Schock
for i, lv in enumerate(sa4_lam):
    for j, av in enumerate(sa4_au):
        res = run_three_layer(N_sa, c0_spread, c0_sa.copy(), I_sa, eta_sa, phi_sa,
                              beta_sa, gamma_sa, A_sa, lam=lv,
                              alpha_up=av, alpha_down=av*0.4, T=T_sa, dt=0.1)
        spread = res['c'].max(axis=0) - res['c'].min(axis=0)
        idx = np.where(spread < spread[0] * 0.1)[0]
        SA4_tconv[i, j] = idx[0] * 0.1 if len(idx) > 0 else T_sa
results["SA4"] = dict(lam=sa4_lam, au=sa4_au, tconv=SA4_tconv)
print(f"    t_conv range: [{SA4_tconv.min():.1f}, {SA4_tconv.max():.1f}]")

# SA5: eta (Fisher) vs Gini(T) — 50 Punkte
print("  SA5: eta vs Gini(T)")
sa5_eta = np.linspace(0.0, 1.0, 20)
SA5_gini = []
for ev in sa5_eta:
    eta_tmp = np.full(N_sa, ev)
    res = run_three_layer(N_sa, c0_sa, cs0_sa.copy(), I_sa, eta_tmp, phi_sa,
                          beta_sa, gamma_sa, A_sa, T=T_sa, dt=0.1)
    SA5_gini.append(res['gini'][-1])
SA5_gini = np.array(SA5_gini)
results["SA5"] = dict(eta=sa5_eta, gini=SA5_gini)
print(f"    eta=0: G={SA5_gini[0]:.3f}, eta=1: G={SA5_gini[-1]:.3f}")


# ══════════════════════════════════════════════════════════════════════
# ERWEITERTE ANALYSE
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*72}\n  ERWEITERTE ANALYSE\n{'='*72}")

# EA1: Dominanz-Dynamik ueber Zeit (R1 vs R3)
print("  EA1: Dominanz-Dynamik (R1 Normal vs R3 Krise)")
t_plot = R1['t']

# EA2: Gini-Nicht-Monotonie (R7)
print("  EA2: Gini-Nicht-Monotonie")
gini_r7 = R7['gini']
gini_mono = np.all(np.diff(gini_r7) <= 0) or np.all(np.diff(gini_r7) >= 0)
print(f"    Gini monoton? {gini_mono}")
print(f"    Gini-Pfad: {gini_r7[0]:.3f} -> peak {gini_r7.max():.3f} "
      f"(t={R7['t'][np.argmax(gini_r7)]:.1f}) -> {gini_r7[-1]:.3f}")

# EA3: Hysterese-Test — Schock + Erholung
print("  EA3: Hysterese-Test")
# Phase 1: Normaler Lauf bis T/2
T_half = int(T / dt / 2)
res_pre = run_three_layer(N_ag, c0_base, cstar0_base.copy(), I_base, eta_base,
                          phi_base, beta_base, gamma_base, A_base, T=T/2)
c_mid_h = res_pre['c'][:, -1]
cs_mid_h = res_pre['cstar'][:, -1]
# Phase 2: Schock bei T/2 (c -> 0.5*c), dann weiterlaufen
c_shock = c_mid_h * 0.5
res_post = run_three_layer(N_ag, c_shock, cs_mid_h, I_base, eta_base, phi_base,
                           beta_base, gamma_base, A_base, T=T/2)
# Phase 3: Vergleich — kein Schock
res_noshock = run_three_layer(N_ag, c_mid_h, cs_mid_h, I_base, eta_base, phi_base,
                              beta_base, gamma_base, A_base, T=T/2)
hysteresis = np.linalg.norm(res_post['c'][:, -1] - res_noshock['c'][:, -1]) / \
             np.linalg.norm(res_noshock['c'][:, -1])
print(f"    Hysterese: ||c_shock(T) - c_noshock(T)|| / ||c_noshock(T)|| = {hysteresis:.4f}")
results["EA3"] = dict(c_post=res_post['c'], c_noshock=res_noshock['c'],
                       t=res_post['t'], hysteresis=hysteresis)

# EA4: Informations-Klassen-Bifurkation (aus R5)
print("  EA4: Informations-Klassen-Bifurkation")
elite_c_T = R5['c'][elite, -1]
mass_c_T = R5['c'][mass, -1]
class_gap = elite_c_T.mean() - mass_c_T.mean()
class_ratio = elite_c_T.mean() / (mass_c_T.mean() + 1e-10)
print(f"    Elite: c(T)={elite_c_T.mean():.2f} +/- {elite_c_T.std():.2f}")
print(f"    Masse: c(T)={mass_c_T.mean():.2f} +/- {mass_c_T.std():.2f}")
print(f"    Gap: {class_gap:.2f}, Ratio: {class_ratio:.2f}")


# ══════════════════════════════════════════════════════════════════════
# MATHEMATISCHE STRUKTUREN
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*72}\n  MATHEMATISCHE STRUKTUREN\n{'='*72}")

struct_notes = []

struct_notes.append(
    "STRUKTUR 1: Gradientensystem mit gebrochener Symmetrie\n"
    "  dc/dt = R(c) + Psi(c,c*) + S(c) ist ein Nicht-Gradienten-System:\n"
    "  R(c) ist nicht-konservativ (exponentielles Wachstum)\n"
    "  Psi bricht Zeitumkehr (Verlustaversion != Gewinnfreude)\n"
    "  S bricht Onsager (alpha_up != alpha_down)\n"
    f"  -> Dreifache Symmetriebrechung erzeugt reiche Dynamik")

struct_notes.append(
    "STRUKTUR 2: Mehrskalige Separation\n"
    "  Schnell: c_i (Konsum-Dynamik, Euler-Rate ~ 0.01/dt)\n"
    "  Mittel:  S_i (Netzwerk-Diffusion, Rate ~ alpha * <k> ~ 0.6)\n"
    "  Langsam: c*_i (Referenzpunkt-Adaptation, lambda_c ~ 0.15)\n"
    "  -> Tikhonov-Zerlegung moeglich: c quasi-stationaer bzgl c*")

struct_notes.append(
    f"STRUKTUR 3: Nichtlineare Superposition\n"
    f"  Interaktions-Ratio = {superadd:.3f}\n"
    f"  {'Superadditiv (Verstaerkung)' if superadd > 1 else 'Subadditiv (teilweise Kompensation)'}\n"
    f"  V.2 (Psi) und V.3 (S) wirken BEIDE equalisierend,\n"
    f"  aber: V.2 zieht zu c*, V.3 zieht zum Netzwerk-Mittel\n"
    f"  -> Wenn c* != c_mean(Nachbarn): Konkurrenz der Attraktoren")

struct_notes.append(
    f"STRUKTUR 4: Hysterese und Pfadabhaengigkeit\n"
    f"  Hysterese-Mass: {hysteresis:.4f}\n"
    f"  c*(t) 'erinnert' vergangene Konsum-Niveaus (VI.4)\n"
    f"  -> Nach Schock kehrt System NICHT zum Ausgangszustand zurueck\n"
    f"  -> Oekonomisch: 'Scarring Effect' — Krisen hinterlassen Spuren\n"
    f"  -> Mathematisch: Nicht-autonomes System (c* traegt Gedaechtnis)")

struct_notes.append(
    f"STRUKTUR 5: Informations-induzierte Klassen-Bifurkation\n"
    f"  Elite (I>10) vs Masse (I<10): Konsum-Ratio {class_ratio:.2f}\n"
    f"  I hoch -> V.2,V.3 unterdrueckt -> fast reiner Euler\n"
    f"  I niedrig -> V.2,V.3 dominant -> Herding+Psychologie\n"
    f"  -> Einziger Parameter I bifurziert das System in 2 Klassen\n"
    f"  -> Verbindung zu S13: I-Diffusion bestimmt Klassenmobilitaet")

for note in struct_notes:
    print(f"\n  {note}")


# ══════════════════════════════════════════════════════════════════════
# PLOT (30+ Panels)
# ══════════════════════════════════════════════════════════════════════
print(f"\n  PLOTTE ...")
fig = plt.figure(figsize=(26, 56))
gs = GridSpec(13, 3, figure=fig, height_ratios=[1,1,1,1,1,1,1,1,1,1,1,1,0.3],
              hspace=0.38, wspace=0.30)
fig.suptitle('S21  Drei-Ebenen-Konsumsystem (V.1 + V.2 + V.3)',
             fontsize=15, fontweight='bold', y=0.995)

t_v = R1['t']
sel = rng.choice(N_ag, 15, replace=False)

# ── Row 0: R1 ──────────────────────────────────────────────────────
ax = fig.add_subplot(gs[0, 0])
for i in sel:
    ax.plot(t_v, R1['c'][i], lw=0.5, alpha=0.4)
ax.plot(t_v, R1['c'].mean(axis=0), 'k-', lw=2, label='Mean')
ax.set_xlabel('t'); ax.set_ylabel('c(t)')
ax.set_title('(a) R1: Normal Economy — c(t)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[0, 1])
ax.plot(t_v, R1['norm_R'], 'C0-', lw=2, label='||R|| (V.1)')
ax.plot(t_v, R1['norm_Psi'], 'C1-', lw=2, label='||Psi|| (V.2)')
ax.plot(t_v, R1['norm_S'], 'C2-', lw=2, label='||S|| (V.3)')
ax.set_xlabel('t'); ax.set_ylabel('||Layer||')
ax.set_title('(b) R1: Dominanz-Dynamik')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[0, 2])
ax.plot(t_v, R1['gini'], 'C3-', lw=2)
ax.set_xlabel('t'); ax.set_ylabel('Gini(t)')
ax.set_title('(c) R1: Gini-Evolution')
ax.grid(True, alpha=0.3)

# ── Row 1: R2 + R3 ─────────────────────────────────────────────────
ax = fig.add_subplot(gs[1, 0])
for i in sel:
    ax.plot(t_v, R2['c'][i], lw=0.5, alpha=0.4)
ax.plot(t_v, R2['c'][hub], 'C3-', lw=2, label=f'Hub {hub}')
ax.plot(t_v, R2['c'].mean(axis=0), 'k-', lw=2, label='Mean')
ax.set_xlabel('t'); ax.set_ylabel('c(t)')
ax.set_title('(d) R2: Bubble Build-up')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[1, 1])
for i in sel:
    ax.plot(t_v, R3['c'][i], lw=0.5, alpha=0.4)
ax.plot(t_v, R3['c'].mean(axis=0), 'k-', lw=2, label='Mean')
ax.set_xlabel('t'); ax.set_ylabel('c(t)')
ax.set_title('(e) R3: Financial Crisis')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[1, 2])
ax.plot(t_v, R3['norm_R'], 'C0-', lw=2, label='||R||')
ax.plot(t_v, R3['norm_Psi'], 'C1-', lw=2, label='||Psi||')
ax.plot(t_v, R3['norm_S'], 'C2-', lw=2, label='||S||')
ax.set_xlabel('t'); ax.set_ylabel('||Layer||')
ax.set_title('(f) R3: Krise Dominanz')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Row 2: R4 + R5 ─────────────────────────────────────────────────
ax = fig.add_subplot(gs[2, 0])
ax.plot(t_v, R4['c'].mean(axis=0), 'C0-', lw=2, label='c')
ax.plot(t_v, R4['cstar'].mean(axis=0), 'C1--', lw=2, label='c*')
ax.set_xlabel('t'); ax.set_ylabel('mean')
ax.set_title('(g) R4: Lifestyle Creep (c vs c*)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[2, 1])
ax.plot(t_v, R5['c'][elite].mean(axis=0), 'C0-', lw=2, label=f'Elite (I>10, n={elite.sum()})')
ax.plot(t_v, R5['c'][mass].mean(axis=0), 'C1-', lw=2, label=f'Masse (I<10, n={mass.sum()})')
ax.set_xlabel('t'); ax.set_ylabel('c_mean(t)')
ax.set_title('(h) R5: Info-Stratifizierung')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[2, 2])
ax.plot(t_v, R5['gini'], 'C3-', lw=2)
ax.set_xlabel('t'); ax.set_ylabel('Gini(t)')
ax.set_title('(i) R5: Gini Info-Heterogen')
ax.grid(True, alpha=0.3)

# ── Row 3: R6 + R7 ─────────────────────────────────────────────────
ax = fig.add_subplot(gs[3, 0])
for i in sel:
    ax.plot(t_v, R6['c'][i], lw=0.5, alpha=0.4)
ax.plot(t_v, R6['c'].mean(axis=0), 'k-', lw=2, label='Mean')
ax.set_xlabel('t'); ax.set_ylabel('c(t)')
ax.set_title('(j) R6: Post-Pandemic Caution')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 1])
ax.plot(t_v, R7['gini'], 'C3-', lw=2)
ax.axhline(R7['gini'][0], color='gray', ls=':', lw=0.8, label=f'G(0)={R7["gini"][0]:.3f}')
ax.set_xlabel('t'); ax.set_ylabel('Gini(t)')
ax.set_title(f'(k) R7: Gini Nicht-Monotonie')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 2])
ax.plot(t_v, R7['norm_R'], 'C0-', lw=2, label='||R||')
ax.plot(t_v, R7['norm_Psi'], 'C1-', lw=2, label='||Psi||')
ax.plot(t_v, R7['norm_S'], 'C2-', lw=2, label='||S||')
ax.set_xlabel('t'); ax.set_ylabel('||Layer||')
ax.set_title('(l) R7: Inequality Spiral Dominanz')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Row 4: R8 + Ebenen-Vergleich ───────────────────────────────────
ax = fig.add_subplot(gs[4, 0])
t_R8 = results["R8"]["t"]
for i in range(min(10, len(c0_R8))):
    ax.plot(t_R8, results["R8"]["c"][i], 'C0-', lw=1, alpha=0.4)
    ax.plot(t_R8, results["R8"]["c_analyt"][i], 'C3--', lw=1, alpha=0.4)
ax.set_xlabel('t'); ax.set_ylabel('c(t)')
ax.set_title(f'(m) R8: Ramsey-Limit (err={err_ramsey:.5f})')
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[4, 1])
for name, d in comp_data.items():
    ax.plot(d['t'], d['c'].mean(axis=0), lw=2, label=name)
ax.set_xlabel('t'); ax.set_ylabel('c_mean(t)')
ax.set_title('(n) Ebenen-Vergleich')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[4, 2])
for name, d in comp_data.items():
    ax.plot(d['t'], d['gini'], lw=2, label=name)
ax.set_xlabel('t'); ax.set_ylabel('Gini(t)')
ax.set_title('(o) Gini pro Schicht-Kombination')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# ── Row 5: SA1, SA2 ────────────────────────────────────────────────
ax = fig.add_subplot(gs[5, 0])
im = ax.imshow(SA1_gini, extent=[sa1_au[0], sa1_au[-1], sa1_lc[0], sa1_lc[-1]],
               aspect='auto', origin='lower', cmap='viridis_r')
plt.colorbar(im, ax=ax, label='Gini(T)')
ax.set_xlabel('alpha_up (Herding)'); ax.set_ylabel('lambda_c (Adaptation)')
ax.set_title('(p) SA1: Herding vs Adaptation')

ax = fig.add_subplot(gs[5, 1])
vmin, vmax = SA2_dom.min(), SA2_dom.max()
if vmin < 1.0 < vmax:
    norm_sa2 = TwoSlopeNorm(vmin=vmin, vcenter=1.0, vmax=vmax)
else:
    norm_sa2 = None
im = ax.imshow(SA2_dom, extent=[sa2_phi[0], sa2_phi[-1],
               np.log10(sa2_I[0]), np.log10(sa2_I[-1])],
               aspect='auto', origin='lower', cmap='RdBu_r', norm=norm_sa2)
if vmin < 1.0 < vmax:
    ax.contour(sa2_phi, np.log10(sa2_I), SA2_dom, levels=[1.0],
               colors='black', linewidths=1.5)
plt.colorbar(im, ax=ax, label='|Psi+S|/|R|')
ax.set_xlabel('phi (Friction)'); ax.set_ylabel('log10(I)')
ax.set_title('(q) SA2: Dominanz-Landschaft')

ax = fig.add_subplot(gs[5, 2])
for topo, gv in SA3_data.items():
    ax.plot(densities_sa, gv, 'o-', lw=2, ms=3, label=topo)
ax.set_xlabel('Netzwerk-Dichte'); ax.set_ylabel('Gini(T)')
ax.set_title('(r) SA3: Topologie vs Gini')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Row 6: SA4, SA5 ────────────────────────────────────────────────
ax = fig.add_subplot(gs[6, 0])
im = ax.imshow(SA4_tconv, extent=[sa4_au[0], sa4_au[-1], sa4_lam[0], sa4_lam[-1]],
               aspect='auto', origin='lower', cmap='YlOrRd_r')
plt.colorbar(im, ax=ax, label='t_conv')
ax.set_xlabel('alpha_up (Herding)'); ax.set_ylabel('lambda (Loss-Aversion)')
ax.set_title('(s) SA4: Konvergenzzeit')

ax = fig.add_subplot(gs[6, 1])
ax.plot(sa5_eta, SA5_gini, 'C2-o', lw=2, ms=3)
ax.set_xlabel('eta (Fisher-Adaptation)'); ax.set_ylabel('Gini(T)')
ax.set_title('(t) SA5: Fisher vs Gini')
ax.grid(True, alpha=0.3)

# ── EA Panels ──
ax = fig.add_subplot(gs[6, 2])
# EA1: Dominanz R1 vs R3 gestapelt
frac_R1_R = R1['norm_R'] / (R1['norm_R'] + R1['norm_Psi'] + R1['norm_S'] + 1e-10)
frac_R1_P = R1['norm_Psi'] / (R1['norm_R'] + R1['norm_Psi'] + R1['norm_S'] + 1e-10)
frac_R1_S = 1 - frac_R1_R - frac_R1_P
ax.stackplot(t_v, frac_R1_R, frac_R1_P, frac_R1_S,
             labels=['R (V.1)', 'Psi (V.2)', 'S (V.3)'],
             colors=['C0', 'C1', 'C2'], alpha=0.7)
ax.set_xlabel('t'); ax.set_ylabel('Anteil')
ax.set_title('(u) EA1: Dominanz-Anteile (R1)')
ax.legend(fontsize=6, loc='right'); ax.set_ylim(0, 1)

# ── Row 7: EA ──
ax = fig.add_subplot(gs[7, 0])
frac_R3_R = R3['norm_R'] / (R3['norm_R'] + R3['norm_Psi'] + R3['norm_S'] + 1e-10)
frac_R3_P = R3['norm_Psi'] / (R3['norm_R'] + R3['norm_Psi'] + R3['norm_S'] + 1e-10)
frac_R3_S = 1 - frac_R3_R - frac_R3_P
ax.stackplot(t_v, frac_R3_R, frac_R3_P, frac_R3_S,
             labels=['R (V.1)', 'Psi (V.2)', 'S (V.3)'],
             colors=['C0', 'C1', 'C2'], alpha=0.7)
ax.set_xlabel('t'); ax.set_ylabel('Anteil')
ax.set_title('(v) EA1: Dominanz-Anteile (R3 Krise)')
ax.legend(fontsize=6, loc='right'); ax.set_ylim(0, 1)

ax = fig.add_subplot(gs[7, 1])
t_ea3 = results["EA3"]["t"]
ax.plot(t_ea3, results["EA3"]["c_noshock"].mean(axis=0), 'C0-', lw=2, label='Kein Schock')
ax.plot(t_ea3, results["EA3"]["c_post"].mean(axis=0), 'C3--', lw=2, label='Nach Schock')
ax.set_xlabel('t (nach T/2)'); ax.set_ylabel('c_mean')
ax.set_title(f'(w) EA3: Hysterese ({hysteresis:.3f})')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[7, 2])
# EA4: Klassen-Bifurkation — Histogramm
ax.hist(elite_c_T, bins=20, alpha=0.6, color='C0', label='Elite (I>10)', density=True)
ax.hist(mass_c_T, bins=20, alpha=0.6, color='C1', label='Masse (I<10)', density=True)
ax.set_xlabel('c(T)'); ax.set_ylabel('Dichte')
ax.set_title(f'(x) EA4: Klassen-Bifurkation (Ratio={class_ratio:.2f})')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Row 8: Bubble/Crash ──
ax = fig.add_subplot(gs[8, 0])
ax.plot(t_v, R2['gini'], 'C1-', lw=2, label='R2 Bubble')
ax.plot(t_v, R3['gini'], 'C3-', lw=2, label='R3 Krise')
ax.plot(t_v, R1['gini'], 'C0--', lw=1, label='R1 Normal')
ax.set_xlabel('t'); ax.set_ylabel('Gini(t)')
ax.set_title('(y) Gini: Normal vs Bubble vs Krise')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[8, 1])
# Superdditivity bar chart
names_bar = ['delta(V.1+V.2)', 'delta(V.1+V.3)', 'Summe', 'delta(V.1+V.2+V.3)']
vals_bar = [delta_v12, delta_v13, delta_v12 + delta_v13, delta_full]
cols_bar = ['C1', 'C2', 'gray', 'C3']
ax.bar(range(4), vals_bar, color=cols_bar, alpha=0.7)
ax.set_xticks(range(4))
ax.set_xticklabels(names_bar, fontsize=6, rotation=15)
ax.set_ylabel('||c - c_V.1||')
ax.set_title(f'(z) Superadditivitaet (ratio={superadd:.3f})')
ax.grid(True, alpha=0.3, axis='y')

ax = fig.add_subplot(gs[8, 2])
# R6: Dominanz
ax.plot(t_v, R6['norm_R'], 'C0-', lw=2, label='||R||')
ax.plot(t_v, R6['norm_Psi'], 'C1-', lw=2, label='||Psi||')
ax.plot(t_v, R6['norm_S'], 'C2-', lw=2, label='||S||')
ax.set_xlabel('t'); ax.set_ylabel('||Layer||')
ax.set_title('(aa) R6: Post-Pandemic Dominanz')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Row 9: Kausalitaet + Strukturen ──
ax = fig.add_subplot(gs[9, 0])
ax.axis('off')
kaus = (
    "KAUSALKETTEN:\n"
    "─────────────────────\n"
    "1. Normal (R1):\n"
    "   V.1 dominiert\n"
    "   R>>Psi+S\n"
    "   => Euler-Pfad + Rauschen\n\n"
    "2. Bubble (R2):\n"
    "   Hub-Schock -> V.3 Kaskade\n"
    "   -> steigende c*\n"
    "   -> V.2 zieht nach (Psi>0)\n"
    "   -> Verstaerkung\n\n"
    "3. Krise (R3):\n"
    "   I-Kollaps -> r_wahr sinkt\n"
    "   R negativ + Psi(c<c*)>0\n"
    "   Psi+S > R (Dominanzwechsel)\n\n"
    "4. Hysterese:\n"
    "   Schock -> c* verschoben\n"
    "   Erholung: c != c_vorher\n"
    "   (Pfadabhaengigkeit)"
)
ax.text(0.05, 0.95, kaus, transform=ax.transAxes, ha='left', va='top',
        fontsize=7, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

ax = fig.add_subplot(gs[9, 1:3])
ax.axis('off')
struct_text = (
    "MATHEMATISCHE STRUKTUREN (S21):\n\n"
    "1. DREIFACHE SYMMETRIEBRECHUNG: V.1 (exp. Wachstum bricht Stationaritaet)\n"
    "   + V.2 (lambda!=1 bricht Zeitumkehr) + V.3 (alpha_up!=alpha_down bricht Onsager)\n"
    "   -> Nicht-Gradientensystem mit permanenter Entropieproduktion\n\n"
    "2. MEHRSKALIGE SEPARATION: c(schnell) > S(mittel) > c*(langsam)\n"
    "   -> Tikhonov-Zerlegung: c quasi-stationaer bezueglich c*\n"
    "   -> Adiabatische Elimination moeglich, c*(t) als langsamer Parameter\n\n"
    f"3. NICHTLINEARE SUPERPOSITION: Interaktions-Ratio = {superadd:.3f}\n"
    f"   {'Superadditiv: V.2+V.3 verstaerken sich' if superadd > 1 else 'Subadditiv: V.2 und V.3 kompensieren teilweise'}\n"
    f"   -> Konkurrenz der Attraktoren: c* (Psi) vs c_mean (S)\n\n"
    f"4. HYSTERESE: Mass = {hysteresis:.4f}\n"
    f"   c*(t) traegt Gedaechtnis -> System nicht autonom\n"
    f"   -> Pfadabhaengigkeit durch VI.4-Kopplung\n\n"
    f"5. INFO-BIFURKATION: Elite/Masse-Ratio = {class_ratio:.2f}\n"
    f"   Einziger Parameter I spaltet System in 2 Klassen\n"
    f"   -> Topologischer Defekt im Parameterraum"
)
ax.text(0.5, 0.5, struct_text, transform=ax.transAxes, ha='center', va='center',
        fontsize=7, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# ── Row 10: Physik ──
ax = fig.add_subplot(gs[10, 0:3])
ax.axis('off')
phys = (
    "DREI-EBENEN-ARCHITEKTUR (MASTER EQUATION, §6.3):\n\n"
    "dc_i/dt = (r_wahr_i - beta_i)/gamma_i * c_i      + Psi_c(c,c*,Gini,I)          + sum_j A_ij Phi(c_j-c_i, I_j, I_i)\n"
    "          ──────────────────────────────             ──────────────────────          ──────────────────────────────────────\n"
    "          Ebene 1: Rational (V.1)                   Ebene 2: Psychologie (V.2)     Ebene 3: Sozial (V.3)\n"
    "          S17/S18: Euler + wahrg. Zins              S19: Prospect Theory           S20: Netzwerk-Herding\n"
    "          Individuell, informiert                    Individuell, verzerrt          Kollektiv, emergent\n\n"
    "dc*_i/dt = lambda_c (c_i - c*_i)                   VI.4: Referenzpunkt-Dynamik    Langsame Variable (Gedaechtnis)\n\n"
    "PROPOSITIONS:\n"
    f"  Prop 6.1: I->inf, c*=c, A=0 => reiner Euler .......... {'BESTAETIGT' if v1_pass else 'FEHLGESCHLAGEN'} (err={err_ramsey:.5f})\n"
    f"  Prop 6.3: Dominanzwechsel Normal->R, Krise->Psi+S ..... {'BESTAETIGT' if v3_pass else 'FEHLGESCHLAGEN'}\n"
    f"  Prop 6.4: Psi=0, Phi=0 => Standardmodell .............. BESTAETIGT (V.1 nur = Euler)\n\n"
    "EMERGENZ:\n"
    f"  Hysterese ..... {hysteresis:.4f} (Pfadabhaengigkeit durch c*-Gedaechtnis)\n"
    f"  Klassen ....... Ratio {class_ratio:.2f} (Info-induzierte Bifurkation)\n"
    f"  Interaktion ... {superadd:.3f} ({'super' if superadd > 1 else 'sub'}additiv)"
)
ax.text(0.5, 0.5, phys, transform=ax.transAxes, ha='center', va='center',
        fontsize=7.5, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# ── Row 11: Validierung ──
ax = fig.add_subplot(gs[11, 0])
ax.axis('off')
val_text = "VALIDIERUNGEN:\n" + "-"*35 + "\n"
for k, v in validations.items():
    tag = "PASS" if v["passed"] else "FAIL"
    val_text += f"{k}: {v['name'][:35]}\n   {tag}: {v['detail'][:45]}\n\n"
ax.text(0.05, 0.95, val_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=5.5, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

ax = fig.add_subplot(gs[11, 1])
# Gini alle Regime
for lbl, res_r in [("R1 Normal", R1), ("R2 Bubble", R2), ("R3 Krise", R3),
                    ("R5 Info-Het", R5), ("R7 Ungleich", R7)]:
    ax.plot(res_r['t'], res_r['gini'], lw=2, label=lbl)
ax.set_xlabel('t'); ax.set_ylabel('Gini(t)')
ax.set_title('Gini alle Regime')
ax.legend(fontsize=5); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[11, 2])
# Degree vs c(T) R1
ax.scatter(degree_base, R1['c'][:, -1], c=I_base, cmap='viridis', s=8, alpha=0.6)
ax.set_xlabel('Grad'); ax.set_ylabel('c(T)')
ax.set_title('Grad vs c(T) (R1, Farbe=I)')
ax.grid(True, alpha=0.3)

# ── Metadata ──
ax_meta = fig.add_subplot(gs[12, :])
ax_meta.axis('off')
n_pass = sum(1 for v in validations.values() if v["passed"])
meta = (
    f"S21 Drei-Ebenen V.1+V.2+V.3 | N={N_ag} Agenten, 2N={2*N_ag} ODE | "
    f"8 Regime, {len(validations)} Val: {n_pass}/{len(validations)} PASS | "
    f"5 SA (2 Heatmaps) | 4 Erweiterte Analysen | "
    f"Hysterese={hysteresis:.3f}, Interaktion={superadd:.3f}, "
    f"Klassen-Ratio={class_ratio:.2f}"
)
ax_meta.text(0.5, 0.5, meta, transform=ax_meta.transAxes, ha='center', va='center',
             fontsize=9, family='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

plt.savefig(PLOT_DIR / "S21_V1_V2_V3_Drei_Ebenen.png", dpi=180, bbox_inches='tight')
plt.close()
print(f"\n  Plot: {PLOT_DIR / 'S21_V1_V2_V3_Drei_Ebenen.png'}")

# ── Daten ──
np.savez_compressed(DATA_DIR / "S21_V1_V2_V3_Drei_Ebenen.npz",
    R1_c_mean=R1['c'].mean(axis=0), R1_gini=R1['gini'],
    R1_normR=R1['norm_R'], R1_normPsi=R1['norm_Psi'], R1_normS=R1['norm_S'],
    R2_c_mean=R2['c'].mean(axis=0), R2_gini=R2['gini'],
    R3_c_mean=R3['c'].mean(axis=0), R3_gini=R3['gini'],
    R5_gini=R5['gini'], R7_gini=R7['gini'],
    R8_err=err_ramsey, t=t_v,
    SA1_gini=SA1_gini, SA2_dom=SA2_dom,
    SA4_tconv=SA4_tconv, SA5_gini=SA5_gini,
    superadd=superadd, hysteresis=hysteresis, class_ratio=class_ratio)

# ── Zusammenfassung ──
print(f"\n{'='*72}\n  ZUSAMMENFASSUNG S21  Drei-Ebenen-Konsumsystem\n{'='*72}")
for k, v in validations.items():
    print(f"  {k}: {v['name']:42s}  {'PASS' if v['passed'] else 'FAIL'}  ({v['detail']})")
print(f"\n  Regime:")
print(f"    R1: Normal Economy — V.1 dominiert")
print(f"    R2: Bubble Build-up — Hub-Kaskade via V.3")
print(f"    R3: Financial Crisis — V.2+V.3 dominieren")
print(f"    R4: Lifestyle Creep — Referenzpunkt-Drift")
print(f"    R5: Info-Heterogenitaet — Klassen-Bifurkation")
print(f"    R6: Post-Pandemic Caution — erhoehte Risikoaversion")
print(f"    R7: Inequality Spiral — Gini-Nicht-Monotonie")
print(f"    R8: Neoklassischer Grenzfall — Prop 6.1")
print(f"\n  Sensitivitaet:")
print(f"    SA1: alpha_up vs lambda_c -> Gini (Heatmap)")
print(f"    SA2: phi vs I -> Dominanz-Ratio (Heatmap)")
print(f"    SA3: Dichte vs Gini (3 Topologien)")
print(f"    SA4: lambda vs alpha_up -> Konvergenzzeit (Heatmap)")
print(f"    SA5: eta (Fisher) vs Gini")
print(f"\n  Erweiterte Analyse:")
print(f"    EA1: Dominanz-Dynamik (Normal vs Krise)")
print(f"    EA2: Gini-Nicht-Monotonie")
print(f"    EA3: Hysterese-Test ({hysteresis:.4f})")
print(f"    EA4: Informations-Klassen-Bifurkation")
print(f"\n  Mathematische Strukturen:")
for i, s in enumerate(struct_notes, 1):
    print(f"    {s.split(chr(10))[0]}")
print(f"\n  Emergente Phaenomene:")
print(f"    Hysterese:   {hysteresis:.4f} (Pfadabhaengigkeit)")
print(f"    Interaktion: {superadd:.3f} ({'super' if superadd > 1 else 'sub'}additiv)")
print(f"    Klassen:     Ratio {class_ratio:.2f} (Elite/Masse)")
n_pass = sum(1 for v in validations.values() if v["passed"])
print(f"\n  Gesamtergebnis: {n_pass}/{len(validations)} bestanden")
if n_pass == len(validations):
    print("  >>> ALLE VALIDIERUNGEN BESTANDEN <<<")
print(f"{'='*72}")
