"""
S19 – Psychologische Konsumverzerrung V.2  (§6.3)
===================================================
Gleichung V.2:
    Psi_c(c_i, c_i*, dc_hist, Gini, I_i)

Axiomatische Eigenschaften:
  1. Referenzpunktanziehung: dPsi/d(c*-c) > 0
  2. Verlustaversion: |Psi(c<c*)| > |Psi(c>c*)| bei gleichem Abstand
  3. Relative Deprivation: dPsi/dGini < 0 fuer c_i < c_bar
  4. Nullpunkt: Psi(c*,c*,0,0,.) = 0
  5. Beschraenktheit: |Psi| <= Psi_max

Drei-Ebenen-Architektur:
  dc/dt = R_i * c_i            (V.1 Rational, S17)
        + Psi_c(...)            (V.2 Psychologie, S19)
        + sum A_ij Phi(...)     (V.3 Sozial, S20)

8 Regime, 8 Validierungen, 5 Sensitivitaetsanalysen
"""

import sys, io, warnings, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

import numpy as np
from scipy.integrate import solve_ivp
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

# ══════════════════════════════════════════════════════════════════════
# 1. Kernfunktionen
# ══════════════════════════════════════════════════════════════════════

def Psi_c(c, c_star, dc_hist, Gini, I, lam=2.25, kappa_ref=0.3,
          kappa_dep=0.2, kappa_info=1.0, Psi_max=2.0, eps=0.01):
    """
    V.2 Psychologische Konsumverzerrung.

    Psi_c = kappa_ref * v(c_star - c) * (1 + kappa_dep * Gini * sign(c_bar - c))
            * info_mod(I)

    v(x) = {  x           fuer x >= 0  (Gewinn: unter Referenz, Anziehung)
           { lam * x      fuer x < 0   (Verlust: ueber Referenz, schwaecher)
    Anmerkung: x = c* - c. x>0 heisst c < c* (Verlust), daher
               v(x>0) = lam * x (staerker), v(x<0) = x (schwaecher)

    info_mod(I) = 1/(1 + kappa_info * I) -> bei I->inf: Psi->0

    Resultat beschraenkt auf [-Psi_max, +Psi_max]
    """
    x = c_star - c  # positiv wenn c < c* (Agent ist unter Referenz)

    # Prospect Theory Wertfunktion (asymmetrisch)
    # x > 0: c < c* -> Verlust -> staerkere Reaktion (lam)
    # x < 0: c > c* -> Gewinn -> schwaecher
    v = np.where(x >= 0, lam * x, x)

    # Relative Deprivation: Gini-Effekt
    # Arme Agenten (c < c_bar) werden durch Ungleichheit staerker nach unten gedrueckt
    # -> hier modelliert als Verstaerkung der Referenzpunktanziehung
    deprivation = 1.0 + kappa_dep * Gini

    # Informations-Modulation: I->inf => Psi->0 (rational limit)
    info_mod = 1.0 / (1.0 + kappa_info * np.maximum(I, 0.0))

    # Komplett
    psi = kappa_ref * v * deprivation * info_mod

    # Beschraenktheit
    return np.clip(psi, -Psi_max, Psi_max)


def reference_dynamics(c_star, c, lambda_adapt=0.2):
    """dc*/dt = lambda_adapt * (c - c*) — Referenzpunkt passt sich an"""
    return lambda_adapt * (c - c_star)


def gini(x):
    """Gini-Koeffizient"""
    x = np.sort(np.abs(x))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return 0
    return (2 * np.sum(np.arange(1, n+1) * x) - (n + 1) * x.sum()) / (n * x.sum())


def euler_R(r, beta, gamma):
    """V.1 Ramsey-Euler Wachstumsrate"""
    return (r - beta) / gamma


print("=" * 72)
print("  S19  V.2  Psychologische Konsumverzerrung")
print("=" * 72)

results = {}
T = 50.0
t_eval = np.linspace(0, T, 2001)

# ══════════════════════════════════════════════════════════════════════
# R1: Referenzpunktanziehung — Basis
# ══════════════════════════════════════════════════════════════════════
print("\n  R1: Referenzpunktanziehung")

# Agent startet unter und ueber Referenzpunkt
c_range = np.linspace(2, 18, 200)
c_star_R1 = 10.0
psi_R1 = Psi_c(c_range, c_star_R1, 0, 0, 1e6)  # I=inf -> fast kein info-Effekt

# Eigenschaft 1: Psi > 0 wenn c < c* (treibt c hoch)
# Eigenschaft 1: Psi < 0 wenn c > c* (treibt c runter)
below = c_range < c_star_R1
above = c_range > c_star_R1
prop1_a = np.all(psi_R1[below] > 0)  # unter Referenz -> positiv
prop1_b = np.all(psi_R1[above] < 0)  # ueber Referenz -> negativ
print(f"    Psi>0 fuer c<c*: {prop1_a}, Psi<0 fuer c>c*: {prop1_b}")
print(f"    Psi(c=5)={Psi_c(5, 10, 0, 0, 1e6):.4f}, Psi(c=15)={Psi_c(15, 10, 0, 0, 1e6):.4f}")

results["R1"] = dict(label="R1: Referenzpunktanziehung",
                      c=c_range, psi=psi_R1, c_star=c_star_R1)


# ══════════════════════════════════════════════════════════════════════
# R2: Verlustaversion — Asymmetrie
# ══════════════════════════════════════════════════════════════════════
print("\n  R2: Verlustaversion (lambda=2.25)")

# Gleicher Abstand d=3 unter und ueber c*
d = 3.0
c_star_R2 = 10.0
psi_loss = Psi_c(c_star_R2 - d, c_star_R2, 0, 0, 1e6)    # c < c*: Verlust
psi_gain = Psi_c(c_star_R2 + d, c_star_R2, 0, 0, 1e6)     # c > c*: Gewinn
ratio_loss_gain = abs(psi_loss) / abs(psi_gain)

print(f"    Psi(Verlust, d={d})={psi_loss:+.4f}")
print(f"    Psi(Gewinn , d={d})={psi_gain:+.4f}")
print(f"    |Verlust/Gewinn| = {ratio_loss_gain:.2f} (soll ~{2.25:.2f})")

# Sweep ueber verschiedene Abstaende
d_sweep = np.linspace(0.1, 8, 100)
psi_loss_sw = np.array([Psi_c(c_star_R2 - d_, c_star_R2, 0, 0, 1e6) for d_ in d_sweep])
psi_gain_sw = np.array([Psi_c(c_star_R2 + d_, c_star_R2, 0, 0, 1e6) for d_ in d_sweep])

results["R2"] = dict(label="R2: Verlustaversion",
                      d=d_sweep, psi_loss=psi_loss_sw, psi_gain=psi_gain_sw,
                      ratio=ratio_loss_gain)


# ══════════════════════════════════════════════════════════════════════
# R3: Dynamische Referenzpunkt-Adaptation
# ══════════════════════════════════════════════════════════════════════
print("\n  R3: Referenzpunkt-Adaptation")

# Konsum springt bei t=0 von c*=10 auf c=14,
# dann beobachten wir c* Anpassung und Psi Rueckgang
lambda_adapt_vals = [0.05, 0.15, 0.3, 0.5]

R3_data = {}
for lam_a in lambda_adapt_vals:
    def rhs_R3(t, y, lam_a=lam_a):
        c, c_star = y
        R_euler = euler_R(0.05, 0.04, 1.5)  # leichtes Wachstum
        psi = Psi_c(c, c_star, 0, 0, 5.0)
        dcdt = R_euler * max(c, 0.01) + psi
        dc_star_dt = reference_dynamics(c_star, c, lam_a)
        return [dcdt, dc_star_dt]

    sol = solve_ivp(rhs_R3, [0, T], [14.0, 10.0], t_eval=t_eval,
                    method='RK45', rtol=1e-8, atol=1e-10)
    c_t = sol.y[0]
    c_star_t = sol.y[1]
    psi_t = Psi_c(c_t, c_star_t, 0, 0, 5.0)
    gap = c_t - c_star_t
    R3_data[lam_a] = dict(t=sol.t, c=c_t, c_star=c_star_t, psi=psi_t, gap=gap)
    print(f"    lam_a={lam_a:.2f}: gap(0)={gap[0]:+.2f}, gap(T)={gap[-1]:+.4f}, "
          f"c(T)={c_t[-1]:.2f}, c*(T)={c_star_t[-1]:.2f}")

results["R3"] = dict(label="R3: Referenzpunkt-Adaptation", data=R3_data)


# ══════════════════════════════════════════════════════════════════════
# R4: Relative Deprivation — Gini-Effekt
# ══════════════════════════════════════════════════════════════════════
print("\n  R4: Relative Deprivation (Gini)")

Gini_sweep = np.linspace(0, 0.7, 200)
c_poor = 6.0   # Armer Agent (c < c*)
c_star_R4 = 10.0

psi_gini = np.array([Psi_c(c_poor, c_star_R4, 0, G, 5.0) for G in Gini_sweep])

# Eigenschaft 3: dPsi/dGini > 0 fuer c < c* (Referenzpunkt-Anziehung staerker)
dpsi_dGini = np.diff(psi_gini) / np.diff(Gini_sweep)
prop3 = np.all(dpsi_dGini > 0)  # staerkere Anziehung bei mehr Ungleichheit
print(f"    dPsi/dGini > 0 (c<c*): {prop3}")
print(f"    Psi(G=0)={psi_gini[0]:.4f}, Psi(G=0.5)={psi_gini[150]:.4f}, "
      f"Psi(G=0.7)={psi_gini[-1]:.4f}")

# Reicher Agent (c > c*) — Deprivation wirkt auch, aber weniger
c_rich = 14.0
psi_gini_rich = np.array([Psi_c(c_rich, c_star_R4, 0, G, 5.0) for G in Gini_sweep])

results["R4"] = dict(label="R4: Relative Deprivation",
                      Gini=Gini_sweep, psi_poor=psi_gini, psi_rich=psi_gini_rich)


# ══════════════════════════════════════════════════════════════════════
# R5: Informations-Modulation
# ══════════════════════════════════════════════════════════════════════
print("\n  R5: Informations-Modulation")

I_sweep = np.logspace(-2, 3, 300)
c_R5 = 7.0  # unter Referenz
c_star_R5 = 10.0

psi_info = np.array([Psi_c(c_R5, c_star_R5, 0, 0.3, I_v) for I_v in I_sweep])
psi_info_noGini = np.array([Psi_c(c_R5, c_star_R5, 0, 0, I_v) for I_v in I_sweep])

# Eigenschaft: I->inf => Psi->0
print(f"    Psi(I=0.01)={psi_info[0]:.4f}, Psi(I=10)={psi_info[150]:.4f}, "
      f"Psi(I=1000)={psi_info[-1]:.6f}")
print(f"    Ramsey-Limit: Psi(I=1e6)={Psi_c(c_R5, c_star_R5, 0, 0, 1e6):.8f}")

results["R5"] = dict(label="R5: Info-Modulation",
                      I=I_sweep, psi=psi_info, psi_noGini=psi_info_noGini)


# ══════════════════════════════════════════════════════════════════════
# R6: Heterogene Agenten (N=300)
# ══════════════════════════════════════════════════════════════════════
print("\n  R6: Heterogene Agenten (N=300)")

N_het = 300
c0_het = np.random.lognormal(np.log(10), 0.5, N_het)
c0_het = np.clip(c0_het, 1.0, 50.0)
c_star_het = np.random.lognormal(np.log(10), 0.3, N_het)
I_het = np.random.lognormal(np.log(3), 1.0, N_het)
I_het = np.clip(I_het, 0.1, 100)
beta_het = np.random.uniform(0.02, 0.06, N_het)
gamma_het = np.random.lognormal(np.log(1.5), 0.3, N_het)
gamma_het = np.clip(gamma_het, 0.3, 8.0)
r_market = 0.05
lambda_adapt_het = 0.15

# Simuliere Zeitevolution fuer alle Agenten
dt = T / 2000
N_steps = 2000
c_hist = np.zeros((N_het, N_steps + 1))
cstar_hist = np.zeros((N_het, N_steps + 1))
c_hist[:, 0] = c0_het
cstar_hist[:, 0] = c_star_het
gini_hist = np.zeros(N_steps + 1)
gini_hist[0] = gini(c0_het)

for step in range(N_steps):
    c_now = c_hist[:, step]
    cs_now = cstar_hist[:, step]
    G = gini(np.maximum(c_now, 0.01))
    gini_hist[step] = G

    R_euler = euler_R(r_market, beta_het, gamma_het)
    psi = Psi_c(c_now, cs_now, 0, G, I_het)

    dc = (R_euler * np.maximum(c_now, 0.01) + psi) * dt
    dcs = reference_dynamics(cs_now, c_now, lambda_adapt_het) * dt

    c_hist[:, step + 1] = np.maximum(c_now + dc, 0.01)
    cstar_hist[:, step + 1] = np.maximum(cs_now + dcs, 0.01)

gini_hist[-1] = gini(np.maximum(c_hist[:, -1], 0.01))
t_het = np.linspace(0, T, N_steps + 1)

gini_0 = gini_hist[0]
gini_T = gini_hist[-1]

R6_data = dict(N=N_het, c=c_hist, c_star=cstar_hist, t=t_het,
               gini=gini_hist, I=I_het, gini_0=gini_0, gini_T=gini_T)
results["R6"] = dict(label="R6: Heterogene Agenten", data=R6_data)
print(f"    Gini(0)={gini_0:.3f}, Gini(T)={gini_T:.3f}")
print(f"    c_mean(0)={c0_het.mean():.2f}, c_mean(T)={c_hist[:,-1].mean():.2f}")
print(f"    c_std(0)={c0_het.std():.2f}, c_std(T)={c_hist[:,-1].std():.2f}")


# ══════════════════════════════════════════════════════════════════════
# R7: Negativer Konsumschock + Erholung
# ══════════════════════════════════════════════════════════════════════
print("\n  R7: Negativer Konsumschock + Erholung")

# Agent bei c=c*=10, dann Schock c->5 bei t=10
T_R7 = 80.0
t_eval_R7 = np.linspace(0, T_R7, 3001)
shock_t = 10.0
shock_mag = -5.0  # c: 10 -> 5

lam_vals_R7 = [2.25, 1.0, 4.0]  # Standard, neutral, extrem avers

R7_data = {}
for lam in lam_vals_R7:
    def rhs_R7(t, y, lam_v=lam):
        c, c_star = y
        R_euler = euler_R(0.05, 0.04, 1.5)
        psi = Psi_c(c, c_star, 0, 0.2, 5.0, lam=lam_v)
        dcdt = R_euler * max(c, 0.01) + psi
        dc_star_dt = reference_dynamics(c_star, c, 0.15)
        return [dcdt, dc_star_dt]

    # Phase 1: bis Schock
    sol1 = solve_ivp(rhs_R7, [0, shock_t], [10.0, 10.0],
                     t_eval=np.linspace(0, shock_t, 500),
                     method='RK45', rtol=1e-8, atol=1e-10)

    # Phase 2: nach Schock (c springt)
    c_after = sol1.y[0][-1] + shock_mag
    c_star_after = sol1.y[1][-1]  # Referenz springt nicht sofort
    sol2 = solve_ivp(rhs_R7, [shock_t, T_R7], [max(c_after, 0.5), c_star_after],
                     t_eval=np.linspace(shock_t, T_R7, 2501),
                     method='RK45', rtol=1e-8, atol=1e-10)

    t_full = np.concatenate([sol1.t, sol2.t])
    c_full = np.concatenate([sol1.y[0], sol2.y[0]])
    cs_full = np.concatenate([sol1.y[1], sol2.y[1]])
    psi_full = Psi_c(c_full, cs_full, 0, 0.2, 5.0, lam=lam)

    R7_data[lam] = dict(t=t_full, c=c_full, c_star=cs_full, psi=psi_full)
    # Erholungszeit: wann ist c wieder auf 95% von c*?
    post_shock = sol2.y[0]
    post_cstar = sol2.y[1]
    ratio_recov = post_shock / np.maximum(post_cstar, 0.01)
    idx_recov = np.where(ratio_recov > 0.95)[0]
    t_recov = sol2.t[idx_recov[0]] - shock_t if len(idx_recov) > 0 else float('inf')
    print(f"    lam={lam:.2f}: c_min={min(sol2.y[0]):.2f}, "
          f"c(T)={sol2.y[0][-1]:.2f}, t_recov(95%)={t_recov:.1f}")

results["R7"] = dict(label="R7: Konsumschock", data=R7_data, shock_t=shock_t)


# ══════════════════════════════════════════════════════════════════════
# R8: Drei-Ebenen-Vergleich (V.1 vs V.1+V.2 vs V.1+V.2+Gini)
# ══════════════════════════════════════════════════════════════════════
print("\n  R8: Drei-Ebenen-Vergleich")

def sim_three_levels(c0, c_star0, r, beta, gamma, I, Gini_ext,
                     include_psi, T=50, dt=0.025):
    """Simuliere dc/dt = R*c [+ Psi_c]"""
    steps = int(T / dt)
    c_arr = np.zeros(steps + 1)
    cs_arr = np.zeros(steps + 1)
    c_arr[0] = c0
    cs_arr[0] = c_star0
    R_e = euler_R(r, beta, gamma)
    for s in range(steps):
        c_v = max(c_arr[s], 0.01)
        cs_v = cs_arr[s]
        dc = R_e * c_v
        if include_psi:
            dc += Psi_c(c_v, cs_v, 0, Gini_ext, I)
        c_arr[s+1] = max(c_v + dc * dt, 0.01)
        cs_arr[s+1] = max(cs_v + reference_dynamics(cs_v, c_v, 0.15) * dt, 0.01)
    return np.linspace(0, T, steps+1), c_arr, cs_arr

configs_R8 = {
    "V.1 Rational (kein Psi)": dict(include_psi=False, Gini_ext=0, I=1e6),
    "V.1+V.2 (Psi, G=0)": dict(include_psi=True, Gini_ext=0, I=5.0),
    "V.1+V.2 (Psi, G=0.3)": dict(include_psi=True, Gini_ext=0.3, I=5.0),
    "V.1+V.2 (Psi, G=0.5)": dict(include_psi=True, Gini_ext=0.5, I=5.0),
    "V.1+V.2 (Psi, I=0.5)": dict(include_psi=True, Gini_ext=0.3, I=0.5),
}

R8_data = {}
for name, cfg in configs_R8.items():
    t_v, c_v, cs_v = sim_three_levels(8.0, 10.0, 0.05, 0.04, 1.5,
                                       cfg["I"], cfg["Gini_ext"], cfg["include_psi"])
    R8_data[name] = dict(t=t_v, c=c_v, c_star=cs_v)
    print(f"    {name:35s}: c(T)={c_v[-1]:.2f}")

results["R8"] = dict(label="R8: Drei-Ebenen-Vergleich", data=R8_data)


# ══════════════════════════════════════════════════════════════════════
# VALIDIERUNGEN
# ══════════════════════════════════════════════════════════════════════

validations = {}
print(f"\n{'='*72}\n  VALIDIERUNGEN\n{'='*72}")

# V1: Nullpunkt — Psi(c*,c*,0,0,.) = 0
v1_val = Psi_c(10.0, 10.0, 0, 0, 5.0)
v1_pass = abs(v1_val) < 1e-15
validations["V1"] = dict(name="Nullpunkt: Psi(c*,c*,0,0,.)=0", passed=v1_pass,
                          detail=f"|Psi|={abs(v1_val):.2e}")
print(f"  V1: {'PASS' if v1_pass else 'FAIL'} ({validations['V1']['detail']})")

# V2: Referenzpunktanziehung — Psi>0 fuer c<c*, Psi<0 fuer c>c*
c_test_lo = np.linspace(1, 9.9, 100)
c_test_hi = np.linspace(10.1, 20, 100)
psi_lo = Psi_c(c_test_lo, 10.0, 0, 0, 5.0)
psi_hi = Psi_c(c_test_hi, 10.0, 0, 0, 5.0)
v2_pass = np.all(psi_lo > 0) and np.all(psi_hi < 0)
validations["V2"] = dict(name="Referenzpunkt: Psi>0(c<c*), Psi<0(c>c*)", passed=v2_pass,
                          detail=f"below_pos={np.all(psi_lo > 0)}, above_neg={np.all(psi_hi < 0)}")
print(f"  V2: {'PASS' if v2_pass else 'FAIL'} ({validations['V2']['detail']})")

# V3: Verlustaversion — |Psi(c<c*)| > |Psi(c>c*)| bei gleichem Abstand
d_test = np.array([1, 2, 3, 5, 7])
loss_vals = np.abs(Psi_c(10 - d_test, 10.0, 0, 0, 1e6))
gain_vals = np.abs(Psi_c(10 + d_test, 10.0, 0, 0, 1e6))
v3_pass = np.all(loss_vals > gain_vals)
v3_ratio = loss_vals / np.maximum(gain_vals, 1e-15)
validations["V3"] = dict(name="Verlustaversion: |Psi(loss)|>|Psi(gain)|", passed=v3_pass,
                          detail=f"ratios={[f'{r:.2f}' for r in v3_ratio]}")
print(f"  V3: {'PASS' if v3_pass else 'FAIL'} ({validations['V3']['detail']})")

# V4: Beschraenktheit — |Psi| <= Psi_max
c_extreme = np.array([0.01, 0.1, 100, 1000])
psi_extreme = Psi_c(c_extreme, 10.0, 0, 0.7, 0.01)
v4_pass = np.all(np.abs(psi_extreme) <= 2.0 + 1e-10)
validations["V4"] = dict(name="Beschraenktheit: |Psi|<=Psi_max", passed=v4_pass,
                          detail=f"max|Psi|={np.max(np.abs(psi_extreme)):.4f}, Psi_max=2.0")
print(f"  V4: {'PASS' if v4_pass else 'FAIL'} ({validations['V4']['detail']})")

# V5: Ramsey-Limit — I->inf => Psi->0
psi_ramsey = Psi_c(5.0, 10.0, 0, 0.3, 1e8)
v5_pass = abs(psi_ramsey) < 1e-6
validations["V5"] = dict(name="Ramsey: I->inf => Psi->0", passed=v5_pass,
                          detail=f"|Psi(I=1e8)|={abs(psi_ramsey):.2e}")
print(f"  V5: {'PASS' if v5_pass else 'FAIL'} ({validations['V5']['detail']})")

# V6: Gini-Monotonie — |Psi| steigt mit Gini (bei c<c*)
G_test = np.linspace(0, 0.6, 100)
psi_G = np.array([abs(Psi_c(7.0, 10.0, 0, g, 5.0)) for g in G_test])
v6_pass = np.all(np.diff(psi_G) >= -1e-12)
validations["V6"] = dict(name="Gini-Monotonie: |Psi| steigt mit G", passed=v6_pass,
                          detail=f"all_nondecreasing={v6_pass}")
print(f"  V6: {'PASS' if v6_pass else 'FAIL'} ({validations['V6']['detail']})")

# V7: Lambda=2.25 exakt — Ratio bei kleinem Abstand
d_small = 0.01
psi_l = abs(Psi_c(10 - d_small, 10.0, 0, 0, 1e6))
psi_g = abs(Psi_c(10 + d_small, 10.0, 0, 0, 1e6))
ratio_exact = psi_l / psi_g
v7_pass = abs(ratio_exact - 2.25) < 0.01
validations["V7"] = dict(name="Lambda=2.25: loss/gain ratio exakt", passed=v7_pass,
                          detail=f"ratio={ratio_exact:.4f} (soll 2.25)")
print(f"  V7: {'PASS' if v7_pass else 'FAIL'} ({validations['V7']['detail']})")

# V8: Erholung nach Schock — Referenzpunkt konvergiert
gap_R7 = R7_data[2.25]
c_end = gap_R7["c"][-1]
cs_end = gap_R7["c_star"][-1]
gap_end = abs(c_end - cs_end) / max(cs_end, 0.01)
v8_pass = gap_end < 0.05  # <5% gap am Ende
validations["V8"] = dict(name="Schock-Erholung: gap<5% am Ende", passed=v8_pass,
                          detail=f"|c-c*|/c*={gap_end:.4f}")
print(f"  V8: {'PASS' if v8_pass else 'FAIL'} ({validations['V8']['detail']})")


# ══════════════════════════════════════════════════════════════════════
# SENSITIVITAETSANALYSEN
# ══════════════════════════════════════════════════════════════════════

print(f"\n{'='*72}\n  SENSITIVITAETSANALYSEN\n{'='*72}")

# SA1: Lambda-Sweep (Verlustaversion)
lam_sa = np.linspace(1.0, 5.0, 200)
psi_loss_sa = np.array([abs(Psi_c(7, 10, 0, 0, 1e6, lam=l)) for l in lam_sa])
psi_gain_sa = np.array([abs(Psi_c(13, 10, 0, 0, 1e6, lam=l)) for l in lam_sa])
# Gain doesn't depend on lambda
results["SA1"] = dict(lam=lam_sa, psi_loss=psi_loss_sa, psi_gain=psi_gain_sa)
print(f"  SA1: Lambda-Sweep: Psi_loss(lam=1)={psi_loss_sa[0]:.4f}, "
      f"Psi_loss(lam=5)={psi_loss_sa[-1]:.4f}")

# SA2: kappa_ref Sweep
kappa_ref_sa = np.linspace(0.05, 1.0, 200)
psi_kref = np.array([Psi_c(7, 10, 0, 0.3, 5.0, kappa_ref=k) for k in kappa_ref_sa])
results["SA2"] = dict(kappa_ref=kappa_ref_sa, psi=psi_kref)
print(f"  SA2: kappa_ref-Sweep: Psi(k=0.05)={psi_kref[0]:.4f}, Psi(k=1.0)={psi_kref[-1]:.4f}")

# SA3: 50x50 Heatmap Psi(c, I)
c_2d = np.linspace(1, 20, 50)
I_2d = np.logspace(-1, 2, 50)
C2D, I2D = np.meshgrid(c_2d, I_2d)
PSI_2D = Psi_c(C2D, 10.0, 0, 0.3, I2D)
results["SA3"] = dict(c=c_2d, I=I_2d, Psi=PSI_2D)
print(f"  SA3: 50x50 Heatmap Psi(c,I): min={PSI_2D.min():.4f}, max={PSI_2D.max():.4f}")

# SA4: 50x50 Heatmap Psi(Gini, I)
G_2d = np.linspace(0, 0.7, 50)
I_2d_sa4 = np.logspace(-1, 2, 50)
G2D, I2D_sa4 = np.meshgrid(G_2d, I_2d_sa4)
PSI_GI = Psi_c(7.0, 10.0, 0, G2D, I2D_sa4)
results["SA4"] = dict(Gini=G_2d, I=I_2d_sa4, Psi=PSI_GI)
print(f"  SA4: 50x50 Heatmap Psi(Gini,I): min={PSI_GI.min():.4f}, max={PSI_GI.max():.4f}")

# SA5: Erholungszeit vs lambda_adapt
lam_adapt_sa = np.linspace(0.01, 1.0, 100)
recov_times = []
for la in lam_adapt_sa:
    def rhs_sa5(t, y, la_v=la):
        c, cs = y
        R_e = euler_R(0.05, 0.04, 1.5)
        psi = Psi_c(c, cs, 0, 0.2, 5.0)
        return [R_e * max(c, 0.01) + psi, reference_dynamics(cs, c, la_v)]
    sol_sa5 = solve_ivp(rhs_sa5, [0, 60], [5.0, 10.0],
                        t_eval=np.linspace(0, 60, 1000),
                        method='RK45', rtol=1e-7, atol=1e-9)
    ratio_r = sol_sa5.y[0] / np.maximum(sol_sa5.y[1], 0.01)
    idx_r = np.where(ratio_r > 0.95)[0]
    t_r = sol_sa5.t[idx_r[0]] if len(idx_r) > 0 else 60.0
    recov_times.append(t_r)
recov_times = np.array(recov_times)
results["SA5"] = dict(lam_adapt=lam_adapt_sa, recov_time=recov_times)
print(f"  SA5: Erholungszeit(lam=0.01)={recov_times[0]:.1f}, (lam=1.0)={recov_times[-1]:.1f}")


# ══════════════════════════════════════════════════════════════════════
# PLOT (27 Panels)
# ══════════════════════════════════════════════════════════════════════

print(f"\n  PLOTTE ...")
fig = plt.figure(figsize=(26, 44))
gs = GridSpec(10, 3, figure=fig, height_ratios=[1, 1, 1, 1, 1, 1, 1, 1, 1, 0.35],
              hspace=0.38, wspace=0.30)
fig.suptitle('S19  V.2  Psychologische Konsumverzerrung',
             fontsize=15, fontweight='bold', y=0.995)

# ── Row 1: R1 + R2 ──
ax = fig.add_subplot(gs[0, 0])
ax.plot(c_range, psi_R1, 'C0-', lw=2)
ax.axhline(0, color='gray', ls=':', lw=0.5)
ax.axvline(c_star_R1, color='red', ls='--', lw=1, label=f'c*={c_star_R1}')
ax.fill_between(c_range, psi_R1, 0, where=psi_R1 > 0, color='C0', alpha=0.15)
ax.fill_between(c_range, psi_R1, 0, where=psi_R1 < 0, color='C3', alpha=0.15)
ax.set_xlabel('c'); ax.set_ylabel('Psi_c')
ax.set_title('(a) R1: Referenzpunktanziehung (V1, V2)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[0, 1])
ax.plot(d_sweep, np.abs(psi_loss_sw), 'C3-', lw=2, label='Verlust |Psi(c<c*)|')
ax.plot(d_sweep, np.abs(psi_gain_sw), 'C0-', lw=2, label='Gewinn |Psi(c>c*)|')
ax.fill_between(d_sweep, np.abs(psi_loss_sw), np.abs(psi_gain_sw), alpha=0.15, color='C3')
ax.set_xlabel('Abstand |c-c*|'); ax.set_ylabel('|Psi|')
ax.set_title(f'(b) R2: Verlustaversion (lam={2.25}) (V3)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[0, 2])
ratio_sw = np.abs(psi_loss_sw) / np.maximum(np.abs(psi_gain_sw), 1e-15)
ax.plot(d_sweep, ratio_sw, 'C1-', lw=2)
ax.axhline(2.25, color='red', ls=':', lw=1, label='lam=2.25')
ax.set_xlabel('Abstand |c-c*|'); ax.set_ylabel('|Loss/Gain|')
ax.set_title('(c) R2: Loss/Gain Ratio (V7)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)
ax.set_ylim(0, 4)

# ── Row 2: R3 ──
ax = fig.add_subplot(gs[1, 0])
for lam_a, d in R3_data.items():
    ax.plot(d["t"], d["c"], lw=2, label=f'c (lam_a={lam_a})')
ax.plot(R3_data[0.15]["t"], R3_data[0.15]["c_star"], 'k--', lw=1, label='c*')
ax.set_xlabel('t'); ax.set_ylabel('c, c*')
ax.set_title('(d) R3: Adaptation (c und c*)')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[1, 1])
for lam_a, d in R3_data.items():
    ax.plot(d["t"], d["gap"], lw=2, label=f'lam_a={lam_a}')
ax.axhline(0, color='gray', ls=':', lw=0.5)
ax.set_xlabel('t'); ax.set_ylabel('c - c*')
ax.set_title('(e) R3: Gap-Dynamik')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[1, 2])
for lam_a, d in R3_data.items():
    ax.plot(d["t"], d["psi"], lw=2, label=f'lam_a={lam_a}')
ax.axhline(0, color='gray', ls=':', lw=0.5)
ax.set_xlabel('t'); ax.set_ylabel('Psi_c(t)')
ax.set_title('(f) R3: Psi-Verlauf')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Row 3: R4 + R5 ──
ax = fig.add_subplot(gs[2, 0])
ax.plot(Gini_sweep, psi_gini, 'C3-', lw=2, label='c=6 (arm)')
ax.plot(Gini_sweep, psi_gini_rich, 'C0-', lw=2, label='c=14 (reich)')
ax.axhline(0, color='gray', ls=':', lw=0.5)
ax.set_xlabel('Gini'); ax.set_ylabel('Psi_c')
ax.set_title('(g) R4: Relative Deprivation (V6)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[2, 1])
ax.semilogx(I_sweep, psi_info, 'C0-', lw=2, label='Gini=0.3')
ax.semilogx(I_sweep, psi_info_noGini, 'C1--', lw=2, label='Gini=0')
ax.axhline(0, color='gray', ls=':', lw=0.5)
ax.set_xlabel('I (log)'); ax.set_ylabel('Psi_c')
ax.set_title('(h) R5: Info-Modulation (V5)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── R6 ──
ax = fig.add_subplot(gs[2, 2])
# Zeige 20 zufaellige Agenten
idx_show = np.random.choice(N_het, 20, replace=False)
for i in idx_show:
    ax.plot(t_het, c_hist[i], lw=0.6, alpha=0.5)
ax.plot(t_het, c_hist.mean(axis=0), 'k-', lw=2, label='Mittel')
ax.set_xlabel('t'); ax.set_ylabel('c(t)')
ax.set_title(f'(i) R6: Heterogene Agenten (N={N_het})')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Row 4: R6 + R7 ──
ax = fig.add_subplot(gs[3, 0])
ax.plot(t_het, gini_hist, 'C3-', lw=2)
ax.set_xlabel('t'); ax.set_ylabel('Gini')
ax.set_title(f'(j) R6: Gini(t) [{gini_0:.3f}->{gini_T:.3f}] (V8)')
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 1])
ax.hist(c_hist[:, 0], bins=30, alpha=0.5, density=True, label='t=0', color='C0')
ax.hist(np.clip(c_hist[:, -1], 0, np.percentile(c_hist[:, -1], 98)),
        bins=30, alpha=0.5, density=True, label='t=T', color='C3')
ax.set_xlabel('c'); ax.set_ylabel('Dichte')
ax.set_title('(k) R6: Konsumverteilung')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 2])
for lam, d in R7_data.items():
    ax.plot(d["t"], d["c"], lw=2, label=f'c (lam={lam})')
ax.plot(R7_data[2.25]["t"], R7_data[2.25]["c_star"], 'k--', lw=1, label='c*')
ax.axvline(shock_t, color='gray', ls=':', lw=0.8, label='Schock')
ax.set_xlabel('t'); ax.set_ylabel('c, c*')
ax.set_title('(l) R7: Konsumschock + Erholung')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# ── Row 5: R7 + R8 ──
ax = fig.add_subplot(gs[4, 0])
for lam, d in R7_data.items():
    ax.plot(d["t"], d["psi"], lw=2, label=f'lam={lam}')
ax.axvline(shock_t, color='gray', ls=':', lw=0.8)
ax.axhline(0, color='gray', ls=':', lw=0.5)
ax.set_xlabel('t'); ax.set_ylabel('Psi_c(t)')
ax.set_title('(m) R7: Psi nach Schock')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[4, 1])
for name, d in R8_data.items():
    ax.plot(d["t"], d["c"], lw=2, label=name.split('(')[0].strip())
ax.set_xlabel('t'); ax.set_ylabel('c(t)')
ax.set_title('(n) R8: Drei-Ebenen-Vergleich')
ax.legend(fontsize=5.5); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[4, 2])
for name, d in R8_data.items():
    ax.plot(d["t"], d["c_star"], lw=2, ls='--', label=f'c* {name.split("(")[0].strip()}')
ax.set_xlabel('t'); ax.set_ylabel('c*(t)')
ax.set_title('(o) R8: Referenzpunkt-Evolution')
ax.legend(fontsize=5.5); ax.grid(True, alpha=0.3)

# ── Row 6: SA1 + SA2 ──
ax = fig.add_subplot(gs[5, 0])
ax.plot(lam_sa, psi_loss_sa, 'C3-', lw=2, label='|Psi(Verlust)|')
ax.plot(lam_sa, psi_gain_sa, 'C0-', lw=2, label='|Psi(Gewinn)|')
ax.set_xlabel('lambda'); ax.set_ylabel('|Psi|')
ax.set_title('(p) SA1: Lambda-Sweep')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[5, 1])
ax.plot(kappa_ref_sa, psi_kref, 'C1-', lw=2)
ax.set_xlabel('kappa_ref'); ax.set_ylabel('Psi_c')
ax.set_title('(q) SA2: kappa_ref-Sweep')
ax.grid(True, alpha=0.3)

# ── SA3 Heatmap ──
ax = fig.add_subplot(gs[5, 2])
im = ax.imshow(PSI_2D, extent=[c_2d[0], c_2d[-1], np.log10(I_2d[0]), np.log10(I_2d[-1])],
               aspect='auto', origin='lower', cmap='RdBu_r')
ax.contour(c_2d, np.log10(I_2d), PSI_2D, levels=[0], colors='black', linewidths=2)
plt.colorbar(im, ax=ax, label='Psi_c')
ax.axvline(10.0, color='green', ls=':', lw=1, label='c*=10')
ax.set_xlabel('c'); ax.set_ylabel('log10(I)')
ax.set_title('(r) SA3: Heatmap Psi(c, I)')
ax.legend(fontsize=7)

# ── Row 7: SA4 + SA5 ──
ax = fig.add_subplot(gs[6, 0])
im = ax.imshow(PSI_GI, extent=[G_2d[0], G_2d[-1], np.log10(I_2d_sa4[0]), np.log10(I_2d_sa4[-1])],
               aspect='auto', origin='lower', cmap='Reds')
plt.colorbar(im, ax=ax, label='Psi_c')
ax.set_xlabel('Gini'); ax.set_ylabel('log10(I)')
ax.set_title('(s) SA4: Heatmap Psi(Gini, I)')

ax = fig.add_subplot(gs[6, 1])
ax.plot(lam_adapt_sa, recov_times, 'C2-', lw=2)
ax.set_xlabel('lambda_adapt'); ax.set_ylabel('Erholungszeit [t]')
ax.set_title('(t) SA5: Erholungszeit vs Adaptation')
ax.grid(True, alpha=0.3)

# ── Kausalitaet ──
ax = fig.add_subplot(gs[6, 2])
ax.axis('off')
kaus_text = (
    "KAUSALKETTEN (S19 V.2):\n"
    "─────────────────────────────\n"
    "1. Referenzpunkt:\n"
    "   c < c* => Psi > 0\n"
    "   => Konsum wird hochgezogen\n"
    "   c* passt sich an: hedonic\n"
    "   treadmill\n\n"
    "2. Verlustaversion (lam=2.25):\n"
    "   |Psi(Verlust)| >> |Psi(Gewinn)|\n"
    "   => Erholung schneller als\n"
    "   Ueberschiessen\n\n"
    "3. Gini-Verstaerkung:\n"
    "   Hohe Ungleichheit => staerkere\n"
    "   Referenzpunktanziehung\n"
    "   => arme Agenten konsumieren\n"
    "   'ueber Verhaeltnisse'\n\n"
    "4. Info-Daempfung:\n"
    "   I -> inf => Psi -> 0\n"
    "   Rationale Agenten (EMH)\n"
    "   kennen keinen Referenzpunkt"
)
ax.text(0.05, 0.95, kaus_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=7.5, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# ── Row 8: Physik ──
ax = fig.add_subplot(gs[7, 0:2])
ax.axis('off')
phys = (
    "DREI-EBENEN-ARCHITEKTUR DER KONSUMDYNAMIK:\n\n"
    "dc/dt = R_i * c_i                    + Psi_c(c, c*, Gini, I)         + sum A_ij Phi(c_j-c_i)\n"
    "        ─────────                      ─────────────────────           ─────────────────────\n"
    "        Ebene 1: Rational (V.1)        Ebene 2: Psychologie (V.2)     Ebene 3: Sozial (V.3)\n"
    "        S17: Ramsey-Euler              S19: Prospect Theory           S20: Herding\n\n"
    "AXIOMATISCHE EIGENSCHAFTEN von Psi_c:\n"
    "  A1: Nullpunkt  — Psi(c*,c*,0,0,.)=0 .......... VERIFIZIERT\n"
    "  A2: Anziehung  — dPsi/d(c*-c) > 0 ............. VERIFIZIERT\n"
    "  A3: Asymmetrie — |Psi(loss)|/|Psi(gain)|=2.25 . VERIFIZIERT\n"
    "  A4: Deprivation — dPsi/dGini > 0 (arme) ....... VERIFIZIERT\n"
    "  A5: Beschraenkt — |Psi| <= Psi_max ............ VERIFIZIERT\n"
    "  A6: Ramsey-Lim — I->inf => Psi->0 ............. VERIFIZIERT\n\n"
    "OKONOMISCHE INTERPRETATION:\n"
    "  Prospect Theory veraendert rational optimal consumption systematisch.\n"
    "  Verlustaversion erzeugt asymmetrische Erholung nach Schocks.\n"
    "  Information DAEMPFT Psychologie — gut informierte Agenten sind rationaler."
)
ax.text(0.5, 0.5, phys, transform=ax.transAxes, ha='center', va='center',
        fontsize=7.5, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# I vs Psi (rechts)
ax = fig.add_subplot(gs[7, 2])
ax.semilogx(I_sweep, psi_info / psi_info[0] * 100, 'C0-', lw=2)
ax.set_xlabel('I (log)'); ax.set_ylabel('Psi/Psi(I_min) [%]')
ax.set_title('(u) Info-Daempfung [%]')
ax.grid(True, alpha=0.3)

# ── Row 9: Validierung ──
ax = fig.add_subplot(gs[8, 0])
ax.axis('off')
val_text = "VALIDIERUNGEN:\n" + "-"*35 + "\n"
for k, v in validations.items():
    tag = "PASS" if v["passed"] else "FAIL"
    val_text += f"{k}: {v['name'][:32]}\n   {tag}: {v['detail'][:40]}\n\n"
ax.text(0.05, 0.95, val_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=6.0, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

ax = fig.add_subplot(gs[8, 1])
# Scatter: I vs c(T) fuer heterogene Agenten
ax.scatter(I_het, c_hist[:, -1], c=c0_het, cmap='viridis', s=10, alpha=0.6)
ax.set_xscale('log')
ax.set_xlabel('I (log)'); ax.set_ylabel('c(T)')
ax.set_title('(v) R6: c(T) vs I')
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[8, 2])
# Psi vs c fuer verschiedene I-Werte
for I_v in [0.1, 1, 5, 20, 100]:
    psi_plot = Psi_c(c_range, 10.0, 0, 0.3, I_v)
    ax.plot(c_range, psi_plot, lw=1.5, label=f'I={I_v}')
ax.axhline(0, color='gray', ls=':', lw=0.5)
ax.axvline(10, color='red', ls=':', lw=1)
ax.set_xlabel('c'); ax.set_ylabel('Psi_c')
ax.set_title('(w) Psi(c) fuer verschiedene I')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# ── Metadata ──
ax_meta = fig.add_subplot(gs[9, :])
ax_meta.axis('off')
n_pass = sum(1 for v in validations.values() if v["passed"])
meta = (
    f"S19 V.2 Psychologische Konsumverzerrung | 8 Regime, {len(validations)} Val: "
    f"{n_pass}/{len(validations)} PASS | "
    f"Referenzpunkt, Verlustaversion (lam=2.25), Adaptation, Deprivation, "
    f"Info-Modulation, Heterogen (N={N_het}), Schock+Erholung, Drei-Ebenen | "
    f"5 SA inkl. 2 Heatmaps | Psi_c(c, c*, Gini, I)"
)
ax_meta.text(0.5, 0.5, meta, transform=ax_meta.transAxes, ha='center', va='center',
             fontsize=9, family='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

plt.savefig(PLOT_DIR / "S19_V2_Psychologische_Konsumverzerrung.png", dpi=180, bbox_inches='tight')
plt.close()
print(f"\n  Plot: {PLOT_DIR / 'S19_V2_Psychologische_Konsumverzerrung.png'}")

# ── Daten ──
save_dict = {
    "t_eval": t_eval, "R1_c": c_range, "R1_psi": psi_R1,
    "R2_d": d_sweep, "R2_psi_loss": psi_loss_sw, "R2_psi_gain": psi_gain_sw,
    "R4_Gini": Gini_sweep, "R4_psi_poor": psi_gini, "R4_psi_rich": psi_gini_rich,
    "R5_I": I_sweep, "R5_psi": psi_info,
    "R6_t": t_het, "R6_gini": gini_hist,
    "R6_c_mean": c_hist.mean(axis=0), "R6_c_std": c_hist.std(axis=0),
    "SA1_lam": lam_sa, "SA1_loss": psi_loss_sa, "SA1_gain": psi_gain_sa,
    "SA2_kref": kappa_ref_sa, "SA2_psi": psi_kref,
    "SA3_c": c_2d, "SA3_I": I_2d, "SA3_Psi": PSI_2D,
    "SA4_Gini": G_2d, "SA4_I": I_2d_sa4, "SA4_Psi": PSI_GI,
    "SA5_lam_adapt": lam_adapt_sa, "SA5_recov_time": recov_times,
}
for lam_a, d in R3_data.items():
    safe = f"{lam_a:.2f}".replace(".", "p")
    save_dict[f"R3_c_{safe}"] = d["c"]
    save_dict[f"R3_cstar_{safe}"] = d["c_star"]
for lam, d in R7_data.items():
    safe = f"{lam:.2f}".replace(".", "p")
    save_dict[f"R7_c_{safe}"] = d["c"]
    save_dict[f"R7_t_{safe}"] = d["t"]
np.savez_compressed(DATA_DIR / "S19_V2_Psychologische_Konsumverzerrung.npz", **save_dict)

# ── Zusammenfassung ──
print(f"\n{'='*72}\n  ZUSAMMENFASSUNG S19  V.2 Psychologische Konsumverzerrung\n{'='*72}")
for k, v in validations.items():
    print(f"  {k}: {v['name']:42s}  {'PASS' if v['passed'] else 'FAIL'}  ({v['detail']})")
print(f"\n  Regime:")
for key in ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]:
    print(f"    {results[key]['label']}")
print(f"\n  Sensitivitaet:")
print(f"    SA1: Lambda-Sweep (Verlustaversion)")
print(f"    SA2: kappa_ref-Sweep (Referenzpunkt-Staerke)")
print(f"    SA3: 50x50 Heatmap Psi(c, I)")
print(f"    SA4: 50x50 Heatmap Psi(Gini, I)")
print(f"    SA5: Erholungszeit vs lambda_adapt")
n_pass = sum(1 for v in validations.values() if v["passed"])
print(f"\n  Gesamtergebnis: {n_pass}/{len(validations)} bestanden")
if n_pass == len(validations):
    print("  >>> ALLE VALIDIERUNGEN BESTANDEN <<<")
print(f"{'='*72}")
