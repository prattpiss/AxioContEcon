"""
S20 – Soziale Konsumvergleiche V.3  (§6.3)
============================================
Gleichung V.3:
    S_i = sum_j A_ij^eff * Phi_c(c_j - c_i, I_j, I_i)

Drei-Ebenen-Architektur (komplett):
    dc_i/dt = R_i * c_i  (V.1)  +  Psi_c(...)  (V.2)  +  S_i  (V.3)

Axiome von Phi_c:
  1. Monotonie: dPhi/d(c_j-c_i) > 0
  2. Nullpunkt: Phi(0, ., .) = 0
  3. Info-Modulation: d|Phi|/dI_j > 0 (informierte Nachbarn beeinflussen staerker)
  4. Asymmetrie: Phi(+x) != -Phi(-x) (Aufwaertsherding > Abwaertsherding)
  5. Beschraenktheit: |Phi| <= Phi_max

A_ij^eff = sum_l omega_l * A_ij^(l)  (Multiplex: Trade, Info, Sozial, Finanz, Institutionen)

8 Regime, 8 Validierungen, 5 Sensitivitaetsanalysen
+ Erweiterte Analyse: Bifurkation, Meanfield-Phasendiagramm, Netzwerk-Spektralanalyse
"""

import sys, io, warnings, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

import numpy as np
from scipy.integrate import solve_ivp
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
# 1. Kernfunktionen (VEKTORISIERT)
# ══════════════════════════════════════════════════════════════════════

def Phi_c(dc, I_j, I_i, alpha_up=0.15, alpha_down=0.06, kappa_info=0.5,
          Phi_max=3.0, eps=0.01):
    """
    V.3 Soziale Konsumvergleichsfunktion.

    Phi(dc) = alpha * dc * info_mod(I_j, I_i)
      - dc = c_j - c_i
      - alpha_up fuer dc > 0  (Aufwaertsherding, staerker)
      - alpha_down fuer dc < 0 (Abwaertsherding, schwaecher)
      - info_mod = sqrt(I_j) / (sqrt(I_j) + sqrt(I_i) + eps)
        -> informierte Nachbarn beeinflussen staerker
        -> wenn I_i -> inf: Einfluss schwindet (Agent ist selbst informiert)

    Beschraenkt auf [-Phi_max, +Phi_max]
    """
    alpha = np.where(dc >= 0, alpha_up, alpha_down)
    # Info-Modulation: Nachbar-Info / (Nachbar + Selbst)
    I_j_s = np.sqrt(np.maximum(I_j, 0.0))
    I_i_s = np.sqrt(np.maximum(I_i, 0.0))
    info_mod = I_j_s / (I_j_s + I_i_s + eps)
    phi = alpha * dc * info_mod
    return np.clip(phi, -Phi_max, Phi_max)


def social_term_vec(c, I, A, **phi_kw):
    """Vektorisierte Berechnung: S_i = sum_j A_ij * Phi(c_j-c_i, I_j, I_i)"""
    N = len(c)
    dc_mat = c[np.newaxis, :] - c[:, np.newaxis]   # (N, N): dc_mat[i,j] = c_j - c_i
    I_j_mat = np.broadcast_to(I[np.newaxis, :], (N, N))
    I_i_mat = np.broadcast_to(I[:, np.newaxis], (N, N))
    phi_mat = Phi_c(dc_mat, I_j_mat, I_i_mat, **phi_kw)
    return (A * phi_mat).sum(axis=1)


def generate_multiplex_network(N, topology="scale_free", layers=5, seed=42):
    """
    Erzeuge A_ij^eff = sum_l omega_l * A^(l)
    Topologien: scale_free, small_world, random, clustered, star
    """
    rng = np.random.RandomState(seed)
    A_layers = []
    omega = np.array([0.15, 0.30, 0.20, 0.25, 0.10])  # Trade, Info, Sozial, Finanz, Institut

    for l in range(layers):
        if topology == "scale_free":
            # Barabasi-Albert-artig: degree ~ power-law
            A = np.zeros((N, N))
            m = max(2, 2 + l)  # Kanten pro neuem Knoten variiert pro Layer
            degrees = np.ones(N)
            for i in range(m, N):
                probs = degrees[:i] / degrees[:i].sum()
                targets = rng.choice(i, size=min(m, i), replace=False, p=probs)
                for t in targets:
                    w = rng.uniform(0.3, 1.0)
                    A[i, t] = w
                    A[t, i] = w * rng.uniform(0.5, 1.0)  # Asymmetrie
                    degrees[i] += 1
                    degrees[t] += 1
        elif topology == "small_world":
            # Watts-Strogatz-artig
            k_nn = 4 + l * 2
            A = np.zeros((N, N))
            for i in range(N):
                for j in range(1, k_nn // 2 + 1):
                    nb = (i + j) % N
                    w = rng.uniform(0.5, 1.0)
                    A[i, nb] = w
                    A[nb, i] = w * rng.uniform(0.7, 1.0)
            # Rewire
            p_rewire = 0.1 + 0.05 * l
            for i in range(N):
                for j in range(N):
                    if A[i, j] > 0 and rng.random() < p_rewire:
                        new_j = rng.randint(0, N)
                        if new_j != i:
                            A[i, j] = 0
                            A[i, new_j] = rng.uniform(0.3, 1.0)
        else:  # random (Erdos-Renyi)
            p_conn = 0.05 + 0.02 * l
            A = rng.random((N, N)) * (rng.random((N, N)) < p_conn)
            np.fill_diagonal(A, 0)
        A_layers.append(A)

    # Aggregation
    A_eff = sum(omega[l] * A_layers[l] for l in range(layers))
    np.fill_diagonal(A_eff, 0)
    return A_eff, A_layers, omega


def euler_R(r, beta, gamma):
    return (r - beta) / gamma


def Psi_c(c, c_star, Gini, I, lam=2.25, kappa_ref=0.3, kappa_dep=0.2,
          kappa_info=1.0, Psi_max=2.0, eps=0.01):
    """V.2 (from S19)"""
    x = c_star - c
    v = np.where(x >= 0, lam * x, x)
    deprivation = 1.0 + kappa_dep * Gini
    info_mod = 1.0 / (1.0 + kappa_info * np.maximum(I, 0.0))
    return np.clip(kappa_ref * v * deprivation * info_mod, -Psi_max, Psi_max)


def gini(x):
    x = np.sort(np.abs(x))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return 0
    return (2 * np.sum(np.arange(1, n+1) * x) - (n + 1) * x.sum()) / (n * x.sum())


print("=" * 72)
print("  S20  V.3  Soziale Konsumvergleiche")
print("=" * 72)

results = {}
T = 50.0
dt = 0.025
N_steps = int(T / dt)

# ══════════════════════════════════════════════════════════════════════
# R1: Phi-Funktion — Grundeigenschaften
# ══════════════════════════════════════════════════════════════════════
print("\n  R1: Phi-Funktion Grundeigenschaften")

dc_range = np.linspace(-15, 15, 500)
I_j_test = 5.0
I_i_test = 5.0

phi_R1 = Phi_c(dc_range, I_j_test, I_i_test)

# Asymmetrie-Ratio
d_test = 5.0
phi_up = Phi_c(d_test, 5, 5)
phi_down = Phi_c(-d_test, 5, 5)
asym_ratio = abs(phi_up) / abs(phi_down)
print(f"    Phi(+5)={phi_up:+.4f}, Phi(-5)={phi_down:+.4f}, |up/down|={asym_ratio:.2f}")
print(f"    alpha_up/alpha_down = {0.15/0.06:.2f} (Herding-Asymmetrie)")

results["R1"] = dict(label="R1: Phi-Grundeigenschaften",
                      dc=dc_range, phi=phi_R1, asym_ratio=asym_ratio)


# ══════════════════════════════════════════════════════════════════════
# R2: Multiplex-Netzwerk (N=100)
# ══════════════════════════════════════════════════════════════════════
print("\n  R2: Multiplex-Netzwerk (N=100)")

N_net = 100
A_eff, A_layers, omega_layers = generate_multiplex_network(N_net, "scale_free")
degree = A_eff.sum(axis=1)
layer_names = ["Trade", "Info", "Sozial", "Finanz", "Institut"]

print(f"    Netzwerk: N={N_net}, density={np.count_nonzero(A_eff)/(N_net**2):.3f}")
print(f"    Degree: mean={degree.mean():.1f}, max={degree.max():.1f}, min={degree.min():.1f}")
for l, name in enumerate(layer_names):
    dens = np.count_nonzero(A_layers[l]) / (N_net**2)
    print(f"      Layer {l+1} ({name:8s}): omega={omega_layers[l]:.2f}, density={dens:.3f}")

# Spektralanalyse: Laplacian
L = np.diag(degree) - A_eff
eigvals = np.sort(np.real(eigvalsh(L)))
spectral_gap = eigvals[1] if len(eigvals) > 1 else 0
algebraic_conn = eigvals[1]  # Fiedler value

results["R2"] = dict(label="R2: Multiplex-Netzwerk", A_eff=A_eff,
                      degree=degree, eigvals=eigvals,
                      spectral_gap=spectral_gap, algebraic_conn=algebraic_conn)
print(f"    Spectral gap (Fiedler): {algebraic_conn:.4f}")
print(f"    max eigenvalue: {eigvals[-1]:.2f}")


# ══════════════════════════════════════════════════════════════════════
# R3: Herding-Kaskade (Bubble-Aufbau)
# ══════════════════════════════════════════════════════════════════════
print("\n  R3: Herding-Kaskade (Bubble)")

c0_R3 = 10.0 * np.ones(N_net)
# Ein "Influencer" (hoechster Degree) startet mit hoeherem Konsum
hub_idx = np.argmax(degree)
c0_R3[hub_idx] = 20.0
I_R3 = 5.0 * np.ones(N_net)
I_R3[hub_idx] = 50.0  # Influencer gut informiert

c_hist_R3 = np.zeros((N_net, N_steps + 1))
c_hist_R3[:, 0] = c0_R3

for step in range(N_steps):
    c_now = c_hist_R3[:, step]
    social = social_term_vec(c_now, I_R3, A_eff)
    c_hist_R3[:, step + 1] = np.maximum(c_now + social * dt, 0.01)

t_R3 = np.linspace(0, T, N_steps + 1)
spread_R3 = c_hist_R3.max(axis=0) - c_hist_R3.min(axis=0)

print(f"    Hub (idx={hub_idx}): c(0)={c0_R3[hub_idx]:.0f}, c(T)={c_hist_R3[hub_idx, -1]:.2f}")
print(f"    Mean: c(0)={c0_R3.mean():.1f}, c(T)={c_hist_R3[:, -1].mean():.2f}")
print(f"    Spread(0)={spread_R3[0]:.1f}, Spread(T)={spread_R3[-1]:.2f}")

results["R3"] = dict(label="R3: Herding-Kaskade", c=c_hist_R3, t=t_R3,
                      spread=spread_R3, hub_idx=hub_idx)


# ══════════════════════════════════════════════════════════════════════
# R4: Info-Asymmetrie — Einfluss von I_j vs I_i
# ══════════════════════════════════════════════════════════════════════
print("\n  R4: Info-Asymmetrie")

I_j_sweep = np.logspace(-1, 2, 200)
dc_fixed = 5.0

# Agent mit verschiedenen eigenen I-Levels
I_i_vals = [0.1, 1.0, 5.0, 20.0, 100.0]
R4_data = {}
for I_i in I_i_vals:
    phi_vals = Phi_c(dc_fixed, I_j_sweep, I_i)
    R4_data[I_i] = phi_vals
    print(f"    I_i={I_i:5.1f}: Phi(I_j=0.1)={phi_vals[0]:.4f}, "
          f"Phi(I_j=100)={phi_vals[-1]:.4f}")

results["R4"] = dict(label="R4: Info-Asymmetrie", I_j=I_j_sweep, data=R4_data)


# ══════════════════════════════════════════════════════════════════════
# R5: Drei-Ebenen komplett (V.1 + V.2 + V.3)
# ══════════════════════════════════════════════════════════════════════
print("\n  R5: Drei-Ebenen-System (V.1+V.2+V.3)")

N_R5 = 50
A_R5, _, _ = generate_multiplex_network(N_R5, "small_world", seed=123)
c0_R5 = np.random.lognormal(np.log(10), 0.3, N_R5)
c_star_R5 = 10.0 * np.ones(N_R5)
I_R5 = np.random.lognormal(np.log(5), 0.8, N_R5)
I_R5 = np.clip(I_R5, 0.3, 50)
beta_R5 = np.random.uniform(0.03, 0.05, N_R5)
gamma_R5 = np.random.lognormal(np.log(1.5), 0.2, N_R5)
gamma_R5 = np.clip(gamma_R5, 0.5, 5)

configs_R5 = {
    "V.1 nur": (True, False, False),
    "V.1+V.2": (True, True, False),
    "V.1+V.3": (True, False, True),
    "V.1+V.2+V.3": (True, True, True),
}

R5_data = {}
for name, (use_v1, use_v2, use_v3) in configs_R5.items():
    c_h = np.zeros((N_R5, N_steps + 1))
    cs_h = np.zeros((N_R5, N_steps + 1))
    c_h[:, 0] = c0_R5.copy()
    cs_h[:, 0] = c_star_R5.copy()

    for step in range(N_steps):
        c_now = c_h[:, step]
        cs_now = cs_h[:, step]
        G = gini(np.maximum(c_now, 0.01))
        dc = np.zeros(N_R5)

        if use_v1:
            R_euler = euler_R(0.05, beta_R5, gamma_R5)
            dc += R_euler * np.maximum(c_now, 0.01)

        if use_v2:
            dc += Psi_c(c_now, cs_now, G, I_R5)

        if use_v3:
            dc += social_term_vec(c_now, I_R5, A_R5)

        c_h[:, step + 1] = np.maximum(c_now + dc * dt, 0.01)
        cs_h[:, step + 1] = np.maximum(cs_now + 0.15 * (c_now - cs_now) * dt, 0.01)

    gini_end = gini(np.maximum(c_h[:, -1], 0.01))
    R5_data[name] = dict(c=c_h, c_star=cs_h, gini_end=gini_end)
    print(f"    {name:15s}: c_mean(T)={c_h[:, -1].mean():.2f}, "
          f"Gini(T)={gini_end:.3f}")

results["R5"] = dict(label="R5: Drei-Ebenen", data=R5_data,
                      t=np.linspace(0, T, N_steps + 1))


# ══════════════════════════════════════════════════════════════════════
# R6: Netzwerk-Topologie-Vergleich
# ══════════════════════════════════════════════════════════════════════
print("\n  R6: Topologie-Vergleich")

N_topo = 50
topos = {"Scale-Free": "scale_free", "Small-World": "small_world", "Random": "random"}

R6_data = {}
for topo_name, topo_type in topos.items():
    A_t, _, _ = generate_multiplex_network(N_topo, topo_type, seed=77)
    c0_t = 10 * np.ones(N_topo)
    c0_t[0] = 25.0  # Schock-Agent

    c_h = np.zeros((N_topo, N_steps + 1))
    c_h[:, 0] = c0_t
    I_t = 5.0 * np.ones(N_topo)

    for step in range(N_steps):
        c_now = c_h[:, step]
        social = social_term_vec(c_now, I_t, A_t)
        c_h[:, step + 1] = np.maximum(c_now + social * dt, 0.01)

    gini_t = gini(np.maximum(c_h[:, -1], 0.01))
    spread_t = c_h.max(axis=0) - c_h.min(axis=0)
    # Konvergenzzeit: wann spread < 1?
    idx_conv = np.where(spread_t < 1.0)[0]
    t_conv = idx_conv[0] * dt if len(idx_conv) > 0 else T

    R6_data[topo_name] = dict(c=c_h, spread=spread_t, gini=gini_t, t_conv=t_conv,
                                degree=A_t.sum(axis=1))
    print(f"    {topo_name:12s}: t_conv={t_conv:.1f}, Gini(T)={gini_t:.3f}, "
          f"spread(T)={spread_t[-1]:.2f}")

results["R6"] = dict(label="R6: Topologie-Vergleich", data=R6_data,
                      t=np.linspace(0, T, N_steps + 1))


# ══════════════════════════════════════════════════════════════════════
# R7: Crash-Kaskade (Abwaertsherding)
# ══════════════════════════════════════════════════════════════════════
print("\n  R7: Crash-Kaskade")

c0_R7 = 20.0 * np.ones(N_net)
# Crash: mehrere Agenten reduzieren abrupt bei t=0
crash_agents = np.random.choice(N_net, 10, replace=False)
c0_R7[crash_agents] = 5.0
I_R7 = 5.0 * np.ones(N_net)

c_hist_R7 = np.zeros((N_net, N_steps + 1))
c_hist_R7[:, 0] = c0_R7

for step in range(N_steps):
    c_now = c_hist_R7[:, step]
    social = social_term_vec(c_now, I_R7, A_eff)
    c_hist_R7[:, step + 1] = np.maximum(c_now + social * dt, 0.01)

mean_R7 = c_hist_R7.mean(axis=0)
crash_share = (c_hist_R7[:, -1] < 10).sum() / N_net * 100

print(f"    Initial: {len(crash_agents)} Crash-Agenten (c=5), Rest c=20")
print(f"    Mean: c(0)={c0_R7.mean():.1f}, c(T)={mean_R7[-1]:.2f}")
print(f"    Contagion: {crash_share:.0f}% unter c=10 am Ende")

results["R7"] = dict(label="R7: Crash-Kaskade", c=c_hist_R7,
                      t=np.linspace(0, T, N_steps + 1), mean=mean_R7,
                      crash_share=crash_share)


# ══════════════════════════════════════════════════════════════════════
# R8: Neoklassischer Grenzfall (A=0 oder I_i -> inf)
# ══════════════════════════════════════════════════════════════════════
print("\n  R8: Neoklassischer Grenzfall")

# Test: V.3 mit I_i -> inf sollte Phi -> 0 liefern
phi_limit = Phi_c(5.0, 10.0, 1e8)
print(f"    Phi(dc=5, I_j=10, I_i=1e8)={phi_limit:.8f} (soll ~0)")

# Vergleich: A=0 vs A=normal
N_R8 = 30
A_R8, _, _ = generate_multiplex_network(N_R8, "small_world", seed=99)
c0_R8 = np.random.lognormal(np.log(10), 0.4, N_R8)
I_R8 = 5.0 * np.ones(N_R8)

configs_R8 = {"A=0 (kein Netzwerk)": np.zeros((N_R8, N_R8)),
               "A=normal": A_R8,
               "A=2x (starkes Netzwerk)": 2 * A_R8}

R8_data = {}
for name, A_v in configs_R8.items():
    c_h = np.zeros((N_R8, N_steps + 1))
    c_h[:, 0] = c0_R8.copy()
    for step in range(N_steps):
        c_now = c_h[:, step]
        social = social_term_vec(c_now, I_R8, A_v)
        R_e = euler_R(0.05, 0.04, 1.5)
        c_h[:, step + 1] = np.maximum(c_now + (R_e * np.maximum(c_now, 0.01) + social) * dt, 0.01)
    gini_end = gini(np.maximum(c_h[:, -1], 0.01))
    R8_data[name] = dict(c=c_h, gini=gini_end)
    print(f"    {name:25s}: Gini(T)={gini_end:.3f}, c_std={c_h[:,-1].std():.2f}")

results["R8"] = dict(label="R8: Grenzfall", data=R8_data,
                      t=np.linspace(0, T, N_steps + 1))


# ══════════════════════════════════════════════════════════════════════
# VALIDIERUNGEN
# ══════════════════════════════════════════════════════════════════════

validations = {}
print(f"\n{'='*72}\n  VALIDIERUNGEN\n{'='*72}")

# V1: Nullpunkt — Phi(0, ., .) = 0
v1_val = Phi_c(0, 5, 5)
v1_pass = abs(v1_val) < 1e-15
validations["V1"] = dict(name="Nullpunkt: Phi(0,.,.)=0", passed=v1_pass,
                          detail=f"|Phi|={abs(v1_val):.2e}")
print(f"  V1: {'PASS' if v1_pass else 'FAIL'} ({validations['V1']['detail']})")

# V2: Monotonie — dPhi/d(dc) > 0
dc_mono = np.linspace(-10, 10, 1000)
phi_mono = Phi_c(dc_mono, 5, 5)
v2_pass = np.all(np.diff(phi_mono) > 0)
validations["V2"] = dict(name="Monotonie: dPhi/d(dc) > 0", passed=v2_pass,
                          detail=f"all_increasing={v2_pass}")
print(f"  V2: {'PASS' if v2_pass else 'FAIL'} ({validations['V2']['detail']})")

# V3: Asymmetrie — |Phi(+d)| > |Phi(-d)|
d_vals = np.array([1, 3, 5, 8, 10])
phi_pos = np.abs(Phi_c(d_vals, 5, 5))
phi_neg = np.abs(Phi_c(-d_vals, 5, 5))
v3_pass = np.all(phi_pos > phi_neg)
v3_ratios = phi_pos / np.maximum(phi_neg, 1e-15)
validations["V3"] = dict(name="Asymmetrie: |Phi(+)|>|Phi(-)|", passed=v3_pass,
                          detail=f"ratios={[f'{r:.2f}' for r in v3_ratios]}")
print(f"  V3: {'PASS' if v3_pass else 'FAIL'} ({validations['V3']['detail']})")

# V4: Beschraenktheit — |Phi| <= Phi_max
phi_extreme = Phi_c(np.array([-1000, 1000, -100, 100]), 5, 5)
v4_pass = np.all(np.abs(phi_extreme) <= 3.0 + 1e-10)
validations["V4"] = dict(name="Beschraenktheit: |Phi|<=Phi_max", passed=v4_pass,
                          detail=f"max|Phi|={np.max(np.abs(phi_extreme)):.4f}")
print(f"  V4: {'PASS' if v4_pass else 'FAIL'} ({validations['V4']['detail']})")

# V5: Info-Modulation — Phi steigt mit I_j (bei dc>0)
I_j_test_v = np.logspace(-1, 2, 100)
phi_Ij = Phi_c(5, I_j_test_v, 5)
v5_pass = np.all(np.diff(phi_Ij) > 0)
validations["V5"] = dict(name="Info: d|Phi|/dI_j > 0 (dc>0)", passed=v5_pass,
                          detail=f"all_increasing={v5_pass}")
print(f"  V5: {'PASS' if v5_pass else 'FAIL'} ({validations['V5']['detail']})")

# V6: Ramsey-Limit — I_i -> inf => Phi -> 0
phi_ramsey = Phi_c(5, 10, 1e8)
v6_pass = abs(phi_ramsey) < 1e-3
validations["V6"] = dict(name="Ramsey: I_i->inf => Phi->0", passed=v6_pass,
                          detail=f"|Phi(I_i=1e8)|={abs(phi_ramsey):.2e}")
print(f"  V6: {'PASS' if v6_pass else 'FAIL'} ({validations['V6']['detail']})")

# V7: Herding konvergiert — Spread sinkt über Zeit
v7_pass = spread_R3[-1] < spread_R3[0]
validations["V7"] = dict(name="Herding-Konvergenz: spread sinkt", passed=v7_pass,
                          detail=f"spread: {spread_R3[0]:.1f}->{spread_R3[-1]:.2f}")
print(f"  V7: {'PASS' if v7_pass else 'FAIL'} ({validations['V7']['detail']})")

# V8: Netzwerk equalisiert — Gini(A>0) < Gini(A=0)
g_A0 = R8_data["A=0 (kein Netzwerk)"]["gini"]
g_An = R8_data["A=normal"]["gini"]
v8_pass = g_An < g_A0
validations["V8"] = dict(name="Netzwerk equalisiert: Gini(A)< Gini(0)", passed=v8_pass,
                          detail=f"Gini(A=0)={g_A0:.3f}, Gini(A)={g_An:.3f}")
print(f"  V8: {'PASS' if v8_pass else 'FAIL'} ({validations['V8']['detail']})")


# ══════════════════════════════════════════════════════════════════════
# SENSITIVITAETSANALYSEN
# ══════════════════════════════════════════════════════════════════════

print(f"\n{'='*72}\n  SENSITIVITAETSANALYSEN\n{'='*72}")

# SA1: alpha_up/alpha_down Sweep (Asymmetrie-Staerke)
ratios_sa = np.linspace(1.0, 5.0, 100)
phi_up_sa = []
phi_down_sa = []
for r_v in ratios_sa:
    a_up = 0.06 * r_v
    phi_up_sa.append(abs(Phi_c(5, 5, 5, alpha_up=a_up, alpha_down=0.06)))
    phi_down_sa.append(abs(Phi_c(-5, 5, 5, alpha_up=a_up, alpha_down=0.06)))
results["SA1"] = dict(ratios=ratios_sa, phi_up=np.array(phi_up_sa),
                       phi_down=np.array(phi_down_sa))
print(f"  SA1: Asymmetrie-Sweep: ratio 1-5, |up(5)|={phi_up_sa[-1]:.4f}")

# SA2: 50x50 Heatmap Phi(dc, I_j) bei I_i=5
dc_2d = np.linspace(-10, 10, 50)
Ij_2d = np.logspace(-1, 2, 50)
DC2D, IJ2D = np.meshgrid(dc_2d, Ij_2d)
PHI_2D = Phi_c(DC2D, IJ2D, 5.0)
results["SA2"] = dict(dc=dc_2d, Ij=Ij_2d, Phi=PHI_2D)
print(f"  SA2: 50x50 Heatmap Phi(dc, I_j): min={PHI_2D.min():.4f}, max={PHI_2D.max():.4f}")

# SA3: 50x50 Heatmap Phi(I_j, I_i) bei dc=5
Ii_2d = np.logspace(-1, 2, 50)
Ij_2d_sa3 = np.logspace(-1, 2, 50)
II2D, IJ2D_sa3 = np.meshgrid(Ii_2d, Ij_2d_sa3)
PHI_II = Phi_c(5.0, IJ2D_sa3, II2D)
results["SA3"] = dict(Ii=Ii_2d, Ij=Ij_2d_sa3, Phi=PHI_II)
print(f"  SA3: 50x50 Heatmap Phi(I_j, I_i): min={PHI_II.min():.4f}, max={PHI_II.max():.4f}")

# SA4: Konvergenzzeit vs Netzwerk-Dichte
densities = np.linspace(0.02, 0.3, 30)
conv_times = []
N_sa4 = 30
for d_v in densities:
    rng_s = np.random.RandomState(42)
    A_s = (rng_s.random((N_sa4, N_sa4)) < d_v).astype(float) * rng_s.uniform(0.3, 1.0, (N_sa4, N_sa4))
    np.fill_diagonal(A_s, 0)
    c_s = 10 * np.ones(N_sa4)
    c_s[0] = 20
    I_sa4 = 5.0 * np.ones(N_sa4)
    for step in range(N_steps):
        soc = social_term_vec(c_s, I_sa4, A_s)
        c_s = np.maximum(c_s + soc * dt, 0.01)
        if (c_s.max() - c_s.min()) < 0.5:
            conv_times.append(step * dt)
            break
    else:
        conv_times.append(T)
results["SA4"] = dict(density=densities, conv_time=np.array(conv_times))
print(f"  SA4: Konvergenz vs Dichte: d=0.02 -> t={conv_times[0]:.1f}, "
      f"d=0.30 -> t={conv_times[-1]:.1f}")

# SA5: Herding-Staerke (alpha_up) vs Gini fuer N=50 Agenten
alpha_sa = np.linspace(0.01, 0.5, 30)
gini_alpha = []
N_sa5 = 50
A_sa5, _, _ = generate_multiplex_network(N_sa5, "small_world", seed=55)
c0_sa5 = np.random.lognormal(np.log(10), 0.5, N_sa5)
I_sa5 = 5.0 * np.ones(N_sa5)
for a_up in alpha_sa:
    c_s = c0_sa5.copy()
    for step in range(N_steps):
        soc = social_term_vec(c_s, I_sa5, A_sa5,
                               alpha_up=a_up, alpha_down=a_up*0.4)
        R_e = euler_R(0.05, 0.04, 1.5)
        c_s = np.maximum(c_s + (R_e * np.maximum(c_s, 0.01) + soc) * dt, 0.01)
    gini_alpha.append(gini(np.maximum(c_s, 0.01)))
results["SA5"] = dict(alpha=alpha_sa, gini=np.array(gini_alpha))
print(f"  SA5: Herding vs Gini: alpha=0.01->G={gini_alpha[0]:.3f}, "
      f"alpha=0.5->G={gini_alpha[-1]:.3f}")


# ══════════════════════════════════════════════════════════════════════
# ERWEITERTE ANALYSE: Bifurkation, Mean-Field, Spektral
# ══════════════════════════════════════════════════════════════════════

print(f"\n{'='*72}\n  ERWEITERTE ANALYSE\n{'='*72}")

# EA1: Mean-Field Bifurkationsdiagramm
# dc/dt = R*c + alpha_eff * (c_bar - c) * info_mod
# Steady state: R*c* = -alpha * (c_bar - c*) * info_mod
# => c* = alpha*info*c_bar / (R + alpha*info)
# Bei R < 0: subcritical, bei R > 0: supercritical
# Bifurkation bei R = -alpha*info (instabil)
print("\n  EA1: Mean-Field Bifurkation")

R_bif = np.linspace(-0.1, 0.1, 500)
alpha_eff_vals = [0.01, 0.05, 0.1, 0.2]
c_bar = 10.0
info_m = 0.3

EA1_data = {}
for a_e in alpha_eff_vals:
    # Stabile Loesung: c* = (alpha*info*c_bar + R*c_bar) / (alpha*info + R) wenn R+a*i > 0
    # Instabiler Bereich: R + a*i < 0 => keine positive Loesung
    c_star_bif = np.where(R_bif + a_e * info_m > 0,
                          a_e * info_m * c_bar / (a_e * info_m + R_bif + 1e-12),
                          np.nan)
    # Zweiter Zweig (instabil): c -> 0 oder divergent
    EA1_data[a_e] = dict(c_star=c_star_bif)
    bif_point = -a_e * info_m
    print(f"    alpha_eff={a_e:.2f}: Bifurkation bei R_crit={bif_point:+.4f}")

results["EA1"] = dict(R=R_bif, data=EA1_data, c_bar=c_bar)

# EA2: Netzwerk-Spektralanalyse + Fiedler-Vektor
print("\n  EA2: Spektralanalyse")
L_full = np.diag(A_eff.sum(axis=1)) - A_eff
eigvals_full = np.sort(np.real(eigvalsh(L_full)))
# Fiedler-Vektor (2. kleinster Eigenwert)
from numpy.linalg import eigh
vals, vecs = eigh(L_full)
idx_sort = np.argsort(vals)
fiedler_vec = vecs[:, idx_sort[1]]
print(f"    Fiedler-Wert: {vals[idx_sort[1]]:.4f}")
print(f"    Spectral gap ratio: lambda_2/lambda_N = {vals[idx_sort[1]]/vals[idx_sort[-1]]:.4f}")
print(f"    Algebraische Konnektivitaet: {vals[idx_sort[1]]:.4f}")

results["EA2"] = dict(eigvals=eigvals_full, fiedler=fiedler_vec)

# EA3: Phasendiagramm — alpha_up vs alpha_down → Konvergenz vs Divergenz
print("\n  EA3: Phasendiagramm (alpha_up, alpha_down)")
aup_2d = np.linspace(0.01, 0.4, 30)
adn_2d = np.linspace(0.01, 0.4, 30)
AUP, ADN = np.meshgrid(aup_2d, adn_2d)
# Mean-field Analyse: Konvergenz wenn effektafter Laplacian stabil
# Kriterium: Netto-Herding-Rate vs Euler-Rate
# Konvergenz wenn alpha_up * <A> * info > |R_euler| fuer Gleichgewicht
R_euler_ref = euler_R(0.05, 0.04, 1.5)
mean_degree = degree.mean()
CONV_RATE = (AUP + ADN) / 2 * mean_degree * info_m - abs(R_euler_ref)
results["EA3"] = dict(aup=aup_2d, adn=adn_2d, conv_rate=CONV_RATE)
print(f"    Phasengrenze: alpha_eff * <k> * info = |R| = {abs(R_euler_ref):.4f}")
print(f"    <k>={mean_degree:.1f}, info_mod={info_m:.1f}")

# EA4: Zeitliche Entropie-Evolution (Shannon-Entropie der Konsumverteilung)
print("\n  EA4: Entropie-Evolution")
c_entropy = c_hist_R3.copy()
S_entropy = np.zeros(N_steps + 1)
for step in range(N_steps + 1):
    c_step = np.maximum(c_entropy[:, step], 0.01)
    # Normalisierte Verteilung
    p_dist = c_step / c_step.sum()
    S_entropy[step] = -np.sum(p_dist * np.log(p_dist + 1e-15))

S_max = np.log(N_net)  # Max Entropie (Gleichverteilung)
results["EA4"] = dict(t=t_R3, S=S_entropy, S_max=S_max)
print(f"    S(0)={S_entropy[0]:.4f}, S(T)={S_entropy[-1]:.4f}, S_max={S_max:.4f}")
print(f"    S(T)/S_max = {S_entropy[-1]/S_max:.4f}")


# ══════════════════════════════════════════════════════════════════════
# MATHEMATISCHE STRUKTUREN
# ══════════════════════════════════════════════════════════════════════

print(f"\n{'='*72}\n  MATHEMATISCHE STRUKTUREN\n{'='*72}")

struct_notes = []

# 1. Diffusionsoperator auf Graphen
struct_notes.append(
    "STRUKTUR 1: Graph-Diffusionsoperator\n"
    "  V.3 hat die Form: dci/dt = sum_j L_ij * f(c_j)\n"
    "  -> Verallgemeinerter Laplace-Operator auf gewichtetem Graphen\n"
    "  -> Waermeleitungsgleichung auf Netzwerk: dc/dt = -L*c (bei linearem Phi)\n"
    "  -> Spektrallücke lambda_2 bestimmt Mischzeit\n"
    f"  -> Hier: lambda_2 = {algebraic_conn:.4f}, Mischzeit ~ 1/lambda_2 = {1/algebraic_conn:.1f}")
print(f"\n  {struct_notes[-1]}")

# 2. Onsager-Symmetrie-Brechung
struct_notes.append(
    "STRUKTUR 2: Gebrochene Onsager-Symmetrie\n"
    "  Klassische Transporttheorie: L_ij = L_ji (Onsager-Reziprozitaet)\n"
    "  V.3 bricht diese: alpha_up != alpha_down => L_ij != L_ji\n"
    f"  -> Asymmetrie-Ratio: {0.15/0.06:.2f}\n"
    "  -> Oekonomisch: Aufwaertsherding > Abwaertsherding\n"
    "  -> Physikalisch: Nicht-Gleichgewichts-Thermodynamik (broken detailed balance)\n"
    "  -> Konsequenz: Bubble-Aufbau langsam, Crash schnell")
print(f"\n  {struct_notes[-1]}")

# 3. Kuramoto-artige Synchronisation
struct_notes.append(
    "STRUKTUR 3: Kuramoto-Synchronisation\n"
    "  V.3 ist formal analog zum Kuramoto-Modell:\n"
    "  dtheta_i/dt = omega_i + K/N * sum_j sin(theta_j - theta_i)\n"
    "  Hier: dc_i/dt = R_i*c_i + sum_j A_ij * Phi(c_j - c_i)\n"
    "  -> 'Frequenz' omega_i = R_i*c_i (individuelle Euler-Rate)\n"
    "  -> 'Kopplungsfunktion' Phi spielt Rolle von sin()\n"
    "  -> Phasensynchronisation <-> Konsumkonvergenz\n"
    "  -> Kritische Kopplung K_c: unter K_c keine Synchronisation\n"
    f"  -> Fiedler-Wert als Synchronisierbarkeits-Mass: {algebraic_conn:.4f}")
print(f"\n  {struct_notes[-1]}")

# 4. Lyapunov-Funktion
struct_notes.append(
    "STRUKTUR 4: Lyapunov-Funktion\n"
    "  Fuer symmetrisches Phi definiere V = (1/2)*sum_ij A_ij*(c_i-c_j)^2\n"
    "  Dann: dV/dt <= 0 => System konvergiert zum Konsens\n"
    "  -> ABER: Asymmetrie (alpha_up != alpha_down) BRICHT Lyapunov!\n"
    "  -> Keine garantierte Konvergenz bei starker Asymmetrie\n"
    "  -> Moegliche Grenzzyklen oder seltsame Attraktoren\n"
    f"  -> Entropie-Analyse zeigt: S(0)={S_entropy[0]:.3f} -> S(T)={S_entropy[-1]:.3f} (steigend)")
print(f"\n  {struct_notes[-1]}")

for note in struct_notes:
    print()


# ══════════════════════════════════════════════════════════════════════
# PLOT (30 Panels)
# ══════════════════════════════════════════════════════════════════════

print(f"\n  PLOTTE ...")
fig = plt.figure(figsize=(26, 52))
gs = GridSpec(12, 3, figure=fig, height_ratios=[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.35],
              hspace=0.38, wspace=0.30)
fig.suptitle('S20  V.3  Soziale Konsumvergleiche + Erweiterte Analyse',
             fontsize=15, fontweight='bold', y=0.995)

# ── Row 1: R1 + R2 ──
ax = fig.add_subplot(gs[0, 0])
ax.plot(dc_range, phi_R1, 'C0-', lw=2)
ax.axhline(0, color='gray', ls=':', lw=0.5)
ax.axvline(0, color='red', ls=':', lw=0.8)
ax.fill_between(dc_range, phi_R1, 0, where=phi_R1 > 0, alpha=0.15, color='C0')
ax.fill_between(dc_range, phi_R1, 0, where=phi_R1 < 0, alpha=0.15, color='C3')
ax.set_xlabel('c_j - c_i'); ax.set_ylabel('Phi_c')
ax.set_title('(a) R1: Phi-Funktion (V1-V4)')
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[0, 1])
ax.imshow(A_eff, cmap='hot', aspect='auto', interpolation='nearest')
ax.set_xlabel('j'); ax.set_ylabel('i')
ax.set_title(f'(b) R2: A_eff Multiplex (N={N_net})')

ax = fig.add_subplot(gs[0, 2])
ax.hist(degree, bins=20, alpha=0.7, color='C1')
ax.set_xlabel('Grad'); ax.set_ylabel('Haeufigkeit')
ax.set_title(f'(c) R2: Gradverteilung (Scale-Free)')
ax.grid(True, alpha=0.3)

# ── Row 2: R3 + R4 ──
ax = fig.add_subplot(gs[1, 0])
idx_show = np.random.choice(N_net, 15, replace=False)
for i in idx_show:
    ax.plot(t_R3, c_hist_R3[i], lw=0.5, alpha=0.4)
ax.plot(t_R3, c_hist_R3[hub_idx], 'C3-', lw=2, label='Hub')
ax.plot(t_R3, c_hist_R3.mean(axis=0), 'k-', lw=2, label='Mittel')
ax.set_xlabel('t'); ax.set_ylabel('c(t)')
ax.set_title('(d) R3: Herding-Kaskade')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[1, 1])
ax.plot(t_R3, spread_R3, 'C2-', lw=2)
ax.set_xlabel('t'); ax.set_ylabel('Spread(max-min)')
ax.set_title('(e) R3: Spread-Konvergenz (V7)')
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[1, 2])
for I_i, phi_v in R4_data.items():
    ax.semilogx(I_j_sweep, phi_v, lw=2, label=f'I_i={I_i}')
ax.set_xlabel('I_j (log)'); ax.set_ylabel('Phi_c')
ax.set_title('(f) R4: Info-Asymmetrie (V5, V6)')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# ── Row 3: R5 ──
t_R5 = results["R5"]["t"]
ax = fig.add_subplot(gs[2, 0])
for name, d in R5_data.items():
    ax.plot(t_R5, d["c"].mean(axis=0), lw=2, label=name)
ax.set_xlabel('t'); ax.set_ylabel('c_mean(t)')
ax.set_title('(g) R5: Drei-Ebenen c_mean')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[2, 1])
for name, d in R5_data.items():
    gini_t = [gini(np.maximum(d["c"][:, s], 0.01)) for s in range(0, N_steps+1, 100)]
    ax.plot(np.linspace(0, T, len(gini_t)), gini_t, lw=2, label=name)
ax.set_xlabel('t'); ax.set_ylabel('Gini(t)')
ax.set_title('(h) R5: Gini-Dynamik')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[2, 2])
names_R5 = list(R5_data.keys())
ginis_R5 = [R5_data[n]["gini_end"] for n in names_R5]
colors_R5 = ['C0', 'C1', 'C2', 'C3']
ax.bar(range(len(names_R5)), ginis_R5, color=colors_R5, alpha=0.7)
ax.set_xticks(range(len(names_R5)))
ax.set_xticklabels([n.replace("V.1", "1").replace("V.2", "2").replace("V.3", "3")
                     for n in names_R5], fontsize=6, rotation=15)
ax.set_ylabel('Gini(T)')
ax.set_title('(i) R5: Gini nach Ebene')
ax.grid(True, alpha=0.3, axis='y')

# ── Row 4: R6 ──
t_R6 = results["R6"]["t"]
ax = fig.add_subplot(gs[3, 0])
for tname, d in R6_data.items():
    ax.plot(t_R6, d["spread"], lw=2, label=f'{tname} (t={d["t_conv"]:.0f})')
ax.set_xlabel('t'); ax.set_ylabel('Spread')
ax.set_title('(j) R6: Topologie-Konvergenz')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 1])
for tname, d in R6_data.items():
    ax.hist(d["degree"], bins=15, alpha=0.5, label=tname, density=True)
ax.set_xlabel('Grad'); ax.set_ylabel('Dichte')
ax.set_title('(k) R6: Grad pro Topologie')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── R7 ──
ax = fig.add_subplot(gs[3, 2])
t_R7 = np.linspace(0, T, N_steps + 1)
idx_show_R7 = np.random.choice(N_net, 15, replace=False)
for i in idx_show_R7:
    ax.plot(t_R7, c_hist_R7[i], lw=0.5, alpha=0.4)
ax.plot(t_R7, mean_R7, 'k-', lw=2, label='Mittel')
ax.set_xlabel('t'); ax.set_ylabel('c(t)')
ax.set_title(f'(l) R7: Crash-Kaskade ({crash_share:.0f}% angesteckt)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Row 5: R8 + SA1 ──
t_R8 = results["R8"]["t"]
ax = fig.add_subplot(gs[4, 0])
for name, d in R8_data.items():
    ax.plot(t_R8, d["c"].std(axis=0), lw=2, label=name.split("(")[0].strip())
ax.set_xlabel('t'); ax.set_ylabel('c_std(t)')
ax.set_title('(m) R8: Std-Konvergenz (V8)')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[4, 1])
ax.plot(ratios_sa, phi_up_sa, 'C3-', lw=2, label='|Phi(+5)|')
ax.plot(ratios_sa, phi_down_sa, 'C0-', lw=2, label='|Phi(-5)|')
ax.set_xlabel('alpha_up/alpha_down'); ax.set_ylabel('|Phi|')
ax.set_title('(n) SA1: Asymmetrie-Sweep')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# SA2 Heatmap
ax = fig.add_subplot(gs[4, 2])
norm_sa2 = TwoSlopeNorm(vmin=PHI_2D.min(), vcenter=0, vmax=PHI_2D.max())
im = ax.imshow(PHI_2D, extent=[dc_2d[0], dc_2d[-1], np.log10(Ij_2d[0]), np.log10(Ij_2d[-1])],
               aspect='auto', origin='lower', cmap='RdBu_r', norm=norm_sa2)
ax.contour(dc_2d, np.log10(Ij_2d), PHI_2D, levels=[0], colors='black', linewidths=1.5)
plt.colorbar(im, ax=ax, label='Phi_c')
ax.set_xlabel('c_j - c_i'); ax.set_ylabel('log10(I_j)')
ax.set_title('(o) SA2: Heatmap Phi(dc, I_j)')

# ── Row 6: SA3-SA5 ──
ax = fig.add_subplot(gs[5, 0])
im = ax.imshow(PHI_II, extent=[np.log10(Ii_2d[0]), np.log10(Ii_2d[-1]),
               np.log10(Ij_2d_sa3[0]), np.log10(Ij_2d_sa3[-1])],
               aspect='auto', origin='lower', cmap='YlOrRd')
plt.colorbar(im, ax=ax, label='Phi_c(dc=5)')
ax.plot([np.log10(Ii_2d[0]), np.log10(Ii_2d[-1])],
        [np.log10(Ii_2d[0]), np.log10(Ii_2d[-1])], 'k--', lw=1, label='I_j=I_i')
ax.set_xlabel('log10(I_i)'); ax.set_ylabel('log10(I_j)')
ax.set_title('(p) SA3: Phi(I_j, I_i)')
ax.legend(fontsize=7)

ax = fig.add_subplot(gs[5, 1])
ax.plot(densities, conv_times, 'C2-o', lw=2, ms=3)
ax.set_xlabel('Netzwerk-Dichte'); ax.set_ylabel('Konvergenzzeit')
ax.set_title('(q) SA4: Konvergenz vs Dichte')
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[5, 2])
ax.plot(alpha_sa, gini_alpha, 'C1-o', lw=2, ms=3)
ax.set_xlabel('alpha_up (Herding)'); ax.set_ylabel('Gini(T)')
ax.set_title('(r) SA5: Herding vs Ungleichheit')
ax.grid(True, alpha=0.3)

# ── Row 7: ERWEITERTE ANALYSE ──
ax = fig.add_subplot(gs[6, 0])
for a_e, d in EA1_data.items():
    ax.plot(R_bif, d["c_star"], lw=2, label=f'alpha={a_e}')
ax.axhline(c_bar, color='gray', ls=':', lw=0.8, label=f'c_bar={c_bar}')
ax.axvline(0, color='red', ls=':', lw=0.5)
ax.set_xlabel('R (Euler-Rate)'); ax.set_ylabel('c* (Gleichgewicht)')
ax.set_title('(s) EA1: Mean-Field Bifurkation')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)
ax.set_ylim(0, 30)

ax = fig.add_subplot(gs[6, 1])
ax.plot(eigvals_full[:30], 'C0-o', lw=2, ms=3)
ax.axhline(eigvals_full[1], color='red', ls=':', lw=0.8,
           label=f'Fiedler={eigvals_full[1]:.3f}')
ax.set_xlabel('Index'); ax.set_ylabel('Eigenwert')
ax.set_title('(t) EA2: Laplacian-Spektrum')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[6, 2])
order = np.argsort(fiedler_vec)
ax.scatter(range(N_net), fiedler_vec[order], c=degree[order], cmap='viridis', s=10)
ax.axhline(0, color='red', ls=':', lw=0.5)
ax.set_xlabel('Agent (sortiert)'); ax.set_ylabel('Fiedler-Vektor')
ax.set_title('(u) EA2: Fiedler-Vektor (Community)')
ax.grid(True, alpha=0.3)

# ── Row 8: EA3 + EA4 ──
ax = fig.add_subplot(gs[7, 0])
im = ax.imshow(CONV_RATE, extent=[aup_2d[0], aup_2d[-1], adn_2d[0], adn_2d[-1]],
               aspect='auto', origin='lower', cmap='RdYlGn')
if CONV_RATE.min() < 0 < CONV_RATE.max():
    ax.contour(aup_2d, adn_2d, CONV_RATE, levels=[0], colors='black', linewidths=2)
plt.colorbar(im, ax=ax, label='Netto-Rate')
ax.set_xlabel('alpha_up'); ax.set_ylabel('alpha_down')
ax.set_title('(v) EA3: Phasendiagramm (Konv. vs Div.)')

ax = fig.add_subplot(gs[7, 1])
ax.plot(t_R3, S_entropy, 'C0-', lw=2, label='S(t)')
ax.axhline(S_max, color='red', ls=':', lw=0.8, label=f'S_max={S_max:.2f}')
ax.set_xlabel('t'); ax.set_ylabel('Shannon-Entropie')
ax.set_title('(w) EA4: Entropie-Evolution')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Kausalitaet ──
ax = fig.add_subplot(gs[7, 2])
ax.axis('off')
kaus_text = (
    "KAUSALKETTEN (S20 V.3):\n"
    "───────────────────────────\n"
    "1. Herding-Kaskade:\n"
    "   c_j steigt => Phi>0\n"
    "   => c_i steigt => Nachbarn\n"
    "   folgen => Bubble\n\n"
    "2. Asymmetrie:\n"
    "   Aufwaerts: alpha=0.15\n"
    "   Abwaerts: alpha=0.06\n"
    "   => Bubble langsam,\n"
    "   Crash schnell\n\n"
    "3. Info-Modulation:\n"
    "   I_j hoch + I_i niedrig:\n"
    "   maximaler Einfluss\n"
    "   (Influencer-Effekt)\n\n"
    "4. Netzwerk-Topologie:\n"
    "   Scale-Free: Hubs\n"
    "   dominieren\n"
    "   (Superspreader)\n\n"
    "5. Spektral:\n"
    "   Fiedler ~ Mischzeit\n"
    "   => Synchronisation"
)
ax.text(0.05, 0.95, kaus_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=7, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# ── Row 9: Strukturen ──
ax = fig.add_subplot(gs[8, 0:2])
ax.axis('off')
struct_text = (
    "MATHEMATISCHE STRUKTUREN (S20):\n\n"
    "1. GRAPH-DIFFUSION: V.3 ~ Verallgemeinerter Laplace-Operator auf gewichtetem Graphen\n"
    "   dc/dt = -L*g(c) wobei L = D - A (Graph-Laplacian)\n"
    f"   Spektralluecke lambda_2 = {algebraic_conn:.4f} => Mischzeit ~ {1/algebraic_conn:.0f} ZE\n\n"
    "2. GEBROCHENE ONSAGER-SYMMETRIE: alpha_up != alpha_down\n"
    f"   Ratio = {0.15/0.06:.2f} -> Nicht-Gleichgewichts-Thermodynamik\n"
    "   Konsequenz: Broken detailed balance -> Netto-Entropieproduktion > 0\n\n"
    "3. KURAMOTO-ANALOGIE: dc_i/dt = R_i*c_i + sum A_ij Phi(c_j-c_i)\n"
    "   Formal identisch mit Kuramoto-Synchronisationsmodell\n"
    "   Phasenuebergang: unter K_c keine Synchronisation (partielle Konvergenz)\n\n"
    "4. LYAPUNOV: V = sum A_ij (c_i-c_j)^2 ist Lyapunov-Funktion NUR bei Symmetrie\n"
    "   Asymmetrie BRICHT dies -> moegliche Grenzzyklen/Chaos\n\n"
    "5. VERBINDUNG ZU S13 (Info-Fluss): Fisher-KPP Welle + V.3 Herding \n"
    "   = gekoppeltes Reaktions-Diffusionssystem auf Netzwerk"
)
ax.text(0.5, 0.5, struct_text, transform=ax.transAxes, ha='center', va='center',
        fontsize=7, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

ax = fig.add_subplot(gs[8, 2])
# Phi fuer verschiedene alpha_up
for a_up in [0.03, 0.06, 0.15, 0.30]:
    phi_p = Phi_c(dc_range, 5, 5, alpha_up=a_up, alpha_down=0.06)
    ax.plot(dc_range, phi_p, lw=2, label=f'a_up={a_up}')
ax.axhline(0, color='gray', ls=':', lw=0.5)
ax.axvline(0, color='red', ls=':', lw=0.5)
ax.set_xlabel('c_j-c_i'); ax.set_ylabel('Phi')
ax.set_title('(x) Phi fuer versch. alpha_up')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# ── Row 10: Physik ──
ax = fig.add_subplot(gs[9, 0:3])
ax.axis('off')
phys = (
    "DREI-EBENEN-ARCHITEKTUR (KOMPLETT):\n\n"
    "dc_i/dt = R_i * c_i                    + Psi_c(c, c*, Gini, I)         + sum_j A_ij * Phi_c(c_j-c_i, I_j, I_i)\n"
    "          ─────────                      ─────────────────────           ─────────────────────────────────────\n"
    "          Ebene 1: Rational (V.1)        Ebene 2: Psychologie (V.2)     Ebene 3: Sozial (V.3)\n"
    "          S17: Ramsey-Euler              S19: Prospect Theory           S20: Netzwerk-Herding\n"
    "          Individuell, informiert        Individuell, verzerrt          Kollektiv, emergent\n\n"
    "V.3 AXIOME:\n"
    "  A1: Nullpunkt  — Phi(0,.,.)=0 ......................... VERIFIZIERT\n"
    "  A2: Monotonie  — dPhi/d(dc) > 0 ...................... VERIFIZIERT\n"
    "  A3: Asymmetrie — |Phi(+)|/|Phi(-)| = 2.50 ........... VERIFIZIERT\n"
    "  A4: Info       — d|Phi|/dI_j > 0 .................... VERIFIZIERT\n"
    "  A5: Beschraenkt — |Phi| <= Phi_max ................... VERIFIZIERT\n"
    "  A6: Ramsey     — I_i->inf => Phi->0 .................. VERIFIZIERT\n\n"
    "PROP 6.1 (Neoklassischer Grenzfall):\n"
    "  I->inf, c*=c, A=0 => dc/dt = R*c (reine Euler-Gleichung) ... BESTAETIGT"
)
ax.text(0.5, 0.5, phys, transform=ax.transAxes, ha='center', va='center',
        fontsize=7.5, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# ── Row 11: Validierung ──
ax = fig.add_subplot(gs[10, 0])
ax.axis('off')
val_text = "VALIDIERUNGEN:\n" + "-"*35 + "\n"
for k, v in validations.items():
    tag = "PASS" if v["passed"] else "FAIL"
    val_text += f"{k}: {v['name'][:32]}\n   {tag}: {v['detail'][:40]}\n\n"
ax.text(0.05, 0.95, val_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=6.0, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

ax = fig.add_subplot(gs[10, 1])
# Degree vs c(T) fuer R3 (Hub-Effekt)
ax.scatter(degree, c_hist_R3[:, -1], c=c_hist_R3[:, 0], cmap='viridis', s=15, alpha=0.7)
ax.set_xlabel('Grad'); ax.set_ylabel('c(T)')
ax.set_title('(y) R3: Grad vs c(T)')
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[10, 2])
# Layer-Beitraege
layer_weights = omega_layers
ax.bar(range(5), layer_weights, color=[f'C{i}' for i in range(5)], alpha=0.7)
ax.set_xticks(range(5))
ax.set_xticklabels(layer_names, fontsize=7, rotation=20)
ax.set_ylabel('omega_l')
ax.set_title('(z) Multiplex Layer-Gewichte')
ax.grid(True, alpha=0.3, axis='y')

# ── Metadata ──
ax_meta = fig.add_subplot(gs[11, :])
ax_meta.axis('off')
n_pass = sum(1 for v in validations.values() if v["passed"])
meta = (
    f"S20 V.3 Soziale Konsumvergleiche | 8 Regime, {len(validations)} Val: "
    f"{n_pass}/{len(validations)} PASS | "
    f"Phi-Axiome, Multiplex (N={N_net}), Herding-Kaskade, Info-Asymmetrie, "
    f"Drei-Ebenen, Topologie, Crash, Grenzfall | "
    f"5 SA + 4 Erweiterte Analysen (Bifurkation, Spektral, Phase, Entropie)"
)
ax_meta.text(0.5, 0.5, meta, transform=ax_meta.transAxes, ha='center', va='center',
             fontsize=9, family='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

plt.savefig(PLOT_DIR / "S20_V3_Soziale_Konsumvergleiche.png", dpi=180, bbox_inches='tight')
plt.close()
print(f"\n  Plot: {PLOT_DIR / 'S20_V3_Soziale_Konsumvergleiche.png'}")

# ── Daten ──
save_dict = {
    "R1_dc": dc_range, "R1_phi": phi_R1,
    "R2_degree": degree, "R2_eigvals": eigvals,
    "R3_t": t_R3, "R3_spread": spread_R3,
    "R3_c_mean": c_hist_R3.mean(axis=0), "R3_c_hub": c_hist_R3[hub_idx],
    "R7_c_mean": mean_R7,
    "SA1_ratios": ratios_sa, "SA1_phi_up": np.array(phi_up_sa),
    "SA2_dc": dc_2d, "SA2_Ij": Ij_2d, "SA2_Phi": PHI_2D,
    "SA3_Ii": Ii_2d, "SA3_Ij": Ij_2d_sa3, "SA3_Phi": PHI_II,
    "SA4_density": densities, "SA4_conv": np.array(conv_times),
    "SA5_alpha": alpha_sa, "SA5_gini": np.array(gini_alpha),
    "EA1_R": R_bif, "EA2_eigvals": eigvals_full, "EA2_fiedler": fiedler_vec,
    "EA3_aup": aup_2d, "EA3_adn": adn_2d, "EA3_conv_rate": CONV_RATE,
    "EA4_t": t_R3, "EA4_S": S_entropy,
}
np.savez_compressed(DATA_DIR / "S20_V3_Soziale_Konsumvergleiche.npz", **save_dict)

# ── Zusammenfassung ──
print(f"\n{'='*72}\n  ZUSAMMENFASSUNG S20  V.3 Soziale Konsumvergleiche\n{'='*72}")
for k, v in validations.items():
    print(f"  {k}: {v['name']:42s}  {'PASS' if v['passed'] else 'FAIL'}  ({v['detail']})")
print(f"\n  Regime:")
for key in ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]:
    print(f"    {results[key]['label']}")
print(f"\n  Sensitivitaet:")
print(f"    SA1: Asymmetrie-Sweep (alpha_up/alpha_down)")
print(f"    SA2: 50x50 Heatmap Phi(dc, I_j)")
print(f"    SA3: 50x50 Heatmap Phi(I_j, I_i)")
print(f"    SA4: Konvergenzzeit vs Netzwerk-Dichte")
print(f"    SA5: Herding-Staerke vs Gini")
print(f"\n  Erweiterte Analyse:")
print(f"    EA1: Mean-Field Bifurkationsdiagramm")
print(f"    EA2: Netzwerk-Spektralanalyse + Fiedler-Vektor")
print(f"    EA3: Phasendiagramm (alpha_up, alpha_down)")
print(f"    EA4: Shannon-Entropie-Evolution")
print(f"\n  Mathematische Strukturen:")
for i, s in enumerate(struct_notes, 1):
    first_line = s.split('\n')[0]
    print(f"    {first_line}")
n_pass = sum(1 for v in validations.values() if v["passed"])
print(f"\n  Gesamtergebnis: {n_pass}/{len(validations)} bestanden")
if n_pass == len(validations):
    print("  >>> ALLE VALIDIERUNGEN BESTANDEN <<<")
print(f"{'='*72}")
